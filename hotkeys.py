from __future__ import annotations

import threading

from pynput import keyboard as _pynput

_held: set[str] = set()
_lock = threading.Lock()


def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _key_to_str(key: _pynput.Key | _pynput.KeyCode) -> str:
    try:
        char = key.char  # type: ignore[union-attr]
        if char:
            return char.lower()
    except AttributeError:
        pass
    try:
        return key.name.lower()  # type: ignore[union-attr]
    except AttributeError:
        return str(key).lower()


def _on_press(key: _pynput.Key | _pynput.KeyCode) -> None:
    with _lock:
        _held.add(_key_to_str(key))


def _on_release(key: _pynput.Key | _pynput.KeyCode) -> None:
    with _lock:
        _held.discard(_key_to_str(key))


_listener = _pynput.Listener(on_press=_on_press, on_release=_on_release, daemon=True)


def start() -> None:
    _listener.start()


def stop() -> None:
    _listener.stop()


def is_held(name: str) -> bool:
    with _lock:
        return _normalize(name) in _held
