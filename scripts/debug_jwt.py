"""Quick JWT debug script to identify why token verification fails."""
import os
import jwt
import base64
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL").strip()
KEY = os.getenv("SUPABASE_KEY").strip()
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET").strip()

print(f">>> JWT Secret (first 20 chars): {JWT_SECRET[:20]}...")
print(f">>> JWT Secret length: {len(JWT_SECRET)}")

# Login to get a real token
supabase = create_client(URL, KEY)
res = supabase.auth.sign_in_with_password({"email": "admin@kyro.health", "password": "Password123!"})
token = res.session.access_token

print(f"\n>>> Token (first 50 chars): {token[:50]}...")

# Decode header without verification to see the algorithm
header = jwt.get_unverified_header(token)
print(f">>> Token Header: {header}")
print(f">>> Token Algorithm: {header.get('alg')}")

# Try raw secret
print("\n>>> Attempting verification with raw secret string...")
try:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[header['alg']], audience="authenticated")
    print(f"    [PASS] Raw string works! Sub: {payload.get('sub')}")
except Exception as e:
    print(f"    [FAIL] {e}")

# Try base64 decoded
print("\n>>> Attempting verification with base64-decoded secret...")
try:
    decoded = base64.b64decode(JWT_SECRET)
    payload = jwt.decode(token, decoded, algorithms=[header['alg']], audience="authenticated")
    print(f"    [PASS] Base64-decoded works! Sub: {payload.get('sub')}")
except Exception as e:
    print(f"    [FAIL] {e}")

# Try without audience
print("\n>>> Attempting verification without audience check...")
try:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[header['alg']], options={"verify_aud": False})
    print(f"    [PASS] No audience works! Sub: {payload.get('sub')}")
    print(f"    user_metadata: {payload.get('user_metadata')}")
except Exception as e:
    print(f"    [FAIL] {e}")
