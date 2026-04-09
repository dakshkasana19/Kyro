"""
Kyro — Queue API Routes

GET  /api/queue  — Get the prioritised triage queue
"""

from __future__ import annotations

from flask import Blueprint

from app.core.logging import get_logger
from app.services.queue_service import get_queue
from app.services.triage_service import resolve_triage_session
from app.utils.helpers import build_response
from app.core.auth import token_required, require_role
from app.core.errors import ValidationError

logger = get_logger("routes.queue")

queue_bp = Blueprint("queue", __name__, url_prefix="/api/queue")


@queue_bp.route("", methods=["GET"])
def fetch_queue():
    """Return the current triage queue, ordered by severity."""
    queue = get_queue()
    return build_response(data=queue)


@queue_bp.route("/resolve/<log_id>", methods=["POST"])
@token_required
@require_role(["Doctor", "Admin"])
def resolve_session(log_id: str):
    """Mark a triage session as resolved and free the doctor."""
    result = resolve_triage_session(log_id)
    return build_response(data=result, message="Case resolved.")
