#!/usr/bin/env python3
"""Compa — a living, discreet, desktop Tux for Linux.

Strategy:
  - GDK_BACKEND=x11 forces GTK to run through XWayland.
  - Under XWayland, Gtk.WindowType.POPUP = X11 override-redirect window.
    Override-redirect completely bypasses KWin/any compositor: zero decorations.
  - Cairo OPERATOR_CLEAR gives true per-pixel RGBA transparency.
"""

from __future__ import annotations

# Force GTK to use XWayland before any display import.
# Under XWayland: POPUP = override-redirect (no decorations).
# Under XWayland: Cairo RGBA transparency works perfectly.
import os
os.environ["GDK_BACKEND"] = "x11"

import io
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import cairo
from PIL import Image


# ─────────────────────────────── personalities ────────────────────────────── #

@dataclass(frozen=True)
class Personality:
    label: str
    speed: float
    sleep: float
    move: float
    play: float
    phrases: tuple[str, ...]


PERSONALITIES = {
    "Curious": Personality("Curious", 1.05, 0.55, 1.45, 1.0,
                           ("What is that?", "The cursor moved!", "Hmm...")),
    "Happy":   Personality("Happy",   1.30, 0.50, 1.15, 1.6,
                           ("(^o^)", "What a lovely day!", "Yay!")),
    "Lazy":    Personality("Lazy",    0.70, 1.80, 0.45, 0.55,
                           ("Five more minutes...", "Zzz...", "I'm comfy here.")),
    "Calm":    Personality("Calm",    0.78, 1.15, 0.55, 0.6,
                           ("A quiet moment.", "Hello.", "All is well.")),
    "Playful": Personality("Playful", 1.18, 0.65, 1.20, 1.8,
                           ("Catch me!", "Again!", "Hehe!")),
}

AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "compa.desktop"

CONFIG_DIR = Path.home() / ".config" / "compa"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOCK_FILE = CONFIG_DIR / "compa.pid"


def acquire_single_instance_lock() -> None:
    """Refuse to start a second Compa if one is already running.

    Best-effort: if the lock file is stale (process no longer exists, or
    we can't even check — e.g. no /proc, or a permissions quirk) we just
    take over the lock rather than blocking the user forever because of a
    leftover file from a crash.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if LOCK_FILE.is_file():
            try:
                old_pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())
                os.kill(old_pid, 0)  # raises if that PID isn't running
                print(f"Compa is already running (PID {old_pid}). Exiting.")
                sys.exit(1)
            except (ValueError, ProcessLookupError, PermissionError, OSError):
                pass  # stale/unreadable lock — fall through and take it
        LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        pass  # can't lock — worst case, allow a duplicate rather than crash


def release_single_instance_lock() -> None:
    try:
        if LOCK_FILE.is_file() and LOCK_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
            LOCK_FILE.unlink()
    except OSError:
        pass


def load_config() -> dict:
    """Best-effort read of the persisted settings. Any problem (missing
    file, corrupt JSON, unreadable) just means "start from defaults" —
    persistence is a nicety, never something that should crash startup."""
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        return {}


def save_config(data: dict) -> None:
    """Best-effort write of the current settings. Failures are swallowed —
    losing the ability to remember settings should never crash or
    interrupt the running companion."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def is_autostart_enabled() -> bool:
    return AUTOSTART_FILE.is_file()


def set_autostart(enable: bool) -> None:
    if enable:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        companion_script = Path(__file__).resolve()
        content = f"""[Desktop Entry]
Type=Application
Name=Compa
GenericName=Desktop Companion
Comment=A living Tux companion for Linux
Exec=python3 "{companion_script}"
Icon=tux
Terminal=false
Categories=Utility;DesktopSettings;
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after=panel
"""
        AUTOSTART_FILE.write_text(content, encoding="utf-8")
    else:
        if AUTOSTART_FILE.is_file():
            AUTOSTART_FILE.unlink()


# ─────────────────────────────── companion ────────────────────────────────── #

