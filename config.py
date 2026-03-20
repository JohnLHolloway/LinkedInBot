import os
import json
import logging
import re

log = logging.getLogger(__name__)

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
XAI_API_KEY = os.environ["XAI_API_KEY"]

ALLOWED_GUILD_IDS: set[int] = set()
_raw = os.getenv("ALLOWED_GUILD_IDS", "")
if _raw.strip():
    ALLOWED_GUILD_IDS = {int(g) for g in _raw.split(",") if g.strip()}

# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
_modes_path = os.path.join(os.path.dirname(__file__), "config", "modes.json")
with open(_modes_path) as f:
    MODES: dict = json.load(f)

DEFAULT_MODE = "corporate"

# ---------------------------------------------------------------------------
# Logging filter – redact secrets from log output
# ---------------------------------------------------------------------------
_SECRET_RE = re.compile(
    r"(xai-[A-Za-z0-9_-]{10,}|"
    r"[A-Za-z0-9_-]{50,}|"
    r"sk-[A-Za-z0-9_-]{10,})",
)


class _SecretFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _SECRET_RE.sub("***REDACTED***", str(record.msg))
        return True


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    for handler in logging.root.handlers:
        handler.addFilter(_SecretFilter())
