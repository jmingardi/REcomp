# Changelog

## Unreleased - 2026-11-16

- Prepare a GitHub Actions Windows pipeline for each main merge/push, with
  hosted Windows builds from private generated inputs, selected checks,
  ZIP/hash verification and automatic versions. Do not use a self-hosted PC runner.
  Create draft prereleases by default; require an explicit repository variable
  to enable public publishing. Keep Windows binaries off Actions artifacts.
- Read a commit/checksum-pinned private input repository using a read-only deploy
  key. Normalize text checkout line endings when checking codegen fingerprints.
- Allow isolated packaging output directories and a version-neutral candidate
  README; preserve the existing 0.0.1 local archive and its rebuild defaults.

## 0.0.3-dev - 2026-11-15

- Package the first local-only Windows binary release as 0.0.1, separate from
  the development version: embedded EXE version, debug tools off, portable
  launcher, clean preferences, app-local C++ runtime and ZIP/checksum.
- Verify an extracted copy outside the checkout through native title/menu
  input, quick-save thumbnail creation and clean close; keep public release
  and campaign qualification pending.

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