class Companion:
    """Borderless, fully-transparent Tux companion on Linux."""

    WIN_W = 220
    WIN_H = 210

    def __init__(self) -> None:
        config = load_config()

        self.size = config.get("size", 1.0)
        self.speed = config.get("speed", 1.0)
        self.opacity = config.get("opacity", 1.0)
        self.keep_above = config.get("keep_above", True)
        self.animations_enabled = config.get("animations_enabled", True)
        self.personality = PERSONALITIES.get(
            config.get("personality", "Curious"), PERSONALITIES["Curious"]
        )
        self._saved_pos = (config.get("pos_x"), config.get("pos_y"))

        # animation state
        self.state = "idle"
        self.state_start = time.monotonic()
        self.state_duration = 1.0

        # blink
        self.is_blinking = False
        self.next_blink = time.monotonic() + random.uniform(2.5, 5.0)

        # life timer
        self.last_event = time.monotonic()
        self._last_autosave = time.monotonic()

        # bubble
        self.bubble_text = ""
        self.bubble_until = 0.0

        # drag
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.press_x_root = 0
        self.press_y_root = 0
        self.is_dragging = False
        self.click_start_time = 0.0

        # walk
        self.walk_direction = 1

        # assets
        self.sprite_dir = Path(__file__).parent / "assets" / "tux" / "poses"
        self.pixbufs: dict[str, GdkPixbuf.Pixbuf] = {}

        # input shape (click-through outside Tux's actual, non-transparent
        # pixels) — tracks (sprite key, rounded dx, rounded dy) so we only
        # recombine the region when something actually changed, not on
        # every single ~40ms tick.
        self._last_shape_sig: tuple | None = None

        # ── GTK window ──────────────────────────────────────────────────── #
        # POPUP under XWayland = X11 override-redirect: WM cannot decorate it.
        self.win = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.win.set_app_paintable(True)
        self.win.set_keep_above(self.keep_above)
        # Belt-and-suspenders: POPUP/override-redirect windows are already
        # excluded from taskbar/Alt-Tab/pager on every WM we've tested, but
        # these hints make that explicit rather than relying purely on
        # window-type behaviour that could differ across WMs.
        self.win.set_skip_taskbar_hint(True)
        self.win.set_skip_pager_hint(True)
        # Clicking Tux must never steal keyboard focus from whatever the
        # user was typing in — he's a companion, not an application window.
        self.win.set_accept_focus(False)

        # RGBA visual for per-pixel transparency
        screen = Gdk.Screen.get_default()
        if screen:
            visual = screen.get_rgba_visual()
            if visual and screen.is_composited():
                self.win.set_visual(visual)

        self.win.set_default_size(self.WIN_W, self.WIN_H)
        self.win.set_size_request(self.WIN_W, self.WIN_H)

        # signals
        self.win.connect("draw",                   self._on_draw)
        self.win.connect("button-press-event",     self._on_press)
        self.win.connect("button-release-event",   self._on_release)
        self.win.connect("motion-notify-event",    self._on_motion)
        self.win.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK   |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )

        self._load_sprites()

        # Restore the last saved position if we have one and it still
        # points at a real monitor; otherwise fall back to the
        # bottom-right corner of whichever monitor currently has the
        # pointer (e.g. first launch, or the saved monitor is gone).
        saved_x, saved_y = self._saved_pos
        display = Gdk.Display.get_default()
        restored = False
        if saved_x is not None and saved_y is not None and display is not None:
            monitor = display.get_monitor_at_point(
                int(saved_x) + self.WIN_W // 2, int(saved_y) + self.WIN_H // 2
            )
            if monitor is not None:
                self.win.move(int(saved_x), int(saved_y))
                restored = True
        if not restored:
            mon = self._monitor_at_pointer()
            self.win.move(mon.x + mon.width - self.WIN_W - 40,
                           mon.y + mon.height - self.WIN_H - 60)
        self.win.show_all()

        GLib.timeout_add(40, self._tick)   # ~25 fps

    # ── multi-monitor helpers ──────────────────────────────────────────── #

    def _monitor_at_pointer(self) -> "Gdk.Rectangle":
        """Geometry of the monitor currently under the mouse pointer.

        Used only at startup, so Tux appears on the screen the user is
        actually looking at rather than always on the "primary" one.
        """
        fallback = Gdk.Rectangle()
        fallback.x, fallback.y, fallback.width, fallback.height = 0, 0, 1920, 1080

        display = Gdk.Display.get_default()
        if display is None:
            return fallback

        seat = display.get_default_seat()
        pointer = seat.get_pointer() if seat else None
        if pointer is not None:
            _screen, px, py = pointer.get_position()
            monitor = display.get_monitor_at_point(px, py)
        else:
            monitor = display.get_monitor(0)

        if monitor is None:
            monitor = display.get_monitor(0)
        return monitor.get_geometry() if monitor else fallback

    def _monitor_at_window(self) -> "Gdk.Rectangle":
        """Geometry of the monitor Tux's window currently sits on.

        Used continuously (walking bounds, settings dialog placement) so
        behaviour stays correct if the window is dragged to another screen,
        or if a monitor is unplugged/reconnected while Compa is running.
        """
        fallback = Gdk.Rectangle()
        fallback.x, fallback.y, fallback.width, fallback.height = 0, 0, 1920, 1080

        display = Gdk.Display.get_default()
        if display is None:
            return fallback

        wx, wy = self.win.get_position()
        monitor = display.get_monitor_at_point(wx + self.WIN_W // 2,
                                                 wy + self.WIN_H // 2)
        if monitor is None:
            # The window ended up outside every known monitor — most likely
            # because a monitor was unplugged. Fall back to monitor 0 and
            # let _ensure_on_screen() below relocate the window there.
            monitor = display.get_monitor(0)
        return monitor.get_geometry() if monitor else fallback

    def _ensure_on_screen(self) -> None:
        """Relocate Tux back onto a real monitor if his current position
        no longer belongs to any (e.g. the monitor he was on got
        unplugged, or resolution changed under him)."""
        display = Gdk.Display.get_default()
        if display is None:
            return
        wx, wy = self.win.get_position()
        monitor = display.get_monitor_at_point(wx + self.WIN_W // 2,
                                                 wy + self.WIN_H // 2)
        if monitor is not None:
            return  # still on a valid monitor, nothing to do

        primary = display.get_primary_monitor() or display.get_monitor(0)
        if primary is None:
            return
        geo = primary.get_geometry()
        self.win.move(geo.x + geo.width - self.WIN_W - 40,
                       geo.y + geo.height - self.WIN_H - 60)

    # ── sprites ─────────────────────────────────────────────────────────── #

    def _load_sprites(self) -> None:
        self.pixbufs.clear()
        max_w = int(160 * self.size)
        max_h = int(170 * self.size)
        for path in self.sprite_dir.glob("*.png"):
            img = Image.open(path).convert("RGBA")
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            loader = GdkPixbuf.PixbufLoader.new_with_type("png")
            loader.write(buf.getvalue())
            loader.close()
            self.pixbufs[path.stem] = loader.get_pixbuf()
        # Sprites just changed size (e.g. the "Size" slider in Settings) —
        # force the input shape to be recomputed on the next draw instead
        # of comparing against a signature computed for the old size.
        self._last_shape_sig = None

    # ── state helpers ───────────────────────────────────────────────────── #

    def _set_state(self, state: str, seconds: float = 1.4) -> None:
        self.state = state
        self.state_start = time.monotonic()
        self.state_duration = seconds

    def _say(self, text: str, seconds: float = 3.0) -> None:
        self.bubble_text = text
        self.bubble_until = time.monotonic() + seconds

    # ── interactions ────────────────────────────────────────────────────── #

    def jump(self)  -> None:
        if not self.is_dragging:
            self._set_state("jump", 0.65)

    def wave(self)  -> None:
        self._set_state("wave", 1.5)
        self._say(random.choice(("Hello!", "Nice to see you!", "(^_^)/")))

    def feed(self)  -> None:
        self._set_state("eat", 2.2)
        self._say("Mmm, fish! 🐟", 2.2)

    def wake(self)  -> None:
        if self.state in {"sleep", "sit-sad"}:
            self._set_state("yawn", 1.6)
            self._say("Yaaawn... hello!", 2.5)

    def play(self)  -> None:
        self._set_state("dance", 2.8)
        self._say(random.choice(("Let's play!", "Whee!", "(^o^)")), 2.2)

    def set_personality(self, name: str) -> None:
        self.personality = PERSONALITIES[name]
        self._say(f"I'm feeling {name.lower()} today.")

    # ── persistence ─────────────────────────────────────────────────────── #

    def _save_config(self) -> None:
        wx, wy = self.win.get_position()
        save_config({
            "size": self.size,
            "speed": self.speed,
            "opacity": self.opacity,
            "keep_above": self.keep_above,
            "animations_enabled": self.animations_enabled,
            "personality": self.personality.label,
            "pos_x": wx,
            "pos_y": wy,
        })

    def _quit(self) -> None:
        self._save_config()
        Gtk.main_quit()

    # ── mouse events ────────────────────────────────────────────────────── #

    def _on_press(self, _w, event) -> bool:
        if event.button == 1:
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.wave()
            else:
                self.drag_start_x = int(event.x)
                self.drag_start_y = int(event.y)
                self.press_x_root = int(event.x_root)
                self.press_y_root = int(event.y_root)
                self.is_dragging = False
                self.click_start_time = time.monotonic()
            return True
        if event.button == 3:
            self._show_menu(event)
            return True
        return False

    def _on_motion(self, _w, event) -> bool:
        if event.state & Gdk.ModifierType.BUTTON1_MASK:
            dx = abs(int(event.x_root) - self.press_x_root)
            dy = abs(int(event.y_root) - self.press_y_root)
            if dx > 4 or dy > 4:
                if not self.is_dragging:
                    self.is_dragging = True
                    self._set_state("drag", 60.0)
                nx = int(event.x_root) - self.drag_start_x
                ny = int(event.y_root) - self.drag_start_y
                self.win.move(nx, ny)
            return True
        return False

    def _on_release(self, _w, event) -> bool:
        if event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                self._set_state("idle", 0.1)
                # Dropped on another monitor? Make sure we're still valid.
                self._ensure_on_screen()
                self._save_config()
            elif time.monotonic() - self.click_start_time < 0.25:
                self.jump()
            return True
        return False

    # ── context menu ────────────────────────────────────────────────────── #

    def _show_menu(self, event) -> None:
        menu = Gtk.Menu()
        self._menu_item(menu, "🐟  Feed Tux",  self.feed)
        self._menu_item(menu, "Wake up",          self.wake)
        self._menu_item(menu, "Play",              self.play)

        p_item = Gtk.MenuItem(label="Personality")
        p_sub  = Gtk.Menu()
        for name in PERSONALITIES:
            self._menu_item(p_sub, name, lambda _=None, n=name: self.set_personality(n))
        p_item.set_submenu(p_sub)
        menu.append(p_item)

        self._menu_item(menu, "Settings…",  self._open_settings)
        menu.append(Gtk.SeparatorMenuItem())
        self._menu_item(menu, "Quit",    self._quit)

        menu.show_all()
        menu.popup_at_pointer(event)

    @staticmethod
    def _menu_item(menu: Gtk.Menu, label: str, callback) -> None:
        item = Gtk.MenuItem(label=label)
        item.connect("activate", lambda _: callback())
        menu.append(item)

    # ── settings dialog ─────────────────────────────────────────────────── #

    def _open_settings(self) -> None:
        dlg = Gtk.Dialog(title="Compa — Settings", parent=None, flags=0)
        dlg.set_keep_above(True)
        dlg.set_resizable(False)
        box = dlg.get_content_area()
        box.set_spacing(10)
        box.set_property("margin", 16)

        def _slider(label: str, lo: int, hi: int, val: int) -> Gtk.Adjustment:
            box.pack_start(Gtk.Label(label=label, xalign=0), False, False, 0)
            adj = Gtk.Adjustment(value=val, lower=lo, upper=hi, step_increment=5)
            box.pack_start(
                Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj),
                False, False, 0
            )
            return adj

        a_size  = _slider("Size (%)",  60, 150, int(self.size  * 100))
        a_speed = _slider("Speed (%)", 50, 160, int(self.speed * 100))
        a_op    = _slider("Opacity (%)", 40, 100, int(self.opacity * 100))

        # Personality
        box.pack_start(Gtk.Label(label="Personality", xalign=0), False, False, 0)
        combo_p = Gtk.ComboBoxText()
        active_idx = 0
        p_names = list(PERSONALITIES.keys())
        for idx, p_name in enumerate(p_names):
            combo_p.append_text(p_name)
            if p_name == self.personality.label:
                active_idx = idx
        combo_p.set_active(active_idx)
        box.pack_start(combo_p, False, False, 0)

        # Switches / CheckButtons
        chk_topmost = Gtk.CheckButton(label="Always on top")
        chk_topmost.set_active(self.keep_above)
        box.pack_start(chk_topmost, False, False, 0)

        chk_anim = Gtk.CheckButton(label="Animations enabled")
        chk_anim.set_active(self.animations_enabled)
        box.pack_start(chk_anim, False, False, 0)

        chk_autostart = Gtk.CheckButton(label="Launch at session startup")
        chk_autostart.set_active(is_autostart_enabled())
        box.pack_start(chk_autostart, False, False, 0)

        dlg.add_button("Apply", Gtk.ResponseType.OK)

        # Show all controls first so GTK calculates full window dimensions
        dlg.show_all()

        # Calculate exact position offset to the side of Tux, clamped to
        # the monitor Tux is currently on (not the full virtual desktop).
        wx, wy = self.win.get_position()
        mon = self._monitor_at_window()
        mx, my, mw, mh = mon.x, mon.y, mon.width, mon.height

        dw, dh = dlg.get_size()
        dw = max(dw, 340)
        dh = max(dh, 440)

        if wx - mx > dw + 50:
            target_x = wx - dw - 40
        else:
            target_x = wx + self.WIN_W + 40
        target_x = min(max(mx, target_x), mx + mw - dw)
        target_y = min(max(my + 30, wy - 120), my + mh - dh - 50)

        dlg.move(target_x, target_y)

        # Temporarily lower Tux window z-order so settings window is completely unobstructed
        self.win.set_keep_above(False)
        dlg.present()

        if dlg.run() == Gtk.ResponseType.OK:
            self.size    = a_size.get_value()  / 100.0
            self.speed   = a_speed.get_value() / 100.0
            self.opacity = a_op.get_value()    / 100.0

            p_selected = combo_p.get_active_text()
            if p_selected in PERSONALITIES:
                self.personality = PERSONALITIES[p_selected]

            self.keep_above = chk_topmost.get_active()
            self.animations_enabled = chk_anim.get_active()
            set_autostart(chk_autostart.get_active())

            self._load_sprites()
            self._save_config()

        self.win.set_keep_above(self.keep_above)
        dlg.destroy()

    # ── sprite selection ────────────────────────────────────────────────── #

    def _sprite_key(self, t: float) -> str:
        s = self.state
        if s == "idle":
            return "blink" if self.is_blinking else "idle"
        if s == "look":
            return "look-left" if int(t) % 2 == 0 else "look-right"
        if s in {"sleep", "yawn"}:
            return "sleep"
        if s == "walk":
            return "walk-a" if int(t * 6) % 2 == 0 else "walk-b"
        if s == "jump":
            return "jump" if "jump" in self.pixbufs else "celebrate"
        if s in {"stretch", "scratch"}:
            return "celebrate"
        if s == "wave":
            return "wave"
        if s == "eat":
            return "eat" if "eat" in self.pixbufs else "celebrate"
        if s == "dance":
            return "dance-a" if int(t * 6) % 2 == 0 else "dance-b"
        return "sit-sad"

    # ── drawing (Cairo) ─────────────────────────────────────────────────── #

    def _on_draw(self, _w, cr: cairo.Context) -> bool:
        # 1. Completely erase the window — this is what makes it transparent.
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        now = time.monotonic()
        elapsed = now - self.state_start
        progress = min(1.0, elapsed / max(0.001, self.state_duration))

        # 2. Vertical physics offset
        bob_y = 0.0
        if self.state == "jump":
            bob_y = -math.sin(progress * math.pi) * 44
        elif self.state == "walk":
            bob_y = math.sin(now * 14.0) * 3.0
        elif self.state == "dance":
            bob_y = math.sin(now * 12.0) * 4.5
        elif self.state == "sleep":
            bob_y = 7.0

        # 3. Draw sprite
        key    = self._sprite_key(now)
        pixbuf = self.pixbufs.get(key) or self.pixbufs.get("idle")
        if pixbuf:
            pw = pixbuf.get_width()
            ph = pixbuf.get_height()
            dx = (self.WIN_W - pw) / 2.0
            dy = self.WIN_H - ph + bob_y - 10

            # Soft ground shadow, drawn first so the sprite sits on top of
            # it. Shrinks/fades while airborne (jump) so it reads as a
            # ground-contact shadow rather than a decal glued to Tux.
            self._draw_shadow(cr, pw, bob_y)

            Gdk.cairo_set_source_pixbuf(cr, pixbuf, dx, dy)
            cr.paint_with_alpha(self.opacity)

            # Only Tux's actual (non-transparent) pixels should receive
            # clicks — the empty margin around him must click through to
            # whatever is on the desktop underneath.
            self._update_input_shape(key, pixbuf, dx, dy)

            # sleep Zzz
            if self.state == "sleep":
                cr.set_source_rgba(0.33, 0.40, 0.45, 0.88)
                cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                                    cairo.FONT_WEIGHT_BOLD)
                cr.set_font_size(13)
                zzz_x = dx + pw - 20
                zzz_y = dy + 28 - math.sin(now * 2.5) * 4
                cr.move_to(zzz_x, zzz_y)
                cr.show_text("Zzz...")

            # eat fish
            if self.state == "eat":
                cr.set_font_size(18)
                cr.move_to(dx + pw - 12, dy + 58)
                cr.show_text("🐟")

        # 4. Speech bubble
        if now < self.bubble_until and self.bubble_text:
            self._draw_bubble(cr, self.bubble_text)

        return False

    def _draw_shadow(self, cr: cairo.Context, pw: float, bob_y: float) -> None:
        """Soft radial-gradient ground shadow under Tux.

        Without this, Tux reads as a flat sticker floating over the
        desktop rather than a character actually standing on it. Cairo
        has no built-in blur, so a radial gradient fading to fully
        transparent gives a cheap, good-enough soft edge.
        """
        floor_y = self.WIN_H - 8.0
        cx = self.WIN_W / 2.0

        # While jumping, the higher off the ground Tux is, the smaller and
        # fainter the shadow — sells the "airborne" feeling instead of the
        # shadow just trailing him around like a fixed decal.
        lift = max(0.0, -bob_y) if self.state == "jump" else 0.0
        shrink = max(0.5, 1.0 - lift / 70.0)

        radius = (pw * 0.42) * shrink
        if radius <= 1.0:
            return
        squash = 0.30  # flatten the circle into a ground-hugging ellipse
        alpha = 0.30 * shrink

        cr.save()
        cr.translate(cx, floor_y)
        cr.scale(1.0, squash)
        gradient = cairo.RadialGradient(0, 0, 0, 0, 0, radius)
        gradient.add_color_stop_rgba(0.0, 0, 0, 0, alpha)
        gradient.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
        cr.set_source(gradient)
        cr.arc(0, 0, radius, 0, 2 * math.pi)
        cr.fill()
        cr.restore()

    def _draw_bubble(self, cr: cairo.Context, text: str) -> None:
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(10)
        ext = cr.text_extents(text)

        px, py = 12.0, 7.0
        r = 9.0
        bw = ext.width  + px * 2
        bh = ext.height + py * 2
        bx = (self.WIN_W - bw) / 2.0
        by = 8.0

        def _rounded_rect(offset_x: float = 0.0, offset_y: float = 0.0) -> None:
            x, y = bx + offset_x, by + offset_y
            cr.new_sub_path()
            cr.arc(x + bw - r, y + r,      r, -math.pi / 2, 0)
            cr.arc(x + bw - r, y + bh - r, r, 0,            math.pi / 2)
            cr.arc(x + r,      y + bh - r, r, math.pi / 2,  math.pi)
            cr.arc(x + r,      y + r,      r, math.pi,      3 * math.pi / 2)
            cr.close_path()

        # Faint soft shadow behind the bubble so it stays legible over both
        # light and dark/busy wallpapers, not just over the white fill's
        # own contrast against a same-toned background.
        _rounded_rect(0.0, 2.0)
        cr.set_source_rgba(0, 0, 0, 0.18)
        cr.fill()

        _rounded_rect()
        cr.set_source_rgba(1, 1, 1, 0.97)
        cr.fill_preserve()
        cr.set_source_rgba(0.10, 0.13, 0.18, 0.92)
        cr.set_line_width(1.6)
        cr.stroke()

        cr.set_source_rgb(0.10, 0.13, 0.18)
        tx = bx + (bw - ext.width)  / 2.0 - ext.x_bearing
        ty = by + (bh - ext.height) / 2.0 - ext.y_bearing
        cr.move_to(tx, ty)
        cr.show_text(text)

    # ── input shape (click-through) ─────────────────────────────────────── #

    def _update_input_shape(self, key: str, pixbuf: GdkPixbuf.Pixbuf,
                             dx: float, dy: float) -> None:
        """Restrict the clickable/draggable area of the window to Tux's
        actual, non-transparent pixels.

        Without this, the whole WIN_W x WIN_H rectangle is clickable —
        including the empty transparent margin around the sprite — which
        is exactly what makes Tux feel like "a window" instead of a
        character sitting on the desktop: clicking right next to him
        would swallow the click instead of passing it through to whatever
        is underneath.
        """
        gdkwin = self.win.get_window()
        if gdkwin is None:
            return

        # Cheap change-detection: only recombine the region when the
        # sprite or its position actually changed (position changes
        # continuously during jump/walk/dance because of bob_y, so we
        # round to whole pixels rather than recomputing on every ~40ms
        # tick for a sub-pixel wobble that wouldn't be visible anyway).
        sig = (key, round(dx), round(dy))
        if sig == self._last_shape_sig:
            return
        self._last_shape_sig = sig

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.WIN_W, self.WIN_H)
        shape_cr = cairo.Context(surface)
        Gdk.cairo_set_source_pixbuf(shape_cr, pixbuf, dx, dy)
        shape_cr.paint()

        region = Gdk.cairo_region_create_from_surface(surface)
        gdkwin.input_shape_combine_region(region, 0, 0)

    # ── life loop ───────────────────────────────────────────────────────── #

    def _random_event(self) -> None:
        choices = [("look", 2.0), ("stretch", 2.2), ("scratch", 1.7),
                   ("sleep", 4.8), ("walk", 2.6), ("dance", 2.6)]
        weights = [1.6, 1.0, 0.6,
                   self.personality.sleep,
                   self.personality.move,
                   self.personality.play]
        state, dur = random.choices(choices, weights=weights)[0]
        self._set_state(state, dur / (self.speed * self.personality.speed))
        if state == "walk":
            self.walk_direction = random.choice((-1, 1))
        if random.random() < 0.25:
            self._say(random.choice(self.personality.phrases))

    def _tick(self) -> bool:
        now = time.monotonic()

        # expire state
        if now > self.state_start + self.state_duration and self.state != "idle":
            self.state = "idle"

        # blink
        if self.state == "idle":
            if not self.is_blinking and now > self.next_blink:
                self.is_blinking = True
                self.next_blink  = now + 0.18
            elif self.is_blinking and now > self.next_blink:
                self.is_blinking = False
                self.next_blink  = now + random.uniform(2.5, 6.0)

        # walk — stay within the bounds of the monitor Tux is currently on,
        # not the combined virtual desktop (which would let him "walk" into
        # the gap between two monitors of different heights/positions).
        if self.state == "walk" and not self.is_dragging:
            wx, wy = self.win.get_position()
            step = max(1, round(3.5 * self.speed * self.personality.speed))
            step *= self.walk_direction
            mon = self._monitor_at_window()
            min_x = mon.x
            max_x = mon.x + mon.width - self.WIN_W
            if not (min_x <= wx + step <= max_x):
                self.walk_direction *= -1
                step *= -1
            self.win.move(wx + step, wy)

        # Every tick is cheap enough to also double-check we're still on a
        # real monitor (handles unplug / resolution change while running).
        self._ensure_on_screen()

        # Periodic safety-net save (in addition to the save-on-drag-end and
        # save-on-settings-applied calls) so a hard kill/crash doesn't lose
        # more than ~a minute of position/state.
        if now - self._last_autosave > 60.0:
            self._last_autosave = now
            self._save_config()

        # expire bubble
        if now > self.bubble_until:
            self.bubble_text = ""

        # random life
        if self.animations_enabled and not self.is_dragging and now - self.last_event > random.uniform(7.0, 14.0):
            self.last_event = now
            self._random_event()

        self.win.queue_draw()
        return True   # keep GLib timer running

    def run(self) -> None:
        Gtk.main()


if __name__ == "__main__":
    acquire_single_instance_lock()
    try:
        Companion().run()
    finally:
        release_single_instance_lock()
