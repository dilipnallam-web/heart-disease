"""
Prediction Routes Blueprint.
POST /api/predict
"""
from flask import Blueprint, request, g
from ..middleware.auth_middleware import login_required
from ..middleware.rate_limiter import predict_rate_limiter
from ..services.prediction_service import PredictionService
from ..utils.responses import success_response, error_response

prediction_bp = Blueprint("prediction", __name__)

@prediction_bp.route("/predict", methods=["POST"])
@login_required
@predict_rate_limiter.limit()
def predict():
    payload = request.get_json(silent=True)
    if payload is None:
        return error_response(
            message="Invalid or missing JSON payload in request body.",
            error_code="INVALID_PAYLOAD",
            status_code=400
        )

    res = PredictionService.run_prediction(g.current_user, payload)
    if not res.get("success"):
        return error_response(
            message=res.get("message"),
            error_code=res.get("code", "PREDICTION_FAILED"),
            details=res.get("details"),
            status_code=res.get("status", 400)
        )

    return success_response(
        data=res.get("data"),
        message=res.get("message"),
        status_code=200
    )
