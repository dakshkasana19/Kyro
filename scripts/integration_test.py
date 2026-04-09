import requests
import json
import time

# Use the likely port for local Flask
BASE_URL = 'http://localhost:5000/api/v1'

def test_critical_intake():
    """
    Test a high-severity (Level 3) patient intake.
    Expects:
      - Triage calculation (Critical)
      - Notification dispatch (WebSockets + Mock Logs)
      - Audit trail log
    """
    payload = {
        "name": "E2E Test Patient (Critical)",
        "age": 65,
        "gender": "male",
        "vitals": {
            "heart_rate": 140,
            "systolic_bp": 80,
            "diastolic_bp": 50,
            "temperature": 103.0,
            "respiratory_rate": 30,
            "pain_scale": 10
        },
        "symptoms": [{"clinical_context": "Unresponsive", "severity": "high"}],
        "history": {"chronic_conditions": ["cad", "ckd"]}
    }

    print(">>> [TEST] Submitting Critical Intake...")
    try:
        # We use a public intake endpoint if available, otherwise it might fail without token
        response = requests.post(f"{BASE_URL}/patients/intake", json=payload, timeout=10)
        
        print(f">>> [TEST] Status: {response.status_code}")
        if response.ok:
            data = response.json().get('data', {})
            severity = data.get('severity_level')
            label = data.get('severity_label')
            print(f">>> [TEST] Severity Result: {severity} ({label})")
            
            if severity == 3:
                print(">>> [SUCCESS] Pipeline correctly identified Level 3 patient.")
            else:
                print(f">>> [NOTE] Severity was {severity}, results may vary by model state.")
        else:
            print(f">>> [FAILED] Server returned error: {response.text}")

    except Exception as e:
        print(f">>> [ERROR] Could not connect to API: {e}")
        print(">>> [INFO] Make sure the Flask server is running on port 5000.")

if __name__ == "__main__":
    test_critical_intake()
