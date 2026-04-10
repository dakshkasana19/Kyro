"""Quick test: verify JWT locally using the same auth logic."""
import os
import jwt
from dotenv import load_dotenv
from supabase import create_client
import requests as http_requests

load_dotenv()

URL = os.getenv("SUPABASE_URL").strip()
KEY = os.getenv("SUPABASE_KEY").strip()

# Login to get token
supabase = create_client(URL, KEY)
res = supabase.auth.sign_in_with_password({"email": "admin@kyro.health", "password": "Password123!"})
token = res.session.access_token

print(f">>> Token algorithm: {jwt.get_unverified_header(token)}")

# Fetch JWKS
jwks_url = f"{URL}/auth/v1/.well-known/jwks.json"
print(f">>> Fetching JWKS from: {jwks_url}")
resp = http_requests.get(jwks_url, timeout=5)
print(f">>> JWKS response code: {resp.status_code}")
jwks = resp.json()
print(f">>> JWKS keys count: {len(jwks.get('keys', []))}")

# Build key
for key_data in jwks.get("keys", []):
    print(f">>> Key: kid={key_data.get('kid')}, kty={key_data.get('kty')}, crv={key_data.get('crv')}")
    try:
        key = jwt.algorithms.ECAlgorithm.from_jwk(key_data)
        payload = jwt.decode(token, key, algorithms=["ES256"], audience="authenticated")
        print(f">>> [PASS] Verification successful!")
        print(f">>> user_metadata: {payload.get('user_metadata')}")
        break
    except Exception as e:
        print(f">>> [FAIL] {e}")
