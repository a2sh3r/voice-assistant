from __future__ import annotations

import sys
import threading

# torch must be imported before PyQt5 — on Windows the DLL load order matters
from config import settings
from llm import ConversationHistory, OpenRouterClient
from screenshot import PilScreenCapture
from stt import WhisperRecognizer
from tts import SileroTTS

from PyQt5.QtWidgets import QApplication

import hotkeys
from app import Assistant
from overlay import OverlayWindow

if __name__ == "__main__":
    hotkeys.start()

    qt_app = QApplication(sys.argv)

    overlay = OverlayWindow()
    overlay.show()

    assistant = Assistant(
        stt=WhisperRecognizer(settings),
        tts=SileroTTS(settings),
        llm=OpenRouterClient(settings, ConversationHistory(settings.history_file)),
        capture=PilScreenCapture(),
        settings=settings,
        overlay=overlay,
    )

    def run_and_quit() -> None:
        assistant.run()
        qt_app.quit()

    thread = threading.Thread(target=run_and_quit, daemon=True)
    thread.start()

    result = qt_app.exec_()
    hotkeys.stop()
    sys.exit(result)
