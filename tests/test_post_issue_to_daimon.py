from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).parents[1] / "scripts" / "post_issue_to_daimon.py"
SPEC = importlib.util.spec_from_file_location("post_issue_to_daimon", SCRIPT)
assert SPEC and SPEC.loader
automation = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = automation
SPEC.loader.exec_module(automation)


def issue(
    *,
    body: str | None = "本文",
    association: str = "OWNER",
    labels: tuple[str, ...] = (),
    pull_request: bool = False,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "id": 987654321,
        "number": 42,
        "title": "日本語の `title` $(touch nope)",
        "body": body,
        "user": {"login": "octocat"},
        "author_association": association,
        "labels": [{"name": label} for label in labels],
        "html_url": "https://github.com/hjosugi/kofun-friends/issues/42",
    }
    if pull_request:
        value["pull_request"] = {"url": "https://api.github.com/pulls/42"}
    return value


def event(value: dict[str, Any] | None = None, *, action: str = "opened") -> dict[str, Any]:
    return {
        "action": action,
        "issue": value or issue(),
        "repository": {"full_name": "hjosugi/kofun-friends"},
    }


def config(summary_path: Path, **overrides: Any) -> Any:
    values = {
        "repository": "hjosugi/kofun-friends",
        "event_path": Path("event.json"),
        "issue_number": None,
        "api_url": "https://daimon.example.test",
        "account": "robot@example.test",
        "password": "super-secret",
        "github_token": "github-secret",
        "allowed_label": "daimon-post",
        "idempotency_supported": False,
        "dry_run": False,
        "summary_path": summary_path,
    }
    values.update(overrides)
    return automation.Config(**values)


class FakeGitHub:
    def __init__(self, issue_value: dict[str, Any] | None = None) -> None:
        self.issue_value = issue_value or issue()
        self.marker_exists = False
        self.markers: list[tuple[Any, str]] = []
        self.fetches: list[tuple[str, int]] = []

    def get_issue(self, repository: str, number: int) -> dict[str, Any]:
        self.fetches.append((repository, number))
        return self.issue_value

    def has_marker(self, context: Any) -> bool:
        return self.marker_exists

    def create_marker(self, context: Any, post_id: str) -> None:
        self.markers.append((context, post_id))


class FakeDaimon:
    def __init__(self) -> None:
        self.logins = 0
        self.posts: list[tuple[str, Any, str]] = []
        self.logouts: list[str] = []

    def login(self) -> str:
        self.logins += 1
        return "session-token"

    def create_post(self, token: str, payload: Any, key: str) -> str:
        self.posts.append((token, payload, key))
        return "post-123"

    def logout(self, token: str) -> None:
        self.logouts.append(token)


