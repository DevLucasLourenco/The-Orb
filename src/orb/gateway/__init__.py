"""Gateway: o servidor local (docs/ARCHITECTURE.md §3). Observa os realms, mantém o mundo e serve o
cliente 3D e os terminais. Orquestra; não interpreta providers."""
from .app import GatewayConfig, Hub, authorized, create_app, main
from .messages import MAX_CLIENT_MESSAGE, handle_client_message
from .realms import Feed, Observatory, Realm

__all__ = ["Feed", "GatewayConfig", "Hub", "MAX_CLIENT_MESSAGE", "Observatory", "Realm", "authorized",
           "create_app", "handle_client_message", "main"]
