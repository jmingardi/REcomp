"""Package/restore PRIVATE generated build inputs; never attach this ZIP to a release."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "private-build-inputs.json"
GAME = r"generated/(?:SLUS_001\.70_(?:dispatch\.c|decls\.h|full_[0-9]+\.c|full\.ranges)|overlays_static(?:_[0-9]+)?\.c)"
BIOS = r"third_party/psxrecomp/generated/OpenBIOS_(?:dispatch|full)\.c"


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fingerprints(root=ROOT):
    files = [root / name for name in ("game.toml", "dependencies.lock.json", "scripts/project.py", "aot/overlays.json")]
    files += sorted((root / "patches").glob("*.patch"))
    files += sorted((root / "seeds").glob("*.txt"))
    # Text checkout line endings differ between local Windows and hosted runners.
    # Patch files are marked -text and retain their exact bytes.
    return {path.relative_to(root).as_posix(): hashlib.sha256(
        path.read_bytes() if path.suffix == ".patch" else path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest() for path in files}


def allowed(name):
    return bool(re.fullmatch(GAME, name) or re.fullmatch(BIOS, name))


def pack(output_dir, root=ROOT):
    files = [p for folder in (root / "generated", root / "third_party/psxrecomp/generated")
             for p in folder.glob("*") if p.is_file() and allowed(p.relative_to(root).as_posix())]
    payload = {path.relative_to(root).as_posix(): sha256(path) for path in sorted(files)}
    required = {"generated/SLUS_001.70_dispatch.c", "generated/SLUS_001.70_decls.h", "generated/overlays_static.c",
                "third_party/psxrecomp/generated/OpenBIOS_dispatch.c", "third_party/psxrecomp/generated/OpenBIOS_full.c"}
    if not required <= payload.keys() or not any(re.fullmatch(r"generated/SLUS_001\.70_full_[0-9]+\.c", n) for n in payload):
        raise ValueError("Missing generated inputs; run project.py prepare/generate with your local disc first")
    if not any(re.fullmatch(r"generated/overlays_static_[0-9]+\.c", n) for n in payload):
        raise ValueError("Missing generated overlay shards")
    manifest = {"schema": 2, "private": True, "created_utc": datetime.now(timezone.utc).isoformat(),
                "codegen_inputs_sha256": fingerprints(root), "files": payload}
    output_dir.mkdir(parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("private-build-inputs-%Y%m%dT%H%M%S%fZ.zip")
    archive_path = output_dir / name
    with zipfile.ZipFile(archive_path, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST, json.dumps(manifest, indent=2) + "\n")
        for name in payload:
            archive.write(root / name, name)
    digest = sha256(archive_path)
    archive_path.with_suffix(".zip.sha256").write_text(f"{digest}  {archive_path.name}\n", encoding="ascii")
    print(f"PRIVATE INPUTS - keep out of the public repo/releases: {archive_path}")
    print(f"RECOMP_BUILD_INPUTS_SHA256={digest}")
    return archive_path


def restore(archive_path, expected_sha256, root=ROOT):
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or sha256(archive_path) != expected_sha256:
        raise ValueError("Private build-input ZIP does not match the pinned SHA-256")
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.orig_filename for entry in entries]
        if len(names) != len(set(names)) or any(n != MANIFEST and not allowed(n) for n in names):
            raise ValueError("Private build-input ZIP contains duplicate or unapproved paths")
        if any(entry.file_size > 400_000_000 for entry in entries) or sum(entry.file_size for entry in entries) > 1_000_000_000:
            raise ValueError("Private input bundle exceeds the bounded generated-source size")
        manifest = json.loads(archive.read(MANIFEST))
        if manifest.get("schema") != 2 or manifest.get("private") is not True:
            raise ValueError("Unsupported private input manifest")
        if manifest["codegen_inputs_sha256"] != fingerprints(root):
            raise ValueError("Codegen inputs changed; regenerate and refresh the private bundle and SHA-256")
        if set(manifest["files"]) != set(names) - {MANIFEST}:
            raise ValueError("Private input ZIP differs from its manifest")
        # Validate every member before writing anything. No extractall, binaries,
        # scripts, saves, executable paths, absolute paths or traversal are allowed.
        existing_bios = set()
        for name, digest in manifest["files"].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError(f"Private input hash mismatch: {name}")
            destination = root.joinpath(*PurePosixPath(name).parts)
            if not destination.resolve().is_relative_to(root.resolve()):
                raise ValueError("Refusing to escape the checkout or overwrite existing generated inputs")
            if destination.exists():
                # Pinned upstream tracks its MIT OpenBIOS generated C. Reuse it
                # only when identical apart from checkout line endings.
                if (re.fullmatch(BIOS, name) and destination.is_file()
                        and destination.read_bytes().replace(b"\r\n", b"\n")
                        == archive.read(name).replace(b"\r\n", b"\n")):
                    existing_bios.add(name)
                else:
                    raise ValueError("Refusing to overwrite existing or mismatching generated inputs")
        for name in manifest["files"]:
            if name in existing_bios:
                continue
            destination = root.joinpath(*PurePosixPath(name).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(name))
        # OpenBIOS's fingerprint must be recomputed against the current checkout.
        # The build driver does this after restoring its generated C.
    print("Restored verified private generated inputs; original disc was not required.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["pack"])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist/private-inputs")
    args = parser.parse_args()
    pack(args.output_dir)


if __name__ == "__main__":
    main()
