# Resident Evil Recompiled status

Updated 2026-11-16. Version: `0.0.3-dev`. Experimental local Windows x64 port;
not a published release or a completed campaign validation.

GitHub source repository: https://github.com/jmingardi/REcomp, branch `main`.
The independent repository contains authored source/setup files and curated QA
metadata. Original discs, extracted/generated game code, native builds, caches,
personal saves and raw QA captures remain local. Public native releases and
a Decomp Buddy listing are still pending.

GitHub Actions release preparation added locally on 2026-11-16:
`.github/workflows/release-candidate.yml` builds each merge/push to main; owner-only
manual runs are also available. A hosted source-package check precedes a
GitHub-hosted Windows x64 build from a privately stored generated-input bundle.
The earlier local-PC runner proposal was withdrawn after the public-repository
security concern; no self-hosted runner is used. The workflow runs selected checks,
packages the versioned EXE/runtime and verifies payload hashes/exclusions.
Windows ZIP/checksum attach directly to a new draft prerelease, without public
Actions binary artifacts. Versions default to `0.0.<workflow run number>`.
Automatic publication requires repository variable `RELEASE_PUBLISH_ENABLED=true`;
unset means draft only. The switch has not been enabled. Player downloads require only their
own supported CUE/BIN, without compilation or GitHub credentials. Setup and
release-note templates are in `docs/GITHUB_ACTIONS.md`, `docs/WINDOWS_PACKAGE.md`
and `docs/RELEASE_NOTES_TEMPLATE.md`. GitHub CLI authentication was restored and
verified as `jmingardi`; authenticated commands require the Windows user credential
context outside the restricted workspace session. GitHub now has an active
`Protect main` ruleset, `.github/CODEOWNERS`, and `RELEASE_PUBLISH_ENABLED=false`.
Private input repository created at https://github.com/jmingardi/REcomp-build-inputs
on 2026-11-16 at the user's request. GitHub reports visibility `PRIVATE`, default
branch `main`. The workflow now fetches a pinned private input commit using a
read-only deploy key (`RECOMP_INPUTS_DEPLOY_KEY`), checks
`RECOMP_BUILD_INPUTS_SHA256`, and restores the schema-2 snapshot. Text codegen
fingerprints normalize LF/CRLF while preserving patch bytes. The approved input
bundle is now uploaded privately at commit `2fa1c61eb490e534fcfe867ab5dba07a72b7e3b6`,
SHA-256 `76f9949ee4418f57d833052e79cd6fd3a9021600e2e65739b7b5d1644d76ca73`.
The read-only deploy key and encrypted Actions secret are configured, along with
the pinned commit/checksum variables. Public publishing remains `false`. Public
Actions allow official GitHub actions with full-SHA pinning, default read-only
tokens, no PR approvals by workflows, and approval for all external contributors.
Actions are disabled in the private storage repository. Workflow PR #1 merged
as `9b372f40237fe2cb338d5cbdb3dfaeff70c7fa9c`, activating the main-merge trigger.
Run `43903891890` passed hosted source packaging/regressions and the private SSH
checkout, then stopped because the pinned upstream already tracks matching MIT
OpenBIOS C. The restore now reuses matching OpenBIOS files without rewriting
them, while still refusing existing game-generated files or mismatching BIOS C.
The fix has 17 local regression checks and actionlint validation; a complete
hosted Windows build remains under validation. No self-hosted runner, draft
release or public binary release has been created by this setup yet.

Local pipeline verification: actionlint 1.7.12 passed; all 17 packaging/input/
publication-policy regression checks passed, as did the existing seven recompiler,
four UI and one motion checks. UI verification first needed the relocated SDL3
static test dependency rebuilt; the repeated UI checks passed. A private generated
snapshot (81 payload files, about 18 MB compressed) round-tripped into an isolated
directory with matching fingerprints/hashes. Portable candidate ZIP/checksum
verification passed using the existing 0.0.1 local executable; no fresh cloud
compilation or new final-gameplay smoke test is claimed. Validation artifacts are
isolated under `dist/pipeline-validation/`; the private input ZIP/checksum is under
ignored `dist/private-inputs/`. Existing local 0.0.1 artifacts were preserved.

