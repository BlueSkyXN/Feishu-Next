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
    if not re.fullmatch(r"0\.3\.0\+codex\.\d{14}", version):
        fail("plugin manifest version must match 0.3.0+codex.YYYYMMDDHHMMSS")
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
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            fail(f"{skill} is missing SKILL.md")
        skill_text = skill_path.read_text()
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
        if frontmatter is None:
            fail(f"{skill} SKILL.md is missing YAML frontmatter")
        description_match = re.search(
            r"^description:\s*(.+)$", frontmatter.group(1), re.MULTILINE
        )
        if description_match is None:
            fail(f"{skill} frontmatter is missing description")
        description = description_match.group(1).strip().strip("'\"")
        if "use when" not in description.lower():
            fail(f"{skill} description must include an explicit 'Use when' trigger")
        if not (skill_dir / "agents" / "openai.yaml").exists():
            fail(f"{skill} is missing agents/openai.yaml")
        agent_text = (skill_dir / "agents" / "openai.yaml").read_text()
        if f"$feishu-next:{skill}" not in agent_text:
            fail(f"{skill} agents/openai.yaml must use the plugin-namespaced default prompt")

    router_text = (skills_dir / "feishu-workflow-router" / "SKILL.md").read_text()
    router_reference = "references/lark-execution-context.md"
    if router_reference not in router_text:
        fail("feishu-workflow-router must conditionally route to lark-execution-context.md")

    for skill in sorted(actual - {"feishu-workflow-router"}):
        skill_text = (skills_dir / skill / "SKILL.md").read_text()
        for marker in (
            "$feishu-next:feishu-workflow-router",
            "`lark_execution` contract",
            "--profile '<profile>'",
            "--as '<identity>'",
        ):
            if marker not in skill_text:
                fail(f"{skill} must preserve direct-invocation execution context: {marker}")

    whiteboard_text = (skills_dir / "feishu-whiteboard-ops" / "SKILL.md").read_text()
    drawio_reference = "references/drawio-pipeline.md"
    if drawio_reference not in whiteboard_text or "If a `.drawio`" not in whiteboard_text:
        fail("feishu-whiteboard-ops must conditionally route .drawio work to its reference")


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
        "Capability gaps and UI fallback": "router must define the CLI capability gap escalation protocol",
        "not execution authorization": "router must forbid treating suggestion wording as UI write authorization",
        "bounded to the single proven gap": "router must bound UI fallback to the proven CLI gap",
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


def validate_execution_context_contract() -> None:
    """Require explicit channel/system parameters without leaking local identity data."""

    router_dir = PLUGIN / "skills" / "feishu-workflow-router"
    router_text = (router_dir / "SKILL.md").read_text()
    reference_path = router_dir / "references" / "lark-execution-context.md"
    if not reference_path.exists():
        fail("feishu-workflow-router must include references/lark-execution-context.md")
    if "references/lark-execution-context.md" not in router_text:
        fail("feishu-workflow-router must link the lark execution context reference")

    reference_text = reference_path.read_text()
    combined = f"{router_text}\n{reference_text}"
    required_markers = {
        "LARK_CHANNEL": "execution routing must diagnose lark-channel bindings",
        "execution_context_mismatch": "execution routing must classify context mismatches",
        "Four-stage model": "execution routing must separate bootstrap, draft, freeze, and execution",
        "lark_execution_draft:": "natural-language onboarding must support an incomplete draft",
        "Discovery before question": "internal execution fields must be discovered before asking the user",
        "Do not ask the user to supply a raw App ID or profile name": (
            "execution routing must not expose internal profile/App fields as user prerequisites"
        ),
        "Expected App anchors": "expected App values must come from an independent anchor",
        "Never copy `config show.appId`": (
            "preflight actual values must not bootstrap their own expected App anchor"
        ),
        "Channel caller responsibilities": (
            "channel execution must require caller App and target metadata"
        ),
        "chat, message, or thread target": (
            "channel execution must carry the incoming-event target"
        ),
        "caller_context_incomplete": (
            "missing channel envelope data must have a bounded stop classification"
        ),
        "system_candidate_ambiguous": (
            "ambiguous system representatives must have a non-raw selection boundary"
        ),
        "Read-only export may retain `resource_owner: unknown`": (
            "read-only export ownership must have an explicit draft/freeze rule"
        ),
        "unknown/legacy-runtime": (
            "execution preflight must support runtimes without profile source fields"
        ),
        "Older runtimes such as `1.0.83`": (
            "profile source compatibility must include the validated legacy runtime"
        ),
        "--profile": "execution routing must pass the requested profile explicitly",
        "--as user": "execution routing must document explicit user identity",
        "--as bot": "execution routing must document explicit bot identity",
        "OAuth scope, not an app": "scope flags must not be treated as app selectors",
        "diagnostic evidence": "environment variables must remain diagnostic evidence",
        "lark_execution:": "the execution contract schema is missing",
        "context: channel | system": "the execution contract must select channel or system",
        "expected_app_id": "the execution contract must assert the app ID",
        "expected_app_name": "the execution contract must assert the app name",
        "resource_owner": "the execution contract must state resource ownership",
        "operation:": "the execution contract must carry the business operation",
        "caller_must_supply_matching_execution_context": (
            "context mismatch diagnostics must return control to the caller"
        ),
        "Generic first-use authentication guidance": (
            "runtime auth guidance must not override execution context preflight"
        ),
        "Before any business, authentication, profile, or identity-policy invocation": (
            "all lark-cli business and lifecycle calls must require the execution contract"
        ),
        "bot-owned, and shared": (
            "execution context preflight must cover bot-owned and shared resources"
        ),
        "config show.profileSource": (
            "execution preflight must consume the runtime profile selector source when present"
        ),
        "Preserve `--profile <profile>` and `--as <identity>`": (
            "cross-command workflows must preserve profile and identity"
        ),
    }
    for marker, message in required_markers.items():
        if marker not in combined:
            fail(message)

    router_markers = {
        "Bootstrap is read-only and does not require a complete business contract": (
            "router must allow safe discovery before contract freeze"
        ),
        "current message, selected resource, reply/quote": (
            "router must resolve deictic resources before asking for URLs"
        ),
        "bounded Base read": "router must define a bounded default for vague Base reads",
        "relative calendar ranges": (
            "router must preserve timezone evidence for natural-language calendar ranges"
        ),
        "proposed identity (routing only; must be verified before execution)": (
            "routing output must not present a proposed identity as verified"
        ),
        "mechanical second confirmation": (
            "router must distinguish an exact send instruction from redundant confirmation"
        ),
        "runtime exit-10 gate": (
            "an exact send instruction must not bypass a runtime high-risk confirmation gate"
        ),
    }
    for marker, message in router_markers.items():
        if marker not in router_text:
            fail(message)

    for skill_dir in sorted((PLUGIN / "skills").iterdir()):
        if not skill_dir.is_dir() or skill_dir.name == "feishu-workflow-router":
            continue
        skill_text = (skill_dir / "SKILL.md").read_text()
        if "do not ask an ordinary\nuser for a raw profile name or App ID" not in skill_text:
            fail(f"{skill_dir.name} must return internal profile/App discovery to the Router")

    for command in (
        "lark-cli auth login",
        "lark-cli profile add",
        "lark-cli profile use",
        "lark-cli config bind",
        "lark-cli config strict-mode",
        "lark-cli config default-as",
    ):
        if command not in reference_text:
            fail(f"execution context reference must prohibit mismatch recovery via {command}")

    concrete_app_id = re.compile(r"\bcli_[a-z0-9]{16,}\b")
    private_home_path = re.compile(r"/(?:Users|home)/[^/\s]+/")
    for path in PLUGIN.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(errors="ignore")
        rel = path.relative_to(ROOT)
        if concrete_app_id.search(text):
            fail(f"{rel} contains a concrete App ID; keep local mappings out of the plugin")
        if private_home_path.search(text):
            fail(f"{rel} contains a private absolute home path")


