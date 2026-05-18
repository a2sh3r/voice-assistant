from __future__ import annotations

import threading
import time

import hotkeys
from config import Settings
from protocols import LLMClientProtocol, OverlayProtocol, ScreenCaptureProtocol, SpeechRecognizerProtocol, TTSProtocol


class Assistant:
    """
    Orchestrates the voice assistant loop.

    Depends on abstractions (Protocols), not concrete implementations,
    so any component can be swapped without touching this class.
    """

    def __init__(
        self,
        stt: SpeechRecognizerProtocol,
        tts: TTSProtocol,
        llm: LLMClientProtocol,
        capture: ScreenCaptureProtocol,
        settings: Settings,
        overlay: OverlayProtocol | None = None,
    ) -> None:
        self._stt = stt
        self._tts = tts
        self._llm = llm
        self._capture = capture
        self._settings = settings
        self._overlay = overlay

        self._exit_event = threading.Event()
        self._processing = threading.Event()

    def run(self) -> None:
        self._llm.clear_history()
        self._print_keybindings()
        self._tts.speak(
            "Привет! Я твой учебный ассистент. "
            "Держи PageUp чтобы говорить, или PageDown чтобы я увидел твой экран."
        )

        while not self._exit_event.is_set():
            s = self._settings

            if hotkeys.is_held(s.key_exit):
                self._tts.stop()
                self._exit_event.set()
                break

            if self._processing.is_set():
                if hotkeys.is_held(s.key_speak) or hotkeys.is_held(s.key_screenshot):
                    self._tts.stop()
                time.sleep(0.05)
                continue

            if hotkeys.is_held(s.key_speak):
                self._start_processing(s.key_speak, with_screenshot=False)
                time.sleep(0.2)

            elif hotkeys.is_held(s.key_screenshot):
                self._start_processing(s.key_screenshot, with_screenshot=True)
                time.sleep(0.2)

            elif hotkeys.is_held(s.key_clear):
                self._tts.stop()
                self._llm.clear_history()
                if self._overlay:
                    self._overlay.clear()
                print("История очищена.")
                threading.Thread(
                    target=self._tts.speak,
                    args=("История разговора очищена.",),
                    daemon=True,
                ).start()
                time.sleep(0.5)

            elif hotkeys.is_held(s.key_overlay_toggle):
                if self._overlay:
                    self._overlay.toggle_visibility()
                time.sleep(0.3)

            elif hotkeys.is_held(s.key_overlay_lock):
                if self._overlay:
                    self._overlay.toggle_lock()
                time.sleep(0.3)

            time.sleep(0.05)

        print("Выход.")

    def _start_processing(self, key: str, with_screenshot: bool) -> None:
        if self._processing.is_set():
            return
        self._tts.stop()
        self._processing.set()
        threading.Thread(
            target=self._process,
            args=(key, with_screenshot),
            daemon=True,
        ).start()

    def _process(self, key: str, with_screenshot: bool) -> None:
        try:
            image_b64 = self._take_screenshot_if_needed(with_screenshot)
            audio = self._stt.record_while_held(key)

            text = self._stt.transcribe(audio)
            if not text:
                print("Не распознал речь, попробуй ещё раз.")
                return

            print(f"\nТы: {text}")
            if self._overlay:
                self._overlay.push_message("user", text)

            print("Думаю...")
            if self._overlay:
                self._overlay.set_loading(True)
            reply = self._llm.ask(text, image_b64)
            if self._overlay:
                self._overlay.set_loading(False)
            print(f"Ассистент: {reply}\n")

            if self._overlay:
                self._overlay.push_message("assistant", reply)

            threading.Thread(
                target=self._tts.speak,
                args=(reply,),
                daemon=True,
            ).start()
        finally:
            self._processing.clear()

    def _take_screenshot_if_needed(self, with_screenshot: bool) -> str | None:
        if not with_screenshot:
            return None
        print("Делаю скриншот...")
        image_b64 = self._capture.capture()
        print("Скриншот сделан.")
        return image_b64

    def _print_keybindings(self) -> None:
        s = self._settings
        print("\n=== Учебный ассистент запущен ===")
        print(f"{s.key_speak.upper():<12} — говорить (держи кнопку)")
        print(f"{s.key_screenshot.upper():<12} — говорить + скриншот (держи кнопку)")
        print(f"{s.key_clear.upper():<12} — очистить историю")
        print(f"{s.key_exit.upper():<12} — выход\n")
