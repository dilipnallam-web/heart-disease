"""
Prediction Engine for Heart Disease Stacking Ensemble Pipeline.
Loads saved joblib artifact, validates raw input features against schema,
and executes inference with estimated probability and confidence calibration.
"""
import os
import joblib
import pandas as pd
import numpy as np

from .data_loader import (
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURE_METADATA
)

class ModelNotLoadedError(Exception):
    """Raised when trained model artifact is missing or corrupt."""
    pass

class ValidationError(Exception):
    """Raised when feature inputs violate bounds, types, or missing keys."""
    pass

class HeartDiseasePredictor:
    """Encapsulates model artifact loading and safe inference."""
    
    def __init__(self, artifact_path=None):
        self.artifact_path = artifact_path or self._default_artifact_path()
        self.pipeline = None
        self.metadata = {}
        self.is_loaded = False
        self._load_artifact()

    def _default_artifact_path(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(base_dir, "ml", "artifacts", "stacking_heart_model.joblib")

    def _load_artifact(self):
        if os.path.exists(self.artifact_path):
            try:
                bundle = joblib.load(self.artifact_path)
                if isinstance(bundle, dict) and "pipeline" in bundle:
                    self.pipeline = bundle["pipeline"]
                    self.metadata = bundle.get("metadata", {})
                else:
                    self.pipeline = bundle
                    self.metadata = {"model_name": "StackingClassifier", "version": "1.0.0"}

                # Force single-threaded execution (n_jobs=1) to prevent multiprocessing/loky crashes in cloud containers
                try:
                    if hasattr(self.pipeline, "named_steps") and "classifier" in self.pipeline.named_steps:
                        clf = self.pipeline.named_steps["classifier"]
                        if hasattr(clf, "n_jobs"):
                            clf.n_jobs = 1
                    elif hasattr(self.pipeline, "n_jobs"):
                        self.pipeline.n_jobs = 1
                except Exception:
                    pass

                self.is_loaded = True
            except Exception as e:
                self.is_loaded = False
                self.pipeline = None
                print(f"[HeartDiseasePredictor] Warning: Failed to load artifact: {e}")
        else:
            self.is_loaded = False
            self.pipeline = None

    def validate_inputs(self, raw_input_dict):
        """
        Validates feature presence, numeric ranges, and categorical values.
        Returns a cleaned, properly typed dictionary.
        """
        if not isinstance(raw_input_dict, dict):
            raise ValidationError("Input payload must be a JSON object / dictionary.")

        cleaned = {}
        missing_fields = []

        for feat in FEATURE_COLUMNS:
            if feat not in raw_input_dict or raw_input_dict[feat] is None or raw_input_dict[feat] == "":
                missing_fields.append(feat)

        if missing_fields:
            raise ValidationError(f"Missing required medical features: {', '.join(missing_fields)}")

        for feat, meta in FEATURE_METADATA.items():
            val = raw_input_dict[feat]
            feat_type = meta["type"]

            if feat_type == "numeric":
                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    raise ValidationError(f"Feature '{feat}' must be a valid number. Received: {val}")

                min_val = meta.get("min")
                max_val = meta.get("max")
                if min_val is not None and num_val < min_val:
                    raise ValidationError(f"Feature '{feat}' value {num_val} is below acceptable minimum ({min_val}).")
                if max_val is not None and num_val > max_val:
                    raise ValidationError(f"Feature '{feat}' value {num_val} exceeds acceptable maximum ({max_val}).")
                
                cleaned[feat] = num_val

            elif feat_type == "categorical":
                try:
                    cat_val = int(val)
                except (ValueError, TypeError):
                    raise ValidationError(f"Feature '{feat}' must be an integer code. Received: {val}")

                allowed_options = meta.get("options", {})
                if allowed_options and cat_val not in allowed_options:
                    allowed_keys = list(allowed_options.keys())
                    raise ValidationError(
                        f"Feature '{feat}' value {cat_val} is invalid. Allowed options: {allowed_keys}"
                    )
                
                cleaned[feat] = cat_val

        return cleaned

    def predict(self, raw_input_dict):
        """
        Executes prediction pipeline on validated inputs.
        Returns dictionary with predicted class, label, probability, risk level, and metadata.
        """
        if not self.is_loaded or self.pipeline is None:
            # Try reloading once in case artifact was recently written
            self._load_artifact()
            if not self.is_loaded or self.pipeline is None:
                raise ModelNotLoadedError(
                    "Trained model artifact not available. Please run `python scripts/train_model.py`."
                )

        validated_data = self.validate_inputs(raw_input_dict)
        # Prepare single-row DataFrame with exact feature column order and matching float64 types
        df_row = pd.DataFrame([validated_data])[FEATURE_COLUMNS].astype(float)

        # Predict class
        pred_class = int(self.pipeline.predict(df_row)[0])

        # Predict probability if supported
        prob_heart_disease = None
        prob_no_heart_disease = None
        confidence = None

        if hasattr(self.pipeline, "predict_proba"):
            try:
                probabilities = self.pipeline.predict_proba(df_row)[0]
                prob_no_heart_disease = round(float(probabilities[0]), 4)
                prob_heart_disease = round(float(probabilities[1]), 4)
                confidence = prob_heart_disease if pred_class == 1 else prob_no_heart_disease
            except Exception:
                prob_heart_disease = None

        # Determine clinical risk tier based on probability
        if prob_heart_disease is not None:
            if prob_heart_disease < 0.30:
                risk_level = "Low Risk"
                risk_badge_class = "risk-low"
            elif prob_heart_disease < 0.65:
                risk_level = "Moderate Risk"
                risk_badge_class = "risk-moderate"
            else:
                risk_level = "Elevated Risk"
                risk_badge_class = "risk-high"
        else:
            risk_level = "Elevated Risk" if pred_class == 1 else "Low Risk"
            risk_badge_class = "risk-high" if pred_class == 1 else "risk-low"

        class_labels = {
            0: "No Heart Disease Detected",
            1: "Presence of Heart Disease Indicator"
        }

        return {
            "prediction": pred_class,
            "prediction_label": class_labels.get(pred_class, f"Class {pred_class}"),
            "probability": prob_heart_disease,
            "probability_breakdown": {
                "no_disease": prob_no_heart_disease,
                "disease": prob_heart_disease
            },
            "confidence": confidence,
            "risk_level": risk_level,
            "risk_badge_class": risk_badge_class,
            "model_version": self.metadata.get("version", "1.0.0"),
            "model_architecture": self.metadata.get("model_name", "StackingClassifier"),
            "validated_features": validated_data,
            "disclaimer": (
                "This prediction is an educational and research machine learning estimate. "
                "It does NOT constitute medical diagnosis or medical advice. Consult a licensed "
                "cardiologist or healthcare provider for any health concerns."
            )
        }

# Global singleton predictor
_predictor_instance = None

def get_predictor(artifact_path=None):
    global _predictor_instance
    if _predictor_instance is None or artifact_path is not None:
        _predictor_instance = HeartDiseasePredictor(artifact_path)
    return _predictor_instance
