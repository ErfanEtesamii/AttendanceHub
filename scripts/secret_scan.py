"""Small dependency-free CI guard for accidentally committed credentials."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORE = {".git", "node_modules", ".next", "__pycache__"}
ALLOWLIST = {"docker-compose.yml", "backend/tests/test_bots.py", "backend/tests/test_config.py"}
PATTERNS = (re.compile(r"(?i)(telegram[_-]?bot[_-]?token|jwt[_-]?secret|password)\s*[=:]\s*['\"]?[A-Za-z0-9_-]{20,}"), re.compile(r"\d{8,12}:[A-Za-z0-9_-]{20,}"))
findings = []
for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in IGNORE for part in path.parts) or path.name in {".env.example", "package-lock.json"} or str(path.relative_to(ROOT)).replace("\\", "/") in ALLOWLIST: continue
    try: text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError: continue
    if any(pattern.search(text) for pattern in PATTERNS): findings.append(str(path.relative_to(ROOT)))
if findings:
    print("Potential secrets found:\n" + "\n".join(findings)); sys.exit(1)
print("Secret scan passed")
