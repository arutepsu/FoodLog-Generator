"""Synchronize canonical FoodLog skills into project-local host discovery folders."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

NAMES = ("foodlog", "money", "taste", "effort", "nutrition", "happiness")
MANIFEST = ".foodlog-manifest.json"
ROOT = Path(__file__).resolve().parents[1]


def validate_structure(folder):
    for name in NAMES:
        file = folder / name / "SKILL.md"
        text = file.read_text(encoding="utf-8")
        match = re.match(r"\A---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n", text)
        if not match or match[1] != name or not match[2].startswith("Use when"):
            raise ValueError(f"Invalid skill frontmatter: {file}")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in link and not (file.parent / link).is_file():
                raise ValueError(f"Broken skill resource link: {file}: {link}")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def expected_files():
    validate_structure(ROOT / "skills")
    files = {}
    for name in NAMES:
        for source in (ROOT / "skills" / name).rglob("*"):
            if source.is_file() and "__pycache__" not in source.parts:
                files[source.relative_to(ROOT/"skills").as_posix()] = source.read_bytes()
    # Generated portable runtime; src/foodlog remains the only maintained implementation.
    for source in (ROOT/"src/foodlog").rglob("*.py"):
        relative = source.relative_to(ROOT/"src").as_posix()
        files[f"foodlog/scripts/_runtime/{relative}"] = source.read_bytes()
    return files


def synchronize(destination, check=False):
    destination = Path(destination).resolve()
    files = expected_files()
    expected = {name: digest(data) for name, data in files.items()}
    plans = []
    # Preflight both hosts before modifying either.
    for host in (".agents", ".claude"):
        base = destination / host / "skills"
        if base.is_symlink() or any((base / name).is_symlink() for name in NAMES):
            raise ValueError(f"Refusing symlinked installation targets: {base}")
        if not base.resolve().is_relative_to(destination):
            raise ValueError(f"Discovery folder escapes destination: {base}")
        marker = base / MANIFEST
        if marker.is_symlink() or not marker.resolve().is_relative_to(destination):
            raise ValueError(f"Refusing linked or escaping manifest: {marker}")
        previous = json.loads(marker.read_text(encoding="utf-8")) if marker.exists() else {}
        if not isinstance(previous, dict) or not all(isinstance(k, str) and isinstance(v, str) for k,v in previous.items()):
            raise ValueError(f"Invalid synchronization manifest: {marker}")
        for relative, content in files.items():
            target = base / relative
            if not target.resolve().is_relative_to(destination):
                raise ValueError(f"Target escapes destination: {target}")
            if target.is_symlink():
                raise ValueError(f"Refusing symlink: {target}")
            if target.exists() and target.read_bytes() != content:
                old = previous.get(relative)
                if old is None or digest(target.read_bytes()) != old:
                    raise ValueError(f"Local edit or unmanaged collision: {target}. Preserve it and resolve manually.")
        for name in NAMES:
            directory = base / name
            if directory.exists() and not previous:
                raise ValueError(f"Unmanaged skill directory: {directory}")
        for relative, old_digest in previous.items():
            if relative not in files:
                raise ValueError(f"Stale managed file requires manual review: {base / relative}")
        if check:
            if previous != expected or any(not (base/k).is_file() or (base/k).read_bytes() != v for k,v in files.items()):
                raise ValueError(f"Skills are missing or out of date: {base}")
        plans.append(base)
    if not check:
        for base in plans:
            for relative, data in files.items():
                target = base / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            (base / MANIFEST).write_text(json.dumps(expected, indent=2, sort_keys=True)+"\n",encoding="utf-8")
    return plans


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT, help="Project root to install into; defaults to this repository")
    parser.add_argument("--check", action="store_true", help="Check discovery copies without writing")
    args = parser.parse_args()
    try:
        paths = synchronize(args.destination, args.check)
        print("Verified" if args.check else "Synchronized", *(str(p) for p in paths), sep="\n")
        return 0
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
