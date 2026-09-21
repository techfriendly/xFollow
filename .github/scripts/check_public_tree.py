"""Reject operational documents, credentials and build outputs in tracked files."""
from pathlib import PurePosixPath
import subprocess

paths = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
blocked_suffixes = {".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".7z", ".db", ".sqlite", ".sqlite3", ".dump", ".pem", ".key", ".p12", ".pfx", ".log", ".jsonl"}
blocked_dirs = {"node_modules", ".next", "__pycache__", "backups", "uploads", "exports", "logs", ".venv", ".codex"}
errors = []
for value in filter(None, paths):
    path = PurePosixPath(value)
    if path.suffix.lower() in blocked_suffixes or blocked_dirs.intersection(path.parts):
        errors.append(value)
    elif path.name.startswith(".env") and path.name not in {".env.example", ".env.local.example"}:
        errors.append(value)
    elif path.parts[0] == "data" and value != "data/README.md":
        errors.append(value)
if errors:
    raise SystemExit("Files outside public distribution policy:\n" + "\n".join(errors))
print("Public distribution paths checked. Review file contents separately for sensitive data.")
