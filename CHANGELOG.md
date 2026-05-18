# Changelog

## Unreleased

- Added native Wayland hotkey handling on Linux via `evdev`, with X11 fallback.
- Fixed PyInstaller Linux packaging for pynput/evdev backend modules.
- Prevented duplicate assistant instances and PyInstaller multiprocessing helper restarts.
- Made TTS interruptible and synchronized `sounddevice` access between playback and recording.
- Updated the overlay so unlocked mode behaves as a regular resizable Hyprland window.
- Updated GitHub Actions Linux build dependencies for `evdev`, PortAudio, and libsndfile.
- Enabled GitHub Actions builds on pushes to `master`.
