"""
Signal tests — unit tests for the Signal class.

Each test creates its own Signal instance so there is no shared state.
"""

from domain.signals import Signal


class TestSignalConnect:
    def test_send_calls_connected_receiver(self):
        sig = Signal()
        calls = []
        sig.connect(lambda **kw: calls.append(kw))
        sig.send(x=1)
        assert calls == [{"x": 1}]

    def test_multiple_receivers_all_called(self):
        sig = Signal()
        a, b = [], []
        sig.connect(lambda **kw: a.append(kw))
        sig.connect(lambda **kw: b.append(kw))
        sig.send(val=42)
        assert a == [{"val": 42}]
        assert b == [{"val": 42}]

    def test_receivers_called_in_connection_order(self):
        sig = Signal()
        order = []
        sig.connect(lambda **_: order.append("first"))
        sig.connect(lambda **_: order.append("second"))
        sig.send()
        assert order == ["first", "second"]

    def test_same_receiver_can_be_connected_twice(self):
        """Not prevented — callers are responsible for de-duplication."""
        sig = Signal()
        calls = []

        def r(**_: object) -> None:
            calls.append(1)

        sig.connect(r)
        sig.connect(r)
        sig.send()
        assert calls == [1, 1]


class TestSignalSend:
    def test_send_with_no_receivers_does_not_raise(self):
        sig = Signal()
        sig.send(x=1)  # no error, no receivers

    def test_send_passes_all_kwargs_to_receiver(self):
        sig = Signal()
        received = {}
        sig.connect(lambda **kw: received.update(kw))
        sig.send(url="http://x.com", title="Test", total_bytes=1024)
        assert received == {"url": "http://x.com", "title": "Test", "total_bytes": 1024}

    def test_receiver_accepting_only_known_kwargs_still_works(self):
        """Receivers can accept specific kwargs + **_ to ignore unknown fields."""
        sig = Signal()
        captured = []
        sig.connect(lambda url, **_: captured.append(url))
        sig.send(url="http://x.com", title="Test", extra="ignored")
        assert captured == ["http://x.com"]


class TestSignalDisconnect:
    def test_disconnect_removes_receiver(self):
        sig = Signal()
        calls = []

        def receiver(**kw):
            calls.append(kw)

        sig.connect(receiver)
        sig.disconnect(receiver)
        sig.send(x=1)
        assert calls == []

    def test_disconnect_removes_all_copies(self):
        """Disconnect removes every copy of the receiver, not just the first."""
        sig = Signal()
        calls = []

        def r(**_: object) -> None:
            calls.append(1)

        sig.connect(r)
        sig.connect(r)
        sig.disconnect(r)
        sig.send()
        assert calls == []

    def test_disconnect_unknown_receiver_does_not_raise(self):
        sig = Signal()
        sig.disconnect(lambda **kw: None)  # never connected — silent no-op

    def test_other_receivers_unaffected_by_disconnect(self):
        sig = Signal()
        a_calls, b_calls = [], []

        def a(**_):
            a_calls.append(1)

        def b(**_):
            b_calls.append(1)

        sig.connect(a)
        sig.connect(b)
        sig.disconnect(a)
        sig.send()
        assert a_calls == []
        assert b_calls == [1]
