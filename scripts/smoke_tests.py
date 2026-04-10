import requests
import json
import time

BASE_URL = "http://localhost:5000"
HOSPITAL_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

ACCOUNTS = {
    "Admin": ("admin@kyro.health", "Password123!"),
    "Doctor": ("doctor@kyro.health", "Password123!"),
    "Nurse": ("nurse@kyro.health", "Password123!")
}

class SmokeTester:
    def __init__(self):
        self.tokens = {}

    def test_login(self):
        print(">>> [TEST] Authenticating users...")
        for role, (email, password) in ACCOUNTS.items():
            res = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
                "email": email,
                "password": password
            })
            if res.status_code == 200:
                data = res.json()
                self.tokens[role] = data["access_token"]
                print(f"    [PASS] {role} logged in. Hospital: {data['user']['hospital_id']}")
            else:
                print(f"    [FAIL] {role} failed to login: {res.text}")

    def test_rbac_audit(self):
        print("\n>>> [TEST] Verifying RBAC (Audit Logs)...")
        # Admin should access
        res = requests.get(f"{BASE_URL}/api/v1/audit", headers={
            "Authorization": f"Bearer {self.tokens['Admin']}"
        })
        print(f"    [INFO] Admin Audit Access: {res.status_code}")
        
        # Nurse should be forbidden
        res = requests.get(f"{BASE_URL}/api/v1/audit", headers={
            "Authorization": f"Bearer {self.tokens['Nurse']}"
        })
        print(f"    [INFO] Nurse Audit Access (Expected 403): {res.status_code}")

    def test_queue_access(self):
        print("\n>>> [TEST] Verifying Scoped Queue retrieval...")
        for role in ["Admin", "Doctor", "Nurse"]:
            res = requests.get(f"{BASE_URL}/api/queue", headers={
                "Authorization": f"Bearer {self.tokens[role]}"
            })
            if res.status_code == 200:
                print(f"    [PASS] {role} fetched queue successfully.")
            else:
                print(f"    [FAIL] {role} could not fetch queue: {res.status_code}")

    def test_triage_flow(self):
        print("\n>>> [TEST] Running complete Triage Flow (Nurse)...")
        payload = {
            "name": "Smoke Test Patient",
            "age": 45,
            "gender": "male",
            "symptoms": [{"name": "chest pain"}, {"name": "shortness of breath"}, {"name": "sweating"}],
            "vitals": {
                "heart_rate": 110,
                "systolic_bp": 160,
                "diastolic_bp": 100,
                "temperature": 37.2,
                "respiratory_rate": 22,
                "oxygen_saturation": 95,
                "pain_scale": 7
            },
            "history": {
                "chronic_conditions": ["htn"]
            }
        }
        
        res = requests.post(f"{BASE_URL}/api/patients/intake", 
            json=payload,
            headers={"Authorization": f"Bearer {self.tokens['Nurse']}"}
        )
        
        if res.status_code == 201:
            data = res.json()
            triage = data.get("data", data).get("triage", {})
            print(f"    [PASS] Triage completed.")
            print(f"    [INFO] Severity: {triage.get('severity_level', triage.get('severity', 'N/A'))}")
            print(f"    [INFO] Assigned Doctor: {triage.get('assigned_doctor_id', 'N/A')}")
        else:
            print(f"    [FAIL] Triage flow failed ({res.status_code}): {res.text[:300]}")

def run_smoke_tests():
    print("====================================================")
    print("         KYRO TRIAGE-AI SMOKE TESTS")
    print("====================================================\n")
    
    tester = SmokeTester()
    try:
        tester.test_login()
        if len(tester.tokens) < 3:
            print("\n!!! Skipping further tests due to login failures.")
            return

        tester.test_rbac_audit()
        tester.test_queue_access()
        tester.test_triage_flow()
        
        print("\n====================================================")
        print("         ALL SMOKE TESTS COMPLETED")
        print("====================================================")
    except Exception as e:
        print(f"\n!!! [ERROR] Smoke tests crashed: {e}")

if __name__ == "__main__":
    run_smoke_tests()
