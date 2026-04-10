"""
Kyro — Authentication Middleware

Verified Supabase JWT tokens and provides role-based access control decorators.
"""

from functools import wraps
from flask import request, jsonify, g
import jwt
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("auth")

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
            # Supabase tokens are signed with the JWT Secret
            # We use HS256 as default for Supabase
            payload = jwt.decode(
                token, 
                settings.supabase.JWT_SECRET, 
                algorithms=["HS256"], 
                audience="authenticated"
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
            return jsonify({"error": "INVALID_TOKEN", "message": "Authentication token is invalid."}), 401
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
            # Assumes token_required has already been called and g.role is populated
            user_role = getattr(g, "role", None)
            
            if not user_role or user_role not in roles:
                logger.warning("Access denied for user %s. Required roles: %s, User role: %s", 
                               getattr(g, "user", {}).get("sub"), roles, user_role)
                return jsonify({"error": "FORBIDDEN", "message": "Access denied. Insufficient permissions."}), 403

            return f(*args, **kwargs)
        return decorated
    return decorator
