# Resident Evil Recompiled - experimental Windows package

The VERSION file and the EXE's Windows file/product version identify this build.
Extract the whole ZIP into a writable folder and double-click
**Resident_Evil_Recompiled.exe**.
Keep the EXE, runtime DLLs, assets, bios, mods and configuration together.

In the launcher, select your own **Resident Evil (USA), PlayStation SLUS-00170**
CUE image; keep its BIN beside it. The disc is not included. Other editions,
regions and standalone extracted game files have not been qualified.
Choose controls under Player 1 / Configure, save the profile, then press Play.
F10 opens/resumes the in-game display menu. Settings and new saves remain
beside the EXE. If startup fails, the optional **Run Resident Evil.cmd** helper
records startup errors in last-run.log for troubleshooting.

Keyboard: arrows = D-pad, X = Cross, S = Circle, Z = Square, A = Triangle,
Enter = Start, right Shift = Select. Original presentation is 4:3; optional
60 FPS Motion is experimental and off by default.

Windows x64 and an OpenGL 3.3-capable driver are required. No retail BIOS is
needed; the package includes open-source OpenBIOS and its notice. No debug
server is built into the candidate. Preserve licenses/ and runtime files.

This is an experimental port. Selected automated tests and earlier local
opening-room QA do not validate both campaigns, combat, original memory-card
save/load, audio fidelity or every physical controller. Interpreter fallback
remains. See the source repository's PROJECT_STATUS.md for recorded coverage.
Fresh-machine compatibility remains to be tested.

Project-authored integration licensing is undecided. Dependencies retain their
own licenses; PSXRecomp uses PolyForm Noncommercial 1.0.0. Game content and
rights remain with their respective owners. Final artifact gameplay QA and
distribution decisions are described in the source project's release plan;
this README alone is not a validation receipt.

Source: https://github.com/jmingardi/REcomp
release-manifest.json records the source revision, inputs and payload hashes.
