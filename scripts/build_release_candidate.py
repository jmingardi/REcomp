"""Build and verify a portable candidate in a fresh Windows Actions checkout."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

from private_build_inputs import restore

ROOT = Path(__file__).resolve().parents[1]


def release_version(value):
    if not re.fullmatch(r"(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})", value):
        raise argparse.ArgumentTypeError("Use major.minor.patch, with components 0-9999 and no leading zeroes")
    return value


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


def candidate_version(override, run_number):
    if override:
        return release_version(override)
    if run_number is None:
        raise argparse.ArgumentTypeError("Supply --version or a GitHub workflow --run-number")
    return release_version(f"0.0.{run_number}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=os.environ.get("RELEASE_VERSION") or None)
    parser.add_argument("--run-number", type=int)
    parser.add_argument("--check-version-only", action="store_true")
    parser.add_argument("--inputs-archive", type=Path, default=ROOT / "_private-build-inputs/inputs.zip")
    args = parser.parse_args()
    try:
        args.version = candidate_version(args.version, args.run_number)
    except argparse.ArgumentTypeError as error:
        parser.error(str(error))
    if args.check_version_only:
        print(args.version)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                output.write(f"version={args.version}\n")
        return
    if os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}:
        parser.error("The binary job requires Windows x64")
    if sys.version_info < (3, 11):
        parser.error("Python 3.11+ is required")
    if not shutil.which("cmake") or not shutil.which("git"):
        parser.error("CMake and Git are required")
    private_digest = os.environ.get("RECOMP_BUILD_INPUTS_SHA256", "")
    if not args.inputs_archive.is_file() or not re.fullmatch(r"[0-9a-f]{64}", private_digest):
        parser.error("Check out the private input ZIP and configure RECOMP_BUILD_INPUTS_SHA256 first")
    if any((ROOT / path).exists() for path in ("build", "generated", "disc", "third_party", "dist")):
        parser.error("Use a fresh checkout; existing builds and generated data are preserved")

    project = ROOT / "scripts/project.py"
    run(sys.executable, project, "bootstrap")
    restore(args.inputs_archive, private_digest)
    framework = ROOT / "third_party/psxrecomp"
    stamp = subprocess.check_output(["cmake", f"-DROOT={framework.as_posix()}",
                                    f"-DPROFILE={(framework / 'bios/OpenBIOS.toml').as_posix()}", "-P",
                                    "tools/bios_emitter_fingerprint.cmake"], cwd=framework, text=True).strip()
    (framework / "generated/OpenBIOS.emitter.sha").write_text(stamp + "\n", encoding="utf-8")
    run(sys.executable, project, "test")
    build = ROOT / "build/game"
    run("cmake", "-S", ROOT, "-B", build, "-G", "Visual Studio 17 2022", "-A", "x64",
        "-DCMAKE_CONFIGURATION_TYPES=Release", "-DRE1_QA_TOOLS=OFF", "-DPSX_STATIC_RUNTIME=ON",
        f"-DRE1_RELEASE_VERSION={args.version}")
    run("cmake", "--build", build, "--config", "Release", "--parallel", "2", "--target", "psx-runtime")
    run(sys.executable, project, "test-ui")
    run(sys.executable, project, "test-motion")
    run(sys.executable, ROOT / "scripts/package_local_release.py", "--version", args.version,
        "--build", build, "--readme", ROOT / "docs/WINDOWS_PACKAGE.md", "--channel", "candidate")
    name = f"Resident-Evil-Recompiled-{args.version}-Windows-x64.zip"
    run(sys.executable, ROOT / "scripts/verify_release.py", ROOT / "dist" / name,
        "--kind", "windows", "--version", args.version)
    print("Candidate packaged. Gameplay smoke testing is still manual; publication obeys the repository switch.")


if __name__ == "__main__":
    main()
