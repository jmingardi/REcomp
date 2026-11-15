# Original-disc overlay coverage

`overlays.json` declares the twelve PS-X EXE files in `PSX/PROG2/` on the
measured USA disc. The PS-X EXE headers provide load addresses: support/menu
programs load at `0x800E0000`; the seven stage programs load at `0x80105400`.
They reuse addresses, so compiled entries must be selected using original-byte
guards. Simply concatenating their dispatch tables would be incorrect.

This project uses upstream `tools/aot_overlay_pipeline.py`, method `psx_exe`,
strict producer bounds and an exact original-track SHA-1 gate. Its output is
`generated/overlays_static.c` plus split translation units, linked by CMake.
The original-disc audit checks the resulting entry identities and guards.

`evidence/overlay-files.json` records the observed file sizes, hashes and header
prefixes. `evidence/disc-inventory.json` lists the 941 ISO files. Neither file
contains a game executable or asset payload. `generated/AOT_STATIC_AUDIT.json`
is the full local audit receipt and explicitly says
`full_static_coverage_proven: false`.

All twelve known program files being represented is not proof that every
callback, transformed code block or campaign route executes natively. Preserve
the fallback and verify real gameplay. There is no runtime overlay compiler
bundled with this development build; uncovered code runs in the interpreter.

Regenerate with `python scripts/project.py overlays`. Full `generate` also runs
this step. The upstream patch adds a framework/profile lookup root to static
generation so nested dependencies work without a root-level framework alias.
