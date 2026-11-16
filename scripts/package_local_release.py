"""Stage a clean, local-only portable Windows build; no disc or personal data."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXE = "Resident_Evil_Recompiled.exe"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.0.1")
    parser.add_argument("--build", type=Path, default=ROOT / "build/local-release-0.0.1")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--readme", type=Path, default=ROOT / "docs/LOCAL_RELEASE_0.0.1.md")
    parser.add_argument("--channel", choices=["local", "candidate"], default="local")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        parser.error("Version must be major.minor.patch")
    build = args.build.resolve()
    cache = (build / "CMakeCache.txt").read_text(encoding="utf-8")
    for setting in ("RE1_QA_TOOLS:BOOL=OFF", "PSX_DEBUG_TOOLS:BOOL=OFF",
                    f"RE1_RELEASE_VERSION:STRING={args.version}"):
        if setting not in cache.splitlines():
            raise ValueError(f"Release build must have {setting}")
    source = build / "Release"
    suffix = "-local" if args.channel == "local" else ""
    name = f"Resident-Evil-Recompiled-{args.version}-Windows-x64{suffix}"
    stage = args.output_dir.resolve() / name
    archive_path = stage.with_name(name + ".zip")
    if stage.exists() or archive_path.exists() or archive_path.with_suffix(".zip.sha256").exists():
        raise FileExistsError(f"Preserve existing release: {stage}")

    # Allowlisted inputs deliberately exclude settings, saves, sidecars and caches.
    files = [(source / EXE, EXE),
             (source / "Resident_Evil_Recompiled.execution.json", "Resident_Evil_Recompiled.execution.json"),
             (args.readme.resolve(), "README.txt")]
    for folder in ("assets", "bios", "mods/bundled"):
        for path in sorted((source / folder).rglob("*")):
            if path.is_file():
                files.append((path, path.relative_to(source).as_posix()))
    for path in sorted((ROOT / "licenses").glob("*")):
        if path.is_file():
            files.append((path, "licenses/" + path.name))
    for path in sorted((ROOT / "third_party/psxrecomp/runtime/licenses").glob("*")):
        if path.is_file():
            files.append((path, "licenses/runtime/" + path.name))
    notices = {
        "SDL3-LICENSE.txt": build / "_deps/sdl3-src/LICENSE.txt",
        "SDL3-HIDAPI-BSD-LICENSE.txt": build / "_deps/sdl3-src/src/hidapi/LICENSE-bsd.txt",
        "Dear-ImGui-LICENSE.txt": ROOT / "third_party/recomp-ui/src/third_party/imgui/LICENSE.txt",
        "fonts-NOTICE.md": ROOT / "third_party/recomp-ui/assets/common/fonts/NOTICE.md",
        "images-NOTICE.md": ROOT / "third_party/recomp-ui/assets/common/img/NOTICE.md",
    }
    files.extend((path, "licenses/" + name) for name, path in notices.items())
    # MSVC uses the DLL CRT even when SDL is linked statically. Ship the
    # redistributable app-local files, never copies from Windows/System32.
    instance = next(line.split("=", 1)[1] for line in cache.splitlines()
                    if line.startswith("CMAKE_GENERATOR_INSTANCE:INTERNAL="))
    visual_studio = Path(instance)
    redists = sorted((visual_studio / "VC/Redist/MSVC").glob("[0-9]*"),
                     key=lambda path: tuple(map(int, path.name.split("."))))
    crt = redists[-1] / "x64/Microsoft.VC143.CRT"
    for name in ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"):
        files.append((crt / name, name))
    redist_notices = sorted((visual_studio / "Licenses").glob("*/Redist.txt"))
    if not redist_notices:
        raise FileNotFoundError("Visual Studio redistributable notice")
    files.append((redist_notices[0], "licenses/Microsoft-Visual-Studio-Redist.txt"))
    for path, _ in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    for required in ("bios/openbios.bin", "bios/OpenBIOS.LICENSE",
                     "assets/fonts/LatoLatin-Regular.ttf", "assets/img/pad_digital.tga",
                     "mods/bundled/re1.enhancement.smooth-motion/0.1.0/manifest.toml"):
        if required not in {target for _, target in files}:
            raise ValueError(f"Missing runtime payload: {required}")
    stage.mkdir(parents=True)
    for path, target in files:
        destination = stage / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    config = (ROOT / "game.toml").read_text(encoding="utf-8")
    # The shared runtime parser requires [recompiler]/seeds even in a compiled
    # binary. Preserve its metadata; these build inputs are not read for play.
    config = re.sub(r'^disc = .*$', 'disc = ""', config, flags=re.MULTILINE)
    (stage / "game.toml").write_text(config, encoding="utf-8")
    (stage / "settings.toml").write_text(
        '[video]\nwindow_width = 1280\nfullscreen = 0\naspect_ratio = "4:3"\n'
        'render_thread = false\npresent_thread = false\nframe_generation = false\n'
        '\n[controller]\np1_device = "keyboard"\np1_mode = "digital"\n'
        '\n[memcard]\ndir = "saves"\n', encoding="utf-8")
    (stage / "Run Resident Evil.cmd").write_bytes((
        '@echo off\nsetlocal\npushd "%~dp0"\nset "PSX_DEBUG_SERVER=0"\n'
        f'"%~dp0{EXE}" --game "%~dp0game.toml" --bios "%~dp0bios\\openbios.bin" '
        '--memcard-dir "%~dp0saves" --launcher %* > "%~dp0last-run.log" 2>&1\n'
        'set "RE1_EXIT=%ERRORLEVEL%"\npopd\n'
        'if not "%RE1_EXIT%"=="0" (\necho Resident Evil exited with code %RE1_EXIT%. See last-run.log.\npause\n)\n'
        'exit /b %RE1_EXIT%\n').replace('\n', '\r\n').encode("utf-8"))
    (stage / "VERSION").write_text(args.version + "\n", encoding="ascii")
    safe = "safe.directory=" + ROOT.as_posix()
    revision = subprocess.check_output(["git", "-c", safe, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    inputs = ["CMakeLists.txt", "game.toml", "src/windows_version.rc.in",
              "src/settings_menu.cpp", "src/smooth_motion.cpp", "dependencies.lock.json",
              "scripts/package_local_release.py"]
    manifest = {
        "version": args.version,
        "channel": "experimental-local-only" if args.channel == "local" else "experimental-release-candidate",
        "platform": "Windows x64",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_project_version": (ROOT / "VERSION").read_text().strip(),
        "source_base_commit": revision,
        "source_inputs_sha256": {path: digest(ROOT / path) for path in inputs},
        "readme_sha256": digest(args.readme.resolve()),
        "debug_tools": False, "game_disc_included": False, "personal_saves_included": False,
        "dependencies": json.loads((ROOT / "dependencies.lock.json").read_text())["dependencies"],
        "files": {p.relative_to(stage).as_posix(): digest(p) for p in sorted(stage.rglob("*")) if p.is_file()},
    }
    (stage / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Only OpenBIOS is allowed as a .bin; never accidentally ship the game image.
    for path in stage.rglob("*"):
        if path.is_file() and (path.suffix.lower() in {".cue", ".iso", ".chd", ".mcr", ".mcd", ".sav", ".lib", ".pdb"}
                               or path.suffix.lower() == ".bin" and path != stage / "bios/openbios.bin"):
            raise ValueError(f"Forbidden release payload: {path}")
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, (Path(stage.name) / path.relative_to(stage)).as_posix())
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Release ZIP failed its CRC check")
        if set(archive.namelist()) != {f"{stage.name}/{path}" for path in manifest["files"]} | {f"{stage.name}/release-manifest.json"}:
            raise ValueError("Release ZIP payload differs from the staged manifest")
    checksum = digest(archive_path)
    archive_path.with_suffix(".zip.sha256").write_text(f"{checksum}  {archive_path.name}\n", encoding="ascii")
    print(f"Local folder: {stage}\nZIP: {archive_path}\nSHA-256: {checksum}")


if __name__ == "__main__":
    main()
