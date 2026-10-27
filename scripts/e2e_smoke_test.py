import urllib.request
import json
import http.cookiejar

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# 1. Check index.html content
req = urllib.request.Request("http://127.0.0.1:5000/")
with opener.open(req) as resp:
    html = resp.read().decode("utf-8")
    assert "About & Methodology" not in html, "About & Methodology found in index.html!"
    print("[+] Confirmed: About & Methodology removed from index.html")

# 2. Check predict.html content
req = urllib.request.Request("http://127.0.0.1:5000/predict.html")
with opener.open(req) as resp:
    html = resp.read().decode("utf-8")
    assert "About & Methodology" not in html, "About & Methodology found in predict.html!"
    assert 'name="patient_name"' in html, "patient_name input not found!"
    assert 'name="patient_phone"' in html, "patient_phone input not found!"
    assert 'name="patient_address"' in html, "patient_address input not found!"
    print("[+] Confirmed: Patient Name, Phone, and Address inputs present in predict.html")

# 3. Register a test doctor
reg_data = json.dumps({
    "name": "Dr. Jane Foster",
    "email": "jane.foster@cardiopredict.org",
    "password": "Password123!",
    "confirm_password": "Password123!"
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:5000/api/auth/register",
    data=reg_data,
    headers={"Content-Type": "application/json"}
)
try:
    with opener.open(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("[+] Registered new doctor user:", res.get("data", {}).get("user", {}).get("email"))
except Exception as e:
    # If already registered, login
    login_data = json.dumps({
        "email": "jane.foster@cardiopredict.org",
        "password": "Password123!"
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    with opener.open(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("[+] Logged in existing doctor user")

# 4. Submit prediction with Patient details
pred_data = json.dumps({
    "patient_name": "Eleanor Vance",
    "patient_phone": "+1 (555) 019-2834",
    "patient_address": "742 Evergreen Terrace, Springfield, IL",
    "age": 58,
    "sex": 0,
    "cp": 2,
    "trestbps": 136,
    "chol": 240,
    "fbs": 0,
    "restecg": 0,
    "thalach": 155,
    "exang": 0,
    "oldpeak": 0.8,
    "slope": 1,
    "ca": 0,
    "thal": 3
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:5000/api/predict",
    data=pred_data,
    headers={"Content-Type": "application/json"}
)
with opener.open(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    data = res["data"]
    assert data["patient_name"] == "Eleanor Vance", f"Expected Eleanor Vance, got {data.get('patient_name')}"
    assert data["patient_phone"] == "+1 (555) 019-2834"
    assert data["patient_address"] == "742 Evergreen Terrace, Springfield, IL"
    print(f"[+] Prediction Success: Risk={data['risk_level']}, Prob={data['probability']}, ID={data['id']}")
    pred_id = data["id"]

# 5. Verify History retrieval
req = urllib.request.Request(f"http://127.0.0.1:5000/api/history/{pred_id}")
with opener.open(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    hist_record = res["data"]["prediction"]
    assert hist_record["patient_name"] == "Eleanor Vance"
    assert hist_record["patient_phone"] == "+1 (555) 019-2834"
    assert hist_record["patient_address"] == "742 Evergreen Terrace, Springfield, IL"
    print("[+] Confirmed: History record returned patient_name, patient_phone, patient_address successfully!")

print("\n>>> All E2E smoke checks PASSED with flying colors! <<<")
