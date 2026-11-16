# Local Windows binary 0.0.1 — 2026-11-15

Artifact: `dist/Resident-Evil-Recompiled-0.0.1-Windows-x64-local.zip`

ZIP SHA-256:
`266d046dc529fa526b03e8433c3e26f417b87578c050ae3fa3571b5c90d81c3f`

This is a local experimental package from the 0.0.3-dev source tree. It has
not been published. The source base revision and changed build-input hashes
are recorded in the package's release-manifest.json. Windows file and product
versions are 0.0.1, with the prerelease flag set. Separate MSVC x64 Release
build: RE1_QA_TOOLS=OFF, PSX_DEBUG_TOOLS=OFF, static SDL3, OpenGL renderer.

## Checks on this exact artifact

- ZIP CRC and every payload hash matched the staged manifest. No original
  CUE/BIN, extracted game executable, generated code directories, personal
  cards, compiler libraries or development toolchain were included. The only
  .bin payload is the bundled open-source OpenBIOS.
- Extracted the package into a fresh temporary directory outside the checkout;
  launched it with a working directory elsewhere. The native text guard used
  the original disc fallback rather than a loose development game executable.
- Actual packaged Run Resident Evil.cmd opened and closed successfully without
  invoking Python. Captured and visually reviewed fresh launcher, keyboard
  binding and display-settings views. Fresh preferences showed Keyboard,
  1280x960, fullscreen off and OpenGL; no disc was preselected.
- A second fresh temporary copy also opened its launcher by running the EXE
  directly with no command-line arguments and a different working directory.
  Its neighboring configuration/assets were discovered and it exited cleanly.
- Supplied the supported original CUE through the native --disc argument.
  Observed original boot animation, Resident Evil title and New Game menu.
  Posted Enter to this process's window; the title advanced to its main menu.
- Pressed F5 through ordinary Windows input. Four quick-save requests produced
  native .pst files and VRAM thumbnails in isolated saves. Visually reviewed
  128x96 thumbnails; these establish visible game output, not complete OpenGL
  presentation fidelity. One transition sample was black; subsequent title
  and menu samples were visible.
- Native frame reports advanced from frame 323 to 1742 during observation,
  with most measured guest VBlank intervals near 59.9 Hz. This does not claim
  60 rendered gameplay FPS.
- Sent F10 twice for pause/resume. The reporting interval reflects a pause,
  followed by resumed progression; the in-game menu framebuffer was not
  captured. Posted WM_CLOSE to the owned window; exit code was zero.
- Inspected native imports and observed MSVCP140.dll, VCRUNTIME140.dll and
  VCRUNTIME140_1.dll loaded from the extracted package, not an assumed global
  Visual C++ installation. Windows system DLLs/Universal CRT remain OS inputs.

Local evidence: `evidence/qa-local-release-0.0.1/final-pass/`, including
report.json, game/launcher logs, launcher views and native thumbnail PNGs.
Initial PrintWindow captures were black because it could not read this
driver's OpenGL surface; desktop screenshot capture was unavailable in the
sandbox. Final native thumbnails were used instead. The earlier failed
packaging tests were corrected before the final artifact was created.

## Limits

The final package was smoke-tested through its title/menu, not replayed through
a campaign. Earlier development gameplay/controller coverage remains recorded
separately. Full campaigns, combat, endings, original memory-card save/load,
actual physical controller button presses and audio listening remain outside
this release check. Quick-save creation is not save-state restore validation.
Upstream compiler warnings remain; this is not a warning-free or stable release.
No new widescreen or 60 FPS gameplay claims are made. The source tree and the
user's development settings/cards were preserved; all tests used private data.
