"""
Kyro — Real-time Routes (SSE)

Exposes a Server-Sent Events stream for real-time updates.
"""

from flask import Blueprint, Response, request, stream_with_context
from app.core.realtime import event_bus
from app.core.logging import get_logger

logger = get_logger("routes.realtime")
realtime_bp = Blueprint("realtime", __name__, url_prefix="/api/v1/realtime")

@realtime_bp.route("/stream")
def stream():
    """Subscribe to the hospital's real-time event stream."""
    hospital_id = request.args.get("hospital_id")
    
    if not hospital_id:
        return {"error": "BAD_REQUEST", "message": "hospital_id is required."}, 400

    def event_generator():
        q = event_bus.subscribe(hospital_id)
        try:
            # Send initial connection success event
            yield event_bus.format_sse({"status": "connected"}, event="ping")
            
            while True:
                # Block until an event is available
                msg = q.get()
                yield event_bus.format_sse(msg["data"], event=msg["type"])
        except GeneratorExit:
            event_bus.unsubscribe(hospital_id, q)
            logger.debug("SSE stream connection closed for %s", hospital_id)

    return Response(
        stream_with_context(event_generator()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
            "Connection": "keep-alive"
        }
    )
