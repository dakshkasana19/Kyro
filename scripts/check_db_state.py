import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(URL, KEY)

def check_db():
    print(">>> Checking Hospitals...")
    try:
        hospitals = supabase.table("hospitals").select("*").execute()
        print(f"    Found {len(hospitals.data)} hospitals.")
        for h in hospitals.data:
            print(f"    - {h['id']}: {h['name']}")
    except Exception as e:
        print(f"    [ERROR] Hospitals table error: {e}")

    print("\n>>> Checking Profiles...")
    try:
        profiles = supabase.table("profiles").select("*").execute()
        print(f"    Found {len(profiles.data)} profiles.")
    except Exception as e:
        print(f"    [ERROR] Profiles table error: {e}")

if __name__ == "__main__":
    check_db()
