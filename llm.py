from __future__ import annotations

import json
import os
from typing import Any

import requests

from config import Settings

Message = dict[str, Any]

_SYSTEM_PROMPT = (
    "Ты — учебный ассистент, помогаешь изучать программирование и математику. "
    "Общайся неформально, как с другом — без официоза, можешь материться если это уместно и естественно. "
    "Говори живо и по-человечески, без занудства. "
    "Никаких списков, пунктов, таблиц, заголовков, markdown-разметки — только обычные предложения. "
    "Если нужно перечислить — через запятую или союзы. Будь кратким и по делу. "
    "Если видишь скриншот экрана — анализируй что на нём.\n"
    "ВАЖНО: твой ответ будет озвучен русской TTS-моделью, которая не умеет читать латиницу. "
    "Пиши ВСЕ технические термины кириллицей: Питон, Раст, Го, Джаваскрипт, "
    "Тайпскрипт, Джейсон, Докер, Кубернетес, Редис, Гит, Линукс, эй-пи-ай, "
    "эйч-ти-ти-пи, дот-энв, трейт, энам, асинк, эвейт, мьютекс, лайфтайм, "
    "горутина, бороу чекер, овнершип. Никаких английских букв в ответе."
)

_HISTORY_KEEP = 40


class ConversationHistory:
    """Stores in-memory conversation and persists it to disk (without images)."""

    def __init__(self, filepath: str) -> None:
        self._filepath = filepath
        self._messages: list[Message] = []

    @property
    def messages(self) -> list[Message]:
        return self._messages

    def append(self, message: Message) -> None:
        self._messages.append(message)

    def pop(self) -> Message:
        return self._messages.pop()

    def clear(self) -> None:
        self._messages.clear()

    def last(self, n: int) -> list[Message]:
        return self._messages[-n:]

    def save(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(self.strip_images(self._messages[-_HISTORY_KEEP:]), f, ensure_ascii=False, indent=2)

    @staticmethod
    def strip_images(messages: list[Message]) -> list[Message]:
        result: list[Message] = []
        for msg in messages:
            if isinstance(msg["content"], list):
                text_parts = [p["text"] for p in msg["content"] if p.get("type") == "text"]
                result.append({"role": msg["role"], "content": " ".join(text_parts)})
            else:
                result.append(msg)
        return result


class OpenRouterClient:
    """Sends chat completion requests to OpenRouter, managing conversation history."""

    _API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, settings: Settings, history: ConversationHistory) -> None:
        self._settings = settings
        self._history = history
        self._headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
        }

    def ask(self, text: str, image_b64: str | None = None) -> str:
        content: Any = self._build_content(text, image_b64)
        self._history.append({"role": "user", "content": content})

        use_vision = image_b64 is not None
        model = self._settings.vision_model if use_vision else self._settings.model
        context = self._history.last(self._settings.context_window)
        if not use_vision:
            context = ConversationHistory.strip_images(context)
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": _SYSTEM_PROMPT}] + context,
            "max_tokens": self._settings.max_tokens,
        }

        try:
            response = requests.post(self._API_URL, headers=self._headers, json=payload, timeout=30)
        except requests.exceptions.RequestException as exc:
            print(f"Сетевая ошибка: {exc}")
            self._history.pop()
            return "Нет соединения с сервером."

        if response.status_code == 200:
            reply: str = response.json()["choices"][0]["message"]["content"]
            self._history.append({"role": "assistant", "content": reply})
            self._history.save()
            return reply

        print(f"Ошибка API: {response.status_code} {response.text}")
        self._history.pop()
        return "Ошибка при обращении к API."

    def clear_history(self) -> None:
        self._history.clear()
        self._history.save()

    @staticmethod
    def _build_content(text: str, image_b64: str | None) -> Any:
        if image_b64 is None:
            return text
        return [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            {"type": "text", "text": text},
        ]