Local binary package **0.0.1** was built separately from these `0.0.3-dev`
sources in `build/local-release-0.0.1/`, with QA/debug tools disabled and Windows
file/product version 0.0.1. Portable folder, ZIP and SHA-256 companion are under
`dist/Resident-Evil-Recompiled-0.0.1-Windows-x64-local*`. It includes runtime
assets, OpenBIOS, app-local Microsoft C++ DLLs, notices and fresh preferences;
no game disc, personal cards or development toolchain. Nothing was uploaded.
An extracted copy outside the source tree passed launcher/controller/display
view checks, native boot/title and keyboard menu input, quick-save thumbnail
creation, frame progression and clean close. F10 was sent to open/resume;
its framebuffer was not captured in this sandbox. This is a limited smoke
test, not campaign or original memory-card save/load validation. See
`qa/LOCAL_RELEASE_0.0.1.md` and `docs/LOCAL_RELEASE_0.0.1.md`.

Workspace layout updated 2026-11-15: the complete project now lives under
`Resident Evil Recomp/`. Original disc files, saves, dependencies, generated
code, builds, release artifacts and QA evidence moved together. The unrelated
PS2 ISO remains in the parent workspace. Active settings/disc references were
migrated; historical evidence retains its recorded paths. Old absolute-path
CMake caches are preserved in `build/previous-location/`; current Release
outputs remain under `build/<target>/Release/` and new build trees use the
new location. This is a layout change; the native executable is unchanged.
Verified after the move: all 11 recorded disc/executable/save/settings
fingerprints matched (migrated settings retain their original backups), player
preferences were preserved, and the PS2 ISO's size/timestamp were unchanged.
Fresh CMake configuration and pinned-dependency validation passed. The
relocated launcher verified the disc, and a private 15-second native boot
observation reached frame 896 with visible Capcom output, zero dispatch/segment
misses and clean exit. Evidence: `evidence/qa-20261115T134000432911Z/` and
`evidence/smoke-20261115T134004423348Z/`. The source setup ZIP/checksum was
regenerated with the layout documentation.

## Measured input

- Original Resident Evil USA, `SLUS-00170`; ISO volume `RESIDENT_EVIL`.
- One `MODE2/2352` data track, 680,379,504 bytes.
- Track SHA-1: `dddb34b5928925d8025e5a5bad9d200a0e4f09b7`.
- Boot EXE `SLUS_001.70`, 653,312 bytes; load `0x80010000`, entry `0x8005F8A0`,
  declared text `0x9F000`, stack `0x801FFFF0`.
- Boot EXE SHA-256:
  `8a42060d85794e151cdfb880e7625ec382e9c654a90852de8f7447a4b7a07b63`.
- 941 ISO files; 12 additional PS-X EXE programs under `PSX/PROG2/`.
- Original BIN/CUE were read in place and were not modified.

## Implemented

- Pinned PSXRecomp `b263b8552e5b8838b317f8921dfde8b6aca97904` as the primary
  translator/runtime. PS1Recomp is a separate, unlinked reference checkout.
- Disc verification, boot extraction, initial 949 JAL/entry seeds, strict
  translation, OpenBIOS generation and reproducible Windows build commands.
- Boot translation produced 2,545 dispatch entries across 54 C shards.
  These are discovery results, not a count of hand-verified game functions.
- Original-disc overlay profile for all 12 known secondary executables.
  Audit: 12 recipes, 27,336 guarded variants, 22 generated translation units;
  all guards match their known input bytes. Full execution coverage is unproven.
- Native x64 executable with those static overlay units linked, SDL3/OpenGL,
  bundled MIT OpenBIOS, local saves, and a local launch wrapper.
- Four tracked framework patches: MSVC constexpr capture compatibility,
  portable release/acquire renderer atomics, and explicit framework lookup
  for static overlay generation, plus bounded presentation-only generation.
  Project CMake enables MSVC C11 atomics for
  the sources that need them and selects Release for the VS generator.
- Checksum-verified dependency prefetch avoids this session's CMake/Schannel
  credential error without disabling TLS validation.
- Isolated hidden smoke runner with screenshots, input timelines, frame/CPU/CD
  and static-overlay observations. Ordinary launch disables the debug listener.

## Validation so far

### 0.0.3-dev: optional 60 FPS motion

- Added `Mods > 60 FPS Motion (Experimental)`, disabled by default. The
  SLUS-00170 package activates the existing recorded-geometry redraw pipeline
  at up to 60 FPS, capped by the host display. It selects OpenGL/the render
  thread for the session, without changing the guest clock or game code.
