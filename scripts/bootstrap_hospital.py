import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
HOSPITAL_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

supabase: Client = create_client(URL, KEY)

def bootstrap_hospital():
    print(f">>> Bootstrapping Hospital: {HOSPITAL_ID}")
    try:
        # Check if table exists by trying to select
        res = supabase.table("hospitals").upsert({
            "id": HOSPITAL_ID,
            "name": "Kyro Central Clinic",
            "address": "77 Health Ave, Silicon Valley"
        }).execute()
        print(f">>> Success: {res.data}")
    except Exception as e:
        print(f">>> [ERROR] Failed to bootstrap hospital: {e}")
        print("    Ensure you have run the supabase_schema.sql successfully first.")

if __name__ == "__main__":
    bootstrap_hospital()
