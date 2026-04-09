"""
Kyro — Audit API Routes

GET /api/v1/audit — Fetch system activity logs (Admin/Doctor)
"""

from flask import Blueprint, request
from app.services.audit_service import list_audit_logs
from app.utils.helpers import build_response
from app.core.auth import token_required, require_role

audit_bp = Blueprint("audit", __name__, url_prefix="/api/v1/audit")

@audit_bp.route("", methods=["GET"])
@token_required
@require_role(["Admin", "Doctor"])
def fetch_audit_logs():
    """
    Retrieve audit trail with filtering.
    QueryParams: action, actor, limit
    """
    action = request.args.get("action")
    actor = request.args.get("actor")
    limit_str = request.args.get("limit", "50")
    
    try:
        limit = int(limit_str)
    except ValueError:
        limit = 50
        
    logs = list_audit_logs(action=action, actor=actor, limit=limit)
    return build_response(data=logs)