- Original-frame fallback remains active for scenes the matcher rejects.
  Menus/FMV retain original timing; interpolation adds latency. Full campaigns,
  combat timing and every foreground-mask interaction are not qualified.
- The dependency patch requests a bounded presentation rate and restores
  pipeline preferences before the next session. It does not change the
  framework's camera fitting, vertex placement or frame-generation algorithm.
- Production-mod measurements on the real high-refresh host: eight seconds
  of turning produced 29.999 original + 29.999 generated frames/second, with
  60.123 guest VBlanks/second and 59.998 total presents/second. A movement/
  transition sample produced 57.832 total presents/second, illustrating that
  the ceiling is not an all-scene guarantee.
- Inspected full-size real/generated frames. Twelve sample pairs differed
  within the character region while preserving the fixed background.
- Enabled the option using the actual launcher checkbox, then completed the
  20-step Jill opening route with a virtual DualSense on the final build.
  Dining-room movement, camera changes and inventory were inspected; unknown
  dispatches/static segment misses were zero. After turning the option off
  and restarting, generation/render thread were both off; the private
  checkpoint and controls worked at 59.883 guest VBlanks/second. QA exited cleanly.
- Native build succeeded; 12 selected tests passed (7 recompiler, 4 UI,
  1 frame-generation core). Reproduce the last with `project.py test-motion`.
- Current executable: `build/game/Release/Resident_Evil_Recompiled.exe`,
  33,078,272 bytes, SHA-256
  `7c4b0116e9dbbc0be8f147718fab0b8af40150418befd8f1fc7944cce81b4872`.
  Release-optimized development build; ordinary launch disables debug access.
- QA details: `qa/QA_MOTION_2026-11-15.md`; curated observations:
  `evidence/motion-qa-summary.json`. Original input/cards and personal
  preferences were preserved; experiments use private profiles.
- Source-only setup artifact: `dist/resident-evil-recomp-source-0.0.3-dev.zip`
  with a regenerated `.zip.sha256` companion. No public release was made.

### 0.0.2-dev: controls, display and playable QA

- Shared Recomp UI pinned at `3c641560c32ab55dc169f21daa9ba210a121eb96`
  (MIT), enabled before play. Controller selection, keyboard primary/alternate
  binds, per-GUID controller maps/deadzones, window sizes, fullscreen choices
  and internal resolution reuse the existing framework implementations.
- Fourth dependency patch makes keyboard binding columns respond to available
  width. At 1100 pixels both binding slots fit; later rows scroll vertically.
- Registered the shared F10 pause/display menu for this single-disc title.
  Full rebinding remains in the pre-game launcher. Ordinary play opens that
  launcher; `run --direct` is available. Existing saves are preserved.
- Eleven selected automated checks passed: the previous seven recompiler
  checks and four UI checks for PSX binds, pad modes, internal resolution and
  settings persistence. `test-ui` is now reproducible through `project.py`.
- Played Jill's opening route through the first door into the dining room
  using an SDL virtual Xbox controller. No guest pad override was active.
  Tested movement, turning, camera changes and inventory. The later observation
  reached frame 22,194 with zero unknown dispatches/static segment misses.
  Repeated all 20 route steps with a virtual DualSense on the final executable;
  inspected dining-room movement, camera changes and reopened inventory.
  Final observation: frame 12,009, no guest override, zero unknown dispatches
  and zero static segment misses; process exited with code 0.
- All four virtual profiles (Xbox, DualShock, DualSense, generic) passed neutral,
  Cross, D-pad, left-stick movement, deadzone, Start and hotplug/release checks.
  Xbox 360 physical-device detection was observed. Physical button presses and
  USB/Bluetooth transport behavior remain unverified.
- Changed keyboard binds through real launcher controls, restarted and played
  with Cross=K, Start=I, Up=U; old Cross=X was inactive. Inputs reached the
  normal SDL mapper, without guest pad overrides. Controller per-GUID remaps
  passed live reload, restart persistence and reset through the production
  binding writer/reload callback (not a physical capture test).
- Window size 1280x960 persisted and matched the runtime drawable. F10 paused
  and resumed. Borderless, Exclusive and Off transitions were observed through
  the real menu, with framebuffer captures. Internal resolution 1x was selected
  through the launcher, reached the renderer and persisted after restart.
