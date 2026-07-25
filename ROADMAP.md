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

## V1.1 — Distribution

- Executables: AppImage first, `.deb` as a complement
- Public repository under MIT license
- Validated compatibility matrix: Ubuntu/GNOME, Fedora/GNOME,
  Mint/Cinnamon, KDE Plasma (X11 + XWayland)
- True multi-monitor support
- Demo video < 20s

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
