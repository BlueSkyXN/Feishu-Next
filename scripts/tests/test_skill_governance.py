import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_governance import (
    catalog_errors,
    public_binding_errors,
    valid_name,
    valid_version,
    validate_frontmatter,
    validate_repository,
)


SKILL = '''---
name: feishu-test-skill
description: Use when testing an offline contract.
metadata:
  version: "0.1.0"
  updated: "2026-10-06"
---

# Test
'''
CATALOG = {
    "schema_version": 1,
    "plugins": {
        "feishu-test": {
            "skills": {"feishu-test-skill": {"legacy_names": ["test-skill"]}}
        }
    },
}


class GovernanceTests(unittest.TestCase):
    def test_semver_accepts_release_prerelease_build(self):
        for value in ("0.1.0", "1.0.0", "12.20.3-alpha.1", "0.2.1+codex.20260817181947", "1.2.3-rc.0+build.2"):
            with self.subTest(value=value):
                self.assertTrue(valid_version(value))

    def test_semver_rejects_ambiguous_versions(self):
        for value in ("0.3", "v1.0.0", "01.0.0", "1.01.0", "1.0.01", "1.0.0-01", "1.0.0+", "1.0.0\n", 1, None):
            with self.subTest(value=value):
                self.assertFalse(valid_version(value))

    def test_stable_names(self):
        self.assertTrue(valid_name("feishu-doc-format-align"))
        for value in ("lark-test", "feishu_test", "feishu-Test", "feishu-test-v2", "feishu-test-20261006", "feishu--test", "feishu-" + "x" * 60):
            with self.subTest(value=value):
                self.assertFalse(valid_name(value))

    def test_frontmatter(self):
        self.assertEqual([], validate_frontmatter(SKILL, "feishu-test-skill"))
        for text in (
            SKILL.replace('"0.1.0"', '"0.1"'),
            SKILL.replace('"2026-10-06"', '"2026-02-30"'),
            SKILL.replace('"2026-10-06"', '2026-10-06'),
            SKILL.replace("Use when", "A skill for"),
            SKILL.replace("name: feishu-test-skill", "name: feishu-other"),
            SKILL.replace("metadata:\n", 'version: "1.0.0"\nmetadata:\n'),
            "no frontmatter",
        ):
            with self.subTest(text=text):
                self.assertTrue(validate_frontmatter(text, "feishu-test-skill"))

    def test_catalog_alias_collisions(self):
        self.assertEqual([], catalog_errors(CATALOG))
        bad = copy.deepcopy(CATALOG)
        bad["plugins"]["feishu-test"]["skills"]["feishu-test-skill"]["legacy_names"] = ["feishu-test-skill"]
        self.assertTrue(catalog_errors(bad))
        bad["plugins"]["feishu-test"]["skills"]["feishu-test-skill"]["legacy_names"] = ["old", "old"]
        self.assertTrue(catalog_errors(bad))

    def test_public_bindings(self):
        self.assertFalse(public_binding_errors("lark-cli skills read lark-doc; <BASE_TOKEN>"))
        samples = [
            "/" + "Users/example/private/",
            "/" + "Volumes/Example/private/",
            "https://example." + "feishu.cn/base/" + "A" * 20,
            "cli_" + "a" * 16,
            "tbl" + "a" * 16,
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertTrue(public_binding_errors(text))

    def test_repository_and_marketplace_version_consistency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skill-catalog.json").write_text(json.dumps(CATALOG))
            market = root / ".agents/plugins/marketplace.json"
            market.parent.mkdir(parents=True)
            payload = {"plugins": [{"name": "feishu-test", "source": {"path": "./plugins/feishu-test"}, "version": "0.1.0"}]}
            market.write_text(json.dumps(payload))
            plugin = root / "plugins/feishu-test"
            (plugin / ".codex-plugin").mkdir(parents=True)
            (plugin / ".codex-plugin/plugin.json").write_text(json.dumps({"name": "feishu-test", "version": "0.1.0", "skills": "./skills/"}))
            skill = plugin / "skills/feishu-test-skill"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(SKILL)
            (skill / "agents/openai.yaml").write_text('default_prompt: "Use $feishu-test:feishu-test-skill"\n')
            self.assertEqual([], validate_repository(root))
            payload["plugins"][0]["version"] = "0.2.0"
            market.write_text(json.dumps(payload))
            self.assertTrue(any("version differs" in x for x in validate_repository(root)))

    def test_real_repository(self):
        root = Path(__file__).resolve().parents[2]
        self.assertEqual([], validate_repository(root))
        catalog = json.loads((root / "skill-catalog.json").read_text())
        actual = {p.name for p in (root / "plugins/feishu-next/skills").iterdir() if p.is_dir()}
        self.assertEqual(actual, set(catalog["plugins"]["feishu-next"]["skills"]))

    def test_project_specific_workflows_are_not_public(self):
        root = Path(__file__).resolve().parents[2]
        catalog = json.loads((root / "skill-catalog.json").read_text())
        public = catalog["plugins"]["feishu-next"]["skills"]
        plugin = root / "plugins/feishu-next"
        router_paths = [
            root / "plugins" / owner / "skills/feishu-workflow-router/SKILL.md"
            for owner, entry in catalog["plugins"].items()
            if "feishu-workflow-router" in entry["skills"]
        ]
        self.assertEqual(1, len(router_paths))
        router = router_paths[0].read_text()
        withdrawn = {
            "feishu-ai-usage-analyze",
            "feishu-project-data-maintain",
            "feishu-insight-evidence",
            "feishu-job-ai-transition",
            "feishu-ai-weekly-report",
        }
        for name in withdrawn:
            with self.subTest(name=name):
                self.assertNotIn(name, public)
                self.assertFalse((plugin / "skills" / name).exists())
                self.assertNotIn(f"$feishu-next:{name}", router)
        for name in ("feishu-doc-format-align", "feishu-mindnote-outline", "feishu-base-snapshot-maintain"):
            self.assertIn(name, public)
        aliases = [alias for skill in public.values() for alias in skill["legacy_names"]]
        self.assertNotIn("maintain-ai-project-snapshots", aliases)

    def test_router_stays_in_next_with_no_official_copy(self):
        root = Path(__file__).resolve().parents[2]
        catalog = json.loads((root / "skill-catalog.json").read_text())
        self.assertIn("feishu-workflow-router", catalog["plugins"]["feishu-next"]["skills"])
        self.assertNotIn("feishu-router", catalog["plugins"])
        self.assertFalse((root / "plugins/feishu-router").exists())
        self.assertFalse((root / "scripts/import_lark_snapshot.py").exists())
        self.assertFalse((root / "plugins/feishu-next/vendor").exists())
        self.assertFalse(list((root / "plugins/feishu-next/skills").glob("lark-*")))

    def test_workflow_and_suite_contract(self):
        import validate_project
        validate_project.validate_workflow_architecture()
        router = Path(__file__).resolve().parents[2] / "plugins/feishu-next/skills/feishu-workflow-router"
        orchestration = (router / "references/workflow-orchestration.md").read_text()
        for marker in ("draft locally", "Export failure blocks", "timed-out", "Do not add publishing"):
            with self.subTest(marker=marker):
                self.assertIn(marker, orchestration)
        suite = (router / "references/official-suite-navigation.md").read_text()
        for marker in ("Runtime-only reads", "machine resource", "without user authorization", "frozen `lark_execution`"):
            with self.subTest(marker=marker):
                self.assertIn(marker, suite)

    def test_asset_fetch_uses_current_output_contract(self):
        import re
        import validate_lark_runtime
        root = Path(__file__).resolve().parents[2]
        asset = (root / "plugins/feishu-next/skills/feishu-doc-asset-map/SKILL.md").read_text()
        fetch_examples = []
        for path in (root / "plugins/feishu-next/skills").rglob("*.md"):
            for example in re.findall(r"```bash\n(.*?)```", path.read_text(), re.DOTALL):
                for command in example.replace("\\\n", " ").splitlines():
                    if "docs +fetch" in command:
                        fetch_examples.append(command)
                        with self.subTest(path=path, command=command):
                            self.assertNotIn("--format", command)
        self.assertTrue(fetch_examples)
        self.assertIn("data.document.reference_map", asset)
        self.assertIn("--doc-format", validate_lark_runtime.REQUIRED_COMMAND_FLAGS[("docs", "+fetch")])
        self.assertNotIn("--format", validate_lark_runtime.REQUIRED_COMMAND_FLAGS[("docs", "+fetch")])

    def test_playbooks_remain_flat_and_router_aware(self):
        root = Path(__file__).resolve().parents[2]
        skills = root / "plugins/feishu-next/skills"
        entries = list(skills.rglob("SKILL.md"))
        catalog = json.loads((root / "skill-catalog.json").read_text())
        self.assertEqual(
            set(catalog["plugins"]["feishu-next"]["skills"]),
            {path.parent.name for path in entries},
        )
        self.assertTrue(all(len(path.relative_to(skills).parts) == 2 for path in entries))
        for path in entries:
            if path.parent.name == "feishu-workflow-router":
                continue
            with self.subTest(skill=path.parent.name):
                text = path.read_text()
                self.assertIn("$feishu-next:feishu-workflow-router", text)
                self.assertIn("without redispatching this active", text)
                self.assertIn("reuse is not blanket approval", text)
                self.assertIn("Return ", text)
                self.assertTrue((path.parent / "../feishu-workflow-router/references/playbook-handoff.md").is_file())

    def test_capability_maps_cover_common_routing_boundaries(self):
        import re
        root = Path(__file__).resolve().parents[2]
        router = root / "plugins/feishu-next/skills/feishu-workflow-router"
        maps = {
            "capabilities-documents.md": ("从零创作", "历史版本", "lark-drive", "lark-wiki", "lark-markdown", "feishu-doc-format-align", "feishu-doc-asset-map", "feishu-mindnote-outline"),
            "capabilities-data.md": ("lark-sheets", "lark-base", "BaseApp", "feishu-base-snapshot-maintain", "普通表格"),
            "capabilities-collaboration.md": ("lark-im", "lark-calendar", "lark-meeting", "lark-approval", "feishu-im-chat-archive", "lark-workflow-standup-report"),
            "capabilities-visual-apps.md": ("lark-slides", "lark-whiteboard", "lark-apps", "feishu-whiteboard-ops", "feishu-readonly-doc-export"),
            "capabilities-platform.md": ("lark-shared", "lark-event", "lark-openapi-explorer", "lark-skill-maker", "lark-application"),
        }
        body = (router / "SKILL.md").read_text()
        self.assertLess(len(body.splitlines()), 500)
        self.assertIn("what Feishu/Lark can do", body)
        self.assertIn("do not demand a URL", body)
        for name, markers in maps.items():
            text = (router / "references" / name).read_text()
            with self.subTest(map=name):
                self.assertIn(f"references/{name}", body)
                self.assertNotIn("```bash", text)
                self.assertFalse(text.startswith("---\n"))
                for marker in markers:
                    self.assertIn(marker, text)
        public = json.loads((root / "skill-catalog.json").read_text())["plugins"]["feishu-next"]["skills"]
        for path in (router / "references").glob("capabilities-*.md"):
            for name in re.findall(r"\$feishu-next:([a-z0-9-]+)", path.read_text()):
                self.assertIn(name, public)

    def test_malformed_marketplace_reports_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skill-catalog.json").write_text(json.dumps(CATALOG))
            market = root / ".agents/plugins/marketplace.json"
            market.parent.mkdir(parents=True)
            for payload in ({"plugins": [None]}, {"plugins": {}}, []):
                market.write_text(json.dumps(payload))
                self.assertTrue(validate_repository(root))


if __name__ == "__main__":
    unittest.main()
