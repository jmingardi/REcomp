# Resident Evil Recompiled 0.0.1 — local experimental release

Windows x64 portable build. This is the first local binary package, built from
the 0.0.3-dev development sources. The executable's Windows file/product version
is 0.0.1. Nothing is uploaded or published by the packaging script.

## Play

1. Extract the entire ZIP into a writable folder. Keep the EXE, assets, bios,
   mods and configuration files together.
2. Double-click **Run Resident Evil.cmd**. Python and development tools are
   not required. The EXE can also be opened directly from this folder.
3. Select your own **Resident Evil (USA), SLUS-00170** CUE in the launcher.
   Keep its BIN beside it. The disc is not included. Other editions have not
   been qualified for this build.
4. Choose Keyboard or your controller under Player 1 / Configure, adjust
   bindings and Save Profile. Settings contains window size/fullscreen options.
5. Press Play. F10 opens the in-game pause/display menu and resumes play.

Keyboard defaults: arrows = D-pad, X = Cross, S = Circle, Z = Square,
A = Triangle, Enter = Start, right Shift = Select. Original presentation is
4:3. The experimental 60 FPS Motion mod is off by default.

Preferences and new memory cards stay beside this executable; the wrapper
uses the local saves/ folder. Existing development saves/settings are not
copied. With both games closed, you may manually copy a backed-up card1.mcd
into this package's saves/ folder. Original game save/load remains unverified.
The wrapper records startup errors in last-run.log. No debug server is built
into this release.

## Scope

This is an experimental test build, not a completed campaign validation.
Earlier development QA reached the title, Jill selection, the opening door,
dining-room movement/camera changes and inventory navigation. Keyboard remaps
and virtual Xbox, DualShock, DualSense and generic SDL pads were exercised.
Physical-device button presses, full campaigns, combat, endings, original
memory-card save/load and audio listening have not all been validated.
Native coverage is incomplete; interpreter fallbacks remain in the runtime.

Requires Windows x64 and an OpenGL 3.3-capable graphics driver. This package
is tested on this local PC; support on other computers remains unqualified.
SDL is linked into the EXE. The Microsoft C++ runtime DLLs, assets and bundled
open-source OpenBIOS must remain next to it. No retail console BIOS is needed.

The repository's own integration license is undecided. Upstream notices are
in licenses/; PSXRecomp is PolyForm Noncommercial 1.0.0. Game content and rights
remain with their respective owners. This package is intended for local use
with your own supported game image.

Source: https://github.com/jmingardi/REcomp
release-manifest.json records the base revision, build inputs and file hashes.

## Rebuild locally

After following the repository bootstrap/generation instructions:

```powershell
cmake -S . -B build/local-release-0.0.1 -G "Visual Studio 17 2022" -A x64 -DCMAKE_CONFIGURATION_TYPES=Release -DRE1_QA_TOOLS=OFF -DPSX_STATIC_RUNTIME=ON "-DRE1_RELEASE_VERSION=0.0.1"
cmake --build build/local-release-0.0.1 --config Release --parallel 2 --target psx-runtime
python scripts/package_local_release.py
```

The packager refuses to overwrite an existing release folder or ZIP.
