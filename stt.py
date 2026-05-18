from __future__ import annotations

import os
import tempfile
import time
import warnings

import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper

from audio_device import SOUNDDEVICE_LOCK
import hotkeys
from config import Settings

_WHISPER_PROMPT = (
    "Расскажи про borrow checker в Rust и как работает ownership. "
    "В Golang есть goroutine и channel, а интерфейсы неявные. "
    "Чем отличается async await в Rust от Go? "
    "Как устроен garbage collector? Что такое lifetime и trait? "
    "Объясни разницу между heap и stack, между mutex и channel. "
    "Как работает gRPC поверх HTTP? Покажи пример на Rust или Golang. "
    "Что такое deadlock и race condition? Как их избежать? "
    "Расскажи про Docker, Kubernetes, микросервисы и DDD. "
    "Как реализовать паттерн repository или SOLID в Go?"
)

_MIN_DURATION_SEC = 0.3


class WhisperRecognizer:
    """Records audio while a key is held and transcribes it with Whisper."""

    def __init__(self, settings: Settings) -> None:
        self._sample_rate = settings.sample_rate

        print(f"Загрузка Whisper ({settings.whisper_model})...")
        self._model = whisper.load_model(settings.whisper_model)
        print("Whisper загружен.")

    def record_while_held(self, key: str) -> np.ndarray:
        """Stream microphone input into chunks while the key is held down."""
        chunks: list[np.ndarray] = []
        print("● Запись... (держи кнопку)")
        with SOUNDDEVICE_LOCK:
            with sd.InputStream(samplerate=self._sample_rate, channels=1, dtype="float32") as stream:
                while hotkeys.is_held(key):
                    chunk, _ = stream.read(int(self._sample_rate * 0.05))
                    chunks.append(chunk.copy())
                    time.sleep(0.01)

        if not chunks:
            return np.array([], dtype="float32")

        audio = np.concatenate(chunks).flatten()
        print(f"■ Запись окончена ({len(audio) / self._sample_rate:.1f} сек)")
        return audio

    def transcribe(self, audio: np.ndarray) -> str:
        """Write audio to a temp WAV and run Whisper on it. Returns empty string on failure."""
        if len(audio) < self._sample_rate * _MIN_DURATION_SEC:
            return ""

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_path = f.name
            sf.write(tmp_path, audio, self._sample_rate)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = self._model.transcribe(
                    tmp_path, language="ru", initial_prompt=_WHISPER_PROMPT
                )
            return result["text"].strip()
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
