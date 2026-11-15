# Validation routes

`routes/new-game-jill.json` is a timed pad-input route for a cold boot, title
menu, Jill selection, opening story, first door/dining room and inventory.
Times are wall-clock seconds on this test machine, not guaranteed scene
boundaries on other PCs. Each screenshot is taken **before** that event's input.
The numbers in `buttons` are active-low PS1 pad words, not guest-memory patches.

Run with:

```powershell
python scripts/smoke.py --seconds 180 --route qa/routes/new-game-jill.json
```

For host-controller QA, build with `python scripts/project.py build --qa`, then:

```powershell
python scripts/qa_control.py --ignore-real --host-route xbox --route qa/routes/new-game-jill.json
```

`--host-route` also accepts `dualshock`, `dualsense` and `generic`. This route
uses actual SDL virtual joystick buttons and asserts the observed active-low
pad state with guest overrides disabled. `--ignore-real` excludes only the
locally detected Xbox 360 from this QA process, so it cannot displace the
virtual pad. It does not disable the device in Windows.

`qa_control.py` stages an executable, immutable assets, private game config,
cards, bindings and mod state under `evidence/qa-*/`. `--reuse` restarts that
same profile without overwriting its preferences. The supervisor closes only
its own process after 25 minutes. Use `qa_control.rpc('quit')` from Python to
finish early; check `exit.json` because shutdown may close the debug response
socket before its reply is delivered. Do not run two such sessions at once:
the active-session pointer is shared.

The module's `key()` posts Windows key events only to the active QA process's
window, exercising the real SDL keyboard mapper. `hostpad()` controls the
QA-only `re1.qa.hostpad` command. Rebind/reset actions call the production UI
binding writer and reload callback; they do not prove physical capture input.
`capture()` records native game images/state. Use upstream `LNG_SCRIPT` via
`--launcher --ui-script` for launcher framebuffer captures, and the debug
`present_shot` command for composited F10-menu captures. These methods do not
capture another application's desktop.

Automated checks:

```powershell
python scripts/project.py test
python scripts/project.py test-ui
python scripts/project.py test-motion
```

The UI tests require SDL3 from an existing native build. Eleven selected
checks plus the motion-renderer check run; this is not the complete upstream test suite. Recorded results:
[QA_REPORT_2026-11-15.md](QA_REPORT_2026-11-15.md).

For the optional production motion mode, use `--smooth-60 on` (or `off`) on a
private `qa_control.py` session. This changes the normal mod selection and
does not override the host refresh. `--motion redraw` is a separate framework
experiment using a simulated 60 Hz host and should not be used as evidence
that the production mod caps a real high-refresh display.

`--capture-burst 24` makes each `present_shot` request capture 24 full-size
composed frames, labelled `r` (real) or `g` (generated), with their flip IDs.
The files are in composition order: a real image is composed before the
intermediate frame that leads to it. Capturing can disturb pacing; take rate
measurements separately. `capture()` also records the frame-generation counters.

Inspect the screenshots and `report.json`; a script returning success proves
frame advancement and a captured display, not correct actions or a finished
game. The runner records static-overlay and interpreter counters, uses private
cards and closes only its own native process. A route snapshot is retained for
new runs so later edits to the source timeline do not change their provenance.

Campaign acceptance remains manual: both characters, all major stage changes,
combat/death/retry, puzzles and item combinations, doors/cameras, map/files,
item boxes, original memory-card save/load, endings, credits, audio and physical
controllers. Keep route-specific outcomes in `PROJECT_STATUS.md` and curated
machine-readable summaries under `evidence/`.
