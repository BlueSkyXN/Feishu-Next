#!/usr/bin/env python3
"""Validate the Feishu Next plugin package and bundled skills."""

from __future__ import annotations

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


def validate_text_hygiene() -> None:
    self_path = Path(__file__).resolve()
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
            continue
        if ".git" in path.parts:
            continue
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


def main() -> None:
    validate_marketplace()
    validate_plugin_manifest()
    validate_skill_surface()
    validate_whiteboard_architecture()
    validate_router_migration()
    validate_text_hygiene()

    if PLUGIN_VALIDATOR.exists():
        run(["python3", str(PLUGIN_VALIDATOR), str(PLUGIN)])
    else:
        print("WARN: plugin validator not found; skipped external manifest validation")

    if SKILL_VALIDATOR.exists():
        for skill_dir in sorted((PLUGIN / "skills").iterdir()):
            if skill_dir.is_dir():
                run(["python3", str(SKILL_VALIDATOR), str(skill_dir)])
    else:
        print("WARN: skill validator not found; skipped external skill validation")

    print("Feishu Next project validation passed")


if __name__ == "__main__":
    main()
