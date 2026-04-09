"""
Kyro — Authentication Routes

Handles user signup and login using Supabase Auth.
"""

from flask import Blueprint, request, jsonify
from app.db.supabase_manager import get_client
from app.core.logging import get_logger
from app.services.audit_service import log_event, AuditAction

logger = get_logger("auth_routes")
auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Sign up a new user with email, password, and role."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not all([email, password, role]):
        return jsonify({"error": "BAD_REQUEST", "message": "Email, password, and role are required."}), 400

    if role not in ["Admin", "Doctor", "Nurse"]:
        return jsonify({"error": "BAD_REQUEST", "message": "Invalid role. Must be 'Admin', 'Doctor', or 'Nurse'."}), 400

    try:
        supabase = get_client()
        # Sign up user with metadata for efficiency (RBAC)
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": role
                }
            }
        })
        
        if response.user:
            logger.info("User signed up successfully: %s with role: %s", email, role)
            log_event(
                actor=email,
                action=AuditAction.SIGNUP,
                resource="user",
                resource_id=response.user.id,
                metadata={"role": role}
            )
            return jsonify({
                "message": "User registered successfully. Please check your email for verification.",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "role": role
                }
            }), 201
        
        return jsonify({"error": "SIGNUP_FAILED", "message": "Failed to create user."}), 400

    except Exception as e:
        logger.exception("Signup error")
        return jsonify({"error": "INTERNAL_ERROR", "message": str(e)}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in an existing user and return a JWT token."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "BAD_REQUEST", "message": "Email and password are required."}), 400

    try:
        supabase = get_client()
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.session:
            user = response.user
            # Role is stored in user_metadata
            role = user.user_metadata.get("role") if user.user_metadata else None
            
            logger.info("User logged in successfully: %s", email)
            log_event(
                actor=email,
                action=AuditAction.LOGIN,
                resource="user",
                resource_id=user.id,
                metadata={"role": role}
            )
            return jsonify({
                "message": "Login successful",
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": role
                }
            }), 200

        return jsonify({"error": "LOGIN_FAILED", "message": "Invalid credentials."}), 401

    except Exception as e:
        logger.exception("Login error")
        return jsonify({"error": "INTERNAL_ERROR", "message": str(e)}), 500
