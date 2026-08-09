"""Data manifest generator.

Writes data/manifest.json with SHA-256 checksums for every data file, as
required by the 'data/source manifest ... and SHA-256 checksums' deliverable.
Re-run after swapping in the organizer case pack so the checksums are real.

    python -m src.manifest
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest() -> dict:
    entries = []
    for path in sorted(DATA_DIR.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            entries.append({
                "file": str(path.relative_to(DATA_DIR)),
                "sha256": sha256_of(path),
                "size_bytes": path.stat().st_size,
                "is_synthetic": "synthetic" in path.parts,
            })
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Synthetic placeholder data unless is_synthetic is false. "
                "Replace with organizer case-pack files and re-run to record real checksums.",
        "files": entries,
    }


def main():
    manifest = build_manifest()
    out = DATA_DIR / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {out} with {len(manifest['files'])} file(s).")


if __name__ == "__main__":
    main()
