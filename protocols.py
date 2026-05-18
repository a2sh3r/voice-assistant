from __future__ import annotations

from typing import Protocol

import numpy as np


class SpeechRecognizerProtocol(Protocol):
    def record_while_held(self, key: str) -> np.ndarray:
        """Record audio chunks while the given key is held. Returns float32 ndarray."""
        ...

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio array to text. Returns empty string if nothing recognized."""
        ...


class TTSProtocol(Protocol):
    def speak(self, text: str) -> None:
        """Synthesize and play text aloud."""
        ...

    def stop(self) -> None:
        """Stop current audio playback, if any."""
        ...


class LLMClientProtocol(Protocol):
    def ask(self, text: str, image_b64: str | None = None) -> str:
        """Send a user message (optionally with a base64 screenshot) and return the reply."""
        ...

    def clear_history(self) -> None:
        """Wipe conversation history."""
        ...


class ScreenCaptureProtocol(Protocol):
    def capture(self) -> str:
        """Take a screenshot and return it as a base64-encoded PNG string."""
        ...


class OverlayProtocol(Protocol):
    def push_message(self, role: str, text: str) -> None:
        """Append a message to the overlay. role is 'user' or 'assistant'."""
        ...

    def clear(self) -> None:
        """Remove all messages from the overlay."""
        ...

    def toggle_visibility(self) -> None:
        """Show the overlay if hidden, hide if visible."""
        ...

    def toggle_lock(self) -> None:
        """Switch between click-through (locked) and draggable (unlocked) mode."""
        ...

    def set_loading(self, active: bool) -> None:
        """Show or hide the loading spinner."""
        ...
