import contextlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validate_privacy as privacy


def synthetic_identity():
    return "ou_" + "A1b2C3d4E5f6G7h8"


class PrivacyRulesTests(unittest.TestCase):
    def test_private_patterns_are_detected_without_returning_values(self):
        samples = {
            "private-path": "/" + "Users/person/private/report.txt",
            "lark-identity": synthetic_identity(),
            "base-resource-id": "tbl" + "A1b2C3d4E5f6G7h8",
            "tenant-resource-url": "https://tenant." + "feishu.cn/docx/" + "A1b2C3d4E5f6G7h8",
            "jwt": "eyJ" + "A" * 20 + "." + "B" * 20 + "." + "C" * 20,
            "private-key": "-----BEGIN " + "PRIVATE KEY-----",
            "credential-literal": 'access_' + 'token = "' + "aB9x" * 8 + '"',
            "bearer-literal": '"Bearer ' + "aB9x" * 8 + '"',
            "personal-email": "person" + "@" + "private.test",
            "phone-number": "139" + "12345678",
        }
        for rule, value in samples.items():
            with self.subTest(rule=rule):
                findings = privacy.scan_text("test", "sample.md", "intro\n" + value, set())
                self.assertIn(rule, {finding.rule for finding in findings})
                self.assertTrue(all(finding.line == 2 for finding in findings))
                self.assertNotIn(value, repr(findings))

    def test_windows_private_path(self):
        value = "C:" + "\\Users\\person\\private.txt"
        self.assertIn("private-path", {x.rule for x in privacy.scan_text("test", "sample.md", value, set())})

    def test_allowlist_is_exact_path_rule_and_hash(self):
        value = synthetic_identity()
        allowed = {("fixture.md", "lark-identity", privacy.sha256(value.encode()))}
        self.assertFalse(privacy.scan_text("test", "fixture.md", value, allowed))
        self.assertTrue(privacy.scan_text("test", "other.md", value, allowed))
        self.assertTrue(privacy.scan_text("test", "fixture.md", value + "X", allowed))
        self.assertTrue(privacy.scan_text("test", "fixture.md", value, {("fixture.md", "jwt", privacy.sha256(value.encode()))}))

    def test_allowlist_rejects_wildcards_missing_reasons_and_unknown_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allow.json"
            entry = {"path": "fixture.md", "rule": "lark-identity", "sha256": "a" * 64, "reason": "Synthetic test fixture"}
            for update in ({"path": "*.md"}, {"reason": ""}, {"rule": "all"}, {"path": "../private.md"}):
                path.write_text(json.dumps({"schema_version": 1, "entries": [{**entry, **update}]}))
                with self.subTest(update=update), self.assertRaises(privacy.CheckError):
                    privacy.load_allowlist(path)

    def test_generated_and_unsafe_paths_are_blocked(self):
        for name in ("local/note.md", "exports/doc.json", "diagrams/image.png", "src/.DS_Store", "__MACOSX/._x",
                     "src/__pycache__/x.pyc", "old.zip", ".env", ".env.production", "../outside", "/absolute", "C:/absolute", "a\\b"):
            with self.subTest(name=name):
                self.assertIsNotNone(privacy.path_rule(name))
        self.assertIsNone(privacy.path_rule("plugins/feishu-test/skills/feishu-test/SKILL.md"))

    def test_binary_and_large_files_fail_closed(self):
        self.assertEqual("binary-requires-privacy-review", privacy.scan_bytes("test", "asset.png", b"\x89PNG\x00", set())[0].rule)
        with patch.object(privacy, "MAX_FILE_BYTES", 4):
            self.assertEqual("file-too-large-for-review", privacy.scan_bytes("test", "large.md", b"12345", set())[0].rule)

    def test_missing_gitleaks_does_not_silently_pass(self):
        with patch.object(privacy.shutil, "which", return_value=None):
            with self.assertRaises(privacy.CheckError):
                privacy.gitleaks_scan(Path.cwd(), [], False)

    def test_gitleaks_report_is_sanitized_and_environment_isolated(self):
        sentinel = "DO_NOT_DISCLOSE_SCANNER_CONTENT"
        seen_commands = []

        def fake_run(command, **kwargs):
            seen_commands.append(command)
            self.assertIn("--redact=100", command)
            self.assertIn("--ignore-gitleaks-allow", command)
            self.assertNotIn("GITLEAKS_CONFIG", kwargs["env"])
            report = Path(command[command.index("--report-path") + 1])
            report.write_text(json.dumps([{"File": "entry-000000.txt", "StartLine": 1, "RuleID": "generic-api-key", "Secret": sentinel, "Match": sentinel}]))
            return subprocess.CompletedProcess(command, 1, sentinel.encode(), sentinel.encode())

        with patch.object(privacy.shutil, "which", return_value="gitleaks"), patch.object(privacy.subprocess, "run", side_effect=fake_run), patch.dict(os.environ, {"GITLEAKS_CONFIG": "untrusted"}):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                findings = privacy.gitleaks_scan(Path.cwd(), [("index", "safe.md", b"content")], False)
            self.assertNotIn(sentinel, repr(findings) + output.getvalue())
            self.assertEqual("gitleaks:generic-api-key", findings[0].rule)
            self.assertEqual("safe.md", findings[0].path)
            self.assertEqual(1, len(seen_commands))


class PrivacyRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "repo"
        self.root.mkdir()
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "Privacy Test")
        self.run_git("config", "user.email", "test@localhost")
        (self.root / ".gitignore").write_text("/local/\n/dist/\n*.zip\n__pycache__/\n")

    def run_git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def findings(self, **kwargs):
        return privacy.check(self.root, static_only=True, **kwargs)[0]

    def test_public_untracked_and_index_are_both_checked(self):
        path = self.root / "candidate.md"
        path.write_text(synthetic_identity())
        self.run_git("add", "candidate.md")
        path.write_text("clean worktree\n")
        findings = self.findings()
        self.assertTrue(any(x.scope == "index" and x.rule == "lark-identity" for x in findings))
        self.assertFalse(any(x.scope == "worktree" and x.path == "candidate.md" for x in findings))
        other = self.root / "untracked.md"
        other.write_text(synthetic_identity())
        self.assertTrue(any(x.scope == "worktree" and x.path == "untracked.md" for x in self.findings()))

    def test_global_excludes_cannot_hide_candidates(self):
        ignore = Path(self.directory.name) / "global-ignore"
        ignore.write_text("hidden.md\n")
        self.run_git("config", "core.excludesFile", str(ignore))
        (self.root / "hidden.md").write_text(synthetic_identity())
        self.assertTrue(any(x.path == "hidden.md" for x in self.findings()))

    def test_local_private_files_are_not_read_or_deleted(self):
        local = self.root / "local"
        local.mkdir()
        path = local / "private.md"
        path.write_text(synthetic_identity())
        before = path.read_bytes()
        self.assertFalse(self.findings())
        self.assertEqual(before, path.read_bytes())
        self.run_git("add", "-f", "local/private.md")
        self.assertTrue(any(x.rule == "private-or-generated-path" for x in self.findings()))

    def test_root_ignore_is_required(self):
        (self.root / ".gitignore").write_text("")
        self.assertTrue(any(x.rule == "missing-repository-local-ignore" for x in self.findings()))

    def test_later_negation_cannot_disable_local_protection(self):
        (self.root / ".gitignore").write_text("/local/\n!/local/\n")
        self.assertTrue(any(x.rule == "local-ignore-overridden" for x in self.findings()))

    def test_history_finds_deleted_sensitive_content(self):
        path = self.root / "old.md"
        path.write_text(synthetic_identity())
        self.run_git("add", ".gitignore", "old.md")
        self.run_git("commit", "-qm", "fixture")
        self.run_git("rm", "old.md")
        self.run_git("commit", "-qm", "remove fixture")
        self.assertFalse(self.findings())
        self.assertTrue(any(x.scope.startswith("history:") and x.rule == "lark-identity" for x in self.findings(history=True)))

    def create_release(self):
        plugin = self.root / "plugins/feishu-test"
        (plugin / ".codex-plugin").mkdir(parents=True)
        (plugin / ".codex-plugin/plugin.json").write_text('{"name":"feishu-test","version":"0.1.0"}\n')
        (plugin / "README.md").write_text("Synthetic public package\n")
        (self.root / "LICENSE").write_text("Synthetic license fixture\n")
        self.run_git("add", ".gitignore", "LICENSE", "plugins")
        self.run_git("commit", "-qm", "release fixture")
        return privacy.approved_package(self.root, "feishu-test", "HEAD")

    def write_archive(self, entries, extra=()):
        archive = Path(self.directory.name) / "release.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(archive, "w") as bundle:
                for name, (_, data) in entries.items():
                    bundle.writestr(name, data)
                for name, data in extra:
                    bundle.writestr(name, data)
        return archive

    def test_archive_must_match_reviewed_revision(self):
        entries = self.create_release()
        archive = self.write_archive(entries)
        self.assertFalse(self.findings(archive=archive, plugin="feishu-test"))
        entries["feishu-test/README.md"] = ("unused", b"changed content")
        archive = self.write_archive(entries)
        self.assertTrue(any(x.rule == "content-differs-from-approved-revision" for x in self.findings(archive=archive, plugin="feishu-test")))

    def test_archive_rejects_metadata_extra_files_and_traversal(self):
        entries = self.create_release()
        archive = self.write_archive(entries, [
            ("feishu-test/.DS_Store", b"private"), ("__MACOSX/._item", b"metadata"),
            ("../escaped.txt", b"outside"), ("feishu-test/extra.md", b"extra"),
            ("feishu-test/old.zip", b"nested"), ("feishu-test/README.md", b"duplicate"),
        ])
        rules = {x.rule for x in self.findings(archive=archive, plugin="feishu-test")}
        self.assertTrue({"private-or-generated-path", "unsafe-path", "file-outside-approved-package", "nested-or-source-archive", "duplicate-archive-entry"}.issubset(rules))
        self.assertFalse((self.root / "escaped.txt").exists())

    def test_archive_rejects_hidden_comments_and_extra_metadata(self):
        entries = self.create_release()
        info = zipfile.ZipInfo("feishu-test/metadata.txt")
        info.comment = b"synthetic comment"
        info.extra = b"\xfe\xca\x04\x00test"
        archive = self.write_archive(entries, [(info, b"metadata fixture")])
        with zipfile.ZipFile(archive, "a") as bundle:
            bundle.comment = b"synthetic archive comment"
        rules = {x.rule for x in self.findings(archive=archive, plugin="feishu-test")}
        self.assertIn("archive-comment-not-allowed", rules)
        self.assertIn("archive-extra-metadata-not-allowed", rules)

    def test_archive_requires_license_and_all_files(self):
        entries = self.create_release()
        entries.pop("feishu-test/LICENSE")
        archive = self.write_archive(entries)
        self.assertTrue(any(x.rule == "missing-approved-package-file" for x in self.findings(archive=archive, plugin="feishu-test")))

    def test_archive_rejects_symlinks_and_size_excess(self):
        entries = self.create_release()
        info = zipfile.ZipInfo("feishu-test/link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive = self.write_archive(entries, [(info, b"../../outside")])
        self.assertTrue(any(x.rule == "archive-symlink" for x in self.findings(archive=archive, plugin="feishu-test")))
        with patch.object(privacy, "MAX_ARCHIVE_BYTES", 1):
            with self.assertRaises(privacy.CheckError):
                self.findings(archive=archive, plugin="feishu-test")


if __name__ == "__main__":
    unittest.main()
