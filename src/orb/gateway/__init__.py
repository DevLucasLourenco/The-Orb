"""Gateway: FastAPI + WebSocket (docs/ARCHITECTURE.md §3). Orquestra; não interpreta providers."""
from .app import GatewayConfig, authorized, create_app, main
from .messages import MAX_CLIENT_MESSAGE, handle_client_message

__all__ = ["GatewayConfig", "MAX_CLIENT_MESSAGE", "authorized", "create_app", "handle_client_message", "main"]
