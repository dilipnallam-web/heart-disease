"""
MongoDB Database Indexes Specification and Initialization.
Ensures unique constraints on email, and fast querying on user_id, timestamps.
"""
import logging
from pymongo import ASCENDING, DESCENDING

logger = logging.getLogger(__name__)

def create_database_indexes(db):
    """
    Creates necessary indexes on 'users', 'predictions', and 'model_metrics' collections.
    """
    results = {}
    try:
        # Users Collection: Unique normalized email, created_at index
        email_idx = db.users.create_index([("email", ASCENDING)], unique=True)
        user_created_idx = db.users.create_index([("created_at", DESCENDING)])
        results["users"] = [email_idx, user_created_idx]

        # Predictions Collection: Compound index (user_id, created_at) and (user_id, patient_name)
        pred_user_idx = db.predictions.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        pred_created_idx = db.predictions.create_index([("created_at", DESCENDING)])
        pred_patient_idx = db.predictions.create_index([("user_id", ASCENDING), ("patient_name", ASCENDING)])
        results["predictions"] = [pred_user_idx, pred_created_idx, pred_patient_idx]

        # Model Metrics Collection: model_version and timestamp
        metrics_ver_idx = db.model_metrics.create_index([("model_version", ASCENDING)])
        results["model_metrics"] = [metrics_ver_idx]

        logger.info(f"[Database Indexes] Successfully ensured indexes: {results}")
    except Exception as e:
        logger.warning(f"[Database Indexes] Index creation warning: {e}")
        results["error"] = str(e)

    return results
