from __future__ import annotations

import os
import threading

_held: set[str] = set()
_lock = threading.Lock()
_stop = threading.Event()
_listener: object | None = None
_evdev_threads: list[threading.Thread] = []


def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _set_held(name: str, held: bool) -> None:
    normalized = _normalize(name)
    with _lock:
        if held:
            _held.add(normalized)
        else:
            _held.discard(normalized)


def _key_to_str(key: object) -> str:
    try:
        char = key.char  # type: ignore[attr-defined]
        if char:
            return char.lower()
    except AttributeError:
        pass
    try:
        return key.name.lower()  # type: ignore[attr-defined]
    except AttributeError:
        return str(key).lower()


def _on_press(key: object) -> None:
    _set_held(_key_to_str(key), True)


def _on_release(key: object) -> None:
    _set_held(_key_to_str(key), False)


def _evdev_name(code: int, ecodes: object) -> str | None:
    raw = ecodes.KEY.get(code)  # type: ignore[attr-defined]
    if isinstance(raw, list):
        raw = raw[0]
    if not isinstance(raw, str):
        return None

    names = {
        "KEY_PAGEUP": "page_up",
        "KEY_PAGEDOWN": "page_down",
        "KEY_ESC": "esc",
    }
    if raw in names:
        return names[raw]
    if raw.startswith("KEY_F") and raw[5:].isdigit():
        return raw[4:].lower()
    if raw.startswith("KEY_") and len(raw) == 5:
        return raw[-1].lower()
    return raw.removeprefix("KEY_").lower()


def _read_evdev_device(device: object, ecodes: object) -> None:
    try:
        for event in device.read_loop():  # type: ignore[attr-defined]
            if _stop.is_set():
                break
            if event.type != ecodes.EV_KEY:  # type: ignore[attr-defined]
                continue
            name = _evdev_name(event.code, ecodes)
            if not name:
                continue
            if event.value == 1:
                _set_held(name, True)
            elif event.value == 0:
                _set_held(name, False)
    except OSError:
        return


def _start_evdev() -> bool:
    try:
        import evdev
        from evdev import ecodes
    except ImportError:
        return False

    started = 0
    for path in evdev.list_devices():
        try:
            device = evdev.InputDevice(path)
            capabilities = device.capabilities()
        except OSError:
            continue

        key_codes = capabilities.get(ecodes.EV_KEY, [])
        if len(key_codes) < 20:
            device.close()
            continue

        thread = threading.Thread(
            target=_read_evdev_device,
            args=(device, ecodes),
            daemon=True,
        )
        thread.start()
        _evdev_threads.append(thread)
        started += 1

    if started:
        print(f"Hotkeys: evdev backend active ({started} keyboard device(s)).")
        return True

    if os.environ.get("WAYLAND_DISPLAY"):
        print(
            "Hotkeys: evdev не видит клавиатуру. Нужен активный доступ к /dev/input "
            "(перелогин после `sudo usermod -a -G input $USER`)."
        )
    return False


def _start_pynput() -> None:
    global _listener
    if os.environ.get("DISPLAY") == "":
        os.environ["DISPLAY"] = ":0"

    from pynput import keyboard as pynput_keyboard

    _listener = pynput_keyboard.Listener(
        on_press=_on_press,
        on_release=_on_release,
        daemon=True,
    )
    _listener.start()  # type: ignore[attr-defined]


def start() -> None:
    if os.environ.get("WAYLAND_DISPLAY") and _start_evdev():
        return
    _start_pynput()


def stop() -> None:
    _stop.set()
    if _listener is not None:
        _listener.stop()  # type: ignore[attr-defined]


def is_held(name: str) -> bool:
    with _lock:
        return _normalize(name) in _held
