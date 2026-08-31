from __future__ import annotations

import json
import sys

from . import db


def main() -> int:
    try:
        result = db.migrate_schema()
    except Exception as exc:  # pragma: no cover - exercised by deployment failures
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
