from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    _base = Path(sys.executable).parent
else:
    _base = Path(__file__).parent

load_dotenv(_base / ".env")


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("MODEL", "qwen/qwen3-235b-a22b"))
    vision_model: str = field(default_factory=lambda: os.getenv("VISION_MODEL", "google/gemini-2.0-flash-001"))
    context_window: int = field(default_factory=lambda: int(os.getenv("CONTEXT_WINDOW", "10")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "400")))

    whisper_model: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "small"))
    sample_rate: int = 16000

    speaker: str = field(default_factory=lambda: os.getenv("SPEAKER", "aidar"))
    speech_rate: float = field(default_factory=lambda: float(os.getenv("SPEECH_RATE", "1.0")))

    key_speak: str = field(default_factory=lambda: os.getenv("KEY_SPEAK", "page up"))
    key_screenshot: str = field(default_factory=lambda: os.getenv("KEY_SCREENSHOT", "page down"))
    key_clear: str = field(default_factory=lambda: os.getenv("KEY_CLEAR", "f10"))
    key_exit: str = field(default_factory=lambda: os.getenv("KEY_EXIT", "esc"))
    key_overlay_toggle: str = field(default_factory=lambda: os.getenv("KEY_OVERLAY_TOGGLE", "f11"))
    key_overlay_lock: str = field(default_factory=lambda: os.getenv("KEY_OVERLAY_LOCK", "f12"))

    history_file: str = "history.json"


settings = Settings()
