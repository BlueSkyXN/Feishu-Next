#!/usr/bin/env python3
"""Reuse this machine's TraeWork Feishu authorization with official lark-cli.

User-owned local helper: reads the Trae client session already stored for the
current OS user, asks Trae cloud for the short-lived Feishu user token the user
already authorized for TraeWork, and injects it via LARKSUITE_CLI_* env vars.

- Cross-platform session paths (macOS / Windows / Linux)
- Default: local session storage; optional file fallback
- Resolve system and agent-environment lark-cli copies; prefer the newest version
- Read-only: never writes Trae storage; never prints JWT/UAT

Usage (from skill scripts dir or with full path):
  python3 traework_local_auth.py about
  python3 traework_local_auth.py status
  python3 traework_local_auth.py whoami
  python3 traework_local_auth.py run -- whoami --json
  python3 traework_local_auth.py run -- drive +search --as user --page-size 3
  eval "$(python3 traework_local_auth.py export-env)"  # prints token; last resort only
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# --- byteCrypto (cockpit-tools / Trae) ---------------------------------------

HEADER_AES = bytes([0x74, 0x63, 0x05, 0x10, 0x00, 0x00])
HEADER_AES_PRIVATE = bytes([18, 57, 32, 32, 2, 3])

# BYTE_CRYPTO_AES_A / BYTE_CRYPTO_AES_B (same as issue #894 iJ / rJ)
AES_A = bytes(
    [
        82, 9, 106, 213, 48, 54, 165, 56, 191, 64, 163, 158, 129, 243, 215, 251,
        124, 227, 57, 130, 155, 47, 255, 135, 52, 142, 67, 68, 196, 222, 233, 203,
        84, 123, 148, 50, 166, 194, 35, 61, 238, 76, 149, 11, 66, 250, 195, 78,
        8, 46, 161, 102, 40, 217, 36, 178, 118, 91, 162, 73, 109, 139, 209, 37,
    ]
)
AES_B = bytes(
    [
        31, 221, 168, 51, 136, 7, 199, 49, 177, 18, 16, 89, 39, 128, 236, 95,
        96, 81, 127, 169, 25, 181, 74, 13, 45, 229, 122, 159, 147, 201, 156, 239,
        160, 224, 59, 77, 174, 42, 245, 176, 200, 235, 187, 60, 131, 83, 153, 97,
        23, 43, 4, 126, 186, 119, 214, 38, 225, 105, 20, 99, 85, 33, 12, 125,
    ]
)
AES_PRIVATE_A = bytes(
    [
        191, 192, 216, 250, 122, 246, 220, 97, 31, 254, 98, 27, 8, 72, 71, 176,
        135, 99, 96, 18, 127, 101, 203, 104, 211, 102, 191, 125, 37, 72, 150, 156,
        51, 229, 121, 35, 17, 153, 141, 177, 110, 131, 150, 128, 172, 255, 254, 6,
        18, 140, 55, 62, 236, 249, 135, 64, 135, 12, 117, 4, 89, 149, 168, 209,
    ]
)
AES_PRIVATE_B = bytes(
    [
        246, 204, 26, 232, 232, 70, 129, 109, 223, 146, 169, 242, 23, 241, 105, 145,
        50, 196, 165, 42, 254, 120, 3, 54, 244, 207, 209, 85, 53, 6, 138, 106,
        175, 148, 31, 204, 186, 186, 165, 182, 87, 142, 49, 10, 39, 110, 26, 154,
        86, 56, 173, 125, 18, 64, 198, 225, 99, 99, 83, 82, 191, 134, 76, 170,
    ]
)

AUTH_KEY_PREFIX = "iCubeAuthInfo://"
DEFAULT_AUTH_KEY = "iCubeAuthInfo://icube.cloudide"
TRAEWORK_APP_ID_CN = "cli_a965abcba6fadbd3"
TRAEWORK_APP_ID_INTL = "cli_a96598a589b89dba"
GET_THIRD_PARTY_PATHS = (
    "/trae/api/v3/GetThirdPartyToken",
    "/api/v3/trae/GetThirdPartyToken",
    "/cloudide/api/v3/trae/GetThirdPartyToken",
)


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def _salt(header: bytes) -> bytes:
    if header == HEADER_AES_PRIVATE:
        left, right = AES_PRIVATE_A, AES_PRIVATE_B
    else:
        left, right = AES_A, AES_B
    return bytes(a ^ b for a, b in zip(left, right))


def _derive_key_iv(enc_key: bytes, header: bytes) -> tuple[bytes, bytes]:
    if len(enc_key) != 32:
        raise ValueError("enc_key must be 32 bytes")
    h1 = _sha512(enc_key)
    h2 = _sha512(h1 + _salt(header))
    return h2[:16], h2[16:32]


def _aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    try:
        from Crypto.Cipher import AES  # type: ignore
        from Crypto.Util.Padding import unpad  # type: ignore

        plain = AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext)
        return unpad(plain, 16)
    except ImportError:
        pass
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7
    from cryptography.hazmat.backends import default_backend

    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def byte_crypto_decrypt(raw: bytes) -> bytes:
    if len(raw) <= 38:
        raise ValueError("cipher too short")
    header = raw[:6]
    if header not in (HEADER_AES, HEADER_AES_PRIVATE):
        raise ValueError(f"unknown header: {header.hex()}")
    enc_key = raw[6:38]
    ciphertext = raw[38:]
    if not ciphertext or len(ciphertext) % 16 != 0:
        raise ValueError("invalid ciphertext length")
    aes_key, iv = _derive_key_iv(enc_key, header)
    decrypted = _aes_cbc_decrypt(aes_key, iv, ciphertext)
    if len(decrypted) < 64:
        raise ValueError("plaintext too short")
    stored_hash, plain = decrypted[:64], decrypted[64:]
    if _sha512(plain) != stored_hash:
        raise ValueError("sha512 mac mismatch")
    return plain


def decrypt_icube_b64(encrypted_b64: str) -> dict[str, Any]:
    raw = base64.b64decode(encrypted_b64.strip())
    plain = byte_crypto_decrypt(raw)
    text = plain.decode("utf-8")
    return json.loads(text)


# --- storage / JWT -----------------------------------------------------------


# Product data folder names (aligned with cockpit-tools TraePlatformKind.display_name)
TRAE_APP_SUPPORT_NAMES = (
    "TRAE SOLO CN",
    "TRAE SOLO",
    "Trae CN",
    "Trae",
    "TRAE",
)
LARK_CLI_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
LARK_CLI_SOURCE_TIEBREAK = {
    "override": -1,
    "path": 0,
    "agent": 1,
    "user": 2,
    "system": 3,
}


def parse_lark_cli_version(raw: str) -> tuple[int, int, int] | None:
    match = LARK_CLI_VERSION_RE.search(raw or "")
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _lark_cli_names() -> tuple[str, ...]:
    if sys.platform == "win32":
        return ("lark-cli.exe", "lark-cli.cmd", "lark-cli.bat", "lark-cli")
    return ("lark-cli",)


def _realpath(path: Path) -> Path:
    try:
        return path.expanduser().resolve()
    except OSError:
        return path.expanduser()


def classify_lark_cli_source(path: Path) -> str:
    text = str(path).replace("\\", "/").lower()
    agent_marks = (
        "fnm_multishells",
        "/.fnm/",
        "/fnm/",
        "/.nvm/",
        "nvm/versions",
        "/.local/state/",
        "appdata/local/fnm",
        "appdata/roaming/fnm",
    )
    if any(mark in text for mark in agent_marks):
        return "agent"
    system_marks = (
        "/usr/local/bin",
        "/opt/homebrew/bin",
        "/opt/local/bin",
        "/usr/bin",
        "program files",
        "program files (x86)",
    )
    if any(mark in text for mark in system_marks):
        return "system"
    if "/.local/bin/" in text or text.endswith("/.local/bin/lark-cli"):
        return "user"
    if "/node_modules/@larksuite/cli" in text:
        return "user"
    return "path"


def _iter_path_lark_cli() -> list[Path]:
    found: list[Path] = []
    names = _lark_cli_names()
    for directory in os.get_exec_path():
        if not directory:
            continue
        root = Path(directory)
        for name in names:
            candidate = root / name
            if candidate.is_file():
                found.append(candidate)
    return found


def _npm_global_bin() -> Path | None:
    npm = shutil.which("npm")
    if not npm:
        return None
    try:
        proc = subprocess.run(
            [npm, "prefix", "-g"],
            capture_output=True,
            text=True,
            timeout=4,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    prefix = (proc.stdout or "").strip()
    if proc.returncode != 0 or not prefix:
        return None
    root = Path(prefix)
    return root if sys.platform == "win32" else root / "bin"


def _well_known_lark_cli_dirs() -> list[Path]:
    home = Path.home()
    dirs: list[Path] = []
    if sys.platform == "win32":
        for key in ("APPDATA", "LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
            raw = os.environ.get(key)
            if not raw:
                continue
            base = Path(raw)
            dirs.extend((base / "npm", base / "nodejs"))
    else:
        dirs.extend(
            (
                Path("/usr/local/bin"),
                Path("/opt/homebrew/bin"),
                Path("/opt/local/bin"),
                Path("/usr/bin"),
                home / ".local" / "bin",
                home / "bin",
            )
        )

    for key in ("FNM_MULTISHELL_PATH", "NVM_BIN"):
        raw = os.environ.get(key)
        if raw:
            dirs.append(Path(raw))

    fnm_dir = os.environ.get("FNM_DIR")
    if fnm_dir:
        alias = Path(fnm_dir) / "aliases" / "default"
        dirs.extend((alias, alias / "bin"))
    nvm_dir = os.environ.get("NVM_DIR")
    if nvm_dir:
        dirs.append(Path(nvm_dir) / "current" / "bin")

    npm_bin = _npm_global_bin()
    if npm_bin is not None:
        dirs.append(npm_bin)
    dirs.append(home / ".npm-global" / "bin")
    return dirs


def _probe_lark_cli(path: Path, source: str) -> dict[str, Any]:
    version_raw = ""
    version = None
    runnable = False
    error = ""
    try:
        proc = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        blob = (proc.stdout or proc.stderr or "").strip()
        version_raw = blob.splitlines()[0] if blob else ""
        version = parse_lark_cli_version(version_raw)
        runnable = proc.returncode == 0 and version is not None
        if not runnable:
            error = f"exit_{proc.returncode}"
    except Exception as exc:  # noqa: BLE001
        error = type(exc).__name__
    return {
        "path": str(path),
        "resolved": str(_realpath(path)),
        "source": source,
        "version": ".".join(str(part) for part in version) if version else None,
        "version_tuple": version,
        "runnable": runnable,
        "version_raw": version_raw[:80],
        "error": error,
    }


def select_lark_cli_candidate(
    candidates: list[dict[str, Any]],
    *,
    override: bool,
) -> dict[str, Any] | None:
    if override:
        for item in candidates:
            if item.get("source") == "override":
                return item
        return candidates[0] if candidates else None
    runnable = [item for item in candidates if item.get("runnable") and item.get("version_tuple")]
    if not runnable:
        return candidates[0] if candidates else None
    runnable.sort(
        key=lambda item: (
            tuple(-part for part in item["version_tuple"]),
            LARK_CLI_SOURCE_TIEBREAK.get(str(item.get("source")), 9),
        )
    )
    return runnable[0]


def resolve_lark_cli() -> dict[str, Any]:
    override = (os.environ.get("TRAEWORK_LARK_CLI") or os.environ.get("LARK_CLI") or "").strip()
    queued: list[tuple[str, Path]] = []
    if override:
        queued.append(("override", Path(override).expanduser()))
    for path in _iter_path_lark_cli():
        queued.append(("path", path))
    names = _lark_cli_names()
    for directory in _well_known_lark_cli_dirs():
        for name in names:
            path = directory / name
            if path.is_file():
                queued.append((classify_lark_cli_source(path), path))

    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for source, path in queued:
        if source == "override" and not path.is_file():
            candidates.append(
                {
                    "path": str(path),
                    "resolved": str(path),
                    "source": "override",
                    "version": None,
                    "version_tuple": None,
                    "runnable": False,
                    "version_raw": "",
                    "error": "not_found",
                }
            )
            continue
        if not path.is_file():
            continue
        key = str(_realpath(path))
        if sys.platform == "win32":
            key = key.lower()
        if key in seen:
            continue
        seen.add(key)
        classified = "override" if source == "override" else classify_lark_cli_source(path)
        if source == "path" and classified == "path":
            classified = "path"
        elif source == "path":
            classified = classify_lark_cli_source(path)
        candidates.append(_probe_lark_cli(path, classified if source != "override" else "override"))

    selected = select_lark_cli_candidate(candidates, override=bool(override))

    def public(item: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in item.items() if key != "version_tuple"}

    return {
        "selected": selected["path"] if selected else None,
        "version": selected.get("version") if selected else None,
        "source": selected.get("source") if selected else None,
        "runnable": bool(selected and selected.get("runnable")),
        "policy": "override" if override else "newest_version",
        "candidates": [public(item) for item in candidates],
    }


def trae_user_data_roots() -> list[Path]:
    """OS-specific roots that contain <AppName>/User/globalStorage/storage.json."""
    home = Path.home()
    roots: list[Path] = []
    system = sys.platform
    if system == "darwin":
        roots.append(home / "Library" / "Application Support")
    elif system == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            roots.append(Path(appdata))
        # Fallback if APPDATA missing
        roots.append(home / "AppData" / "Roaming")
    else:
        # Linux and other Unix: Electron/VS Code style config dir
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            roots.append(Path(xdg))
        roots.append(home / ".config")
    # de-dupe while preserving order
    seen: set[str] = set()
    out: list[Path] = []
    for r in roots:
        key = str(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def default_storage_paths() -> list[Path]:
    """Candidate storage.json paths for all known Trae product folders."""
    out: list[Path] = []
    env = os.environ.get("TRAE_STORAGE_JSON")
    if env:
        out.append(Path(env).expanduser())
    for root in trae_user_data_roots():
        for name in TRAE_APP_SUPPORT_NAMES:
            out.append(root / name / "User" / "globalStorage" / "storage.json")
    return out


def jwt_file_candidates() -> list[Path]:
    """Optional client-written JWT file paths (often absent)."""
    home = Path.home()
    names = [".trae-cn", ".trae", ".trae-cn-dev"]
    out: list[Path] = []
    env = os.environ.get("TRAE_JWT_TOKEN_PATH")
    if env:
        out.append(Path(env).expanduser())
    for name in names:
        out.append(home / name / "trae-jwt-token")
    return out


def _pick_path(obj: Any, paths: list[list[str]]) -> str | None:
    if not isinstance(obj, dict):
        return None
    for path in paths:
        cur: Any = obj
        ok = True
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                ok = False
                break
            cur = cur[key]
        if ok and isinstance(cur, str) and cur.strip():
            return cur.strip()
    return None


TOKEN_PATHS = [
    ["accessToken"],
    ["access_token"],
    ["token"],
    ["data", "accessToken"],
    ["data", "access_token"],
    ["data", "token"],
    ["auth", "accessToken"],
    ["auth", "token"],
]


def resolve_auth_blob(storage: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    # prefer exact default key, else first iCubeAuthInfo:// that is not usertag/device
    keys: list[str] = []
    if DEFAULT_AUTH_KEY in storage:
        keys.append(DEFAULT_AUTH_KEY)
    for k in storage:
        if not k.startswith(AUTH_KEY_PREFIX):
            continue
        if k == DEFAULT_AUTH_KEY:
            continue
        if k.endswith("usertag") or "icube-dc:" in k:
            continue
        keys.append(k)
    if not keys:
        raise FileNotFoundError("no iCubeAuthInfo://* key in storage.json")
    for key in keys:
        val = storage[key]
        if isinstance(val, dict):
            return key, val
        if not isinstance(val, str) or not val.strip():
            continue
        text = val.strip()
        # plain JSON string?
        if text.startswith("{"):
            return key, json.loads(text)
        # cipher b64
        try:
            return key, decrypt_icube_b64(text)
        except Exception as exc:  # noqa: BLE001
            last = exc
            continue
    raise RuntimeError(f"failed to decrypt auth blob: {last}")  # type: ignore[name-defined]


def load_trae_jwt() -> tuple[str, dict[str, Any]]:
    """Return (jwt, meta) without printing jwt.

    Priority (2026-08-14):
      1. Scheme B — decrypt storage.json (default; always available when logged in)
      2. Scheme A — trae-jwt-token file (fallback; remote AB, usually off)
    Override: TRAEWORK_JWT_SOURCE=file|storage|auto (default auto = B then A)
    """
    prefer = (os.environ.get("TRAEWORK_JWT_SOURCE") or "auto").strip().lower()
    errors: list[str] = []

    def try_scheme_b() -> tuple[str, dict[str, Any]] | None:
        last_err: Exception | None = None
        for path in default_storage_paths():
            if not path.is_file():
                continue
            try:
                storage = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(storage, dict):
                    continue
                key, auth = resolve_auth_blob(storage)
                jwt = _pick_path(auth, TOKEN_PATHS)
                if not jwt:
                    raise RuntimeError(f"{key}: no token field")
                meta = {
                    "source": "storage_bytecrypto",
                    "scheme": "B",
                    "path": str(path),
                    "auth_key": key,
                    "user_id": _pick_path(auth, [["userId"], ["user_id"], ["account", "userId"]])
                    or "",
                    "email": _pick_path(
                        auth,
                        [
                            ["email"],
                            ["account", "email"],
                            ["account", "nonPlainTextEmail"],
                            ["user", "email"],
                        ],
                    )
                    or "",
                    "scope": _pick_path(auth, [["account", "scope"], ["scope"]]) or "",
                    "expired_at": _pick_path(auth, [["expiredAt"], ["expired_at"]]) or "",
                    "has_refresh": bool(
                        _pick_path(auth, [["refreshToken"], ["refresh_token"], ["RefreshToken"]])
                    ),
                    "token_len": len(jwt),
                    "token_prefix": jwt[:8] + "…",
                }
                return jwt, meta
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                continue
        if last_err is not None:
            errors.append(f"scheme_B: {last_err}")
        else:
            errors.append("scheme_B: no storage.json found")
        return None

    def try_scheme_a() -> tuple[str, dict[str, Any]] | None:
        for path in jwt_file_candidates():
            if path.is_file() and path.stat().st_size > 0:
                token = path.read_text(encoding="utf-8").strip()
                if token:
                    return token, {
                        "source": "jwt_file",
                        "scheme": "A",
                        "path": str(path),
                        "mode": oct(path.stat().st_mode & 0o777),
                        "token_len": len(token),
                        "token_prefix": token[:8] + "…",
                    }
        errors.append("scheme_A: no trae-jwt-token file")
        return None

    order: list[str]
    if prefer in ("storage", "b", "scheme_b", "bytecrypto"):
        order = ["B"]
    elif prefer in ("file", "a", "scheme_a", "jwt_file"):
        order = ["A"]
    else:
        # default / auto: B first, A fallback
        order = ["B", "A"]

    for scheme in order:
        hit = try_scheme_b() if scheme == "B" else try_scheme_a()
        if hit is not None:
            return hit
    raise RuntimeError("unable to load Trae JWT: " + "; ".join(errors))


# --- cloud -------------------------------------------------------------------


def detect_host(meta: dict[str, Any], jwt: str) -> str:
    """Pick Trae API host from env, path, or jwt-file location."""
    _ = jwt  # reserved for future claims inspection
    env = os.environ.get("TRAE_API_HOST")
    if env:
        return env.rstrip("/")
    path = str(meta.get("path", ""))
    # CN product folders or CN data dir
    if "CN" in path or ".trae-cn" in path:
        return "https://api.trae.cn"
    # International defaults
    if meta.get("source") == "jwt_file" and ".trae" in path and ".trae-cn" not in path:
        return "https://api.trae.ai"
    # Prefer CN when ambiguous (common for this plugin's primary users)
    return "https://api.trae.cn"


def get_third_party_token(jwt: str, host: str) -> dict[str, Any]:
    body = json.dumps({"Types": ["feishu", "lark"]}).encode("utf-8")
    last_err: Exception | None = None
    for path in GET_THIRD_PARTY_PATHS:
        url = host.rstrip("/") + path
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-cloudide-token": jwt,
                "Authorization": f"Bearer {jwt}",
                "User-Agent": "Feishu-Next-local-traework-bridge/0.1",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
                return {"url": url, "http_status": resp.status, "data": data}
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")[:500]
            last_err = RuntimeError(f"{url} HTTP {exc.code}: {err_body}")
            # try next path only on 404
            if exc.code != 404:
                raise last_err from exc
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    raise RuntimeError(f"GetThirdPartyToken failed: {last_err}")


def pick_feishu_uat(api_result: dict[str, Any]) -> dict[str, Any]:
    data = api_result.get("data") or {}
    # common envelopes
    results = (
        data.get("Result")
        or data.get("result")
        or data.get("data")
        or data.get("Tokens")
        or data.get("tokens")
    )
    if isinstance(data, list):
        results = data
    if results is None and isinstance(data.get("AccessToken"), str):
        results = [data]
    if not isinstance(results, list) or not results:
        # keep structure summary only
        keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
        raise RuntimeError(f"empty Result; top-level keys={keys}")

    preferred = None
    for item in results:
        if not isinstance(item, dict):
            continue
        typ = (item.get("Type") or item.get("type") or "").lower()
        token = item.get("AccessToken") or item.get("accessToken") or item.get("access_token")
        if not token:
            continue
        row = {
            "type": typ or "unknown",
            "access_token": token,
            "expire_at": item.get("AccessExpireAt")
            or item.get("accessExpireAt")
            or item.get("expire_at")
            or "",
            "open_id": item.get("ExternalUserID")
            or item.get("openId")
            or item.get("open_id")
            or "",
            "scope": item.get("Scope") or item.get("scope") or "",
            "org": item.get("OrganizationInfo") or item.get("organizationInfo") or {},
        }
        if typ in ("feishu", "lark") and preferred is None:
            preferred = row
        if typ == "feishu":
            preferred = row
            break
    if not preferred:
        raise RuntimeError(f"no feishu/lark token in Result (n={len(results)})")
    return preferred


def app_id_for_host(host: str) -> str:
    if "trae.ai" in host or "traeapi.us" in host:
        return TRAEWORK_APP_ID_INTL
    return TRAEWORK_APP_ID_CN


def brand_for_app(app_id: str) -> str:
    return "lark" if app_id == TRAEWORK_APP_ID_INTL else "feishu"


# --- commands ----------------------------------------------------------------

ABOUT_FALLBACK = (
    "Feishu TraeWork Local Auth: reuse your own TraeWork Feishu authorization "
    "on this machine with official lark-cli. See references/about.md."
)


def about_path() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "about.md"


def about_text() -> str:
    path = about_path()
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ABOUT_FALLBACK + "\n"


def cmd_about(_: argparse.Namespace) -> int:
    text = about_text()
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    lark = resolve_lark_cli()
    report: dict[str, Any] = {
        "jwt_files": [],
        "storage_files": [],
        "lark_cli": lark.get("selected"),
        "lark_cli_resolution": lark,
    }
    for p in jwt_file_candidates():
        report["jwt_files"].append(
            {
                "path": str(p),
                "exists": p.is_file(),
                "size": p.stat().st_size if p.is_file() else 0,
            }
        )
    for p in default_storage_paths():
        entry: dict[str, Any] = {"path": str(p), "exists": p.is_file()}
        if p.is_file():
            try:
                storage = json.loads(p.read_text(encoding="utf-8"))
                keys = [k for k in storage if k.startswith(AUTH_KEY_PREFIX)]
                entry["auth_keys"] = keys
                if DEFAULT_AUTH_KEY in storage and isinstance(storage[DEFAULT_AUTH_KEY], str):
                    raw = base64.b64decode(storage[DEFAULT_AUTH_KEY].strip())
                    entry["header_hex"] = raw[:6].hex()
                    entry["cipher_len"] = len(raw)
            except Exception as exc:  # noqa: BLE001
                entry["error"] = type(exc).__name__
        report["storage_files"].append(entry)

    # try load jwt meta only
    try:
        jwt, meta = load_trae_jwt()
        report["jwt_load"] = {"ok": True, **meta}
        # never include jwt
        _ = jwt
    except Exception as exc:  # noqa: BLE001
        report["jwt_load"] = {"ok": False, "error": str(exc)}

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("jwt_load", {}).get("ok") else 2


def cmd_decrypt_check(_: argparse.Namespace) -> int:
    jwt, meta = load_trae_jwt()
    out = {
        "ok": True,
        **meta,
        "jwt_sha256_8": hashlib.sha256(jwt.encode()).hexdigest()[:8],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def _fetch_bundle() -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    jwt, meta = load_trae_jwt()
    host = detect_host(meta, jwt)
    api = get_third_party_token(jwt, host)
    uat = pick_feishu_uat(api)
    app_id = app_id_for_host(host)
    bundle = {
        "host": host,
        "api_url": api["url"],
        "http_status": api["http_status"],
        "app_id": app_id,
        "brand": brand_for_app(app_id),
        "uat_type": uat["type"],
        "uat_len": len(uat["access_token"]),
        "uat_sha256_8": hashlib.sha256(uat["access_token"].encode()).hexdigest()[:8],
        "expire_at": uat["expire_at"],
        "open_id": uat["open_id"],
        "scope_len": len(str(uat.get("scope") or "")),
        "org_name": "",
    }
    org = uat.get("org") or {}
    if isinstance(org, dict):
        bundle["org_name"] = (
            org.get("Name") or org.get("name") or org.get("TenantName") or org.get("tenant_name") or ""
        )
    return jwt, meta, uat, bundle


def cmd_fetch_uat(_: argparse.Namespace) -> int:
    _, meta, _, bundle = _fetch_bundle()
    print(
        json.dumps(
            {
                "ok": True,
                "jwt_meta": {
                    k: meta[k]
                    for k in meta
                    if k not in ("token_prefix",)  # still ok, no secret
                },
                "third_party": bundle,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _lark_env(bundle: dict[str, Any], uat: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    env["LARKSUITE_CLI_APP_ID"] = bundle["app_id"]
    env["LARKSUITE_CLI_USER_ACCESS_TOKEN"] = uat["access_token"]
    env["LARKSUITE_CLI_BRAND"] = bundle["brand"]
    env.setdefault("LARKSUITE_CLI_NO_UPDATE_NOTIFIER", "1")
    env.setdefault("LARKSUITE_CLI_NO_SKILLS_NOTIFIER", "1")
    for key in ("LARK_APP_ID", "LARK_APP_SECRET", "LARKSUITE_CLI_APP_SECRET"):
        env.pop(key, None)
    return env


def normalize_lark_run_args(lark_args: list[str]) -> list[str]:
    args = list(lark_args or [])
    if args and args[0] == "--":
        args = args[1:]
    if args and Path(args[0]).name.lower() in {"lark-cli", "lark-cli.exe", "lark-cli.cmd", "lark-cli.bat"}:
        args = args[1:]
    return args


def env_mode_forbidden_reason(lark_args: list[str]) -> str | None:
    tokens = [item for item in lark_args if not item.startswith("-")]
    if not tokens:
        return None
    head, sub = tokens[0], tokens[1] if len(tokens) > 1 else ""
    if head == "auth" and sub in {"login", "logout"}:
        return "auth login/logout is not supported under TraeWork env credentials; use whoami or run"
    if head == "profile" and sub in {"add", "use", "remove"}:
        return "profile mutation is not supported under TraeWork env credentials"
    if head == "config" and sub in {"init", "bind", "remove", "strict-mode", "default-as"}:
        return "config mutation is not supported under TraeWork env credentials"
    return None


def cmd_export_env(_: argparse.Namespace) -> int:
    _, _, uat, bundle = _fetch_bundle()
    # shell-safe single-quoted
    def q(s: str) -> str:
        return "'" + s.replace("'", "'\"'\"'") + "'"

    lines = [
        f"export LARKSUITE_CLI_APP_ID={q(bundle['app_id'])}",
        f"export LARKSUITE_CLI_USER_ACCESS_TOKEN={q(uat['access_token'])}",
        f"export LARKSUITE_CLI_BRAND={q(bundle['brand'])}",
        # avoid mixing with local profile secrets
        "unset LARK_APP_ID LARK_APP_SECRET LARKSUITE_CLI_APP_SECRET 2>/dev/null || true",
    ]
    # diagnostics to stderr only
    print(
        json.dumps({"ok": True, "app_id": bundle["app_id"], "brand": bundle["brand"], "uat_len": bundle["uat_len"]}, ensure_ascii=False),
        file=sys.stderr,
    )
    print("\n".join(lines))
    return 0


def cmd_whoami(args: argparse.Namespace) -> int:
    _, meta, uat, bundle = _fetch_bundle()
    env = _lark_env(bundle, uat)

    lark = resolve_lark_cli()
    selected = lark.get("selected")
    if not selected or not lark.get("runnable"):
        print(json.dumps({"ok": False, "error": "lark-cli not found", "lark_cli_resolution": lark}, ensure_ascii=False, indent=2))
        return 3

    cmd = [selected, "whoami", "--json"] if not args.plain else [selected, "whoami"]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    out: dict[str, Any] = {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "lark_cli": selected,
        "lark_cli_version": lark.get("version"),
        "lark_cli_source": lark.get("source"),
        "jwt_source": meta.get("source"),
        "app_id": bundle["app_id"],
        "brand": bundle["brand"],
        "uat_type": bundle["uat_type"],
        "uat_len": bundle["uat_len"],
        "open_id": bundle["open_id"],
        "org_name": bundle["org_name"],
        "expire_at": bundle["expire_at"],
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-2000:],
    }
    # try parse whoami json for safe fields
    try:
        who = json.loads(proc.stdout)
        if isinstance(who, dict):
            safe = {
                k: who.get(k)
                for k in (
                    "appId",
                    "app_id",
                    "identity",
                    "available",
                    "brand",
                    "user",
                    "open_id",
                    "openId",
                    "tenant",
                )
                if k in who
            }
            out["whoami_safe"] = safe
    except Exception:
        pass
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if proc.returncode == 0 else 4


def cmd_run(args: argparse.Namespace) -> int:
    lark_args = normalize_lark_run_args(list(getattr(args, "lark_args", []) or []))
    if not lark_args:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "missing lark-cli arguments",
                    "usage": "python3 traework_local_auth.py run -- <lark-cli args>",
                    "example": "python3 traework_local_auth.py run -- drive +search --as user --page-size 3",
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    forbidden = env_mode_forbidden_reason(lark_args)
    if forbidden:
        print(json.dumps({"ok": False, "error": forbidden}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    lark = resolve_lark_cli()
    selected = lark.get("selected")
    if not selected or not lark.get("runnable"):
        print(json.dumps({"ok": False, "error": "lark-cli not found", "lark_cli_resolution": lark}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 3

    _, _meta, uat, bundle = _fetch_bundle()
    env = _lark_env(bundle, uat)
    proc = subprocess.run([selected, *lark_args], env=env)
    return int(proc.returncode)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Reuse local TraeWork Feishu authorization with lark-cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("about", help="print the built-in self-introduction (no secrets)")
    sub.add_parser("status", help="probe jwt file / storage / decrypt ability (no secrets)")
    sub.add_parser("decrypt-check", help="decrypt storage and report meta only")
    sub.add_parser("fetch-uat", help="GetThirdPartyToken and report meta only")
    sub.add_parser("resolve-lark-cli", help="list system/agent lark-cli copies and pick the newest")
    sub.add_parser("export-env", help="print export lines for LARKSUITE_CLI_* (token on stdout)")
    w = sub.add_parser("whoami", help="fetch UAT, inject env, run lark-cli whoami")
    w.add_argument("--plain", action="store_true", help="run whoami without --json")
    r = sub.add_parser("run", help="fetch UAT and run a lark-cli command without printing the token")
    r.add_argument(
        "lark_args",
        nargs=argparse.REMAINDER,
        help="lark-cli arguments; prefer: run -- drive +search --as user",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "about":
            return cmd_about(args)
        if args.cmd == "status":
            return cmd_status(args)
        if args.cmd == "decrypt-check":
            return cmd_decrypt_check(args)
        if args.cmd == "fetch-uat":
            return cmd_fetch_uat(args)
        if args.cmd == "resolve-lark-cli":
            print(json.dumps(resolve_lark_cli(), ensure_ascii=False, indent=2))
            return 0
        if args.cmd == "export-env":
            return cmd_export_env(args)
        if args.cmd == "whoami":
            return cmd_whoami(args)
        if args.cmd == "run":
            return cmd_run(args)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc), "type": type(exc).__name__}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