def validate_runtime_compatibility_content() -> None:
    """Reject known runtime drift and require the 0.3.0 compatibility surface."""

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
        for obsolete in ("@larksuite/whiteboard-cli@^0.2.11", "@larksuite/whiteboard-cli@^0.2.12"):
            if obsolete in text:
                fail(f"{rel} contains the obsolete whiteboard-cli range {obsolete}")
        if "whiteboard +query" in text or "--output_as" in text:
            fail(f"{rel} contains the retired whiteboard +query/--output_as surface")

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
    if not all("@larksuite/whiteboard-cli@0.2.13" in path.read_text() for path in whiteboard_paths):
        fail("whiteboard skill and draw.io reference must pin whiteboard-cli 0.2.13")

    whiteboard_skill = whiteboard_paths[0].read_text()
    for marker in (
        "--offline",
        "cache miss",
        "explicit user authorization",
        "does not\nauthorize third-party code execution",
        "obtain explicit\nauthorization for the download",
    ):
        if marker not in whiteboard_skill:
            fail(f"whiteboard dependency execution boundary is missing: {marker}")

    plugin_readme = (PLUGIN / "README.md").read_text()
    if (
        "runtime-validated against the installed\n`lark-cli 1.0.83`" not in plugin_readme
        or "source-audited against `lark-cli 1.0.86`" not in plugin_readme
    ):
        fail("plugin README must separate the lark-cli 1.0.83 runtime and 1.0.86 source baselines")

    root_readme_cn = (ROOT / "README_CN.md").read_text()
    if "`lark-cli 1.0.83`" not in root_readme_cn or "`lark-cli 1.0.86`" not in root_readme_cn:
        fail("README_CN must separate the lark-cli runtime and source baselines")

    manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
    long_description = manifest.get("interface", {}).get("longDescription", "")
    if "runtime-validated against lark-cli 1.0.83" not in long_description or "source-audited against lark-cli 1.0.86" not in long_description:
        fail("plugin manifest must separate the lark-cli runtime and source baselines")

    marketplace = load_json(MARKETPLACE)
    marketplace_descriptions = [
        marketplace.get("description", ""),
        marketplace["plugins"][0].get("description", ""),
    ]
    if not all(
        "runtime-validated against lark-cli 1.0.83" in text
        and "source-audited against lark-cli 1.0.86" in text
        for text in marketplace_descriptions
    ):
        fail("marketplace descriptions must separate runtime and source baselines")

    runtime_validator = (ROOT / "scripts" / "validate_lark_runtime.py").read_text()
    for marker in (
        "REQUIRED_SKILL_BODIES",
        "REQUIRED_DIAGNOSTIC_FLAGS",
        "references/lark-whiteboard-workflow.md",
        "references/lark-whiteboard-export.md",
        "references/lark-doc-xml.md",
        "ROUTER_SKILLS",
        "read/non-empty checked",
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
    validate_execution_context_contract()
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
