import os
import re

from config import MODES, DEFAULT_MODE

_DISCORD_MARKUP_RE = re.compile(
    r"<@!?\d+>|<#\d+>|<@&\d+>|<a?:\w+:\d+>|<t:\d+(?::[tTdDfFR])?>",
)
_WHITESPACE_RE = re.compile(r"\s+")
MAX_PROMPT_LEN = 500

_system_prompt_path = os.path.join(os.path.dirname(__file__), "config", "system_prompt.txt")
with open(_system_prompt_path) as f:
    _SYSTEM_PROMPT_TEMPLATE = f.read().strip()


def sanitize_prompt(text: str) -> str:
    text = _DISCORD_MARKUP_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(text) > MAX_PROMPT_LEN:
        text = text[: MAX_PROMPT_LEN - 1] + "…"
    return text


def resolve_mode(mode_key: str | None) -> dict:
    if mode_key and mode_key in MODES:
        return MODES[mode_key]
    return MODES[DEFAULT_MODE]


def build_image_prompt(user_text: str, mode: dict) -> tuple[str, str]:
    item = mode.get("item", "a sharp, tailored business suit")
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.replace("{ITEM}", item)
    return system_prompt, sanitize_prompt(user_text)


def build_text_prompt(user_text: str, mode: dict) -> tuple[str, str]:
    system_prompt = mode["system_prompt"]
    return system_prompt, sanitize_prompt(user_text)
