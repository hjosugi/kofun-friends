#!/usr/bin/env python3
"""Safely publish an eligible GitHub issue to Daimon.

The workflow passes only trusted configuration through environment variables.
Issue content is always read as JSON; it is never interpolated into a shell
command.  A GitHub Actions bot comment acts as the local delivery receipt while
the Idempotency-Key header provides the server-side key Daimon can enforce.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


MAX_POST_RUNES = 40_000
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
TRUNCATION_MARKER = "\n\n…（GitHub Issue本文を40,000文字以内に切り詰めました）"
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
DEFAULT_ALLOWED_LABEL = "daimon-post"
MARKER_AUTHOR = "github-actions[bot]"
MARKER_VERSION = "v1"
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class AutomationError(RuntimeError):
    """Expected configuration, validation, or delivery failure."""


class RequestError(AutomationError):
    """HTTP request failure that is safe to show in Actions logs."""


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not forward GitHub or Daimon authorization headers on redirects."""

    def redirect_request(
        self,
        req: Any,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


NO_REDIRECT_OPENER = urllib.request.build_opener(NoRedirectHandler()).open


@dataclass(frozen=True)
class HttpResponse:
    status: int
    data: Any
    headers: Mapping[str, str]


@dataclass(frozen=True)
class IssueContext:
    repository: str
    issue_id: int
    number: int
    title: str
    body: str
    author: str
    author_association: str
    labels: tuple[str, ...]
    url: str
    is_pull_request: bool

    @property
    def idempotency_key(self) -> str:
        return f"github:{self.repository}:issue:{self.issue_id}"


@dataclass(frozen=True)
class DeliveryDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class PostPayload:
    text: str
    povs: tuple[str, ...]


@dataclass(frozen=True)
class Config:
    repository: str
    event_path: Path
    issue_number: int | None
    api_url: str
    account: str
    password: str
    github_token: str
    allowed_label: str
    idempotency_supported: bool
    dry_run: bool
    summary_path: Path | None

    def validate_live(self) -> None:
        missing = [
            name
            for name, value in (
                ("DAIMON_API_URL", self.api_url),
                ("DAIMON_ACCOUNT", self.account),
                ("DAIMON_PASSWORD", self.password),
                ("GITHUB_TOKEN", self.github_token),
            )
            if not value
        ]
        if missing:
            raise AutomationError(
                "Missing required live configuration: " + ", ".join(missing)
            )


class Summary:
    def __init__(self, path: Path | None) -> None:
        self.path = path

    def write(
        self,
        *,
        status: str,
        context: IssueContext | None,
        detail: str,
        post_id: str | None = None,
    ) -> None:
        if self.path is None:
            return
        lines = ["## Daimon issue posting", "", f"- Status: **{status}**"]
        if context is not None:
            lines.extend(
                [
                    f"- Issue: [{context.repository} #{context.number}]({context.url})",
                    f"- Idempotency key: `{context.idempotency_key}`",
                ]
            )
        if post_id:
            lines.append(f"- Daimon post ID: `{safe_inline_code(post_id)}`")
        lines.append(f"- Detail: {detail}")
        lines.append("")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))


def safe_inline_code(value: str) -> str:
    return value.replace("`", "'").replace("\r", " ").replace("\n", " ")


