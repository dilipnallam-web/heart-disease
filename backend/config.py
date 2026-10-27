"""
Configuration classes for Heart Disease Prediction Flask Application.
Supports Development, Testing, and Production environments via environment variables.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_heart_prediction_default_key_2026")
    
    # Session & Cookie Security
    SESSION_COOKIE_NAME = "heart_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # CORS
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

    # MongoDB Atlas
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "heart_disease_db")
    MONGODB_CONNECT_TIMEOUT_MS = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", 5000))

    # Machine Learning Artifacts
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    @staticmethod
    def _resolve_artifact(env_key, default_rel_path):
        val = os.getenv(env_key)
        base = os.path.abspath(os.path.dirname(__file__))
        if not val:
            return os.path.join(base, default_rel_path)
        if os.path.isabs(val):
            return val
        # Check relative to backend directory
        cand1 = os.path.join(base, val)
        if os.path.exists(cand1):
            return cand1
        # Check relative to repo root
        cand2 = os.path.join(os.path.dirname(base), val)
        if os.path.exists(cand2):
            return cand2
        return cand1

    MODEL_ARTIFACT_PATH = _resolve_artifact.__func__("MODEL_ARTIFACT_PATH", os.path.join("ml", "artifacts", "stacking_heart_model.joblib"))
    METRICS_ARTIFACT_PATH = _resolve_artifact.__func__("METRICS_ARTIFACT_PATH", os.path.join("ml", "artifacts", "model_metrics.json"))
    COMPARISON_ARTIFACT_PATH = _resolve_artifact.__func__("COMPARISON_ARTIFACT_PATH", os.path.join("ml", "artifacts", "model_comparison.json"))

    # App Settings
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    MONGODB_DB_NAME = "heart_disease_test_db"
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = "test_environment_secret_key"

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}

def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)
