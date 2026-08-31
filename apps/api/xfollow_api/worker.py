from __future__ import annotations

import time

from . import ai_jobs, db
from .config import load_runtime_config


def main() -> None:
    config = load_runtime_config()
    while True:
        if not db.db_available():
            time.sleep(config.ai_worker_poll_seconds)
            continue
        processed = ai_jobs.process_one()
        time.sleep(0.1 if processed else config.ai_worker_poll_seconds)


if __name__ == "__main__":
    main()
