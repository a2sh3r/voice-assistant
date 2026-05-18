from __future__ import annotations

import atexit
import fcntl
import multiprocessing
import os
import sys
import threading
from pathlib import Path


_lock_file = None


def _acquire_single_instance_lock() -> None:
    global _lock_file
    lock_path = Path(os.getenv("XDG_RUNTIME_DIR", "/tmp")) / "voice-assistant.lock"
    _lock_file = open(lock_path, "w")
    try:
        fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Ассистент уже запущен. Сначала закрой старый процесс (F4 или pkill -f assistant).")
        sys.exit(1)

    _lock_file.write(str(os.getpid()))
    _lock_file.flush()
    atexit.register(_lock_file.close)


def main() -> int:
    # Keep these imports after multiprocessing.freeze_support(). In a frozen
    # PyInstaller binary, multiprocessing helper processes reuse the executable;
    # importing torch/whisper before freeze_support can start a full assistant
    # instance instead of the helper.
    from config import settings
    from llm import ConversationHistory, OpenRouterClient
    from screenshot import PilScreenCapture
    from stt import WhisperRecognizer
    from tts import SileroTTS

    # torch must be imported before PyQt5 — on Windows the DLL load order matters
    from PyQt5.QtWidgets import QApplication

    import hotkeys
    from app import Assistant
    from overlay import OverlayWindow

    _acquire_single_instance_lock()
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

    try:
        result = qt_app.exec_()
    except KeyboardInterrupt:
        result = 130
    finally:
        hotkeys.stop()
    return result


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
