from __future__ import annotations

import base64
import io

from PIL import ImageGrab


class PilScreenCapture:
    """Captures the full screen and returns a base64-encoded PNG string."""

    def capture(self) -> str:
        screenshot = ImageGrab.grab()
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
