from __future__ import annotations

import re
import threading
import time

import sounddevice as sd
import torch

from audio_device import SOUNDDEVICE_LOCK
from config import Settings

_EN_TO_RU: dict[str, str] = {
    r"\bPython\b": "Питон",
    r"\bRust\b": "Раст",
    r"\bGolang\b": "Го",
    r"\bGo\b": "Го",
    r"\bJavaScript\b": "Джаваскрипт",
    r"\bTypeScript\b": "Тайпскрипт",
    r"\bC\+\+": "Си плюс плюс",
    r"\bJava\b": "Джава",
    r"\bKotlin\b": "Котлин",
    r"\bSwift\b": "Свифт",
    r"\bgoroutine\b": "горутина",
    r"\bgoroutines\b": "горутины",
    r"\bborrow checker\b": "бороу чекер",
    r"\bownership\b": "овнершип",
    r"\blifetime\b": "лайфтайм",
    r"\blifetimes\b": "лайфтаймы",
    r"\btrait\b": "трейт",
    r"\btraits\b": "трейты",
    r"\benum\b": "энам",
    r"\bstruct\b": "структ",
    r"\basync\b": "асинк",
    r"\bawait\b": "эвейт",
    r"\bchannel\b": "канал",
    r"\bmutex\b": "мьютекс",
    r"\bclosure\b": "клоужер",
    r"\bclosures\b": "клоужеры",
    r"\binterface\b": "интерфейс",
    r"\bgenerics\b": "дженерики",
    r"\bDocker\b": "Докер",
    r"\bKubernetes\b": "Кубернетес",
    r"\bRedis\b": "Редис",
    r"\bPostgres\b": "Постгрес",
    r"\bGit\b": "Гит",
    r"\bGitHub\b": "Гитхаб",
    r"\bLinux\b": "Линукс",
    r"\bWindows\b": "Виндоус",
    r"\bJSON\b": "Джейсон",
    r"\bSQL\b": "Эс-Кью-Эл",
    r"\bNoSQL\b": "Но-Эс-Кью-Эл",
    r"\bHTTP\b": "Эйч-Ти-Ти-Пи",
    r"\bgRPC\b": "Джи-Ар-Пи-Си",
    r"\bAPI\b": "Эй-Пи-Ай",
    r"\b\.env\b": "дот-энв",
    r"\bWhisper\b": "Вишпер",
    r"\bGemini\b": "Джемини",
    r"\bClaude\b": "Клод",
}


class TextNormalizer:
    """Converts English technical terms to Russian phonetics for Silero TTS."""

    def normalize(self, text: str) -> str:
        for pattern, replacement in _EN_TO_RU.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        text = re.sub(r"[A-Za-z][A-Za-z0-9\-\.]*", "", text)
        text = re.sub(r" {2,}", " ", text).strip()
        return text


class SileroTTS:
    """Text-to-speech using Silero v3 Russian model."""

    _SILERO_SAMPLE_RATE = 48000

    def __init__(self, settings: Settings) -> None:
        self._speaker = settings.speaker
        self._rate = settings.speech_rate
        self._normalizer = TextNormalizer()
        self._state_lock = threading.Lock()
        self._generation = 0
        self._stop_event = threading.Event()

        print("Загрузка Silero TTS...")
        self._model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="ru",
            speaker="v3_1_ru",
        )
        print("Silero загружен.")

    def speak(self, text: str) -> None:
        with self._state_lock:
            self._generation += 1
            generation = self._generation
            self._stop_event.clear()

        text = self._normalizer.normalize(text)
        if not text:
            return
        try:
            audio = self._model.apply_tts(
                text=text,
                speaker=self._speaker,
                sample_rate=self._SILERO_SAMPLE_RATE,
            )

            with self._state_lock:
                if generation != self._generation:
                    return

            samplerate = int(self._SILERO_SAMPLE_RATE * self._rate)
            samples = audio.numpy()
            duration = len(samples) / samplerate

            with SOUNDDEVICE_LOCK:
                with self._state_lock:
                    if generation != self._generation:
                        return
                sd.stop()
                sd.play(samples, samplerate=samplerate)

            deadline = time.monotonic() + duration
            while time.monotonic() < deadline:
                with self._state_lock:
                    if generation != self._generation:
                        break
                if self._stop_event.wait(0.05):
                    break

            with SOUNDDEVICE_LOCK:
                sd.stop()
        except Exception as exc:
            print(f"Ошибка TTS: {exc}")

    def stop(self) -> None:
        with self._state_lock:
            self._generation += 1
            self._stop_event.set()
        with SOUNDDEVICE_LOCK:
            sd.stop()
        time.sleep(0.05)
