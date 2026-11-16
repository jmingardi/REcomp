# Resident Evil Recompiled

[REcomp](https://github.com/jmingardi/REcomp) is an experimental native Windows
x64 recompilation project for the original PlayStation Resident Evil. Build it
locally from your own supported disc image. This repository contains setup
sources, integration code, dependency patches and QA summaries.

Local development project for a native Windows x64 build of the original
PlayStation **Resident Evil (USA), SLUS-00170**. Uses PSXRecomp rather than a new
CPU translator or hardware runtime. This is an experimental port; see
[PROJECT_STATUS.md](PROJECT_STATUS.md) for actual validation and remaining work.

The main program and declared secondary programs are translated from your own
disc to C and compiled to x64. GPU, audio, CD-ROM and other PS1 devices are
provided by the upstream runtime. Its interpreter remains a fallback for code
that has not been covered. Native compilation does not establish complete
gameplay support, accuracy, or a wholly interpretation-free run.

Locally verified so far: boot/FMV, title menu, Jill selection, the opening door,
dining-room movement and camera changes, inventory navigation, custom keyboard
bindings and SDL virtual gamepads. Twelve selected upstream checks pass.
Full campaigns, physical-device input and original memory-card save/load remain
unverified. See [the recorded QA results](qa/QA_REPORT_2026-11-15.md).

## Run this local build

A portable **0.0.1 local binary release** is available in
`dist/Resident-Evil-Recompiled-0.0.1-Windows-x64-local/`, with a ZIP and SHA-256
file beside it. Double-click that folder's **Run Resident Evil.cmd**, then
browse to your own supported CUE. Python/build tools are unnecessary for the
portable package. See [local release instructions](docs/LOCAL_RELEASE_0.0.1.md)
and [its QA record](qa/LOCAL_RELEASE_0.0.1.md). This local binary package uses
the `0.0.3-dev` development sources; it has not been uploaded to GitHub.

After building locally, double-click **Run Resident Evil.cmd**, or run:

```powershell
python scripts/project.py run
```

The build stays local at `build/game/Release/Resident_Evil_Recompiled.exe`.
The wrapper supplies absolute config and disc paths, and disables the debug
listener during ordinary play. Keep your original CUE and BIN together in
`Resident Evil (USA)/`. An alternative location can be passed with `--disc`.

After the workspace move, previous absolute-path CMake caches were preserved
under `build/previous-location/`. Current Release executables and preferences
remain at their normal paths. Build directories are configured afresh for this
location; the next compilation may rebuild objects. Historical QA logs keep
their original recorded paths.

The launcher opens before play:

- **Player 1 / Configure**: choose Keyboard or an SDL-recognized controller.
  Xbox/XInput, DualShock, DualSense and generic gamepads use the shared SDL3
  input backend. Connect the pad before choosing it. Click a binding and press
  the replacement key/button; keyboard bindings also have an alternate slot.
  Scroll to reach the remaining bindings. **Save Profile** returns to the dashboard.
- **Settings**: choose window size and fullscreen Off, Borderless or Exclusive.
  The original presentation uses 4:3.
- **Mods > Internal Resolution**: select native 1x or a higher render scale,
  then **Play** to apply and save the selection. The default is 4x; GPU/memory
  limits can reduce the effective scale. Pre-rendered backgrounds and FMVs
  retain their original source detail.
- **Mods > 60 FPS Motion (Experimental)**: enable and press **Play**. This uses
  geometry redraw to add intermediate frames, up to 60 FPS and your display's
  refresh rate. Original gameplay, audio and FMV timing remain unchanged.
  It selects OpenGL and the render thread for this session. Restart after
  changing the option. It is off by default and falls back to original frames
  when a scene cannot be matched; it adds interpolation latency.
- **F10** during play opens the pause/display menu. Enter/Cross selects,
  arrows/D-pad navigate, Escape/Circle goes back. F10 resumes. Full keybind
  and controller configuration is in the launcher before play.

Default keyboard mapping: arrows = D-pad, **X = Cross**, S = Circle,
Z = Square, A = Triangle, Enter = Start, right Shift = Select. Preferences live
beside the executable in `settings.toml`, `keybinds.ini`, `input.ini` and
`mods/state.toml`. The wrapper keeps memory cards in `saves/`.
`python scripts/project.py run --direct` skips the launcher.

Controller support follows SDL's device recognition; “all” is the support
target, not a claim that every controller/driver/USB/Bluetooth combination has
been physically tested. Xbox 360 detection was observed locally. The four
controller families were exercised with SDL virtual devices, including
disconnect/reconnect, deadzones and actual game input.

## Reproduce the build

Requires Windows x64, Python 3.11+, Git, CMake 3.20+, Visual Studio 2022 with
Desktop development with C++ and the Windows SDK, plus Clang (the usual LLVM
installation is detected). These are the tools used here. Other hosts have
not been qualified for this project.

Clone the repository, then place your supported USA CUE/BIN pair in
`Resident Evil (USA)/` inside the clone:

```powershell
git clone https://github.com/jmingardi/REcomp.git
cd REcomp
```

Build and run:

```powershell
python scripts/project.py all
python scripts/project.py run
```

Or run individual steps:

```powershell
python scripts/project.py bootstrap
python scripts/project.py prepare
python scripts/project.py generate
python scripts/project.py build
python scripts/project.py test
python scripts/project.py test-ui
python scripts/project.py test-motion
```

`bootstrap` downloads the pinned framework and checksum-verifies its dependency
archives. It applies the patches under `patches/`; it refuses a different
framework revision or incompatible local changes. Network access is needed
for this development setup. No game file is downloaded or uploaded.

`prepare` verifies the original image before extracting its boot executable.
It leaves the original image, curated seeds and configuration intact.
`generate` translates both the boot executable and the 12 declared PS-X EXE
overlays, using the framework's original-disc extractor and audit pipeline.
An explicit Clang path can be supplied with `--clang 'C:/path/to/clang.exe'`.
First compilation can take several minutes.

The default CUE path is relative to this repository. To use an external image,
set `game.disc` in `game.toml` to its path, using forward slashes. The port
currently accepts only the exact measured image revision. The preparation,
generation, full-build and run commands also accept `--disc`.

## Observe a boot

```powershell
python scripts/project.py build --qa
python scripts/smoke.py --seconds 25
```

Smoke testing launches one hidden instance with isolated memory cards and a
temporary localhost debug port. It writes logs, screenshots and JSON under
`evidence/smoke-*/`, then closes that instance. It checks frame advancement and
capture availability; a person still has to inspect the images. A successful
observation is not a completed gameplay test. `--press-start` injects brief
Start presses through the upstream pad interface.

## Dependencies and distribution

GitHub Actions release preparation is documented in
[docs/GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md). Merges/pushes to `main` build a
portable Windows EXE package on GitHub-hosted Windows machines using private
generated build inputs. No runner is installed on the maintainer's PC;
players only extract the download and select their own supported CUE/BIN.
Each successful run creates an unpublished GitHub draft by default. Automatic
public publishing requires `RELEASE_PUBLISH_ENABLED=true` in repository variables.
That switch is off while unset. The pipeline is prepared locally and has
not yet been activated or run on GitHub.

- [PSXRecomp](https://github.com/RetroPortingToolKit/psxrecomp), pinned in
  `dependencies.lock.json`: primary framework, PolyForm Noncommercial 1.0.0.
- [Recomp UI](https://github.com/RetroPortingToolKit/recomp-ui): pinned shared
  launcher, rebinding and display controls, MIT. A local patch makes the
  keyboard binding grid fit narrower windows.
- [PS1Recomp](https://github.com/PS1Recomp/ps1-recomp): comparison reference,
  GPL-3.0; its code is not linked here. Fetch optionally with
  `python scripts/project.py bootstrap --reference`.
- OpenBIOS and its notice are provided by the framework under MIT. No retail
  Sony BIOS is required by this configuration.

Preserve upstream licenses and attribution for any eventual distribution.
Original discs, extracted executables, generated game code, saves and build
outputs are excluded by `.gitignore`. The current source setup builds game
code locally from the user's own image. Native release downloads and catalog
submission are not available. A license for the project-authored integration
files has not yet been selected; dependencies retain their own licenses.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development and bug-report guidance.

[Decomp Buddy](https://decompbuddy.com/) is a potential future catalog for the
native port. `.recomp.json` is starter community metadata, with status
`exploring`; it is not a submission receipt or a promise of browser play.
See [docs/RELEASE_PLAN.md](docs/RELEASE_PLAN.md) before preparing a release.

`python scripts/package_source.py` creates a source-only setup ZIP and SHA-256
file under `dist/`. The archive includes local metadata and upstream notices;
it excludes the disc, extracted executables, generated code and native builds.
