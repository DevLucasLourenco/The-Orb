"""Protocol: o contrato de eventos do The Orb (docs/PROTOCOL.md). Não depende de nenhum outro módulo."""
from .events import (MAX_BODY_BYTES, MAX_INNER_TEXT, MAX_STRING, Event, clip_body, clip_text,
                     make_event, validate)
from .vocab import (ACTIVITIES, ALL_STATES, DERIVED_STATES, PROTOCOL_VERSION, SIGNAL_FIELDS,
                    SYSTEM_SIGNALS)

__all__ = [
    "ACTIVITIES", "ALL_STATES", "DERIVED_STATES", "Event", "MAX_BODY_BYTES", "MAX_INNER_TEXT",
    "MAX_STRING", "PROTOCOL_VERSION", "SIGNAL_FIELDS", "SYSTEM_SIGNALS", "clip_body", "clip_text",
    "make_event", "validate",
]
