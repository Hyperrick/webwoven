from __future__ import annotations

import argparse
import json
from pathlib import Path

from webwoven_api.main import create_app
from webwoven_api.settings import Settings

OUTPUT = Path("generated/openapi.json")


def rendered_schema() -> str:
    fixture = Path("data/fixtures/smoke")
    app = create_app(
        Settings(
            environment="testing",
            graph_path=fixture / "graph.sqlite3",
            graph_manifest_path=fixture / "manifest.json",
        )
    )
    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export or verify the Webwoven OpenAPI contract")
    parser.add_argument(
        "--check", action="store_true", help="fail when the committed schema drifts"
    )
    args = parser.parse_args()
    rendered = rendered_schema()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"{OUTPUT} is stale; run `uv run python scripts/export_openapi.py`")
            return 1
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
