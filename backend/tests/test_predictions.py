"""
Tests for Prediction Endpoints, Input Validation, and Schema Verification.
"""
import pytest

def test_predict_unauthenticated(client, sample_prediction_payload):
    res = client.post("/api/predict", json=sample_prediction_payload)
    assert res.status_code == 401
    assert res.get_json()["error_code"] == "UNAUTHORIZED"

def test_predict_invalid_schema_missing_fields(auth_client):
    payload = {"age": 50, "sex": 1}  # Missing other required features
    res = auth_client.post("/api/predict", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error_code"] == "VALIDATION_ERROR"

def test_predict_out_of_bounds(auth_client, sample_prediction_payload):
    invalid_payload = sample_prediction_payload.copy()
    invalid_payload["age"] = 150  # Out of valid bounds
    res = auth_client.post("/api/predict", json=invalid_payload)
    assert res.status_code == 400
    assert res.get_json()["error_code"] == "VALIDATION_ERROR"

def test_predict_invalid_category(auth_client, sample_prediction_payload):
    invalid_payload = sample_prediction_payload.copy()
    invalid_payload["sex"] = 9  # Only 0 or 1 allowed
    res = auth_client.post("/api/predict", json=invalid_payload)
    assert res.status_code == 400
    assert res.get_json()["error_code"] == "VALIDATION_ERROR"

def test_predict_success_and_persistence(auth_client, sample_prediction_payload):
    res = auth_client.post("/api/predict", json=sample_prediction_payload)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "prediction" in data
    assert data["prediction"] in (0, 1)
    assert "risk_level" in data
    assert "probability" in data
    assert data["id"] is not None

    # Verify history now contains 1 record
    hist_res = auth_client.get("/api/history")
    assert hist_res.status_code == 200
    hist_items = hist_res.get_json()["data"]["items"]
    assert len(hist_items) == 1
    assert hist_items[0]["id"] == data["id"]

def test_predict_with_patient_demographics(auth_client, sample_prediction_payload):
    payload = sample_prediction_payload.copy()
    payload["patient_name"] = "Eleanor Vance"
    payload["patient_phone"] = "+1 (555) 019-2834"
    payload["patient_address"] = "742 Evergreen Terrace, Springfield"

    res = auth_client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["patient_name"] == "Eleanor Vance"
    assert data["patient_phone"] == "+1 (555) 019-2834"
    assert data["patient_address"] == "742 Evergreen Terrace, Springfield"

    # Verify history detail preserves patient details
    hist_res = auth_client.get(f"/api/history/{data['id']}")
    assert hist_res.status_code == 200
    item = hist_res.get_json()["data"]["prediction"]
    assert item["patient_name"] == "Eleanor Vance"
    assert item["patient_phone"] == "+1 (555) 019-2834"
    assert item["patient_address"] == "742 Evergreen Terrace, Springfield"
