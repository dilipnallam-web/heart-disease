"""
Prediction Document Model and Serialization.
Stores user-associated inference records with validated features, probabilities, and model version.
"""
from datetime import datetime, timezone
from bson import ObjectId

class Prediction:
    """Represents a saved patient prediction record."""

    @staticmethod
    def create_document(user_id, validated_features: dict, prediction_result: dict, patient_info: dict = None) -> dict:
        """Constructs a MongoDB prediction document."""
        patient_info = patient_info or {}
        return {
            "user_id": str(user_id),
            "patient_name": str(patient_info.get("name") or "Anonymous Patient").strip(),
            "patient_phone": str(patient_info.get("phone") or "").strip(),
            "patient_address": str(patient_info.get("address") or "").strip(),
            "validated_features": validated_features,
            "prediction": prediction_result["prediction"],
            "prediction_label": prediction_result["prediction_label"],
            "probability": prediction_result.get("probability"),
            "probability_breakdown": prediction_result.get("probability_breakdown", {}),
            "risk_level": prediction_result.get("risk_level", "Unknown"),
            "model_version": prediction_result.get("model_version", "1.0.0"),
            "created_at": datetime.now(timezone.utc)
        }

    @staticmethod
    def to_safe_dict(doc: dict) -> dict:
        """Serializes MongoDB prediction record into JSON-serializable dictionary."""
        if not doc:
            return {}
        
        pred_id = str(doc["_id"]) if "_id" in doc else None
        created_at = doc.get("created_at")

        return {
            "id": pred_id,
            "user_id": str(doc.get("user_id")),
            "patient_name": doc.get("patient_name", "Anonymous Patient"),
            "patient_phone": doc.get("patient_phone", ""),
            "patient_address": doc.get("patient_address", ""),
            "validated_features": doc.get("validated_features", {}),
            "prediction": doc.get("prediction"),
            "prediction_label": doc.get("prediction_label"),
            "probability": doc.get("probability"),
            "probability_breakdown": doc.get("probability_breakdown", {}),
            "risk_level": doc.get("risk_level"),
            "model_version": doc.get("model_version"),
            "created_at": created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
        }
