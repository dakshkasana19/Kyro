"""
Kyro — Model Management API

POST /api/v1/admin/retrain — Retrain AI model from uploaded CSV
"""

import os
from flask import Blueprint, request, g
from werkzeug.utils import secure_filename
from app.services.model_service import retrain_from_csv
from app.utils.helpers import build_response
from app.core.auth import token_required, require_role
from app.core.errors import ValidationError

model_bp = Blueprint("model", __name__, url_prefix="/api/v1/admin")

ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@model_bp.route("/retrain", methods=["POST"])
@token_required
@require_role(["Admin"])
def start_retraining():
    """
    Handle CSV upload and trigger background retraining.
    """
    if "file" not in request.files:
        raise ValidationError("No file part in the request.")
    
    file = request.files["file"]
    if file.filename == "":
        raise ValidationError("No selected file.")
    
    if file and allowed_file(file.filename):
        # Save temp file
        filename = secure_filename(file.filename)
        temp_dir = "app/ai/temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        try:
            actor = getattr(g, "user", {}).get("email", "ADMIN")
            task_id = retrain_from_csv(temp_path, actor)
            
            return build_response(
                data={"taskId": task_id},
                message="Retraining started in the background. You'll be notified upon completion.",
                status_code=202
            )
        except Exception as e:
            # Cleanup temp if it failed immediately
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValidationError(str(e))
    
    raise ValidationError("Invalid file type. Only CSV allowed.")
