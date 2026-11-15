# Changelog

## 0.0.3-dev - 2026-11-15

- Move the full Resident Evil project into its own workspace subfolder;
  migrate active paths and preserve old CMake caches and QA evidence.
- Add opt-in 60 FPS Motion (Experimental) under Mods. Reuse the framework's
  recorded-geometry redraw and original-frame fallback, preserving guest timing.
- Bound the presentation request to 60 FPS and the host refresh; select OpenGL
  and its render thread for the session without saving forced pipeline settings.
- Clear the request and restore pipeline preferences before the next session.
- Add real/generated-frame burst QA, on/off comparisons and `test-motion`.

## 0.0.2-dev - 2026-11-15

- Enable the shared launcher for controller selection, controller/keyboard
  rebinding, window sizing, fullscreen and internal render resolution.
- Enable the F10 pause/display menu for this single-disc game.
- Make the keyboard binding grid adapt to available width so alternate binds fit.
- Open settings before ordinary play; retain `run --direct` for direct boot.
- Add SDL virtual-device QA, owned-window keyboard input, private settings/cards,
  recorded gameplay evidence and a reproducible `test-ui` command.

## 0.0.1-dev - 2026-11-14

- Initial native Windows build for SLUS-00170 with original-disc static overlays,
  OpenBIOS, reproducible setup and initial Jill gameplay smoke testing.
