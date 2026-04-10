import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# We use the Service Role Key to bypass RLS and direct-create users
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")  # Ensure this is the SERVICE_ROLE_KEY
HOSPITAL_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479"  # Kyro Central Clinic

if not URL or not KEY:
    print(">>> [ERROR] Missing SUPABASE_URL or SUPABASE_KEY in .env")
    exit(1)

supabase: Client = create_client(URL, KEY)

STAFF_ACCOUNTS = [
    {
        "email": "admin@kyro.health",
        "password": "Password123!",
        "role": "Admin",
        "name": "Kyro Administrator"
    },
    {
        "email": "doctor@kyro.health",
        "password": "Password123!",
        "role": "Doctor",
        "name": "Dr. Smith"
    },
    {
        "email": "nurse@kyro.health",
        "password": "Password123!",
        "role": "Nurse",
        "name": "Nurse Joy"
    }
]

def seed_staff():
    print(f">>> Seeding staff for Hospital: {HOSPITAL_ID}")
    
    for account in STAFF_ACCOUNTS:
        email = account["email"]
        password = account["password"]
        role = account["role"]
        name = account["name"]
        
        print(f">>> Processing {role}: {email}...")
        
        # Check if user already exists
        response = supabase.auth.admin.list_users()
        # Some versions return a list, others a response object with .users
        user_list = response if isinstance(response, list) else getattr(response, 'users', [])
        
        existing_user = next((u for u in user_list if u.email == email), None)
        
        if existing_user:
            print(f"    - User already exists ({existing_user.id}). Updating metadata...")
            supabase.auth.admin.update_user_by_id(
                existing_user.id,
                {
                    "user_metadata": {
                        "role": role,
                        "hospital_id": HOSPITAL_ID,
                        "full_name": name
                    }
                }
            )
        else:
            print(f"    - Creating new user...")
            supabase.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "role": role,
                    "hospital_id": HOSPITAL_ID,
                    "full_name": name
                }
            })
    
    print(">>> Seeding complete.")

if __name__ == "__main__":
    seed_staff()
