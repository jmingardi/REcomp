"""Verify a source or portable Windows ZIP and its SHA-256 companion."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

FORBIDDEN_SUFFIXES = {".cue", ".iso", ".chd", ".mcr", ".mcd", ".sav", ".pdb", ".lib"}
FORBIDDEN_PARTS = {"generated", "disc", "third_party", "build", "saves", "cache", "overlay_cache"}


def verify(archive_path, kind, version=None):
    archive_path = Path(archive_path)
    expected = archive_path.with_suffix(".zip.sha256").read_text(encoding="ascii").strip()
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if expected != f"{digest}  {archive_path.name}":
        raise ValueError("ZIP checksum or companion filename does not match")
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError("Duplicate ZIP entries or corrupt payload")
        for entry in archive.infolist():
            # Validate spelling before zipfile normalizes Windows separators.
            name = entry.orig_filename
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
                raise ValueError(f"Unsafe ZIP path: {name}")
            if set(part.lower() for part in path.parts) & FORBIDDEN_PARTS:
                raise ValueError(f"Development or personal data in ZIP: {name}")
            if path.suffix.lower() in FORBIDDEN_SUFFIXES:
                raise ValueError(f"Forbidden payload: {name}")
            if kind == "source" and path.suffix.lower() in {".exe", ".dll", ".bin"}:
                raise ValueError(f"Binary in source ZIP: {name}")
        if kind == "source":
            required = {"CMakeLists.txt", "game.toml", "VERSION", "dependencies.lock.json",
                        "scripts/project.py", "scripts/package_local_release.py", "src/windows_version.rc.in",
                        "scripts/build_release_candidate.py", "scripts/verify_release.py",
                        "scripts/private_build_inputs.py", "scripts/create_github_release.py",
                        ".github/workflows/release-candidate.yml", "docs/GITHUB_ACTIONS.md",
                        "docs/WINDOWS_PACKAGE.md"}
            if not required <= set(names):
                raise ValueError(f"Source ZIP missing required files: {sorted(required - set(names))}")
            if version and archive.read("VERSION").decode().strip() != version:
                raise ValueError("Source version mismatch")
        else:
            roots = {PurePosixPath(name).parts[0] for name in names}
            if len(roots) != 1:
                raise ValueError("Windows ZIP must contain one portable folder")
            prefix = roots.pop() + "/"
            files = {name.removeprefix(prefix) for name in names}
            required = {"Resident_Evil_Recompiled.exe", "Resident_Evil_Recompiled.execution.json",
                        "Run Resident Evil.cmd", "game.toml", "settings.toml", "VERSION", "README.txt",
                        "bios/openbios.bin", "bios/OpenBIOS.LICENSE", "release-manifest.json",
                        "msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"}
            if not required <= files:
                raise ValueError(f"Windows ZIP missing required files: {sorted(required - files)}")
            if any(name.lower().endswith(".bin") and name != "bios/openbios.bin" for name in files):
                raise ValueError("Only bundled OpenBIOS may be a .bin payload")
            manifest = json.loads(archive.read(prefix + "release-manifest.json"))
            if set(manifest["files"]) != files - {"release-manifest.json"}:
                raise ValueError("ZIP contents differ from release manifest")
            for name, expected_hash in manifest["files"].items():
                if hashlib.sha256(archive.read(prefix + name)).hexdigest() != expected_hash:
                    raise ValueError(f"Manifest hash mismatch: {name}")
            package_version = archive.read(prefix + "VERSION").decode().strip()
            if manifest["version"] != package_version or version and version != package_version:
                raise ValueError("Windows package version mismatch")
            if (manifest["debug_tools"] is not False or manifest["game_disc_included"] is not False
                    or manifest["personal_saves_included"] is not False):
                raise ValueError("Candidate must disable debug tools and exclude disc/personal saves")
    print(f"Verified {kind} ZIP: {archive_path.name}; SHA-256 {digest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--kind", required=True, choices=["source", "windows"])
    parser.add_argument("--version")
    args = parser.parse_args()
    verify(args.archive, args.kind, args.version)


if __name__ == "__main__":
    main()