def parse_bool(value: str | bool | None, *, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise AutomationError(f"Invalid boolean value: {value!r}")


def parse_issue_number(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    text = str(value)
    if not re.fullmatch(r"[1-9][0-9]*", text):
        raise AutomationError("Issue number must be a positive integer")
    return int(text)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise AutomationError("Expected issue text to be a string")
    return value.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").strip()


def issue_context(issue: Mapping[str, Any], repository: str) -> IssueContext:
    if not REPOSITORY_RE.fullmatch(repository):
        raise AutomationError("Repository must use owner/name form")

    try:
        issue_id = int(issue["id"])
        number = int(issue["number"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AutomationError("Issue payload is missing a numeric id or number") from exc
    if issue_id <= 0 or number <= 0:
        raise AutomationError("Issue id and number must be positive")

    user = issue.get("user")
    author = user.get("login", "") if isinstance(user, Mapping) else ""
    if not isinstance(author, str) or not author:
        raise AutomationError("Issue payload is missing the author login")

    labels: list[str] = []
    raw_labels = issue.get("labels", [])
    if not isinstance(raw_labels, Sequence) or isinstance(raw_labels, (str, bytes)):
        raise AutomationError("Issue labels must be an array")
    for raw_label in raw_labels:
        if isinstance(raw_label, Mapping):
            name = raw_label.get("name")
        else:
            name = raw_label
        if isinstance(name, str):
            cleaned = clean_text(name)
            if cleaned:
                labels.append(cleaned)

    url = clean_text(issue.get("html_url"))
    if not url.startswith("https://github.com/"):
        raise AutomationError("Issue URL must be an https://github.com URL")

    return IssueContext(
        repository=repository,
        issue_id=issue_id,
        number=number,
        title=clean_text(issue.get("title")),
        body=clean_text(issue.get("body")),
        author=author,
        author_association=clean_text(issue.get("author_association")).upper(),
        labels=tuple(dict.fromkeys(labels)),
        url=url,
        is_pull_request="pull_request" in issue,
    )


def delivery_decision(
    context: IssueContext,
    *,
    action: str,
    event_label: str,
    allowed_label: str,
    manual: bool,
) -> DeliveryDecision:
    if context.is_pull_request:
        return DeliveryDecision(False, "Pull requests are not posted")
    if manual:
        return DeliveryDecision(True, "Manual dispatch by a repository maintainer")
    if action == "opened":
        if context.author_association in TRUSTED_ASSOCIATIONS:
            return DeliveryDecision(
                True, f"Trusted author association: {context.author_association}"
            )
        return DeliveryDecision(
            False,
            "Untrusted issue author; a maintainer must add the opt-in label",
        )
    if action == "labeled" and event_label == allowed_label:
        return DeliveryDecision(True, f"Maintainer opt-in label added: {allowed_label}")
    return DeliveryDecision(False, f"Event action is not eligible: {action or 'unknown'}")


def clean_pov(value: str) -> str:
    return " ".join(clean_text(value).split())[:300]


def make_payload(context: IssueContext) -> PostPayload:
    labels_text = ", ".join(context.labels) if context.labels else "(none)"
    prefix = f"[GitHub Issue] {context.repository} #{context.number}\n{context.title}\n\n"
    suffix = (
        f"\n\nAuthor: @{context.author}"
        f"\nLabels: {labels_text}"
        f"\nURL: {context.url}"
    )
    body = context.body or "(本文なし)"
    available = MAX_POST_RUNES - len(prefix) - len(suffix)
    if available < len(TRUNCATION_MARKER):
        raise AutomationError("Issue metadata is too large for a Daimon post")
    if len(body) > available:
        body = body[: available - len(TRUNCATION_MARKER)] + TRUNCATION_MARKER
    text = prefix + body + suffix
    if len(text) > MAX_POST_RUNES:
        raise AutomationError("Formatted Daimon post exceeds the maximum length")

    repository_name = context.repository.split("/", 1)[1]
    pov_candidates = ["GitHub Issue", repository_name, *context.labels]
    povs = tuple(
        dict.fromkeys(
            cleaned
            for value in pov_candidates[:22]
            if (cleaned := clean_pov(value))
        )
    )
    return PostPayload(text=text, povs=povs)


def retry_delay(headers: Mapping[str, str], attempt: int) -> float:
    retry_after = headers.get("Retry-After") or headers.get("retry-after")
    if retry_after and retry_after.isdigit():
        return min(float(retry_after), 60.0)
    return min(float(2**attempt), 30.0)


def request_json(
    method: str,
    url: str,
    *,
    payload: Any = None,
    headers: Mapping[str, str] | None = None,
    timeout: float = 15.0,
    retries: int = 0,
    opener: Callable[..., Any] | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> HttpResponse:
    open_request = opener or NO_REDIRECT_OPENER
    sleep = sleeper or time.sleep
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "kofun-friends-daimon-automation/1",
        **(dict(headers) if headers else {}),
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    for attempt in range(retries + 1):
        request = urllib.request.Request(
            url, data=data, headers=request_headers, method=method
        )
        try:
            with open_request(request, timeout=timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise RequestError(
                        f"{method} {redacted_url(url)} returned an oversized response"
                    )
                parsed = json.loads(raw.decode("utf-8")) if raw else None
                return HttpResponse(
                    status=response.status,
                    data=parsed,
                    headers=dict(response.headers.items()),
                )
        except urllib.error.HTTPError as exc:
            response_headers = dict(exc.headers.items()) if exc.headers else {}
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            exc.close()
            if retryable and attempt < retries:
                sleep(retry_delay(response_headers, attempt))
                continue
            raise RequestError(
                f"{method} {redacted_url(url)} failed with HTTP {exc.code}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt < retries:
                sleep(retry_delay({}, attempt))
                continue
            raise RequestError(f"{method} {redacted_url(url)} failed") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RequestError(
                f"{method} {redacted_url(url)} returned invalid JSON"
            ) from exc
    raise AssertionError("unreachable")


def redacted_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def validate_api_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    local_http = parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}
    if parsed.scheme != "https" and not local_http:
        raise AutomationError("DAIMON_API_URL must use HTTPS")
    if not parsed.hostname or parsed.username or parsed.password:
        raise AutomationError("DAIMON_API_URL must be a credential-free absolute URL")
    if parsed.query or parsed.fragment:
        raise AutomationError("DAIMON_API_URL must not contain a query or fragment")
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "")
    )


class GitHubClient:
    def __init__(
        self,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        requester: Callable[..., HttpResponse] = request_json,
    ) -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.requester = requester

    def _request(
        self, method: str, path: str, *, payload: Any = None, retries: int = 2
    ) -> HttpResponse:
        if not self.token:
            raise AutomationError("GITHUB_TOKEN is required")
        return self.requester(
            method,
            f"{self.api_url}{path}",
            payload=payload,
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            retries=retries,
        )

    def get_issue(self, repository: str, number: int) -> Mapping[str, Any]:
        response = self._request("GET", f"/repos/{repository}/issues/{number}")
        if not isinstance(response.data, Mapping):
            raise AutomationError("GitHub issue response is not an object")
        return response.data

    def has_marker(self, context: IssueContext) -> bool:
        marker = marker_text(context.idempotency_key)
        for page in range(1, 101):
            response = self._request(
                "GET",
                f"/repos/{context.repository}/issues/{context.number}/comments"
                f"?per_page=100&page={page}",
            )
            if not isinstance(response.data, list):
                raise AutomationError("GitHub comments response is not an array")
            for comment in response.data:
                if not isinstance(comment, Mapping):
                    continue
                user = comment.get("user")
                login = user.get("login") if isinstance(user, Mapping) else None
                body = comment.get("body")
                if login == MARKER_AUTHOR and isinstance(body, str) and marker in body:
                    return True
            if len(response.data) < 100:
                return False
        raise AutomationError("Too many issue comments to verify the delivery marker")

    def create_marker(self, context: IssueContext, post_id: str) -> None:
        body = (
            f"{marker_text(context.idempotency_key)}\n"
            f"Daimonへ自動投稿済み（post ID: `{safe_inline_code(post_id)}`）。"
        )
        self._request(
            "POST",
            f"/repos/{context.repository}/issues/{context.number}/comments",
            payload={"body": body},
            retries=0,
        )


def marker_text(idempotency_key: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.:/-]+", idempotency_key):
        raise AutomationError("Unsafe idempotency key")
    return f"<!-- daimon-post:{MARKER_VERSION} key={idempotency_key} -->"


class DaimonClient:
    def __init__(
        self,
        api_url: str,
        account: str,
        password: str,
        *,
        idempotency_supported: bool,
        requester: Callable[..., HttpResponse] = request_json,
    ) -> None:
        self.api_url = validate_api_url(api_url)
        self.account = account
        self.password = password
        self.idempotency_supported = idempotency_supported
        self.requester = requester

    def login(self) -> str:
        response = self.requester(
            "POST",
            f"{self.api_url}/auth/login",
            payload={"email_or_username": self.account, "password": self.password},
            retries=2,
        )
        token = response.data.get("token") if isinstance(response.data, Mapping) else None
        if not isinstance(token, str) or not token:
            raise AutomationError("Daimon login response did not include a token")
        return token

    def create_post(self, token: str, payload: PostPayload, key: str) -> str:
        response = self.requester(
            "POST",
            f"{self.api_url}/posts/",
            payload={"text": payload.text, "povs": list(payload.povs)},
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": key,
            },
            retries=2 if self.idempotency_supported else 0,
        )
        post_id = response.data.get("id") if isinstance(response.data, Mapping) else None
        if not isinstance(post_id, str) or not post_id:
            raise AutomationError("Daimon post response did not include an id")
        return post_id

    def logout(self, token: str) -> None:
        self.requester(
            "POST",
            f"{self.api_url}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            retries=1,
        )


def load_event(path: Path) -> Mapping[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise AutomationError(f"Could not read GitHub event JSON: {path}") from exc
    if not isinstance(value, Mapping):
        raise AutomationError("GitHub event JSON must be an object")
    return value


def event_repository(event: Mapping[str, Any]) -> str:
    repository = event.get("repository")
    name = repository.get("full_name", "") if isinstance(repository, Mapping) else ""
    return name if isinstance(name, str) else ""


def run_automation(
    config: Config,
    event: Mapping[str, Any],
    github: GitHubClient,
    daimon_factory: Callable[[], DaimonClient],
    summary: Summary,
) -> str:
    event_repo = event_repository(event)
    repository = config.repository or event_repo
    if config.repository and event_repo and config.repository != event_repo:
        raise AutomationError("Event repository does not match GITHUB_REPOSITORY")

    manual = config.issue_number is not None
    if manual:
        issue = github.get_issue(repository, config.issue_number)
        action = "workflow_dispatch"
        event_label = ""
    else:
        issue = event.get("issue")
        if not isinstance(issue, Mapping):
            raise AutomationError("GitHub issue event is missing the issue object")
        action = clean_text(event.get("action"))
        label = event.get("label")
        event_label = clean_text(label.get("name")) if isinstance(label, Mapping) else ""

    context = issue_context(issue, repository)
    decision = delivery_decision(
        context,
        action=action,
        event_label=event_label,
        allowed_label=config.allowed_label,
        manual=manual,
    )
    if not decision.allowed:
        summary.write(status="skipped", context=context, detail=decision.reason)
        print(f"Skipped {context.repository}#{context.number}: {decision.reason}")
        return "skipped"

    payload = make_payload(context)
    if config.dry_run:
        summary.write(
            status="dry-run",
            context=context,
            detail=(
                f"Eligible ({decision.reason}); formatted {len(payload.text)} characters "
                f"and {len(payload.povs)} POVs without posting"
            ),
        )
        print(f"Dry run completed for {context.repository}#{context.number}")
        return "dry-run"

    config.validate_live()
    if github.has_marker(context):
        summary.write(
            status="skipped",
            context=context,
            detail="A trusted GitHub Actions delivery receipt already exists",
        )
        print(f"Already posted: {context.repository}#{context.number}")
        return "already-posted"

    daimon = daimon_factory()
    token = ""
    post_id = ""
    try:
        token = daimon.login()
        post_id = daimon.create_post(token, payload, context.idempotency_key)
    finally:
        if token:
            try:
                daimon.logout(token)
            except AutomationError as exc:
                print(f"Warning: Daimon logout failed: {exc}", file=sys.stderr)

    try:
        github.create_marker(context, post_id)
    except AutomationError as exc:
        summary.write(
            status="needs-attention",
            context=context,
            post_id=post_id,
            detail="Daimon accepted the post, but GitHub could not record the receipt",
        )
        raise AutomationError(
            f"Daimon post {safe_inline_code(post_id)} succeeded, but the GitHub receipt failed"
        ) from exc

    summary.write(
        status="posted",
        context=context,
        post_id=post_id,
        detail=f"Posted successfully ({decision.reason})",
    )
    print(f"Posted {context.repository}#{context.number} to Daimon as {post_id}")
    return "posted"


def config_from_args(argv: Sequence[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH", ""))
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument(
        "--issue-number", default=os.getenv("DAIMON_ISSUE_NUMBER", "")
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.event_path:
        raise AutomationError("GITHUB_EVENT_PATH or --event-path is required")
    allowed_label = os.getenv("DAIMON_POST_LABEL", DEFAULT_ALLOWED_LABEL).strip()
    if not allowed_label:
        raise AutomationError("DAIMON_POST_LABEL cannot be empty")
    summary_value = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    return Config(
        repository=args.repository.strip(),
        event_path=Path(args.event_path),
        issue_number=parse_issue_number(args.issue_number),
        api_url=os.getenv("DAIMON_API_URL", "").strip(),
        account=os.getenv("DAIMON_ACCOUNT", "").strip(),
        password=os.getenv("DAIMON_PASSWORD", ""),
        github_token=os.getenv("GITHUB_TOKEN", ""),
        allowed_label=allowed_label,
        idempotency_supported=parse_bool(
            os.getenv("DAIMON_IDEMPOTENCY_SUPPORTED"), default=False
        ),
        dry_run=args.dry_run
        or parse_bool(os.getenv("DAIMON_DRY_RUN"), default=False),
        summary_path=Path(summary_value) if summary_value else None,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = Summary(None)
    try:
        config = config_from_args(argv)
        summary = Summary(config.summary_path)
        event = load_event(config.event_path)
        github = GitHubClient(config.github_token)
        run_automation(
            config,
            event,
            github,
            lambda: DaimonClient(
                config.api_url,
                config.account,
                config.password,
                idempotency_supported=config.idempotency_supported,
            ),
            summary,
        )
        return 0
    except AutomationError as exc:
        summary.write(status="failed", context=None, detail=str(exc))
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
