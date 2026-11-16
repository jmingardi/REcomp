"""Regression checks for release payload exclusions, integrity and version inputs."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from build_release_candidate import candidate_version, release_version
from create_github_release import release_commands
from private_build_inputs import fingerprints, pack, restore
from verify_release import verify

ROOT = Path(__file__).resolve().parents[1]


class ReleasePipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def write_zip(self, entries):
        path = self.output / "candidate.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in entries.items():
                entry = zipfile.ZipInfo(name)
                # ZipInfo normalizes Windows backslashes at construction.
                # Override so the traversal fixture tests a raw unsafe member.
                entry.filename = name
                archive.writestr(entry, data)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(".zip.sha256").write_text(f"{digest}  {path.name}\n", encoding="ascii")
        return path

    def windows_entries(self):
        files = {name: b"fixture" for name in (
            "Resident_Evil_Recompiled.exe", "Resident_Evil_Recompiled.execution.json",
            "Run Resident Evil.cmd", "game.toml", "settings.toml", "README.txt",
            "bios/openbios.bin", "bios/OpenBIOS.LICENSE", "msvcp140.dll",
            "vcruntime140.dll", "vcruntime140_1.dll")}
        files["VERSION"] = b"0.0.1\n"
        manifest = {"version": "0.0.1", "debug_tools": False, "game_disc_included": False,
                    "personal_saves_included": False,
                    "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
        files["release-manifest.json"] = json.dumps(manifest).encode()
        return {"portable/" + name: data for name, data in files.items()}

    def check(self, path, kind="windows", version="0.0.1"):
        with contextlib.redirect_stdout(io.StringIO()):
            verify(path, kind, version)

    def test_authored_source_archive_is_complete_and_contains_no_binaries(self):
        subprocess.run([sys.executable, str(ROOT / "scripts/package_source.py"),
                        "--output-dir", str(self.output)], cwd=ROOT, check=True, capture_output=True)
        version = (ROOT / "VERSION").read_text().strip()
        self.check(self.output / f"resident-evil-recomp-source-{version}.zip", "source", version)

    def test_windows_package_accepts_openbios(self):
        self.check(self.write_zip(self.windows_entries()))

    def test_bad_download_checksum_is_rejected(self):
        path = self.write_zip(self.windows_entries())
        path.with_suffix(".zip.sha256").write_text("0" * 64 + "  candidate.zip\n")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.check(path)

    def test_changed_payload_with_recomputed_zip_checksum_is_rejected(self):
        entries = self.windows_entries()
        entries["portable/Resident_Evil_Recompiled.exe"] = b"changed executable"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.check(self.write_zip(entries))

    def test_disc_saves_and_generated_data_are_rejected(self):
        for name in ("game.cue", "game.bin", "CARD.MCD", "saves/card", "generated/game.c"):
            with self.subTest(name=name):
                entries = self.windows_entries()
                entries["portable/" + name] = b"must stay local"
                with self.assertRaises(ValueError):
                    self.check(self.write_zip(entries))

    def test_unlisted_payload_is_rejected(self):
        entries = self.windows_entries()
        entries["portable/unlisted.txt"] = b"unexpected"
        with self.assertRaisesRegex(ValueError, "contents differ"):
            self.check(self.write_zip(entries))

    def test_zip_traversal_and_windows_absolute_paths_are_rejected(self):
        for name in ("../escape", "/absolute", "C:/absolute", "portable\\escape"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "Unsafe ZIP"):
                    self.check(self.write_zip({name: b"unexpected"}))

    def test_version_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            self.check(self.write_zip(self.windows_entries()), version="0.0.2")

    def test_version_input_rejects_paths_shell_text_and_invalid_windows_versions(self):
        import argparse
        for value in ("../1.2.3", "1.2.3;echo injected", "1.2.3\n", "01.2.3", "10000.0.0", "v1.2.3"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                release_version(value)
        self.assertEqual(release_version("0.0.1"), "0.0.1")

    def test_automatic_versions_change_per_run_and_remain_stable_for_reruns(self):
        self.assertEqual(candidate_version(None, 17), "0.0.17")
        self.assertEqual(candidate_version(None, 18), "0.0.18")
        self.assertEqual(candidate_version("0.1.0", 18), "0.1.0")

    def test_release_is_a_draft_unless_publication_is_explicit(self):
        commands = release_commands("0.0.1", ["candidate.zip"], "a" * 40)
        self.assertEqual(len(commands), 1)
        self.assertIn("--draft", commands[0])
        self.assertNotIn("--draft=false", commands[0])

    def test_enabled_publication_happens_after_draft_asset_creation(self):
        commands = release_commands("0.0.1", ["candidate.zip"], "a" * 40, publish=True)
        self.assertEqual(len(commands), 2)
        self.assertIn("--draft", commands[0])
        self.assertEqual(commands[1][1:4], ["release", "edit", "v0.0.1"])
        self.assertIn("--draft=false", commands[1])

    def private_fixture(self, root):
        files = ["game.toml", "dependencies.lock.json", "scripts/project.py", "aot/overlays.json",
                 "seeds/functions.txt", "patches/generator.patch", "generated/SLUS_001.70_dispatch.c",
                 "generated/SLUS_001.70_decls.h", "generated/SLUS_001.70_full_00.c",
                 "generated/overlays_static.c", "generated/overlays_static_0000.c",
                 "third_party/psxrecomp/generated/OpenBIOS_dispatch.c",
                 "third_party/psxrecomp/generated/OpenBIOS_full.c"]
        for name in files:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n")
        return files

    def test_private_inputs_exclude_disc_and_restore_into_a_clean_checkout(self):
        source = self.output / "source"
        files = self.private_fixture(source)
        (source / "generated/disc.bin").write_bytes(b"never bundle")
        with contextlib.redirect_stdout(io.StringIO()):
            archive = pack(self.output / "private", source)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        with zipfile.ZipFile(archive) as contents:
            self.assertNotIn("generated/disc.bin", contents.namelist())
        destination = self.output / "checkout"
        for name in files:
            if not name.startswith(("generated/", "third_party/")):
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((source / name).read_bytes())
        with contextlib.redirect_stdout(io.StringIO()):
            restore(archive, digest, destination)
        self.assertEqual((destination / "generated/SLUS_001.70_full_00.c").read_text(), "fixture\n")

    def test_stale_codegen_inputs_are_rejected_before_any_restore(self):
        source = self.output / "source"
        self.private_fixture(source)
        with contextlib.redirect_stdout(io.StringIO()):
            archive = pack(self.output / "private", source)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (source / "game.toml").write_text("changed codegen config")
        with self.assertRaisesRegex(ValueError, "Codegen inputs changed"):
            restore(archive, digest, source)

    def test_checkout_line_endings_do_not_invalidate_codegen_fingerprints(self):
        source = self.output / "source"
        files = self.private_fixture(source)
        before = fingerprints(source)
        for name in files:
            path = source / name
            if name in before and path.suffix != ".patch":
                path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.assertEqual(fingerprints(source), before)


if __name__ == "__main__":
    unittest.main()
