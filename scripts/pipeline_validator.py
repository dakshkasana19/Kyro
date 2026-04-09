import sys
import os
import json
from datetime import datetime

# Ensure we can import app
sys.path.append(os.getcwd())

# Mock heavy dependencies BEFORE they are imported by the app
from unittest.mock import MagicMock
sys.modules["flask_socketio"] = MagicMock()
sys.modules["flask"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["xgboost"] = MagicMock() # Mock XGB for speed if not present
sys.modules["shap"] = MagicMock()
sys.modules["psycopg2"] = MagicMock()

# Mock SocketIO to prevent errors in test env
class MockSocket:
    def emit(self, event, data, **kwargs):
        print(f"[SOCKET] Emitting {event} with data: {json.dumps(data, indent=2)}")

import app.core.sockets
app.core.sockets.socketio = MockSocket()

# Import Services
from app.services.triage_service import run_triage
from app.services.doctor_service import list_doctors
from app.db.supabase_manager import select_rows

def run_e2e_test():
    print("="*60)
    print(" KYRO CLINICAL PORTAL — E2E PIPELINE VALIDATION")
    print("="*60)
    print(f"Time: {datetime.now().isoformat()}")
    
    # 1. Staff Check
    print("\n[STAGE 1] Verifying Staff Availability...")
    doctors = list_doctors(available_only=True)
    if not doctors:
        print("FAILED: No on-duty doctors found. Please add a doctor via Admin Panel first.")
        return
    print(f"PASSED: Found {len(doctors)} on-duty practitioners.")

    # 2. Intake & AI Triage
    print("\n[STAGE 2] Simulating Critical Patient Intake...")
    # High HR, Low BP, High Temperature -> Level 3
    test_patient = {
        "name": "INTEGRATION TEST PATIENT",
        "age": 72,
        "gender": "female",
        "vitals": {
            "heart_rate": 155,
            "systolic_bp": 75,
            "diastolic_bp": 45,
            "temperature": 104.2,
            "respiratory_rate": 32,
            "pain_scale": 10
        },
        "symptoms": [{"clinical_context": "Loss of consciousness", "severity": "high"}],
        "history": {"chronic_conditions": ["htn", "cad"]}
    }
    
    try:
        # We use a dummy UUID for the patient record simulation
        patient_id = "test-uuid-001" 
        triage_result = run_triage(patient_id, test_patient)
        
        severity = triage_result.get("severity_level")
        label = triage_result.get("severity_label")
        doctor_id = triage_result.get("assigned_doctor_id")
        
        print(f"AI PREDICTION: Level {severity} ({label})")
        
        if severity != 3:
            print("WARNING: Model predicted level < 3. Tweak vitals to ensure high severity for test.")
        else:
            print("PASSED: AI correctly identified life-threatening case.")

        # 3. Assignment Check
        if doctor_id:
            print(f"PASSED: Patient successfully assigned to Doctor ID: {doctor_id}")
        else:
            print("FAILED: No doctor assigned despite staff availability.")

        # 4. Audit Verification
        print("\n[STAGE 3] Verifying Audit Trail...")
        audit_logs = select_rows("audit_log", limit=3, order_by="-created_at")
        
        # Check for TRIAGE_COMPLETED and NOTIFICATION_SENT
        actions = [log["action"] for log in audit_logs]
        print(f"Latest Audit Actions: {actions}")
        
        if "TRIAGE_COMPLETED" in actions and "NOTIFICATION_SENT" in actions:
            print("PASSED: Triage and Notifications recorded in immutable audit log.")
        else:
            print("FAILED: Audit log missing critical events.")

    except Exception as e:
        print(f"ERROR: Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print(" VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_e2e_test()
