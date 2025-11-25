from __future__ import annotations

import queue
import threading
from typing import Optional

try:  # Optional dependency; falls back gracefully if missing.
    import pyttsx3  # type: ignore
except Exception:  # pragma: no cover - optional voice output
    pyttsx3 = None  # type: ignore


class VoiceOutput:
    """Lightweight text-to-speech wrapper with background queue processing."""

    def __init__(self, enabled: bool = True, rate: int = 185) -> None:
        self.enabled = enabled and pyttsx3 is not None
        self._engine = pyttsx3.init() if self.enabled else None  # type: ignore[assignment]
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        if self._engine:
            try:
                self._engine.setProperty("rate", rate)
            except Exception:
                pass
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def speak(self, text: str) -> bool:
        """Queue text for asynchronous playback."""
        if not self.enabled or not self._engine:
            return False
        self._queue.put(text)
        return True

    def close(self) -> None:
        if not self._engine:
            return
        self._stop.set()
        self._queue.put("")  # unblock queue
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._engine.stop()
        self._engine = None

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _worker(self) -> None:
        assert self._engine is not None
        while not self._stop.is_set():
            try:
                text = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if not text:
                continue
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                # swallow TTS errors so the UI stays responsive
                continue


__all__ = ["VoiceOutput"]

