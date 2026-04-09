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
            # Assumes token_required has already been called and g.user is populated
            user = getattr(g, "user", None)
            if not user:
                return jsonify({"error": "UNAUTHORIZED", "message": "User not authenticated."}), 401

            # Roles are stored in user_metadata or app_metadata
            # In Supabase, custom roles can be in user_metadata if set during signup
            user_metadata = user.get("user_metadata", {})
            user_role = user_metadata.get("role")

            if not user_role or user_role not in roles:
                logger.warning("Access denied for user %s. Required roles: %s, User role: %s", 
                               user.get("sub"), roles, user_role)
                return jsonify({"error": "FORBIDDEN", "message": "Access denied. Insufficient permissions."}), 403

            return f(*args, **kwargs)
        return decorated
    return decorator