class FakeResponse:
    def __init__(self, data: Any, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self.status = status
        self.headers = headers or {}
        self._body = json.dumps(data).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self._body


class IssueFormattingTests(unittest.TestCase):
    def test_formats_unicode_empty_body_and_metadata(self) -> None:
        context = automation.issue_context(issue(body=None), "hjosugi/kofun-friends")
        payload = automation.make_payload(context)
        self.assertIn("日本語", payload.text)
        self.assertIn("(本文なし)", payload.text)
        self.assertTrue(payload.text.endswith(context.url))
        self.assertEqual(payload.povs[:2], ("GitHub Issue", "kofun-friends"))

    def test_truncates_by_unicode_codepoint_and_preserves_url(self) -> None:
        context = automation.issue_context(
            issue(body="🗿" * 50_000), "hjosugi/kofun-friends"
        )
        payload = automation.make_payload(context)
        self.assertEqual(len(payload.text), automation.MAX_POST_RUNES)
        self.assertIn(automation.TRUNCATION_MARKER, payload.text)
        self.assertTrue(payload.text.endswith(context.url))

    def test_normalizes_nuls_and_line_endings(self) -> None:
        value = issue(body="a\x00\r\nb\rc")
        context = automation.issue_context(value, "hjosugi/kofun-friends")
        self.assertEqual(context.body, "a\nb\nc")


class EligibilityTests(unittest.TestCase):
    def decide(self, value: dict[str, Any], **kwargs: Any) -> Any:
        context = automation.issue_context(value, "hjosugi/kofun-friends")
        return automation.delivery_decision(
            context,
            action=kwargs.get("action", "opened"),
            event_label=kwargs.get("event_label", ""),
            allowed_label="daimon-post",
            manual=kwargs.get("manual", False),
        )

    def test_trusted_author_is_allowed(self) -> None:
        self.assertTrue(self.decide(issue(association="MEMBER")).allowed)

    def test_untrusted_author_is_skipped(self) -> None:
        self.assertFalse(self.decide(issue(association="NONE")).allowed)

    def test_untrusted_opened_issue_cannot_self_opt_in(self) -> None:
        decision = self.decide(
            issue(association="NONE", labels=("daimon-post",)), action="opened"
        )
        self.assertFalse(decision.allowed)

    def test_opt_in_label_event_is_allowed(self) -> None:
        decision = self.decide(
            issue(association="NONE", labels=("daimon-post",)),
            action="labeled",
            event_label="daimon-post",
        )
        self.assertTrue(decision.allowed)

    def test_unrelated_label_event_is_skipped(self) -> None:
        decision = self.decide(
            issue(association="OWNER", labels=("documentation",)),
            action="labeled",
            event_label="documentation",
        )
        self.assertFalse(decision.allowed)

    def test_pull_request_is_never_posted(self) -> None:
        self.assertFalse(self.decide(issue(pull_request=True), manual=True).allowed)


class AutomationFlowTests(unittest.TestCase):
    def run_flow(
        self, value: dict[str, Any], **overrides: Any
    ) -> tuple[str, FakeGitHub, FakeDaimon, str]:
        with tempfile.TemporaryDirectory() as directory:
            summary_path = Path(directory) / "summary.md"
            github = FakeGitHub(value)
            daimon = FakeDaimon()
            result = automation.run_automation(
                config(summary_path, **overrides),
                event(value),
                github,
                lambda: daimon,
                automation.Summary(summary_path),
            )
            summary = summary_path.read_text(encoding="utf-8")
        return result, github, daimon, summary

    def test_posts_logs_out_and_records_marker(self) -> None:
        result, github, daimon, summary = self.run_flow(issue())
        self.assertEqual(result, "posted")
        self.assertEqual(daimon.logins, 1)
        self.assertEqual(daimon.logouts, ["session-token"])
        self.assertEqual(len(daimon.posts), 1)
        self.assertEqual(
            daimon.posts[0][2], "github:hjosugi/kofun-friends:issue:987654321"
        )
        self.assertEqual(len(github.markers), 1)
        self.assertIn("post-123", summary)
        self.assertNotIn("super-secret", summary)
        self.assertNotIn("github-secret", summary)

    def test_untrusted_issue_skips_without_credentials_or_network(self) -> None:
        result, github, daimon, summary = self.run_flow(
            issue(association="NONE"), api_url="", account="", password="", github_token=""
        )
        self.assertEqual(result, "skipped")
        self.assertEqual(daimon.logins, 0)
        self.assertFalse(github.markers)
        self.assertIn("skipped", summary)

    def test_dry_run_does_not_call_daimon_or_write_marker(self) -> None:
        result, github, daimon, summary = self.run_flow(
            issue(), dry_run=True, api_url="", account="", password=""
        )
        self.assertEqual(result, "dry-run")
        self.assertEqual(daimon.logins, 0)
        self.assertFalse(github.markers)
        self.assertIn("dry-run", summary)

    def test_existing_trusted_marker_prevents_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary_path = Path(directory) / "summary.md"
            github = FakeGitHub(issue())
            github.marker_exists = True
            daimon = FakeDaimon()
            result = automation.run_automation(
                config(summary_path),
                event(),
                github,
                lambda: daimon,
                automation.Summary(summary_path),
            )
        self.assertEqual(result, "already-posted")
        self.assertEqual(daimon.logins, 0)

    def test_manual_dispatch_fetches_issue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary_path = Path(directory) / "summary.md"
            github = FakeGitHub(issue(association="NONE"))
            daimon = FakeDaimon()
            result = automation.run_automation(
                config(summary_path, issue_number=42, dry_run=True),
                {"repository": {"full_name": "hjosugi/kofun-friends"}},
                github,
                lambda: daimon,
                automation.Summary(summary_path),
            )
        self.assertEqual(result, "dry-run")
        self.assertEqual(github.fetches, [("hjosugi/kofun-friends", 42)])


class HttpTests(unittest.TestCase):
    def test_encodes_json_and_headers_without_logging_secrets(self) -> None:
        captured: list[Any] = []

        def opener(request: Any, timeout: float) -> FakeResponse:
            captured.append((request, timeout))
            return FakeResponse({"ok": True})

        response = automation.request_json(
            "POST",
            "https://example.test/posts",
            payload={"text": "日本語"},
            headers={"Authorization": "Bearer secret"},
            opener=opener,
        )
        request, timeout = captured[0]
        self.assertEqual(response.data, {"ok": True})
        self.assertEqual(timeout, 15.0)
        self.assertEqual(json.loads(request.data), {"text": "日本語"})
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")

    def test_retries_transient_server_error_when_enabled(self) -> None:
        attempts = 0
        sleeps: list[float] = []

        def opener(request: Any, timeout: float) -> FakeResponse:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise urllib.error.HTTPError(
                    request.full_url,
                    503,
                    "unavailable",
                    {"Retry-After": "2"},
                    io.BytesIO(b"{}"),
                )
            return FakeResponse({"ok": True})

        automation.request_json(
            "GET",
            "https://example.test/health",
            retries=1,
            opener=opener,
            sleeper=sleeps.append,
        )
        self.assertEqual(attempts, 2)
        self.assertEqual(sleeps, [2.0])

    def test_redirects_are_disabled_to_protect_authorization_headers(self) -> None:
        handler = automation.NoRedirectHandler()
        self.assertIsNone(
            handler.redirect_request(
                object(), None, 302, "found", {}, "https://attacker.example/"
            )
        )

    def test_does_not_retry_post_without_idempotency_support(self) -> None:
        calls: list[dict[str, Any]] = []

        def requester(method: str, url: str, **kwargs: Any) -> Any:
            calls.append(kwargs)
            raise automation.RequestError("temporary failure")

        client = automation.DaimonClient(
            "https://daimon.example.test",
            "account",
            "password",
            idempotency_supported=False,
            requester=requester,
        )
        with self.assertRaises(automation.RequestError):
            client.create_post("token", automation.PostPayload("text", ()), "key")
        self.assertEqual(calls[0]["retries"], 0)

    def test_retries_post_only_when_server_idempotency_is_confirmed(self) -> None:
        calls: list[dict[str, Any]] = []

        def requester(method: str, url: str, **kwargs: Any) -> Any:
            calls.append(kwargs)
            return automation.HttpResponse(200, {"id": "post-1"}, {})

        client = automation.DaimonClient(
            "https://daimon.example.test",
            "account",
            "password",
            idempotency_supported=True,
            requester=requester,
        )
        client.create_post("token", automation.PostPayload("text", ()), "key")
        self.assertEqual(calls[0]["retries"], 2)
        self.assertEqual(calls[0]["headers"]["Idempotency-Key"], "key")


class MarkerTests(unittest.TestCase):
    def test_only_actions_bot_comment_is_a_receipt(self) -> None:
        context = automation.issue_context(issue(), "hjosugi/kofun-friends")
        marker = automation.marker_text(context.idempotency_key)
        responses = iter(
            [
                automation.HttpResponse(
                    200,
                    [{"user": {"login": "attacker"}, "body": marker}],
                    {},
                )
            ]
        )

        def requester(*args: Any, **kwargs: Any) -> Any:
            return next(responses)

        client = automation.GitHubClient("token", requester=requester)
        self.assertFalse(client.has_marker(context))


if __name__ == "__main__":
    unittest.main()