- QA profiles contain private cards, config, bindings and mod state. The
  staging tool preserves their settings across restarts; personal cards and
  profiles are not used. Report: `qa/QA_REPORT_2026-11-15.md`; curated evidence:
  `evidence/settings-qa-summary.json`. Raw captures remain local and ignored.
- 0.0.2-dev executable: `build/game/Release/Resident_Evil_Recompiled.exe`,
  33,075,712 bytes, SHA-256
  `f16e4cdcf724c2d7644790a0d70d58d0c8a6fe61b228f9b17d09e33778b6c979`.
  Release optimization, QA tools compiled in, debug listener disabled by the
  ordinary launch wrapper. No public release/submission was made.
- Source-only setup artifact: `dist/resident-evil-recomp-source-0.0.2-dev.zip`,
  with a regenerated `.zip.sha256` companion. Includes the new C++ integration,
  QA helper, pinned UI dependency/patch/license and recorded results; excludes
  disc data, generated game code, executables and personal saves.

### Historical 0.0.1-dev bring-up

- Native build succeeded with Visual Studio 2022/MSVC 19.38 and Windows SDK
  10.0.22621. OpenGL context: NVIDIA RTX 3080, driver 621.01, Windows host.
- Seven selected upstream tests passed: control-flow metadata, recompiler
  patches, BIOS address model, error exits, cross-page delay slots, AOT methods,
  and MSVC continuation code generation.
- Broader upstream `aot_overlay_discovery` test was attempted and cannot finish
  its real loaded-DLL regression without MinGW GCC. This environment does not
  have that compiler. No claim that the full upstream suite passed.
- Boot captures visually inspected: Capcom animation, opening FMV, Resident
  Evil title, New Game/Load Game menu, Jill selection and mansion introduction.
- A 100-second scripted run ended cleanly at guest frame 6,010 with zero
  reported unknown dispatches and zero reported static segment misses.
- That run recorded 31,875 static-overlay hits. It also recorded 52,639
  interpreter fallback dispatches; their complete causes and instruction cost
  have not been profiled. This is not a claim of 100% native execution.
- Full `python scripts/project.py all --qa` completed successfully: verification,
  translation, audited overlay reuse, native rebuild and all seven selected tests.
- A 180-second follow-up reached the dining room through the first door and
  opened the inventory. Direction inputs changed its menu selection; the route
  was then refined to close the inventory before testing character movement.
- The refined 180-second route visually confirmed walking, turning, camera
  transitions and reopening inventory in Jill's dining room. It exited cleanly
  at guest frame 10,818, with zero reported unknown dispatches and zero reported
  static segment misses. Evidence: `evidence/smoke-20261114T214501826283Z/`,
  including screenshots 15 through 20 and the retained input-route snapshot.
- Historical 0.0.1-dev executable:
  `build/game/Release/Resident_Evil_Recompiled.exe`, 31,584,768 bytes, SHA-256
  `caf2146f0954252406f69d64ca027b2cf784e95af15d2f81cf06aafa1a1ca438`.
  This is a Release-optimized development build with QA tools compiled in;
  `Run Resident Evil.cmd` disables the debug listener for ordinary play.
- The source-only ZIP was extracted into a separate local directory. Its
  bootstrap fetched the exact framework, applied all three patches and verified
  dependencies; preparation then accepted the original disc supplied by path.
  A fresh-machine full compilation remains untested.
- Initial screenshots/logs: `evidence/smoke-20261114T212952791628Z/`,
  `evidence/smoke-20261114T213516627644Z/`, and
  `evidence/smoke-20261114T213656957509Z/`. Local evidence is gitignored.

## Remaining

- Listen to audio; compare timing, graphics and FMVs against an original-game
  reference. Capture availability alone does not validate fidelity.
- Both campaigns, combat, doors, stage transitions, save/load, inventory,
  endings and physical-controller behavior need a recorded test matrix.
- Investigate residual interpreter paths proportionally, without disabling
  fallback or fabricating function/overlay coverage.
- Current upstream MSVC warnings include a bool comparison and a const-qualifier
  mismatch. Their gameplay impact is not qualified; they are not compile errors.
- Before public distribution: choose project licensing/ownership, validate a
  fresh-machine source setup and prepare accurately scoped release artifacts.
  Source hosting is configured at the GitHub repository above. No standalone
  website, native download or Decomp Buddy listing has been published.
