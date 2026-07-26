# Compa — Roadmap

> The full product direction and guardrails are in
> [THE_COMPA_MANIFESTO.md](THE_COMPA_MANIFESTO.md) and [mvp.md](mvp.md).
> This document only lists the versions and what each one adds.

## Long-term vision

Compa has two phases, established from the start:

1. **V1 → V3: the foundation.** A purely living, emotional companion with
   no data or utility functions. This is what makes attachment possible.
2. **V4 and beyond: the community project.** Compa opens up as open source
   (MIT license) and can become truly useful through optional extensions
   ("domain packs") — never by modifying the foundation.

The foundation never changes shape to accommodate utility. Utility lives
only in extensions, never in base Tux.

---

## V1 — LIVE ✅ *(validated)*

Tux living on the Linux desktop: real transparency, drag and drop, click/
double-click, 5 personalities, full settings, autostart. Zero data,
zero utility — see exit criteria in [mvp.md](mvp.md).

## V1.1 — Distribution ✅ *(mostly done)*

- [x] Executables: AppImage (built on Ubuntu 22.04 for glibc compatibility,
      Python actually bundled, not symlinked) + `.deb`, both attached to
      the [v1.1 GitHub release](https://github.com/jomvick/compa/releases/tag/v1.1)
- [x] Public repository under MIT license
- [x] True multi-monitor support
- [ ] Validated compatibility matrix: Ubuntu/GNOME, Fedora/GNOME,
      Mint/Cinnamon, KDE Plasma (X11 + XWayland) — installs verified on
      Fedora/KDE only so far; still needs a run on a *different* machine
      than the one the AppImage was built on (the real portability test)
- [ ] Demo video < 20s

## V1.2 — Consolidation: stability & native feel

Before adding any new behavior (V2), Compa must stop feeling like "a script
someone ran" and start feeling like something that belongs on the desktop.
This phase adds no new animations or systems — it hardens what already
exists.

**Input shape / click-through** ✅
- [x] Apply an input shape mask to the window so only Tux's actual (non-
      transparent) pixels receive clicks — implemented via
      `Gdk.cairo_region_create_from_surface` + `input_shape_combine_region`,
      recomputed on sprite/position change (see `_update_input_shape` in
      `companion.py`).
- [x] Recompute the input shape whenever the sprite/size changes (resize in
      settings, personality change, new pose) — the shape signature is
      reset in `_load_sprites()` and re-derived each draw when the sprite
      key or its rounded position changes.

**Window/compositor robustness**
- [ ] Graceful fallback when no RGBA visual / no compositor is available
      (currently unverified — must not crash or render as a solid box).
- [x] Confirm/enforce Tux never appears in the taskbar, Alt-Tab, or
      Overview on GNOME/KDE/XFCE — explicit `skip_taskbar_hint` /
      `skip_pager_hint` added on top of the POPUP window type default.
- [x] Confirm clicking Tux never steals keyboard focus from the active
      window — `set_accept_focus(False)` added.
- [ ] Verify behavior across workspace/virtual desktop switches — Tux should
      either follow or stay put consistently, not vanish or duplicate.
      (Expected by design: override-redirect windows aren't managed by the
      WM's workspace logic, so Tux should simply always be visible on
      whichever workspace is active — needs confirming on a real GNOME/KDE
      session.)
- [ ] Verify behavior through screen lock / suspend-resume (no stuck state,
      no frozen animation loop, no zombie process).
- [ ] Handle display hot-plug / resolution change without Tux ending up
      off-screen (position is currently computed once at launch only).
- [x] Prevent launching a second instance — PID lock file at
      `~/.config/compa/compa.pid`, stale/unreadable locks are taken over
      automatically (see `acquire_single_instance_lock` /
      `release_single_instance_lock`).

**Persistence** ✅
- [x] Save settings (personality, size, speed, opacity, keep-above,
      animations toggle, last position) to `~/.config/compa/config.json` and
      restore them on next launch. Saved on: settings applied, drag end,
      clean quit, and a 60s safety-net autosave (in case of a hard
      kill/crash).

**Performance**
- [ ] Confirm idle CPU/GPU usage stays low over a long run (the 30-minute
      fluidity exit criterion, extended here to multi-hour idle sessions).
- [ ] Check for memory growth over several hours (leak check on the pixbuf
      cache and the GLib timeout loop).
- [ ] Confirm zero flicker/tearing on draw across the tested compositors.

**Visual integration**
- [ ] Add a soft, subtle drop shadow under Tux so he reads as sitting *on*
      the desktop rather than floating as a flat cut-out sprite.
- [ ] Check contrast of the speech bubble against both light and dark
      system themes/wallpapers.
- [ ] Settings dialog: match sizing/spacing conventions closely enough that
      it doesn't look like a bare default-GTK debug window.

This phase closes when Tux can run for a full multi-hour session, survive a
lock/unlock and a workspace switch, remember its settings, and never once be
clickable where there's nothing to see. Only then does V2 start.

## V2 — Desktop reactivity

- Light events (notification, new window, late hour) translated
  into emotion, never into displayed data
- Subtle ambient sound (jump, yawn)
- Memory/continuity: Tux learns user habits, small
  rituals (e.g., install anniversary)
- Day/night cycles and seasons

## V3 — Cross-platform

- Windows and macOS adapters (the portable core stays identical, only
  the desktop adapter changes)

## V4 — Domain packs (community phase begins)

- 2-3 official packs created internally (e.g., Coder, Fitness, Focus) to
  validate the concept before any external opening
- A domain pack changes vocabulary, emotion triggers, and
  Tux's accessories — never a panel, chart, or list
- The exact permissiveness (what a pack is allowed to display as
  an information "bonus") is **to be formalized before starting this
  version**, not before — see note in the manifesto

## V5 — Focus Companion

- The productivity dimension, expressed solely through Tux's mood and
  behavior — never any numbers, progress bars, or lists displayed
  continuously
- Light read-only connection to an external calendar/todo

## Post-V5 — Open ecosystem

- Public domain pack creation API, with technical guardrails
  (no free-text canvas access, only emotion/event hooks)
- Optional social presence between friends (distant, non-binding track)
