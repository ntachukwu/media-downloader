"""
Destination contract tests — verify adapters satisfy the Destination port.

Each concrete adapter must:
- Pass ``isinstance(adapter, Destination)``.
- Expose a ``last_verified`` date in ISO-8601 format (``YYYY-MM-DD``).
- Be reachable by name through the registry.
"""

import re

import pytest

from adapters.destinations.instagram_story import InstagramStory
from adapters.destinations.registry import all_destinations, get
from adapters.destinations.whatsapp_status import WhatsAppStatus
from domain.ports import Destination

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ALL_ADAPTERS = [WhatsAppStatus(), InstagramStory()]


class TestDestinationPort:
    def test_whatsapp_status_satisfies_destination_port(self) -> None:
        assert isinstance(WhatsAppStatus(), Destination)

    def test_instagram_story_satisfies_destination_port(self) -> None:
        assert isinstance(InstagramStory(), Destination)

    def test_destination_port_rejects_class_missing_constraints(self) -> None:
        class NoConstraints:
            name = "x"
            label = "X"

        assert not isinstance(NoConstraints(), Destination)


class TestDestinationConstraints:
    def test_last_verified_is_iso_date(self) -> None:
        for d in _ALL_ADAPTERS:
            assert _DATE_PATTERN.match(d.constraints.last_verified), (
                f"{d.name}: last_verified must be an ISO-8601 date (YYYY-MM-DD)"
            )

    def test_required_codec_is_non_empty_string(self) -> None:
        for d in _ALL_ADAPTERS:
            assert d.constraints.required_codec, f"{d.name}: required_codec must not be empty"

    def test_constraints_are_immutable(self) -> None:
        c = WhatsAppStatus().constraints
        with pytest.raises((AttributeError, TypeError)):
            c.max_duration_seconds = 999  # type: ignore[misc]


class TestRegistry:
    def test_get_returns_whatsapp_status_by_name(self) -> None:
        d = get("whatsapp_status")
        assert isinstance(d, WhatsAppStatus)

    def test_get_returns_instagram_story_by_name(self) -> None:
        d = get("instagram_story")
        assert isinstance(d, InstagramStory)

    def test_get_raises_for_unknown_name(self) -> None:
        with pytest.raises(ValueError, match="Unknown destination"):
            get("telegram")

    def test_get_error_lists_available_destinations(self) -> None:
        with pytest.raises(ValueError, match="whatsapp_status"):
            get("__nonexistent__")

    def test_all_destinations_returns_every_registered_adapter(self) -> None:
        names = {d.name for d in all_destinations()}
        assert "whatsapp_status" in names
        assert "instagram_story" in names

    def test_all_destinations_returns_a_copy(self) -> None:
        """Mutating the returned list does not affect the registry."""
        first = all_destinations()
        first.clear()
        assert len(all_destinations()) > 0
