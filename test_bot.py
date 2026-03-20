import os
import json

# Set required env vars before importing modules
os.environ.setdefault("DISCORD_BOT_TOKEN", "test-token")
os.environ.setdefault("XAI_API_KEY", "test-key")

from prompts import sanitize_prompt, resolve_mode, build_image_prompt, build_text_prompt
from rate_limit import RateLimiter
from config import MODES, DEFAULT_MODE


class TestSanitizePrompt:
    def test_strips_mentions(self):
        assert sanitize_prompt("<@123456> hello") == "hello"

    def test_strips_channel_refs(self):
        assert sanitize_prompt("<#999> check this") == "check this"

    def test_strips_role_mentions(self):
        assert sanitize_prompt("<@&789> hi") == "hi"

    def test_strips_emoji(self):
        assert sanitize_prompt("<:smile:123> nice") == "nice"

    def test_collapses_whitespace(self):
        assert sanitize_prompt("hello    world") == "hello world"

    def test_truncates_long_text(self):
        long = "a" * 600
        result = sanitize_prompt(long)
        assert len(result) <= 500

    def test_empty_string(self):
        assert sanitize_prompt("") == ""


class TestResolveMode:
    def test_default_mode(self):
        mode = resolve_mode(None)
        assert mode == MODES[DEFAULT_MODE]

    def test_known_mode(self):
        mode = resolve_mode("motivational")
        assert mode["label"] == "Motivational Post"

    def test_unknown_mode_falls_back(self):
        mode = resolve_mode("nonexistent")
        assert mode == MODES[DEFAULT_MODE]


class TestBuildPrompts:
    def test_image_prompt_has_item(self):
        mode = resolve_mode("suits")
        system, user = build_image_prompt("test", mode)
        assert "suit" in system.lower()
        assert user == "test"

    def test_text_prompt_uses_system(self):
        mode = resolve_mode("corporate")
        system, user = build_text_prompt("hello world", mode)
        assert "LinkedIn" in system or "corporate" in system.lower()
        assert user == "hello world"


class TestRateLimiter:
    def test_first_request_allowed(self):
        rl = RateLimiter(cooldown=1.0)
        assert rl.check(1) is True

    def test_immediate_second_blocked(self):
        rl = RateLimiter(cooldown=1.0)
        rl.check(1)
        assert rl.check(1) is False

    def test_different_users_independent(self):
        rl = RateLimiter(cooldown=1.0)
        assert rl.check(1) is True
        assert rl.check(2) is True


class TestModes:
    def test_default_mode_exists(self):
        assert DEFAULT_MODE in MODES

    def test_all_modes_have_required_fields(self):
        for key, mode in MODES.items():
            assert "type" in mode, f"{key} missing type"
            assert "label" in mode, f"{key} missing label"
            assert "description" in mode, f"{key} missing description"
            if mode["type"] == "text":
                assert "system_prompt" in mode, f"{key} missing system_prompt"
            elif mode["type"] == "image":
                assert "item" in mode, f"{key} missing item"

    def test_modes_have_both_types(self):
        types = {m["type"] for m in MODES.values()}
        assert "text" in types
        assert "image" in types
