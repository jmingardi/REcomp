"""Reproducible Windows bring-up using the pinned upstream tools (Python 3.11+)."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / "third_party/psxrecomp"
BUILD = ROOT / "build"
EVIDENCE = ROOT / "evidence"
BOOT_SHA256 = "8a42060d85794e151cdfb880e7625ec382e9c654a90852de8f7447a4b7a07b63"
TEST_TARGETS = ["control_flow_metadata_test", "bios_address_model_test", "recompiler_patch_test"]


def run(*args, cwd=ROOT, log=None):
    command = [str(a) for a in args]
    print(subprocess.list2cmdline(command), flush=True)
    if log:
        EVIDENCE.mkdir(exist_ok=True)
        with (EVIDENCE / log).open("w", encoding="utf-8") as output:
            result = subprocess.run(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            print((EVIDENCE / log).read_text(encoding="utf-8", errors="replace")[-10000:])
        result.check_returncode()
    else:
        subprocess.run(command, cwd=cwd, check=True)


def config():
    return tomllib.loads((ROOT / "game.toml").read_text(encoding="utf-8"))


def bootstrap(reference=False):
    dependencies = json.loads((ROOT / "dependencies.lock.json").read_text())["dependencies"]
    for dep in dependencies:
        if dep.get("optional", False) and not reference:
            continue
        path = ROOT / "third_party" / dep["name"]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            run("git", "clone", "--no-checkout", "--depth", "1", dep["url"], path)
            run("git", "-C", path, "fetch", "--depth", "1", "origin", dep["commit"])
            run("git", "-C", path, "checkout", "--detach", dep["commit"])
        actual = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        if actual != dep["commit"]:
            raise ValueError(f"{path} is at {actual}; expected {dep['commit']}. Preserve local work before changing revisions.")
    for dep in dependencies:
        if dep.get("optional", False) and not reference:
            continue
        checkout = ROOT / "third_party" / dep["name"]
        for relative_patch in dep.get("patches", []):
            patch = ROOT / relative_patch
            check = subprocess.run(["git", "apply", "--check", str(patch)], cwd=checkout,
                                   capture_output=True)
            if check.returncode == 0:
                run("git", "apply", patch, cwd=checkout)
            else:
                reverse = subprocess.run(["git", "apply", "--reverse", "--check", str(patch)],
                                         cwd=checkout, capture_output=True)
                if reverse.returncode:
                    raise ValueError(f"Cannot safely apply {patch.name}; inspect local dependency changes")
    # Use Python's TLS stack: CMake/curl's Schannel can fail in managed Windows sessions.
    # Every archive is checked against upstream's pinned digest before CMake sees it.
    archive_root = FW / "third_party"
    for line in (archive_root / "deps.manifest").read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, filename, expected, url = line.split()
        if name not in {"psx_libchdr", "psx_libwebp", "SDL3", "psx_zlib"}:
            continue
        target = archive_root / filename
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Dependency digest mismatch: {target}")
            continue
        print(f"Downloading pinned dependency: {name}", flush=True)
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Downloaded dependency digest mismatch: {name}")
        target.write_bytes(data)


def disc_tools():
    if not FW.exists():
        raise ValueError("Run bootstrap first")
    sys.path.insert(0, str(FW / "tools"))
    from aot_overlay_pipeline import Disc
    return Disc


def prepare(disc=None):
    cfg = config()
    cue = Path(disc).resolve() if disc else ROOT / cfg["game"]["disc"]
    original = disc_tools()(cue)
    expected = cfg["prepare_disc"]
    binary = Path(original.binary)
    if binary.stat().st_size not in expected["known_sizes"]:
        raise ValueError("Unsupported disc size; this project targets SLUS-00170 only")
    with binary.open("rb") as source:
        sha1 = hashlib.file_digest(source, "sha1").hexdigest()
    if sha1 not in expected["known_sha1"]:
        raise ValueError("Unsupported disc SHA-1; original files were not changed")
    boot = original.read(expected["boot_exe"])
    if hashlib.sha256(boot).hexdigest() != BOOT_SHA256:
        raise ValueError("Boot executable digest mismatch")
    (ROOT / "disc").mkdir(exist_ok=True)
    (ROOT / cfg["game"]["exe"]).write_bytes(boot)
    EVIDENCE.mkdir(exist_ok=True)
    # Do not overwrite manually curated seeds or the game configuration.
    with tempfile.TemporaryDirectory(dir=BUILD if BUILD.exists() else ROOT) as temporary:
        seeds = Path(temporary) / "seeds.txt"
        run(sys.executable, FW / "tools/new_project_layout/probe_disc.py", cue,
            "--json-out", EVIDENCE / "disc_probe.json", "--write-seeds", seeds)
        destination = ROOT / cfg["recompiler"]["seeds"]
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(seeds, destination)
    files = [{"path": n, "lba": lba, "size": size}
             for n, (lba, size) in sorted(original.files.items())]
    inventory = {"file_count": len(files), "disc_sha1": sha1,
                 "extensions": dict(Counter(Path(f["path"]).suffix for f in files)), "files": files}
    (EVIDENCE / "disc-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print(f"Verified {cfg['game']['id']}; {len(files)} files. Original image unchanged.")


def compiler(name):
    return BUILD / "recompiler/Release" / (name + ".exe")


def configure_compiler():
    run("cmake", "-S", FW / "recompiler", "-B", BUILD / "recompiler",
        "-G", "Visual Studio 17 2022", "-A", "x64", "-DPSXRECOMP_ENABLE_CHD=OFF",
        log="configure-recompiler.log")


def overlays(clang=None, disc=None):
    clang = clang or shutil.which("clang") or r"C:\Program Files\LLVM\bin\clang.exe"
    if not Path(clang).is_file():
        raise ValueError("Clang is required for the overlay workflow; supply --clang path/to/clang.exe")
    disc_args = ["--disc", Path(disc).resolve()] if disc else []
    run(sys.executable, FW / "tools/aot_overlay_pipeline.py", "static",
        "--profile", ROOT / "aot/overlays.json", "--game-toml", ROOT / "game.toml",
        "--recompiler", compiler("psxrecomp-game"), "--project-root", FW,
        "--work-dir", BUILD / "aot", "--gcc", clang, "--workers", "2", "--reuse", *disc_args,
        log="aot-static.log")
    print((EVIDENCE / "aot-static.log").read_text(encoding="utf-8", errors="replace")[-3000:])


def generate(clang=None, disc=None):
    if not (ROOT / config()["game"]["exe"]).exists():
        prepare(disc)
    if hashlib.sha256((ROOT / config()["game"]["exe"]).read_bytes()).hexdigest() != BOOT_SHA256:
        raise ValueError("Extracted boot executable changed; run prepare to restore it from the supported disc")
    configure_compiler()
    run("cmake", "--build", BUILD / "recompiler", "--config", "Release", "--parallel", "2",
        "--target", "psxrecomp-game", "psxrecomp-bios", log="build-recompiler.log")
    run(compiler("psxrecomp-game"), "--config", ROOT / "game.toml", log="generate-game.log")
    run(compiler("psxrecomp-bios"), "--config", "bios/OpenBIOS.toml", cwd=FW, log="generate-bios.log")
    stamp = subprocess.check_output(["cmake", f"-DROOT={FW.as_posix()}",
                                    f"-DPROFILE={(FW / 'bios/OpenBIOS.toml').as_posix()}", "-P",
                                    "tools/bios_emitter_fingerprint.cmake"], cwd=FW, text=True).strip()
    (FW / "generated/OpenBIOS.emitter.sha").write_text(stamp + "\n", encoding="utf-8")
    overlays(clang, disc)


def build(qa=False):
    run("cmake", "-S", ROOT, "-B", BUILD / "game", "-G", "Visual Studio 17 2022", "-A", "x64",
        "-DCMAKE_CONFIGURATION_TYPES=Release",
        f"-DRE1_QA_TOOLS={'ON' if qa else 'OFF'}", "-DPSX_STATIC_RUNTIME=ON",
        log="configure-game.log")
    run("cmake", "--build", BUILD / "game", "--config", "Release", "--parallel", "2",
        "--target", "psx-runtime", log="build-game.log")


def test():
    configure_compiler()
    run("cmake", "--build", BUILD / "recompiler", "--config", "Release", "--parallel", "2",
        "--target", *TEST_TARGETS, "psxrecomp-game", log="build-tests.log")
    selected = "^(" + "|".join(TEST_TARGETS + ["recompiler_error_exit", "overlay_cross_page_delay_codegen",
                                              "aot_overlay_methods", "msvc_cps_codegen"]) + ")$"
    run("ctest", "--test-dir", BUILD / "recompiler", "-C", "Release", "--output-on-failure",
        "-R", selected, log="tests.log")
    print((EVIDENCE / "tests.log").read_text(encoding="utf-8", errors="replace"))


def test_ui():
    sdl = BUILD / "game/_deps/sdl3-build"
    if not (sdl / "SDL3Config.cmake").exists():
        raise ValueError("Build the native game first to provide its pinned SDL3 to UI tests")
    targets = ["recomp-ui-psx-binds", "recomp-ui-launcher-pad-mode",
               "recomp-ui-launcher-internal-resolution", "recomp-ui-launcher-settings"]
    run("cmake", "-S", ROOT / "third_party/recomp-ui", "-B", BUILD / "ui-tests",
        "-G", "Visual Studio 17 2022", "-A", "x64", "-DCMAKE_CONFIGURATION_TYPES=Release",
        f"-DSDL3_DIR={sdl.as_posix()}", "-DCMAKE_C_FLAGS=/DLNG_SDL3=1 /DSDL_MAIN_HANDLED=1",
        log="configure-ui-tests.log")
    run("cmake", "--build", BUILD / "ui-tests", "--config", "Release", "--parallel", "2",
        "--target", *(target + "-test" for target in targets), log="build-ui-tests.log")
    run("ctest", "--test-dir", BUILD / "ui-tests", "-C", "Release", "--output-on-failure",
        "-R", "^(" + "|".join(targets) + ")$", log="tests-ui.log")
    print((EVIDENCE / "tests-ui.log").read_text(encoding="utf-8", errors="replace"))


def test_motion():
    run("cmake", "-S", FW / "runtime", "-B", BUILD / "motion-tests",
        "-G", "Visual Studio 17 2022", "-A", "x64", "-DCMAKE_CONFIGURATION_TYPES=Release",
        "-DPSX_ENABLE_VULKAN=OFF", "-DPSX_RECOMP_UI=OFF", "-DPSX_NETPLAY=OFF", "-DPSX_REWIND=OFF",
        log="configure-motion-tests.log")
    run("cmake", "--build", BUILD / "motion-tests", "--config", "Release", "--parallel", "2",
        "--target", "frame_gen_test", log="build-motion-tests.log")
    run("ctest", "--test-dir", BUILD / "motion-tests", "-C", "Release", "--output-on-failure",
        "-R", "^frame_gen_test$", log="tests-motion.log")
    print((EVIDENCE / "tests-motion.log").read_text(encoding="utf-8", errors="replace"))


def launch(disc=None, direct=False):
    executable = BUILD / "game/Release/Resident_Evil_Recompiled.exe"
    if not executable.exists():
        raise ValueError("Native executable is missing; run generate then build")
    cue = Path(disc).resolve() if disc else ROOT / config()["game"]["disc"]
    os.environ.setdefault("PSX_DEBUG_SERVER", "0")
    run(executable, "--game", ROOT / "game.toml", "--disc", cue,
        "--bios", BUILD / "game/Release/bios/openbios.bin",
        "--memcard-dir", ROOT / "saves", "--no-launcher" if direct else "--launcher")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["bootstrap", "prepare", "generate", "overlays", "build", "test", "test-ui", "test-motion", "run", "all"])
    parser.add_argument("--disc", help="Local supported CUE override (never copied or uploaded)")
    parser.add_argument("--reference", action="store_true", help="Also fetch PS1Recomp for comparison")
    parser.add_argument("--qa", action="store_true", help="Build upstream debug tools for local smoke testing")
    parser.add_argument("--clang", help="Clang executable for upstream static overlay generation")
    parser.add_argument("--direct", action="store_true", help="Boot directly; normally show controller/display settings first")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("This initial build workflow targets Windows x64 with Visual Studio 2022")
    if args.command in ("bootstrap", "all"):
        bootstrap(args.reference)
    if args.command in ("prepare", "all"):
        prepare(args.disc)
    if args.command in ("generate", "all"):
        generate(args.clang, args.disc)
    if args.command == "overlays":
        overlays(args.clang, args.disc)
    if args.command in ("build", "all"):
        build(args.qa)
    if args.command in ("test", "all"):
        test()
    if args.command in ("test-ui", "all"):
        test_ui()
    if args.command in ("test-motion", "all"):
        test_motion()
    if args.command == "run":
        launch(args.disc, args.direct)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
