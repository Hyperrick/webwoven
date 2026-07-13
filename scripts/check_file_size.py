from __future__ import annotations

from pathlib import Path

ROOTS = (Path("apps"), Path("services"), Path("packages"), Path("scripts"))
EXTENSIONS = {".py", ".ts", ".svelte", ".css"}
EXCLUDED_PARTS = {"node_modules", "generated", "migrations", ".venv"}
MAX_LINES = 600


def authored_files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.suffix in EXTENSIONS
                and not EXCLUDED_PARTS.intersection(path.parts)
            ):
                files.append(path)
    return files


def main() -> int:
    oversized: list[tuple[Path, int]] = []
    for path in authored_files():
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_LINES:
            oversized.append((path, line_count))
    if oversized:
        for path, line_count in oversized:
            print(f"{path}: {line_count} lines (maximum {MAX_LINES})")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
