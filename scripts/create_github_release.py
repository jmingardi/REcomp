"""Attach verified ZIPs to a new GitHub draft; publish only with --publish."""
import argparse
import os
from pathlib import Path
import re
import subprocess

from build_release_candidate import release_version
from verify_release import verify

ROOT = Path(__file__).resolve().parents[1]


def release_commands(version, assets, commit, publish=False):
    tag = f"v{version}"
    commands = [["gh", "release", "create", tag, *map(str, assets), "--draft", "--prerelease",
                 "--latest=false", "--target", commit, "--title",
                 f"Resident Evil Recompiled {version} (experimental)",
                 "--notes-file", "docs/RELEASE_NOTES_TEMPLATE.md"]]
    if publish:
        commands.append(["gh", "release", "edit", tag, "--draft=false", "--prerelease", "--latest=false"])
    return commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, type=release_version)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    commit = os.environ.get("SOURCE_COMMIT", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        parser.error("SOURCE_COMMIT must be the workflow's full source commit SHA")
    source_version = (ROOT / "VERSION").read_text().strip()
    windows = ROOT / "dist" / f"Resident-Evil-Recompiled-{args.version}-Windows-x64.zip"
    source = ROOT / "dist" / f"resident-evil-recomp-source-{source_version}.zip"
    verify(windows, "windows", args.version)
    verify(source, "source", source_version)
    assets = [windows, windows.with_suffix(".zip.sha256"), source, source.with_suffix(".zip.sha256")]
    # An existing tag could target different source even without a release.
    # Exit 2 means no matching tag; network/auth failures must fail closed.
    probe = subprocess.run(["git", "ls-remote", "--exit-code", "--tags", "origin", f"refs/tags/v{args.version}"],
                           cwd=ROOT, capture_output=True, text=True)
    if probe.returncode == 0:
        raise ValueError("Release tag already exists; refusing to reuse it")
    if probe.returncode != 2:
        raise RuntimeError(f"Could not check remote release tag: {probe.stderr}")
    for command in release_commands(args.version, assets, commit, args.publish):
        subprocess.run(command, cwd=ROOT, check=True)
    print("Published experimental prerelease." if args.publish else "Created unpublished draft prerelease.")


if __name__ == "__main__":
    main()
