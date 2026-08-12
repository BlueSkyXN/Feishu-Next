#!/usr/bin/env python3
"""Validate Feishu Next against the currently installed lark-cli surface."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "feishu-next"

CORE_SKILLS = {
    "lark-shared",
    "lark-doc",
    "lark-drive",
    "lark-im",
    "lark-whiteboard",
}

ROUTER_SKILLS = {
    "lark-approval",
    "lark-apps",
    "lark-attendance",
    "lark-base",
    "lark-calendar",
    "lark-contact",
    "lark-event",
    "lark-mail",
    "lark-markdown",
    "lark-minutes",
    "lark-note",
    "lark-okr",
    "lark-openapi-explorer",
    "lark-sheets",
    "lark-skill-maker",
    "lark-slides",
    "lark-task",
    "lark-vc",
    "lark-vc-agent",
    "lark-wiki",
    "lark-workflow-meeting-summary",
    "lark-workflow-standup-report",
}

REQUIRED_SKILL_BODIES = set(CORE_SKILLS)

REQUIRED_REFERENCES = {
    "lark-doc": {
        "references/lark-doc-fetch.md",
        "references/lark-doc-mindnote.md",
        "references/lark-doc-resource-cover.md",
        "references/lark-doc-update.md",
        "references/lark-doc-xml.md",
    },
    "lark-drive": {
        "references/lark-drive-export.md",
        "references/lark-drive-inspect.md",
    },
    "lark-im": {
        "references/lark-im-chat-search.md",
        "references/lark-im-chat-messages-list.md",
        "references/lark-im-messages-resources-download.md",
        "references/lark-im-messages-search.md",
        "references/lark-im-threads-messages-list.md",
    },
    "lark-whiteboard": {
        "references/lark-whiteboard-export.md",
        "references/lark-whiteboard-update.md",
        "references/lark-whiteboard-workflow.md",
    },
}

REQUIRED_COMMAND_FLAGS = {
    ("docs", "+fetch"): {
        "--detail",
        "--doc",
        "--doc-format",
        "--format",
        "--max-depth",
        "--scope",
        "--start-block-id",
    },
    ("docs", "+media-download"): {"--output", "--token", "--type"},
    ("docs", "+media-preview"): {"--output", "--token"},
    ("docs", "+resource-download"): {"--doc", "--output", "--type"},
    ("drive", "+inspect"): {"--format", "--type", "--url"},
    ("drive", "+export"): {
        "--doc-type",
        "--file-extension",
        "--only-schema",
        "--output-dir",
        "--sub-id",
        "--token",
        "--url",
    },
    ("drive", "+task_result"): {
        "--file-token",
        "--scenario",
        "--task-id",
        "--ticket",
    },
    ("drive", "+export-download"): {"--file-token", "--output-dir"},
    ("im", "+chat-search"): {"--page-token", "--query"},
    ("im", "+chat-messages-list"): {
        "--chat-id",
        "--download-resources",
        "--end",
        "--order",
        "--page-size",
        "--page-token",
        "--start",
    },
    ("im", "+messages-search"): {
        "--end",
        "--page-all",
        "--page-size",
        "--page-token",
        "--query",
        "--start",
    },
    ("im", "+threads-messages-list"): {
        "--order",
        "--page-size",
        "--page-token",
        "--thread",
    },
    ("whiteboard", "+export"): {
        "--output",
        "--output-type",
        "--overwrite",
        "--whiteboard-token",
    },
    ("whiteboard", "+update"): {
        "--dry-run",
        "--idempotent-token",
        "--input_format",
        "--overwrite",
        "--source",
        "--whiteboard-token",
    },
}

REQUIRED_DIAGNOSTIC_FLAGS = {
    ("whoami",): {"--as"},
    ("auth", "status"): {"--json", "--verify"},
    ("config", "show"): set(),
    ("profile", "list"): set(),
    ("doctor",): {"--offline"},
}

OPTIONAL_DOMAINS = {
    "application": ("+slash-command-list",),
    "mindnotes": (),
}

WHITEBOARD_FILES = (
    PLUGIN / "skills" / "feishu-whiteboard-ops" / "SKILL.md",
    PLUGIN / "skills" / "feishu-whiteboard-ops" / "references" / "drawio-pipeline.md",
)


class ValidationError(RuntimeError):
    """Raised when the installed runtime cannot satisfy a core workflow."""


def fail(message: str) -> None:
    raise ValidationError(message)


def runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    return env


def run(cli: str, *args: str) -> str:
    result = subprocess.run(
        [cli, *args],
        cwd=ROOT,
        env=runtime_env(),
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        fail(f"command failed ({result.returncode}): lark-cli {' '.join(args)}: {detail}")
    return result.stdout


def parse_version(raw: str) -> str:
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", raw)
    if not match:
        fail(f"could not parse lark-cli version from: {raw.strip()!r}")
    return match.group(1)


def load_skill_catalog(cli: str) -> set[str]:
    raw = run(cli, "skills", "list")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"lark-cli skills list did not return valid JSON: {exc}")

    skills = payload.get("skills")
    if payload.get("ok") is not True or not isinstance(skills, list):
        fail("lark-cli skills list returned an unexpected envelope")

    names = {item.get("name") for item in skills if isinstance(item, dict)}
    missing = CORE_SKILLS - names
    if missing:
        fail(f"missing core runtime skills: {', '.join(sorted(missing))}")

    for name in sorted(ROUTER_SKILLS - names):
        print(
            "WARN: router skill is unavailable in this invocation "
            f"(possibly trimmed by its distribution): {name}"
        )

    return {name for name in names if isinstance(name, str)}


def validate_skill_reads(cli: str, discovered_skills: set[str]) -> tuple[str, int, int]:
    skill_bodies: dict[str, str] = {}
    for skill in sorted(REQUIRED_SKILL_BODIES):
        content = run(cli, "skills", "read", skill)
        if not content.strip():
            fail(f"runtime skill is empty: {skill}")
        skill_bodies[skill] = content

    router_bodies_read = 0
    for skill in sorted(ROUTER_SKILLS & discovered_skills):
        content = run(cli, "skills", "read", skill)
        if not content.strip():
            fail(f"discovered router skill is empty: {skill}")
        router_bodies_read += 1

    shared = skill_bodies["lark-shared"]
    if "# lark-cli" not in shared and "name: lark-shared" not in shared:
        fail("lark-shared content did not match the expected skill format")

    for skill, references in sorted(REQUIRED_REFERENCES.items()):
        for reference in sorted(references):
            content = run(cli, "skills", "read", skill, reference)
            if not content.strip():
                fail(f"runtime reference is empty: {skill}/{reference}")
    return skill_bodies["lark-whiteboard"], len(skill_bodies), router_bodies_read


def long_flags(help_text: str) -> set[str]:
    return set(re.findall(r"--[A-Za-z0-9_-]+", help_text))


def validate_help_flags(
    cli: str, probes: dict[tuple[str, ...], set[str]]
) -> None:
    for command, required_flags in sorted(probes.items()):
        help_text = run(cli, *command, "--help")
        available = long_flags(help_text)
        missing = required_flags - available
        if missing:
            rendered = " ".join(command)
            fail(f"lark-cli {rendered} is missing required flags: {', '.join(sorted(missing))}")


def validate_command_help(cli: str) -> None:
    validate_help_flags(cli, REQUIRED_COMMAND_FLAGS)
    validate_help_flags(cli, REQUIRED_DIAGNOSTIC_FLAGS)


def validate_optional_domains(cli: str) -> int:
    validated = 0
    for domain, shortcuts in OPTIONAL_DOMAINS.items():
        try:
            run(cli, domain, "--help")
        except ValidationError as exc:
            print(f"WARN: optional lark-cli domain is unavailable: {domain}: {exc}")
            continue
        validated += 1
        for shortcut in shortcuts:
            try:
                run(cli, domain, shortcut, "--help")
            except ValidationError as exc:
                print(f"WARN: optional shortcut is unavailable: {domain} {shortcut}: {exc}")
            else:
                validated += 1
    return validated


def validate_repository_guidance(whiteboard_skill: str) -> str:
    for path in PLUGIN.rglob("*.md"):
        text = path.read_text()
        rel = path.relative_to(ROOT)
        if "--api-version" in text:
            fail(f"deprecated docs --api-version guidance remains in {rel}")
        for obsolete in ("@larksuite/whiteboard-cli@^0.2.11", "@larksuite/whiteboard-cli@^0.2.12"):
            if obsolete in text:
                fail(f"obsolete whiteboard-cli range {obsolete} remains in {rel}")
        if "whiteboard +query" in text or "--output_as" in text:
            fail(f"retired whiteboard +query/--output_as surface remains in {rel}")

    match = re.search(r"@larksuite/whiteboard-cli@\^(\d+\.\d+\.\d+)", whiteboard_skill)
    if not match:
        fail("could not discover the whiteboard-cli range from lark-whiteboard")
    expected = match.group(1)

    discovered: set[str] = set()
    for path in WHITEBOARD_FILES:
        discovered.update(
            re.findall(
                r"@larksuite/whiteboard-cli@(?:\^)?(\d+\.\d+\.\d+)",
                path.read_text(),
            )
        )
    if discovered != {expected}:
        fail(
            "whiteboard-cli guidance does not match the runtime skill: "
            f"expected ^{expected}, found {sorted(discovered)}"
        )
    return expected


def main() -> None:
    cli = shutil.which("lark-cli")
    if cli is None:
        print(
            "FAIL: lark-cli was not found on PATH; install or update the "
            "official CLI before running runtime validation",
            file=sys.stderr,
        )
        raise SystemExit(1)

    try:
        version = parse_version(run(cli, "--version"))
        skills = load_skill_catalog(cli)
        whiteboard_skill, core_body_count, router_body_count = validate_skill_reads(
            cli, skills
        )
        validate_command_help(cli)
        optional_command_count = validate_optional_domains(cli)
        whiteboard_version = validate_repository_guidance(whiteboard_skill)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Detected lark-cli {version} at {cli}")
    print(
        f"Validated {core_body_count} core skill bodies and required references; "
        f"read/non-empty checked {router_body_count} available router skill bodies; "
        f"catalog discovered {len(skills)} skills"
    )
    print(f"Validated {optional_command_count} optional domain/shortcut help surfaces")
    print(f"Validated whiteboard-cli guidance ^{whiteboard_version}")
    print("Feishu Next lark-cli runtime validation passed")


if __name__ == "__main__":
    main()
