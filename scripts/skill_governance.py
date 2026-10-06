#!/usr/bin/env python3
"""Validate stable skill names, catalog wiring and semantic versions offline."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path


NUMBER = r"(?:0|[1-9][0-9]*)"
PRERELEASE = rf"(?:{NUMBER}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER = re.compile(
    rf"{NUMBER}\.{NUMBER}\.{NUMBER}"
    rf"(?:-{PRERELEASE}(?:\.{PRERELEASE})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
NAME = re.compile(r"feishu-[a-z0-9]+(?:-[a-z0-9]+)*")
LEGACY_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
VERSION_SUFFIX = re.compile(r"-(?:v[0-9]+(?:-[0-9]+)*|[0-9]{8})$")


def valid_version(value: object) -> bool:
    return isinstance(value, str) and SEMVER.fullmatch(value) is not None


def valid_name(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= 64
        and NAME.fullmatch(value) is not None
        and VERSION_SUFFIX.search(value) is None
    )


def read_frontmatter(text: str) -> dict:
    try:
        import yaml
    except ImportError as exc:
        raise ValueError("PyYAML is required, as for the Codex skill validator") from exc

    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md requires YAML frontmatter")
    try:
        value = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError("invalid YAML frontmatter") from exc
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be a mapping")
    return value


def validate_frontmatter(text: str, expected_name: str) -> list[str]:
    try:
        meta = read_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if not valid_name(expected_name) or meta.get("name") != expected_name:
        errors.append("name must match the stable feishu- directory name")
    if "version" in meta:
        errors.append("use metadata.version rather than top-level version")
    description = meta.get("description")
    if not isinstance(description, str) or "use when" not in description.lower():
        errors.append("description must include a Use when trigger")
    metadata = meta.get("metadata")
    if not isinstance(metadata, dict):
        return errors + ["metadata must contain version and updated"]
    if not valid_version(metadata.get("version")):
        errors.append("metadata.version must be a quoted SemVer string")
    updated = metadata.get("updated")
    try:
        if not isinstance(updated, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", updated):
            raise ValueError
        dt.date.fromisoformat(updated)
    except ValueError:
        errors.append("metadata.updated must be a quoted ISO date")
    return errors


def catalog_errors(catalog: object) -> list[str]:
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        return ["catalog schema_version must be 1"]
    plugins = catalog.get("plugins")
    if not isinstance(plugins, dict) or not plugins:
        return ["catalog plugins must be a non-empty mapping"]
    errors = []
    names: set[str] = set()
    aliases: set[str] = set()
    for plugin, entry in plugins.items():
        if not valid_name(plugin):
            errors.append(f"invalid plugin name: {plugin}")
        skills = entry.get("skills") if isinstance(entry, dict) else None
        if not isinstance(skills, dict) or not skills:
            errors.append(f"{plugin}: skills must be a non-empty mapping")
            continue
        for name, skill in skills.items():
            if not valid_name(name) or name in names:
                errors.append(f"invalid or duplicate canonical name: {name}")
            names.add(name)
            old_names = skill.get("legacy_names") if isinstance(skill, dict) else None
            if not isinstance(old_names, list):
                errors.append(f"{name}: legacy_names must be an array")
                continue
            for old in old_names:
                if not isinstance(old, str) or len(old) > 64 or not LEGACY_NAME.fullmatch(old):
                    errors.append(f"{name}: invalid legacy name")
                elif old in aliases:
                    errors.append(f"duplicate legacy alias: {old}")
                else:
                    aliases.add(old)
    if names & aliases:
        errors.append("legacy aliases must not collide with canonical names")
    return errors


def public_binding_errors(text: str) -> list[str]:
    patterns = {
        "private absolute path": r"/(?:Volumes/[^/\s]+|Users/[^/\s]+|home/[^/\s]+)/",
        "tenant resource URL": r"https?://[^/\s]+\.(?:feishu\.cn|larksuite\.com)/(?:wiki|docx|base|sheets|mindnotes?)/[A-Za-z0-9]{8,}",
        "concrete Lark identity": r"\b(?:cli|ou|oc|om)_[A-Za-z0-9]{16,}\b",
        "concrete Base identifier": r"\b(?:tbl|vew|fld|rec)[A-Za-z0-9]{12,}\b",
    }
    return [label for label, pattern in patterns.items() if re.search(pattern, text)]


def validate_repository(root: Path) -> list[str]:
    try:
        catalog = json.loads((root / "skill-catalog.json").read_text(encoding="utf-8"))
        marketplace = json.loads((root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"unable to read catalog/marketplace: {exc}"]
    errors = catalog_errors(catalog)
    if errors:
        return errors
    plugins = catalog["plugins"]
    market_plugins = marketplace.get("plugins") if isinstance(marketplace, dict) else None
    if not isinstance(market_plugins, list) or not all(
        isinstance(entry, dict) and valid_name(entry.get("name")) for entry in market_plugins
    ):
        return ["marketplace plugins must be an array of named plugin objects"]
    entries = {entry["name"]: entry for entry in market_plugins}
    if len(entries) != len(market_plugins):
        errors.append("duplicate marketplace plugin name")
    if set(entries) != set(plugins):
        errors.append("catalog and marketplace plugin sets differ")
    if (root / "skills").exists():
        errors.append("root-level skills directory is not allowed")
    router_path = root / "plugins/feishu-next/skills/feishu-workflow-router/SKILL.md"
    router = router_path.read_text(encoding="utf-8") if router_path.is_file() else ""
    for plugin, entry in plugins.items():
        plugin_dir = root / "plugins" / plugin
        manifest_path = plugin_dir / ".codex-plugin/plugin.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            errors.append(f"{plugin}: missing or invalid manifest")
            continue
        if not isinstance(manifest, dict):
            errors.append(f"{plugin}: manifest must be an object")
            continue
        if manifest.get("name") != plugin or not valid_version(manifest.get("version")):
            errors.append(f"{plugin}: manifest name/version invalid")
        if manifest.get("skills") != "./skills/":
            errors.append(f"{plugin}: skills path must be ./skills/")
        market_entry = entries.get(plugin, {})
        source = market_entry.get("source")
        if not isinstance(source, dict) or source.get("path") != f"./plugins/{plugin}":
            errors.append(f"{plugin}: marketplace source mismatch")
        if "version" in market_entry and market_entry["version"] != manifest.get("version"):
            errors.append(f"{plugin}: marketplace version differs from manifest")
        skills_dir = plugin_dir / "skills"
        actual = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.is_dir() else set()
        if actual != set(entry["skills"]):
            errors.append(f"{plugin}: catalog/skill directories differ")
        for name in entry["skills"]:
            skill_dir = skills_dir / name
            skill_path = skill_dir / "SKILL.md"
            if not skill_path.is_file():
                errors.append(f"{name}: missing SKILL.md")
                continue
            text = skill_path.read_text(encoding="utf-8")
            errors.extend(f"{name}: {error}" for error in validate_frontmatter(text, name))
            agent_path = skill_dir / "agents/openai.yaml"
            agent = agent_path.read_text(encoding="utf-8") if agent_path.is_file() else ""
            if f"${plugin}:{name}" not in agent:
                errors.append(f"{name}: missing namespaced agent prompt")
            if plugin == "feishu-next" and name != "feishu-workflow-router":
                if f"$feishu-next:{name}" not in router:
                    errors.append(f"{name}: missing workflow router entry")
        if plugin == "feishu-next":
            for path in plugin_dir.rglob("*"):
                if path.is_symlink():
                    errors.append(f"{path.relative_to(root)}: public package must not depend on symlinks")
                elif path.is_file() and path.suffix in {".md", ".json", ".yaml", ".yml", ".py"}:
                    errors.extend(
                        f"{path.relative_to(root)}: {error}"
                        for error in public_binding_errors(path.read_text(encoding="utf-8"))
                    )
    return errors
