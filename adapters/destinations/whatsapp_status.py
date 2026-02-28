"""
WhatsApp Status destination adapter.

Constraints verified against WhatsApp's published limits as of 2024-02-01.
Update `last_verified` whenever you re-confirm the values against the platform.
"""

from domain.ports import Destination, DestinationConstraints


class WhatsAppStatus:
    """WhatsApp Status (vertical short-form video, up to 90 seconds)."""

    name = "whatsapp_status"
    label = "WhatsApp Status"

    @property
    def constraints(self) -> DestinationConstraints:
        return DestinationConstraints(
            max_duration_seconds=90,
            max_file_mb=16,
            preferred_aspect="9:16",
            required_codec="h264",
            last_verified="2024-02-01",
        )


_: Destination = WhatsAppStatus()  # static check: satisfies the port
