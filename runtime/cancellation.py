"""Cooperative cancellation primitive shared by inference backends."""

from threading import Event


class CancellationToken:
    """Thread-safe cancellation signal with no host-side side effects."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def wait(self, timeout: float | None = None) -> bool:
        return self._event.wait(timeout)
