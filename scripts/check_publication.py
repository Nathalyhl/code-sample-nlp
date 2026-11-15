"""Scan this self-contained sample before publication; report file names only."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
patterns = [r"\b(?:AK" + r"IA|ASIA)[A-Z0-9]{16}\b", r"sk-" + r"[A-Za-z0-9_-]{30,}",
            r"gh" + r"p_[A-Za-z0-9]{30,}", r"-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
errors = []
for path in root.rglob("*"):
    if not path.is_file() or any(p in path.parts for p in (".git", ".venv", "__pycache__", ".ruff_cache")):
        continue
    name = path.relative_to(root).as_posix()
    if path.name.startswith(".env") or path.suffix.lower() in {".xlsx", ".docx", ".pdf", ".db", ".zip"}:
        errors.append(name)
        continue
    content = path.read_text("utf8")
    if any(re.search(pattern, content) for pattern in patterns):
        errors.append(name)
if errors:
    raise SystemExit("Publication review required: " + ", ".join(errors))
print("Publication scan passed")
