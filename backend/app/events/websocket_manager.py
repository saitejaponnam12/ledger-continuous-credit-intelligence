"""
LEDGER — WebSocket Connection Manager
Manages live connections for real-time Financial Twin updates.

Architecture:
  POST /events/simulate
    → persist event
    → recompute ML
    → broadcast via WebSocket
    → UI animates update

NOT Kafka. This is a prototype event pipeline.
Production evolution: Kinesis/Kafka → consumer → WebSocket gateway.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from fastapi.websockets import WebSocketState


class WebSocketManager:
    """
    Manages WebSocket connections per application_id.
    Multiple underwriters can subscribe to the same application.
    """

    def __init__(self):
        # application_id → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, application_id: str) -> None:
        await websocket.accept()
        self._connections[application_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, application_id: str) -> None:
        connections = self._connections.get(application_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self._connections.pop(application_id, None)

    async def broadcast(self, application_id: str, message: dict[str, Any]) -> None:
        """Send an update to all subscribers of this application."""
        connections = self._connections.get(application_id, [])
        dead = []

        for ws in connections:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            if ws in connections:
                connections.remove(ws)

    def active_connections(self, application_id: str) -> int:
        return len(self._connections.get(application_id, []))


# Singleton instance
ws_manager = WebSocketManager()


def build_event_message(
    event_type: str,
    application_id: str,
    payload: dict[str, Any],
) -> dict:
    """Standard message envelope for WebSocket events."""
    import datetime
    return {
        "event_type": event_type,
        "application_id": application_id,
        "payload": payload,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# Event type constants
EVENT_TWIN_UPDATED = "twin_updated"
EVENT_MODEL_UPDATED = "model_updated"
EVENT_PATHWAY_UPDATED = "pathway_updated"
EVENT_EVIDENCE_RECEIVED = "evidence_received"
EVENT_FRAUD_DETECTED = "fraud_detected"
