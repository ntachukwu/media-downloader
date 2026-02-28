"""
Destination registry — the single source of truth for available platforms.

Add a new destination by:
1. Creating a new adapter module under ``adapters/destinations/``.
2. Importing and adding its class to ``_ALL`` below.

The domain, pipeline, API, and any Flutter client are untouched.
"""

from adapters.destinations.instagram_story import InstagramStory
from adapters.destinations.whatsapp_status import WhatsAppStatus
from domain.ports import Destination

_ALL: list[Destination] = [WhatsAppStatus(), InstagramStory()]

DESTINATIONS: dict[str, Destination] = {d.name: d for d in _ALL}


def get(name: str) -> Destination:
    """Return the destination with the given machine key.

    Args:
        name: Machine key for the destination (e.g. ``"whatsapp_status"``).

    Returns:
        The matching :class:`~domain.ports.Destination` adapter.

    Raises:
        ValueError: If *name* is not in the registry.
    """
    if name not in DESTINATIONS:
        raise ValueError(f"Unknown destination '{name}'. Available: {list(DESTINATIONS)}")
    return DESTINATIONS[name]


def all_destinations() -> list[Destination]:
    """Return all registered destinations.

    Used by the API to build the destination picker — callers receive the
    live list, so adding an adapter here is immediately visible.

    Returns:
        Ordered list of every registered :class:`~domain.ports.Destination`.
    """
    return list(_ALL)
