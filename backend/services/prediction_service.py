"""
Prediction Service.
Orchestrates medical feature validation, stacking ensemble inference,
and persistence to MongoDB predictions collection.
"""
import logging
from ..database.mongodb import get_db
from ..models.prediction import Prediction
from ..ml.predict_model import get_predictor, ModelNotLoadedError, ValidationError

logger = logging.getLogger(__name__)

class PredictionService:

    @staticmethod
    def run_prediction(user_dict: dict, input_payload: dict):
        """
        Validates medical inputs, runs model inference, stores record in DB,
        and returns prediction result.
        """
        predictor = get_predictor()

        try:
            # Run inference & schema validation
            prediction_result = predictor.predict(input_payload)
        except ValidationError as e:
            return {
                "success": False,
                "message": str(e),
                "code": "VALIDATION_ERROR",
                "status": 400
            }
        except ModelNotLoadedError as e:
            return {
                "success": False,
                "message": (
                    "The machine learning model is currently unavailable on the server. "
                    "Please ensure the model training script (`python scripts/train_model.py`) has completed."
                ),
                "code": "MODEL_UNAVAILABLE",
                "status": 503
            }
        except Exception as e:
            logger.exception(f"Unexpected error during inference execution: {e}")
            return {
                "success": False,
                "message": f"Inference calculation error: {str(e)}",
                "code": "INFERENCE_ERROR",
                "details": str(e),
                "status": 500
            }

        # Extract patient demographic information
        patient_name = str(input_payload.get("patient_name") or "").strip()
        patient_phone = str(input_payload.get("patient_phone") or "").strip()
        patient_address = str(input_payload.get("patient_address") or "").strip()

        patient_info = {
            "name": patient_name if patient_name else "Anonymous Patient",
            "phone": patient_phone,
            "address": patient_address
        }

        # Save prediction record to MongoDB for the authenticated user
        db = get_db()
        user_id = str(user_dict["_id"])
        
        pred_doc = Prediction.create_document(
            user_id=user_id,
            validated_features=prediction_result["validated_features"],
            prediction_result=prediction_result,
            patient_info=patient_info
        )

        try:
            insert_res = db.predictions.insert_one(pred_doc)
            pred_doc["_id"] = insert_res.inserted_id
            saved_id = str(insert_res.inserted_id)
        except Exception as e:
            logger.warning(f"Failed to persist prediction record to database: {e}")
            saved_id = None

        response_data = {
            "id": saved_id,
            "patient_name": pred_doc["patient_name"],
            "patient_phone": pred_doc["patient_phone"],
            "patient_address": pred_doc["patient_address"],
            "prediction": prediction_result["prediction"],
            "prediction_label": prediction_result["prediction_label"],
            "probability": prediction_result.get("probability"),
            "probability_breakdown": prediction_result.get("probability_breakdown"),
            "confidence": prediction_result.get("confidence"),
            "risk_level": prediction_result["risk_level"],
            "risk_badge_class": prediction_result["risk_badge_class"],
            "model_version": prediction_result["model_version"],
            "model_architecture": prediction_result["model_architecture"],
            "validated_features": prediction_result["validated_features"],
            "created_at": pred_doc["created_at"].isoformat(),
            "disclaimer": prediction_result["disclaimer"]
        }

        return {
            "success": True,
            "message": "Prediction generated successfully.",
            "data": response_data,
            "status": 200
        }
