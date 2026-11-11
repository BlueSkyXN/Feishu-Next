#!/usr/bin/env python3
"""Offline privacy checks for Git candidates, the index, history and release ZIPs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 5000
PRIVATE_DIRS = {
    "local", "diagrams", "whiteboard-work", "exports", "lark-im-resources",
    "asset-maps", "chat-archives", "dist", "__pycache__", "__macosx", ".git",
}
PRIVATE_SUFFIXES = {".pyc", ".pyo", ".log", ".har", ".db", ".sqlite", ".sqlite3"}
ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar"}
RULES = {
    "private-path": re.compile(r"(?:/(?:Users|home)/[^/\s`\"'<>]+/[^\s`\"'<>)]*|/(?:Volumes)/[^/\s`\"'<>]+/[^\s`\"'<>)]*|[A-Za-z]:\\+Users\\+[^\\\s`\"'<>]+\\+[^\s`\"'<>)]*)"),
    "lark-identity": re.compile(r"\b(?:cli|ou|oc|om|on|omt)_[A-Za-z0-9]{12,}\b"),
    "base-resource-id": re.compile(r"\b(?:tbl|vew|fld|rec)[A-Za-z0-9]{12,}\b"),
    "tenant-resource-url": re.compile(r"https?://[^/\s`\"'<>]+\.(?:feishu\.cn|larksuite\.com|larkoffice\.com)/(?:wiki|docx?|base|sheets|mindnotes?|slides|file|folder)/[A-Za-z0-9]{8,}", re.IGNORECASE),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "credential-literal": re.compile(r"\b(?:app[_-]?secret|client[_-]?secret|access[_-]?token|refresh[_-]?token|api[_-]?key|password)\b[\"']?\s*[:=]\s*[\"'](?P<value>[A-Za-z0-9_+/=.:-]{12,})[\"']", re.IGNORECASE),
    "bearer-literal": re.compile(r"[\"']Bearer (?P<value>[A-Za-z0-9_./+=-]{12,})[\"']", re.IGNORECASE),
    "personal-email": re.compile(r"(?<![\w@])[A-Za-z0-9_.+%-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}"),
    "phone-number": re.compile(r"(?<!\d)(?:\+86[- ]?)?1[3-9]\d{9}(?!\d)"),
}


@dataclass(frozen=True)
class Finding:
    scope: str
    path: str
    line: int
    rule: str
    fingerprint: str = ""


class CheckError(RuntimeError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise CheckError("local Git inspection failed; no command output was disclosed")
    return result.stdout


def load_allowlist(path: Path) -> set[tuple[str, str, str]]:
    if not path.is_file():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload["entries"]
        if payload.get("schema_version") != 1 or not isinstance(entries, list):
            raise ValueError
        allowed = set()
        for entry in entries:
            if set(entry) != {"path", "rule", "sha256", "reason"}:
                raise ValueError
            name = entry["path"]
            if not isinstance(name, str) or not safe_path(name) or any(c in name for c in "*?["):
                raise ValueError
            if entry["rule"] not in RULES or not re.fullmatch(r"[a-f0-9]{64}", entry["sha256"]):
                raise ValueError
            if not isinstance(entry["reason"], str) or not entry["reason"].strip():
                raise ValueError
            key = (name, entry["rule"], entry["sha256"])
            if key in allowed:
                raise ValueError
            allowed.add(key)
        return allowed
    except (OSError, ValueError, KeyError, TypeError):
        raise CheckError("invalid privacy allowlist; exact path/rule/hash/reason entries are required") from None


def safe_path(name: str) -> bool:
    return bool(name) and not (
        name.startswith("/") or "\\" in name or re.match(r"^[A-Za-z]:", name)
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or any(ord(char) < 32 for char in name)
    )


def path_rule(name: str) -> str | None:
    if not safe_path(name):
        return "unsafe-path"
    path = PurePosixPath(name)
    parts = {part.lower() for part in path.parts}
    base = path.name.lower()
    if parts & PRIVATE_DIRS:
        return "private-or-generated-path"
    if base == ".ds_store" or base.startswith("._") or path.suffix.lower() in PRIVATE_SUFFIXES:
        return "private-or-generated-path"
    if path.suffix.lower() in ARCHIVE_SUFFIXES:
        return "nested-or-source-archive"
    if base in {".env", "storage.json", "cookies.txt", "id_rsa", "id_ed25519"} or base.startswith(".env."):
        return "credential-file"
    return None


def scan_text(scope: str, name: str, text: str, allowed: set[tuple[str, str, str]]) -> list[Finding]:
    findings = []
    for rule, pattern in RULES.items():
        for match in pattern.finditer(text):
            value = match.groupdict().get("value") or match.group()
            fingerprint = sha256(value.encode("utf-8"))
            if (name, rule, fingerprint) in allowed:
                continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append(Finding(scope, name, line, rule, fingerprint))
    return findings


def scan_bytes(scope: str, name: str, data: bytes, allowed: set[tuple[str, str, str]]) -> list[Finding]:
    if len(data) > MAX_FILE_BYTES:
        return [Finding(scope, name, 0, "file-too-large-for-review")]
    try:
        text = data.decode("utf-8")
        if "\x00" in text:
            raise UnicodeError
    except UnicodeError:
        return [Finding(scope, name, 0, "binary-requires-privacy-review")]
    return scan_text(scope, name, text, allowed)


def index_entries(root: Path) -> list[tuple[str, str, str, str]]:
    entries = []
    for raw in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if raw:
            meta, name = raw.decode("utf-8").split("\t", 1)
            mode, oid, stage = meta.split()
            entries.append((mode, oid, stage, name))
    return entries


def read_blob(root: Path, oid: str) -> bytes:
    if int(git(root, "cat-file", "-s", oid)) > MAX_FILE_BYTES:
        raise CheckError("a Git blob exceeds the bounded privacy review size")
    return git(root, "cat-file", "blob", oid)


def worktree_and_index(root: Path) -> tuple[list[Finding], list[tuple[str, str, bytes]]]:
    findings = []
    records = []
    indexed = index_entries(root)
    candidates = {name for _, _, _, name in indexed}
    sparse_paths = {
        item[2:].decode("utf-8") for item in git(root, "ls-files", "-t", "-z").split(b"\0")
        if item.startswith(b"S ")
    }
    if sparse_paths:
        raise CheckError("sparse checkout is not supported for complete privacy validation")
    # Only repository ignore files define candidates; global ignores must not hide them.
    candidates.update(raw.decode("utf-8") for raw in git(
        root, "ls-files", "--others", "--exclude-per-directory=.gitignore", "-z"
    ).split(b"\0") if raw)
    for name in sorted(candidates):
        rule = path_rule(name)
        if rule:
            findings.append(Finding("worktree", name, 0, rule))
            continue
        path = root / name
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root):
            findings.append(Finding("worktree", name, 0, "symlink-not-publishable"))
        elif path.is_file():
            if path.stat().st_size > MAX_FILE_BYTES:
                findings.append(Finding("worktree", name, 0, "file-too-large-for-review"))
            else:
                records.append(("worktree", name, path.read_bytes()))
    for mode, oid, stage, name in indexed:
        rule = path_rule(name)
        if rule or mode not in {"100644", "100755"} or stage != "0":
            findings.append(Finding("index", name, 0, rule or "non-regular-or-unmerged-index-entry"))
        else:
            records.append(("index", name, read_blob(root, oid)))
    return findings, records


def history_records(root: Path) -> tuple[list[Finding], list[tuple[str, str, bytes]], int]:
    findings = []
    records = []
    seen = set()
    commits = git(root, "rev-list", "--all").decode().splitlines()
    for commit in commits:
        for raw in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
            if not raw:
                continue
            meta, name = raw.decode("utf-8").split("\t", 1)
            mode, kind, oid = meta.split()
            if (name, oid) in seen:
                continue
            seen.add((name, oid))
            scope = "history:" + commit[:12]
            rule = path_rule(name)
            if rule or kind != "blob" or mode not in {"100644", "100755"}:
                findings.append(Finding(scope, name, 0, rule or "non-regular-history-entry"))
            else:
                records.append((scope, name, read_blob(root, oid)))
    return findings, records, len(commits)


def approved_package(root: Path, plugin: str, ref: str) -> dict[str, tuple[str, bytes]]:
    if not re.fullmatch(r"feishu-[a-z0-9]+(?:-[a-z0-9]+)*", plugin):
        raise CheckError("invalid plugin name")
    commit = git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    approved = {}
    prefix = f"plugins/{plugin}/"
    for raw in git(root, "ls-tree", "-r", "-z", commit, "--", f"plugins/{plugin}", "LICENSE").split(b"\0"):
        if not raw:
            continue
        meta, name = raw.decode("utf-8").split("\t", 1)
        mode, kind, oid = meta.split()
        if kind != "blob" or mode not in {"100644", "100755"} or path_rule(name):
            raise CheckError("approved revision contains a non-publishable package entry")
        rel = name.removeprefix(prefix) if name.startswith(prefix) else name
        member = f"{plugin}/{rel}"
        data = read_blob(root, oid)
        if member in approved and approved[member][1] != data:
            raise CheckError("plugin license differs from root license; resolve packaging explicitly")
        approved[member] = (name, data)
    for required in (f"{plugin}/.codex-plugin/plugin.json", f"{plugin}/LICENSE"):
        if required not in approved:
            raise CheckError("approved revision lacks plugin manifest or license")
    return approved


def archive_records(root: Path, archive: Path, plugin: str, ref: str) -> tuple[list[Finding], list[tuple[str, str, bytes]]]:
    approved = approved_package(root, plugin, ref)
    findings = []
    records = []
    seen = set()
    members = set()
    with zipfile.ZipFile(archive) as bundle:
        if bundle.comment:
            findings.append(Finding("archive", "<archive-metadata>", 0, "archive-comment-not-allowed"))
        entries = bundle.infolist()
        if len(entries) > MAX_ARCHIVE_ENTRIES or sum(x.file_size for x in entries) > MAX_ARCHIVE_BYTES:
            raise CheckError("ZIP exceeds bounded archive review limits")
        for entry in entries:
            name = entry.filename.rstrip("/") if entry.is_dir() else entry.filename
            rule = path_rule(name)
            if name.casefold() in seen:
                rule = "duplicate-archive-entry"
            seen.add(name.casefold())
            if stat.S_ISLNK(entry.external_attr >> 16):
                rule = "archive-symlink"
            if entry.flag_bits & 1:
                rule = "encrypted-archive-entry"
            if entry.comment or entry.extra:
                findings.append(Finding("archive", name, 0, "archive-extra-metadata-not-allowed"))
            if rule:
                findings.append(Finding("archive", name, 0, rule))
                continue
            if entry.is_dir():
                if not any(key.startswith(name + "/") for key in approved):
                    findings.append(Finding("archive", name, 0, "unapproved-archive-directory"))
                continue
            members.add(name)
            if entry.file_size > MAX_FILE_BYTES:
                findings.append(Finding("archive", name, 0, "file-too-large-for-review"))
                continue
            try:
                with bundle.open(entry) as stream:
                    data = stream.read(MAX_FILE_BYTES + 1)
            except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
                raise CheckError("ZIP entry could not be inspected; privacy validation is incomplete") from None
            if len(data) > MAX_FILE_BYTES:
                findings.append(Finding("archive", name, 0, "file-too-large-for-review"))
                continue
            source = approved.get(name)
            if source is None:
                findings.append(Finding("archive", name, 0, "file-outside-approved-package"))
            elif source[1] != data:
                findings.append(Finding("archive", name, 0, "content-differs-from-approved-revision"))
            records.append(("archive", source[0] if source else name, data))
    for missing in sorted(approved.keys() - members):
        findings.append(Finding("archive", missing, 0, "missing-approved-package-file"))
    return findings, records


def check_local_ignore(root: Path) -> list[Finding]:
    path = root / ".gitignore"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    if "/local/" not in {line.strip() for line in lines}:
        return [Finding("policy", ".gitignore", 0, "missing-repository-local-ignore")]
    probe = "local/.privacy-ignore-probe"
    visible = git(root, "ls-files", "--others", "--exclude-per-directory=.gitignore", "-z", "--", "local")
    if visible:
        return [Finding("policy", ".gitignore", 0, "local-ignore-overridden")]
    result = subprocess.run(
        ["git", "-C", str(root), "-c", "core.excludesFile=/dev/null", "check-ignore", "--no-index", "--stdin"],
        input=(probe + "\n").encode(), capture_output=True,
    )
    if result.returncode != 0:
        return [Finding("policy", ".gitignore", 0, "local-ignore-overridden")]
    return []


def gitleaks_scan(root: Path, records: list[tuple[str, str, bytes]], history: bool) -> list[Finding]:
    executable = shutil.which("gitleaks")
    if executable is None:
        raise CheckError("gitleaks is unavailable; use --static-only only for explicitly degraded non-release checks")
    findings = []
    env = {key: value for key, value in os.environ.items() if not key.startswith("GITLEAKS_")}
    with tempfile.TemporaryDirectory(prefix="feishu-privacy-") as directory:
        work = Path(directory)
        sources = work / "sources"
        sources.mkdir()
        mapping = {}
        for number, (scope, name, data) in enumerate(records):
            filename = f"entry-{number:06d}.txt"
            (sources / filename).write_bytes(data)
            mapping[filename] = (scope, name)
        config = work / "rules.toml"
        config.write_text("[extend]\nuseDefault = true\n", encoding="utf-8")
        scans = [("content", ["dir", str(sources)])]
        if history:
            scans.append(("git", ["git", str(root), "--log-opts=--all"]))
        for label, args in scans:
            report = work / f"{label}.json"
            command = [executable, *args, "--config", str(config), "--redact=100", "--no-banner", "--no-color",
                       "--ignore-gitleaks-allow", "--gitleaks-ignore-path", str(work / "no-ignore"),
                       "--max-decode-depth", "5", "--report-format", "json", "--report-path", str(report)]
            try:
                result = subprocess.run(command, env=env, cwd=work, capture_output=True, timeout=120)
            except subprocess.TimeoutExpired:
                raise CheckError("gitleaks timed out; privacy validation is incomplete") from None
            if result.returncode not in (0, 1) or not report.is_file():
                raise CheckError("gitleaks did not complete; raw output was withheld")
            try:
                leaks = json.loads(report.read_text(encoding="utf-8"))
                if not isinstance(leaks, list) or result.returncode == 1 and not leaks:
                    raise ValueError
                for leak in leaks:
                    if label == "content":
                        scope, name = mapping[Path(leak["File"]).name]
                    else:
                        scope = "history:" + str(leak.get("Commit", ""))[:12]
                        name = leak["File"]
                    findings.append(Finding(scope, name, int(leak["StartLine"]), "gitleaks:" + leak["RuleID"]))
            except (OSError, ValueError, KeyError, TypeError):
                raise CheckError("gitleaks report is invalid; privacy validation is incomplete") from None
    return findings


def check(root: Path, *, history: bool = False, static_only: bool = False,
          archive: Path | None = None, plugin: str | None = None, ref: str = "HEAD") -> tuple[list[Finding], dict]:
    root = root.resolve()
    allowed = load_allowlist(root / "scripts/privacy_allowlist.json")
    findings = check_local_ignore(root)
    current_findings, records = worktree_and_index(root)
    findings.extend(current_findings)
    counts = {"worktree_files": sum(s == "worktree" for s, _, _ in records),
              "index_files": sum(s == "index" for s, _, _ in records), "commits": 0, "archive_files": 0}
    if history:
        historical_findings, old_records, commits = history_records(root)
        findings.extend(historical_findings)
        records.extend(old_records)
        counts["commits"] = commits
    if archive is not None:
        if not plugin:
            raise CheckError("--archive requires --plugin")
        archive_findings, package_records = archive_records(root, archive, plugin, ref)
        findings.extend(archive_findings)
        records.extend(package_records)
        counts["archive_files"] = len(package_records)
    for scope, name, data in records:
        findings.extend(scan_bytes(scope, name, data, allowed))
    if not static_only:
        findings.extend(gitleaks_scan(root, records, history))
    counts["gitleaks"] = not static_only
    return sorted(set(findings), key=lambda f: (f.scope, f.path, f.line, f.rule)), counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="store_true", help="also inspect all locally reachable commits; never fetch")
    parser.add_argument("--static-only", action="store_true", help="explicit non-release check without gitleaks")
    parser.add_argument("--archive", type=Path, help="inspect a release ZIP without extracting into the repository")
    parser.add_argument("--plugin", help="expected plugin name for --archive")
    parser.add_argument("--ref", default="HEAD", help="reviewed local commit/tag used to verify release ZIP bytes")
    args = parser.parse_args()
    if bool(args.archive) != bool(args.plugin) or args.ref != "HEAD" and not args.archive:
        parser.error("use --archive and --plugin together; --ref applies to archive checks")
    try:
        findings, counts = check(ROOT, history=args.history, static_only=args.static_only,
                                 archive=args.archive, plugin=args.plugin, ref=args.ref)
    except (CheckError, OSError, UnicodeError, zipfile.BadZipFile, RuntimeError) as exc:
        message = str(exc) if isinstance(exc, CheckError) else "local inspection failed; details withheld to avoid exposing private values"
        parser.exit(2, f"FAIL: {message}\n")
    if args.static_only:
        print("WARN: gitleaks explicitly skipped; static-only checks do not satisfy release validation")
    for finding in findings:
        print(json.dumps(asdict(finding), ensure_ascii=True))
    print(json.dumps({"privacy": "FAIL" if findings else "PASS", **counts, "findings": len(findings)}))
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
