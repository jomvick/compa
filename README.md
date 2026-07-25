# Compa

> Bring Linux to Life.

A small, animated, discreet, and interactive Tux that lives on your Linux desktop.

Product direction, V1 scope, and exit criteria are in [the MVP](mvp.md).
Long-term vision and project rules are in [the manifesto](THE_COMPA_MANIFESTO.md).
Upcoming versions are listed in [the roadmap](ROADMAP.md).

## License

Compa is open source under the [MIT](LICENSE) license.

## System Requirements & Dependencies

Compa uses **GTK3 (PyGObject)** and **Cairo** to deliver 100% per-pixel transparency with no borders on Linux desktops (X11 and Wayland).

### 1. Install system packages

Depending on your distribution, install the required system dependencies (GTK3, PyGObject, Cairo, Pillow):

* **Ubuntu / Debian / Mint**:
  ```bash
  sudo apt update
  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pil
  ```

* **Fedora / RHEL**:
  ```bash
  sudo dnf install python3-gobject gtk3 python3-pillow
  ```

* **Arch Linux / Manjaro**:
  ```bash
  sudo pacman -S python-gobject gtk3 python-pillow
  ```

### 2. Python installation (Virtual environment / Pip)

If you use a Python virtual environment (`venv`), install the dependencies listed in `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
```

> **Note**: Installing `PyGObject` or `pycairo` via `pip` requires system development headers (`libgirepository1.0-dev` / `cairo-devel`). Using your distribution packages (above) is recommended.

## Running the demo

```bash
python3 companion.py
```

The script automatically uses `GDK_BACKEND=x11` to force transparent overlay rendering with zero borders on both Wayland and X11.

## Session autostart

The reliable way to enable autostart: check
**"Launch at session startup"** in Tux's Settings (right-click
on Tux → Settings…). Compa then generates its own XDG Autostart file
(with the absolute path to `companion.py`) in
`~/.config/autostart/compa.desktop`.

A [`compa.desktop.example`](compa.desktop.example) file is provided as a
reference only — do not copy it as-is into
`~/.config/autostart/`; its relative path will not work outside the
project directory.

## Gestures & Interactions

- **single click**: Tux jumps (smooth sinusoidal physics);
- **double click**: Tux waves and shows a speech bubble;
- **drag & drop**: click and drag Tux freely across your screen;
- **right click**: opens the context menu (Feed Tux 🐟, Wake up, Play, change Personality, or open Settings).

## Scope of this slice

The demo already makes the desktop feel alive: continuous animations, random events, emotions, rare phrases, and personalities that genuinely modulate probabilities and speed. It intentionally excludes AI, monitoring, launchers, widgets, and any productivity features — this foundation will not change shape in future versions either (see [the roadmap](ROADMAP.md)).

Remaining system integrations — true multi-monitor support and `.deb`/Flatpak packaging — come after the initial demo, per distribution target, respecting each platform's X11/Wayland rules.
