"""
Kyro — Real-time Event Bus (SSE)

Provides a multi-producer, multi-consumer event stream for Server-Sent Events.
Fallbacks to in-memory broadcast if Redis is unavailable.
"""

import json
import queue
from typing import Dict, List, Set

from app.core.logging import get_logger

logger = get_logger("realtime")

class EventBus:
    """Manages SSE connections and event distribution."""

    def __init__(self) -> None:
        # Map of hospital_id -> Set of Queues (one per client)
        self.subscribers: Dict[str, Set[queue.Queue]] = {}
        logger.info("Real-time Event Bus initialised")

    def subscribe(self, hospital_id: str) -> queue.Queue:
        """Create a new subscriber queue for a specific hospital."""
        q = queue.Queue(maxsize=50)
        if hospital_id not in self.subscribers:
            self.subscribers[hospital_id] = set()
        
        self.subscribers[hospital_id].add(q)
        logger.debug("New subscriber joined hospital: %s (Total: %d)", hospital_id, len(self.subscribers[hospital_id]))
        return q

    def unsubscribe(self, hospital_id: str, q: queue.Queue) -> None:
        """Remove a subscriber queue."""
        if hospital_id in self.subscribers:
            self.subscribers[hospital_id].discard(q)
            if not self.subscribers[hospital_id]:
                del self.subscribers[hospital_id]
        logger.debug("Subscriber left hospital: %s", hospital_id)

    def publish(self, hospital_id: str, event_type: str, data: dict) -> None:
        """Broadcast an event to all subscribers in a hospital."""
        if hospital_id not in self.subscribers:
            return

        message = {
            "type": event_type,
            "data": data
        }
        
        dead_queues = set()
        for q in self.subscribers[hospital_id]:
            try:
                q.put_nowait(message)
            except queue.Full:
                # If a client is too slow, we'll mark it for removal
                dead_queues.add(q)
        
        for dq in dead_queues:
            self.unsubscribe(hospital_id, dq)

    def format_sse(self, data: dict, event: str = None) -> str:
        """Format a message as a Server-Sent Event."""
        msg = f"data: {json.dumps(data)}\n\n"
        if event:
            msg = f"event: {event}\n{msg}"
        return msg

# Singleton instance
event_bus = EventBus()
