#!/usr/bin/env python3
"""Validate the Feishu Next plugin package and bundled skills."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "feishu-next"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_VALIDATOR = (
    Path.home()
    / ".codex"
    / "skills"
    / ".system"
    / "plugin-creator"
    / "scripts"
    / "validate_plugin.py"
)
SKILL_VALIDATOR = (
    Path.home()
    / ".codex"
    / "skills"
    / ".system"
    / "skill-creator"
    / "scripts"
    / "quick_validate.py"
)


TEXT_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".py", ".txt", ".toml"}
PLACEHOLDER_PATTERNS = [
    re.compile(r"\[TODO\b", re.IGNORECASE),
    re.compile(r"\bTODO:", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bscaffold\b", re.IGNORECASE),
]
SENSITIVE_PATTERNS = [
    re.compile(r"app_secret\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE),
    re.compile(r"access_token\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE),
    re.compile(r"refresh_token\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE),
    re.compile(r"verification_url\s*[:=]\s*['\"]https?://", re.IGNORECASE),
]
HYGIENE_FILES = (
    MARKETPLACE,
    ROOT / "README.md",
    ROOT / "README_CN.md",
    ROOT / "Makefile",
)
HYGIENE_DIRS = (
    PLUGIN,
    ROOT / "scripts",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001 - report validation context.
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=ROOT, text=True)
    if result.returncode != 0:
        fail("command failed: " + " ".join(cmd))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-missing-codex-validators",
        action="store_true",
        help=(
            "allow static-only validation when Codex plugin/skill validators "
            "are unavailable; never use for release validation"
        ),
    )
    return parser.parse_args()


def validate_marketplace() -> None:
    if not MARKETPLACE.exists():
        fail(".agents/plugins/marketplace.json is missing")

    payload = load_json(MARKETPLACE)
    if payload.get("name") != "feishu-next":
        fail("marketplace name must be feishu-next")

    plugins = payload.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        fail("marketplace must contain exactly one plugin entry")

    entry = plugins[0]
    if entry.get("name") != "feishu-next":
        fail("marketplace plugin entry name must be feishu-next")
    if entry.get("source", {}).get("path") != "./plugins/feishu-next":
        fail("marketplace source path must be ./plugins/feishu-next")
    if entry.get("policy", {}).get("installation") != "AVAILABLE":
        fail("marketplace installation policy must be AVAILABLE")
    if entry.get("policy", {}).get("authentication") != "ON_INSTALL":
        fail("marketplace authentication policy must be ON_INSTALL")


def validate_plugin_manifest() -> None:
    manifest_path = PLUGIN / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        fail("plugin manifest is missing")

    manifest = load_json(manifest_path)
    if manifest.get("name") != "feishu-next":
        fail("plugin manifest name must be feishu-next")
    version = manifest.get("version", "")
    if not re.fullmatch(r"0\.2\.0\+codex\.\d{14}", version):
        fail("plugin manifest version must match 0.2.0+codex.YYYYMMDDHHMMSS")
    default_prompts = manifest.get("interface", {}).get("defaultPrompt", [])
    if not isinstance(default_prompts, list) or not all(isinstance(item, str) for item in default_prompts):
        fail("plugin manifest interface.defaultPrompt must be a string array")
    for index, prompt in enumerate(default_prompts):
        if len(prompt) > 128:
            fail(f"plugin manifest interface.defaultPrompt[{index}] exceeds 128 characters")
    if manifest.get("skills") != "./skills/":
        fail("plugin manifest skills path must be ./skills/")
    if not (PLUGIN / "skills").is_dir():
        fail("plugin skills directory is missing")


def validate_skill_surface() -> None:
    skills_dir = PLUGIN / "skills"
    expected = {
        "feishu-workflow-router",
        "feishu-readonly-doc-export",
        "feishu-doc-asset-map",
        "feishu-im-chat-archive",
        "feishu-whiteboard-ops",
    }
    actual = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    if actual != expected:
        fail(f"unexpected skill surface: {sorted(actual)}")

    for skill in sorted(actual):
        skill_dir = skills_dir / skill
        if not (skill_dir / "SKILL.md").exists():
            fail(f"{skill} is missing SKILL.md")
        if not (skill_dir / "agents" / "openai.yaml").exists():
            fail(f"{skill} is missing agents/openai.yaml")
        agent_text = (skill_dir / "agents" / "openai.yaml").read_text()
        if f"$feishu-next:{skill}" not in agent_text:
            fail(f"{skill} agents/openai.yaml must use the plugin-namespaced default prompt")


def validate_whiteboard_architecture() -> None:
    """Keep whiteboard routing as one workflow skill plus a draw.io reference."""

    skill_dir = PLUGIN / "skills" / "feishu-whiteboard-ops"
    skill_text = (skill_dir / "SKILL.md").read_text()
    reference_path = skill_dir / "references" / "drawio-pipeline.md"
    if not reference_path.exists():
        fail("feishu-whiteboard-ops must include references/drawio-pipeline.md")
    if "references/drawio-pipeline.md" not in skill_text:
        fail("feishu-whiteboard-ops must reference drawio-pipeline.md from SKILL.md")
    for marker in (
        "references/lark-whiteboard-workflow.md",
        "--output ./whiteboard-work/<timestamp>/before.code",
        "--dry-run",
    ):
        if marker not in skill_text:
            fail(f"feishu-whiteboard-ops is missing required workflow guardrail: {marker}")
    if "Keep one Feishu Next whiteboard skill" not in skill_text:
        fail("feishu-whiteboard-ops must document the single-skill whiteboard boundary")
    if "Official skill relationship" not in skill_text or "lark-whiteboard" not in skill_text:
        fail("feishu-whiteboard-ops must document official lark-whiteboard authority")

    router_text = (PLUGIN / "skills" / "feishu-workflow-router" / "SKILL.md").read_text()
    if "feishu-whiteboard-ops" not in router_text or ".drawio" not in router_text:
        fail("feishu-workflow-router must route whiteboard and .drawio workflows")
    if "Authority model" not in router_text or "Official `lark-cli skills read <lark-*>` output" not in router_text:
        fail("feishu-workflow-router must document official-vs-Feishu Next authority")

    asset_map_text = (PLUGIN / "skills" / "feishu-doc-asset-map" / "SKILL.md").read_text()
    if "<whiteboard" not in asset_map_text or "feishu-whiteboard-ops" not in asset_map_text:
        fail("feishu-doc-asset-map must route editable whiteboards to feishu-whiteboard-ops")


def validate_router_migration() -> None:
    """Ensure the plugin router replaces the old standalone lark-cli guide layer."""

    router_text = (PLUGIN / "skills" / "feishu-workflow-router" / "SKILL.md").read_text()
    required_router_markers = {
        "lark-cli-guide": "router must state that it supersedes standalone lark-cli-guide",
        "lark-cli skills list": "router must remind agents to inspect current embedded skills",
        "lark-cli skills read lark-shared": "router must require lark-shared for auth/scope/safety",
        "lark-cli skills read <skill>": "router must point to official runtime skill reads",
        "Do not copy or vendor official `lark-*`": "router must forbid vendoring official lark-* skills",
        "`--as user` / `--as bot`": "router must document identity choice reminders",
        "`--dry-run`": "router must preserve dry-run safety discipline",
        "`--yes`": "router must preserve high-risk confirmation discipline",
        "lark-openapi-explorer": "router must route uncovered APIs through official exploration",
        "lark-cli application --help": "router must support domains without embedded skills",
        "do not invent a `lark-application` skill": "router must reject a fabricated application skill",
        "lark-cli whoami": "router must use whoami for effective identity diagnosis",
        "lark-cli auth status --json --verify": "router must document complete auth verification",
        "lark-cli doctor --offline": "router must keep offline diagnosis available",
        "lark-markdown": "router must route native Markdown operations",
        "lark-vc-agent": "router must distinguish live meeting operations",
        "lark-skill-maker": "router must route custom lark-cli skill authoring",
        "lark-workflow-meeting-summary": "router must prefer the official meeting summary workflow",
        "lark-workflow-standup-report": "router must prefer the official standup workflow",
        "lark-drive-comment-location": "router must route comment-to-document location workflows",
        "--need-relation": "router must preserve the comment-location shortcut flag",
    }
    for marker, message in required_router_markers.items():
        if marker not in router_text:
            fail(message)

    manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
    interface = manifest.get("interface", {})
    prompt = "\n".join(interface.get("defaultPrompt", []))
    if "$feishu-next:feishu-workflow-router" not in prompt:
        fail("plugin default prompt must point to the namespaced router")
    if "official lark-*" not in prompt and "official lark-cli" not in interface.get("longDescription", ""):
        fail("plugin manifest must document official lark-* runtime dependency")

    marketplace = load_json(MARKETPLACE)
    entry = marketplace["plugins"][0]
    entry_description = entry.get("description", "")
    if "standalone Feishu guide" not in entry_description:
        fail("marketplace entry must advertise replacement of standalone Feishu guide skills")

    readme_text = (PLUGIN / "README.md").read_text()
    root_readme_cn = (ROOT / "README_CN.md").read_text()
    if "~/.codex/skills" not in readme_text or "official `lark-cli` skills" not in readme_text:
        fail("plugin README must explain plugin-first migration and official skill boundary")
    if "旧的全局 `lark-cli-guide`" not in root_readme_cn:
        fail("README_CN must document standalone lark-cli-guide retirement path")


def validate_runtime_compatibility_content() -> None:
    """Reject known runtime drift and require the 0.2.0 compatibility surface."""

    production_text_paths = [
        *PLUGIN.rglob("*.md"),
        ROOT / "README.md",
        ROOT / "README_CN.md",
    ]
    for path in production_text_paths:
        if not path.exists():
            continue
        text = path.read_text()
        rel = path.relative_to(ROOT)
        if "--api-version" in text:
            fail(f"{rel} contains deprecated docs --api-version guidance")
        if "@larksuite/whiteboard-cli@^0.2.11" in text:
            fail(f"{rel} contains the obsolete whiteboard-cli 0.2.11 range")

    export_text = (
        PLUGIN / "skills" / "feishu-readonly-doc-export" / "SKILL.md"
    ).read_text()
    for marker in (
        "--url '<FEISHU_OR_LARK_URL>'",
        "--doc-type '<doc|docx|sheet|bitable|slides|wiki>'",
        "--only-schema",
    ):
        if marker not in export_text:
            fail(f"readonly export skill is missing current runtime marker: {marker}")

    asset_text = (PLUGIN / "skills" / "feishu-doc-asset-map" / "SKILL.md").read_text()
    for marker in ("synced_reference", "resource-download --type cover", "lark-cli mindnotes"):
        if marker not in asset_text:
            fail(f"asset map skill is missing current asset routing marker: {marker}")
    if "map its presence" in asset_text:
        fail("asset map must not claim metadata-only Docx cover presence detection")
    if "Do not infer cover presence from" not in asset_text:
        fail("asset map must document the current cover metadata boundary")

    im_text = (PLUGIN / "skills" / "feishu-im-chat-archive" / "SKILL.md").read_text()
    for marker in (
        "process exits with code `0` and",
        "`ok == true`",
        "Do not test the legacy condition `code == 0`",
    ):
        if marker not in im_text:
            fail(f"IM archive skill is missing typed envelope guidance: {marker}")
    if im_text.count("`code == 0`") != 1:
        fail("IM archive skill must mention `code == 0` exactly once, only in the prohibition")

    whiteboard_paths = [
        PLUGIN / "skills" / "feishu-whiteboard-ops" / "SKILL.md",
        PLUGIN / "skills" / "feishu-whiteboard-ops" / "references" / "drawio-pipeline.md",
    ]
    if not all("@larksuite/whiteboard-cli@^0.2.12" in path.read_text() for path in whiteboard_paths):
        fail("whiteboard skill and draw.io reference must use whiteboard-cli ^0.2.12")

    plugin_readme = (PLUGIN / "README.md").read_text()
    if "validated against `lark-cli 1.0.72`" not in plugin_readme:
        fail("plugin README must document the lark-cli 1.0.72 validation baseline")

    root_readme_cn = (ROOT / "README_CN.md").read_text()
    if "`lark-cli 1.0.72`" not in root_readme_cn:
        fail("README_CN must document the lark-cli 1.0.72 validation baseline")

    manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
    if "lark-cli 1.0.72" not in manifest.get("interface", {}).get("longDescription", ""):
        fail("plugin manifest longDescription must document the lark-cli 1.0.72 validation baseline")

    marketplace = load_json(MARKETPLACE)
    marketplace_descriptions = [
        marketplace.get("description", ""),
        marketplace["plugins"][0].get("description", ""),
    ]
    if not all("lark-cli 1.0.72" in text for text in marketplace_descriptions):
        fail("marketplace descriptions must document the lark-cli 1.0.72 validation baseline")

    runtime_validator = (ROOT / "scripts" / "validate_lark_runtime.py").read_text()
    for marker in (
        "REQUIRED_SKILL_BODIES",
        "REQUIRED_DIAGNOSTIC_FLAGS",
        "references/lark-whiteboard-workflow.md",
        '"--dry-run"',
    ):
        if marker not in runtime_validator:
            fail(f"runtime validator is missing compatibility probe marker: {marker}")

    makefile = (ROOT / "Makefile").read_text()
    for target in ("validate-runtime:", "validate-all:"):
        if target not in makefile:
            fail(f"Makefile is missing target {target[:-1]}")


def iter_hygiene_paths() -> list[Path]:
    paths = {path for path in HYGIENE_FILES if path.is_file()}
    for directory in HYGIENE_DIRS:
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in TEXT_EXTENSIONS:
                paths.add(path)
    return sorted(paths)


def validate_text_hygiene() -> None:
    self_path = Path(__file__).resolve()
    for path in iter_hygiene_paths():
        if path.resolve() == self_path:
            continue
        text = path.read_text(errors="ignore")
        rel = path.relative_to(ROOT)
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                fail(f"{rel} contains placeholder text matching {pattern.pattern}")
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                fail(f"{rel} appears to contain a sensitive runtime value")


def validate_codex_validators(*, allow_missing: bool) -> bool:
    missing = [
        name
        for name, path in (
            ("plugin validator", PLUGIN_VALIDATOR),
            ("skill validator", SKILL_VALIDATOR),
        )
        if not path.exists()
    ]
    if missing:
        detail = ", ".join(missing)
        if not allow_missing:
            fail(
                "required Codex validators are unavailable: "
                f"{detail}; install the Codex system skills or rerun with "
                "--allow-missing-codex-validators for non-release static inspection"
            )
        print(f"WARN: explicitly skipped unavailable Codex validators: {detail}")
        return False

    run(["python3", str(PLUGIN_VALIDATOR), str(PLUGIN)])
    for skill_dir in sorted((PLUGIN / "skills").iterdir()):
        if skill_dir.is_dir():
            run(["python3", str(SKILL_VALIDATOR), str(skill_dir)])
    return True


def main(*, allow_missing_codex_validators: bool = False) -> None:
    validate_marketplace()
    validate_plugin_manifest()
    validate_skill_surface()
    validate_whiteboard_architecture()
    validate_router_migration()
    validate_runtime_compatibility_content()
    validate_text_hygiene()

    validators_ran = validate_codex_validators(
        allow_missing=allow_missing_codex_validators
    )
    if validators_ran:
        print("Feishu Next project validation passed")
    else:
        print("Feishu Next static validation passed; Codex validators were explicitly skipped")


if __name__ == "__main__":
    args = parse_args()
    main(
        allow_missing_codex_validators=args.allow_missing_codex_validators
    )
