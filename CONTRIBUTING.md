# Contributing

This is an experimental Windows x64 project for Resident Evil USA, SLUS-00170.
Read [PROJECT_STATUS.md](PROJECT_STATUS.md) before relying on a compatibility or
feature claim. Build instructions and the supported disc revision are in
[README.md](README.md).

Keep changes focused and preserve original game timing by default. Reuse the
pinned framework and shared UI where practical; record dependency changes in
`dependencies.lock.json` and keep local patches under `patches/`.

For relevant changes, run the selected checks:

```powershell
python scripts/project.py test
python scripts/project.py test-ui
python scripts/project.py test-motion
```

UI checks require an existing native build. Changes to runtime behavior also
need proportional gameplay testing with isolated cards. Describe exactly what
was tested; a successful build or boot is not a completed campaign test.

Bug reports should include the project revision, Windows version, CPU/GPU,
disc serial, selected options, steps to reproduce, and expected/actual results.
Share only relevant log excerpts and remove personal filesystem paths. Do not
attach disc images, extracted executables, generated game code, save states
or memory dumps to public issues or pull requests.

Keep status, README instructions and changelog entries synchronized with
changes. Upstream notices must remain intact. The license for project-authored
integration files is currently undecided; this document grants no additional
license to those files.
