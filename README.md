# Voice Assistant

***Вайбкод***

## Стек

- **STT** — Whisper (локально)
- **LLM** — OpenRouter (Qwen3, Gemini и др.)
- **TTS** — Silero (локально)
- **UI** — PyQt5 оверлей

## Установка

```bash
pip install -r requirements.txt
```

Создать `.env` рядом с `main.py` (см. `.env.example`).

## Запуск

```bash
python main.py
```

При первом запуске скачаются модели Whisper (~150 МБ) и Silero (~60 МБ).

## Горячие клавиши

| Клавиша | Действие |
|---|---|
| `Page Up` | Говорить (держать) |
| `Page Down` | Говорить + скриншот экрана (держать) |
| `F2` | Очистить историю |
| `F4` | Выход |
| `F10` | Показать / скрыть оверлей |
| `F12` | Заблокировать / разблокировать оверлей (для перетаскивания) |

Все клавиши настраиваются через `.env`.

## Конфигурация

```env
OPENROUTER_API_KEY=your_key

MODEL=qwen/qwen3-235b-a22b
VISION_MODEL=google/gemini-2.0-flash-001

WHISPER_MODEL=small        # tiny / base / small / medium / large
SPEAKER=eugene             # aidar / eugene / baya / kseniya / xenia
SPEECH_RATE=1.0

KEY_SPEAK=page up
KEY_SCREENSHOT=page down
KEY_CLEAR=f2
KEY_EXIT=f4
KEY_OVERLAY_TOGGLE=f10
KEY_OVERLAY_LOCK=f12

CONTEXT_WINDOW=10
MAX_TOKENS=400
```

## Сборка бинаря

**Windows:**
```powershell
.\build.ps1
```

**Linux / macOS:**
```bash
./build.sh
```

Результат в `dist/assistant/`. Скопируй `.env` рядом с бинарём.

## Linux / Wayland

На Wayland глобальные горячие клавиши читаются через `evdev` из `/dev/input`.
Добавь пользователя в группу `input` и перелогинься:

```bash
sudo usermod -a -G input $USER
```

После повторного входа при старте должно появиться:

```text
Hotkeys: evdev backend active (... keyboard device(s)).
```
