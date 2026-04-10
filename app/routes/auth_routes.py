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

DEFAULT_HOSPITAL_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Sign up a new user with email, password, and role."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    full_name = data.get("name", "Unknown Staff")
    hospital_id = data.get("hospital_id", DEFAULT_HOSPITAL_ID)

    if not all([email, password, role]):
        return jsonify({"error": "BAD_REQUEST", "message": "Email, password, and role are required."}), 400

    if role not in ["Admin", "Doctor", "Nurse"]:
        return jsonify({"error": "BAD_REQUEST", "message": "Invalid role. Must be 'Admin', 'Doctor', or 'Nurse'."}), 400

    try:
        supabase = get_client()
        # 1. Sign up user in Supabase Auth
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": role,
                    "hospital_id": hospital_id
                }
            }
        })
        
        if response.user:
            user_id = response.user.id
            
            # 2. Create the internal profile record
            # We use the admin client to bypass RLS for initial setup
            profile_data = {
                "id": user_id,
                "hospital_id": hospital_id,
                "role": role,
                "full_name": full_name
            }
            supabase.table("profiles").insert(profile_data).execute()

            logger.info("User signed up and profile created: %s with role: %s", email, role)
            log_event(
                actor=email,
                action=AuditAction.SIGNUP,
                resource="user",
                resource_id=user_id,
                metadata={"role": role, "hospital_id": hospital_id}
            )
            return jsonify({
                "message": "User registered successfully. Please check your email for verification.",
                "user": {
                    "id": user_id,
                    "email": email,
                    "role": role,
                    "hospital_id": hospital_id
                }
            }), 201
        
        return jsonify({"error": "SIGNUP_FAILED", "message": "Failed to create user account."}), 400

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
            # Role and hospital_id are stored in user_metadata
            role = user.user_metadata.get("role") if user.user_metadata else None
            hospital_id = user.user_metadata.get("hospital_id") if user.user_metadata else None
            
            logger.info("User logged in successfully: %s", email)
            log_event(
                hospital_id=hospital_id,
                actor=email,
                action=AuditAction.LOGIN,
                resource="user",
                resource_id=user.id,
                metadata={"role": role, "hospital_id": hospital_id}
            )
            return jsonify({
                "message": "Login successful",
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": role,
                    "hospital_id": hospital_id
                }
            }), 200

        return jsonify({"error": "LOGIN_FAILED", "message": "Invalid credentials."}), 401

    except Exception as e:
        logger.exception("Login error")
        return jsonify({"error": "INTERNAL_ERROR", "message": str(e)}), 500
