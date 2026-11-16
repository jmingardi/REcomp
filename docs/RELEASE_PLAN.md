# Release and future catalog listing

Initial target: Windows x64, original USA SLUS-00170 disc, stock single-player
game behavior. The source uses PSXRecomp and Recomp UI pinned by commit, plus
four framework patches and one responsive keyboard-layout patch.
Source repository: https://github.com/jmingardi/REcomp. The repository contains
setup sources and integration code. Local-only binary package 0.0.1 is under
`dist/`; see `LOCAL_RELEASE_0.0.1.md` and `../qa/LOCAL_RELEASE_0.0.1.md`.
Public binary release artifacts and a catalog listing remain pending.
Actions release preparation is defined in
[GITHUB_ACTIONS.md](GITHUB_ACTIONS.md): build/test a portable Windows candidate
on GitHub-hosted Windows machines after each main merge/push, using a privately
stored generated-source bundle instead of a local-PC runner. Attach the ZIP to an unpublished draft,
and publish automatically only after `RELEASE_PUBLISH_ENABLED=true` is explicitly
configured. The variable is explicitly `false` for now. Private input hosting
and read-only access are configured, and the workflow is activated. The first
full hosted Windows build is under validation; an initial matching-OpenBIOS
restore issue is being corrected.
Publisher identity and project licensing have not
been selected. Do not invent them or submit a catalog listing automatically.

Before a playable release:

1. Verify a clean build from the source setup, with a locally supplied disc.
2. Repeat boot, title-menu input and both character selections on the final build.
3. Test both campaigns: opening rooms, doors, camera transitions, inventory,
   map/files, combat, item boxes, save/load, death/retry, all stage transitions,
   endings and credits. Record exact routes and known failures.
4. Compare rendering, audio, FMVs, timing and input to the original behavior.
   Record runtime interpretation/overlay coverage without calling a metadata
   audit complete execution coverage.
5. Verify physical gamepads, keyboard mapping, window/fullscreen transitions,
   quitting, ordinary saves and a second cold boot. Use isolated QA saves.
6. Resolve build warnings that affect behavior and any native crashes.
7. Choose a project license and distribution model, retain all upstream notices,
   and validate the final archive contains no original disc data, retail BIOS,
   personal saves or accidental extracted/generated game payloads.
8. Produce checksums and accurate screenshots for the exact artifact tested.

Future Decomp Buddy listing information:

- Game: Resident Evil (1996), PlayStation; USA SLUS-00170.
- Project: Resident Evil Recompiled (working project name).
- Type: static recompilation using PSXRecomp, with fallback execution disclosed.
- Platform: Windows x64 only until other hosts are tested.
- Required input: user's own supported CUE/BIN image; bundled MIT OpenBIOS.
- Status and features: only what final artifact testing establishes.
- Source URL, download URL, maintainer details and screenshots: fill after the
  user chooses where to publish and approves the concrete public artifact.

The `.recomp.json` file is community metadata from the framework's helper.
Do not assume a catalog accepts that format, hosts binaries, or has accepted
this project. Recheck the site's current submission workflow at release time.
