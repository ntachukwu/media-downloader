"""
Instagram Story destination adapter.

Constraints verified against Instagram's published limits as of 2024-01-15.
Update `last_verified` whenever you re-confirm the values against the platform.
"""

from domain.ports import Destination, DestinationConstraints


class InstagramStory:
    """Instagram Story (vertical short-form video, up to 60 seconds)."""

    name = "instagram_story"
    label = "Instagram Story"

    @property
    def constraints(self) -> DestinationConstraints:
        return DestinationConstraints(
            max_duration_seconds=60,
            max_file_mb=100,
            preferred_aspect="9:16",
            required_codec="h264",
            last_verified="2024-01-15",
        )


_: Destination = InstagramStory()  # static check: satisfies the port
