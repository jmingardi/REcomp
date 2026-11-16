"""Package only authored setup sources and curated metadata; never game/build data."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = [".gitignore", ".gitattributes", ".recomp.json", "CMakeLists.txt", "dependencies.lock.json",
              "game.toml", "README.md", "PROJECT_STATUS.md", "Run Resident Evil.cmd", "VERSION", "CHANGELOG.md",
              "CONTRIBUTING.md", ".github/CODEOWNERS"]
PATTERNS = ["scripts/*.py", "docs/*.md", "patches/*.patch", "seeds/*.txt", "aot/*.json",
            "aot/*.md", "licenses/*.txt", "licenses/*.md", "qa/*.md", "qa/routes/*.json", "evidence/aot-summary.json",
            "evidence/disc-inventory.json", "evidence/overlay-files.json", "evidence/validation-summary.json",
            "src/*.cpp", "src/*.in", "qa/*.cpp", "evidence/settings-qa-summary.json",
            "mods/preloaded/packages/*/*/manifest.toml", "evidence/motion-qa-summary.json",
            ".github/ISSUE_TEMPLATE/*.yml", ".github/workflows/*.yml"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    sources = {ROOT / name for name in ROOT_FILES}
    for pattern in PATTERNS:
        sources.update(ROOT.glob(pattern))
    for source in sources:
        if not source.is_file():
            raise ValueError(f"Missing source: {source}")
        if source.suffix.lower() in {".exe", ".bin", ".cue", ".iso", ".chd", ".dll"}:
            raise ValueError(f"Unexpected binary input: {source}")
    version = (ROOT / "VERSION").read_text().strip()
    output = args.output_dir / f"resident-evil-recomp-source-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(sources):
            archive.write(source, source.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(sources)
        assert {"src/settings_menu.cpp", "qa/host_input_probe.cpp", "src/smooth_motion.cpp",
                "mods/preloaded/packages/re1.enhancement.smooth-motion/0.1.0/manifest.toml",
                "patches/psxrecomp-bounded-frame-generation.patch"} <= set(archive.namelist())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(f"{output}\n{len(sources)} source/metadata files; SHA-256 {digest}")


if __name__ == "__main__":
    main()
