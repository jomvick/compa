# Compa

> Bring Linux to Life.

A small, animated, discreet, and interactive Tux that lives on your Linux desktop.

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

## Multi-monitor

Compa places itself on whichever monitor currently has the pointer at
startup, and its walking/settings-dialog placement stay clamped to the
monitor it's currently on (not the combined virtual desktop). If a monitor
is unplugged or resolution changes while Compa is running, it relocates
itself back onto a valid monitor automatically.

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

## Building packages

Packaging scaffolding lives under [`packaging/`](packaging/). Both are
work-in-progress starting points, not push-button production pipelines yet
— see the TODO notes each script prints.

* **AppImage**:
  ```bash
  bash packaging/appimage/build-appimage.sh
  ```
  Downloads `linuxdeploy` + its GTK plugin on first run, bundles GTK3 and
  produces `packaging/appimage/build/Compa*.AppImage`. Build on an
  Ubuntu/Debian machine for the widest glibc compatibility, then **test the
  resulting AppImage on a different machine** — that's the real portability
  check.

* **.deb**:
  ```bash
  bash packaging/debian/build-deb.sh
  ```
  Requires `build-essential debhelper devscripts`. Produces a `.deb` one
  directory above the project root.

## Scope of this slice

The demo already makes the desktop feel alive: continuous animations, random events, emotions, rare phrases, and personalities that genuinely modulate probabilities and speed. It intentionally excludes AI, monitoring, launchers, widgets, and any productivity features — this foundation will not change shape in future versions either (see [the roadmap](ROADMAP.md)).

Remaining work before V1.1 is closed — validating the compatibility matrix
across distros/desktop environments, and cutting a demo video — is tracked
in [the roadmap](ROADMAP.md).
