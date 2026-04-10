"""
Kyro — Authentication Middleware

Verifies Supabase JWT tokens and provides role-based access control decorators.
Supports both ES256 (JWKS-based) and HS256 (secret-based) token verification.
"""

from functools import wraps
from flask import request, jsonify, g
import jwt
import requests as http_requests
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("auth")

# Cache for JWKS keys
_jwks_cache = {}

def _get_jwks_key(token):
    """Fetch and cache the JWKS public key from Supabase for ES256 verification."""
    global _jwks_cache
    
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    
    if kid and kid in _jwks_cache:
        return _jwks_cache[kid]
    
    # Fetch JWKS from Supabase
    jwks_url = f"{settings.supabase.URL}/auth/v1/.well-known/jwks.json"
    try:
        resp = http_requests.get(jwks_url, timeout=5)
        resp.raise_for_status()
        jwks = resp.json()
        
        for key_data in jwks.get("keys", []):
            key = jwt.algorithms.ECAlgorithm.from_jwk(key_data)
            _jwks_cache[key_data["kid"]] = key
        
        if kid and kid in _jwks_cache:
            return _jwks_cache[kid]
    except Exception as e:
        logger.warning("Failed to fetch JWKS: %s", e)
    
    return None

def token_required(f):
    """Decorator to verify the Supabase JWT token in the Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "UNAUTHORIZED", "message": "Authentication token is missing."}), 401

        try:
            header = jwt.get_unverified_header(token)
            alg = header.get("alg", "HS256")
            
            payload = None
            
            if alg == "ES256":
                # Use JWKS public key for ES256
                public_key = _get_jwks_key(token)
                if public_key:
                    payload = jwt.decode(
                        token,
                        public_key,
                        algorithms=["ES256"],
                        audience="authenticated",
                        leeway=30  # Handle clock skew
                    )
                else:
                    return jsonify({"error": "AUTH_ERROR", "message": "Could not fetch verification key."}), 401
            else:
                # Fallback to HS256 with JWT secret
                payload = jwt.decode(
                    token, 
                    settings.supabase.JWT_SECRET, 
                    algorithms=["HS256"], 
                    audience="authenticated",
                    leeway=30
                )

            g.user = payload
            # Extract role and hospital_id for easier access in routes
            user_metadata = payload.get("user_metadata", {})
            g.hospital_id = user_metadata.get("hospital_id")
            g.role = user_metadata.get("role")
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "TOKEN_EXPIRED", "message": "Authentication token has expired."}), 401
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token attempt: %s", str(e))
            return jsonify({"error": "INVALID_TOKEN", "message": f"Authentication token is invalid: {str(e)}"}), 401
        except Exception as e:
            logger.exception("Token verification error")
            return jsonify({"error": "AUTH_ERROR", "message": "An error occurred during authentication."}), 401

        return f(*args, **kwargs)

    return decorated

def require_role(roles: list[str]):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_role = getattr(g, "role", None)
            
            if not user_role or user_role not in roles:
                logger.warning("Access denied for user %s. Required roles: %s, User role: %s", 
                               getattr(g, "user", {}).get("sub"), roles, user_role)
                return jsonify({"error": "FORBIDDEN", "message": "Access denied. Insufficient permissions."}), 403

            return f(*args, **kwargs)
        return decorated
    return decorator
