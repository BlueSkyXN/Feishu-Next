---
name: feishu-traework-local-auth
description: "Use when 需要通过当前用户已登录并完成飞书授权的 TraeWork 云端登录态，为同一台电脑上的飞书 CLI 提供可持续复用的认证入口：每次按需换取短时用户访问令牌，并通过官方 lark-cli 环境变量凭据执行 TraeWork 已授权范围内的命令。"
metadata:
  version: "0.2.1"
  updated: "2026-08-17"
---

# Feishu TraeWork 本地授权

在同一台电脑、同一个 OS 用户下，复用当前用户已经授予 TraeWork 的飞书授权。每次调用按需换取短时用户访问令牌，权限范围沿用 TraeWork 已授予的 scopes。这是可选路径，不是 Feishu Next 的默认鉴权。

## 脚本入口

```text
scripts/traework_local_auth.py
```

优先执行脚本，不要反复重读脚本源码。默认不打印完整凭据；只有用户明确要求导出时才使用 `export-env`。

```bash
# macOS / Linux 用 python3；Windows 优先 python，没有再用 py -3
python3 "<skill-dir>/scripts/traework_local_auth.py" about
python3 "<skill-dir>/scripts/traework_local_auth.py" status
python3 "<skill-dir>/scripts/traework_local_auth.py" whoami
python3 "<skill-dir>/scripts/traework_local_auth.py" run -- drive +search --as user --page-size 3
```

| 命令 | 凭据与输出 | 用途 |
| --- | --- | --- |
| `about` | 不输出凭据 | 查看能力、适用范围和运行方式 |
| `status` | 不输出完整凭据；包含本机路径和诊断元数据 | 检查 Python、依赖、会话和 `lark-cli` 就绪状态 |
| `decrypt-check` | 不输出完整凭据；包含会话元数据和短哈希 | 确认本机会话能够读取和解密 |
| `fetch-uat` | 不输出完整凭据；包含身份、组织元数据和短哈希 | 确认云端换票成功 |
| `resolve-lark-cli` | 不输出凭据；包含本机 CLI 路径和版本 | 扫描 system/agent 多份 CLI 并选择最新可运行版本 |
| `whoami` | 不输出完整凭据；包含当前飞书身份信息 | 注入环境变量并执行 `lark-cli whoami` |
| `run` | 不主动输出注入的凭据；透传业务命令结果 | 获取短时 UAT，并执行一次 `lark-cli` 业务命令 |
| `export-env` | **输出短时 UAT** | 仅在用户明确要求时使用；先提示 shell 历史记录风险 |

## 工作流

1. 用户询问“这是什么”、TraeWork、用法或场景时，先运行 `about`。只有命令无法运行时才读取 [about.md](references/about.md)。
2. 确认本机 Trae 已登录、TraeWork 飞书授权已完成，并且有 `lark-cli`、Python 3.10+，以及 `pycryptodome` 或 `cryptography`。检查、`-m pip` 和脚本执行用同一个解释器：macOS/Linux 用 `python3`，Windows 先 `python` 再 `py -3`。Windows 的 `lark-cli` 优先选 `lark-cli.exe`；macOS/Linux 只有无后缀的 `lark-cli`，不要写 `.exe`。细节见 [user-guide.md](references/user-guide.md)。
3. 运行 `status`。没有会话时看 [platforms.md](references/platforms.md)。确认 `lark_cli_resolution` 可运行；缺加密库时，用 `runtime.dependency_install_argv` 补依赖后重试。
4. 运行 `whoami`。成功标准：TraeWork `appId`、`identity=user`、`available=true`。
5. 执行业务 `lark-cli` 时使用 `run -- <args>`。它只为当前子进程注入 `LARKSUITE_CLI_*`。环境契约见 [env-contract.md](references/env-contract.md)。除非用户明确要求，否则不要使用 `export-env`。
6. 不要通过 `auth login`、profile 或 config 变更来“修复”环境凭据。授权失效时在 Trae 中重新授权；不适合本机复用时改用自有飞书应用。
7. 身份就绪后，转交 `$feishu-next:feishu-workflow-router` 或官方 `lark-cli` skills。

## 硬性规则

- 除非用户明确要求执行 `export-env`，否则绝不打印 JWT、UAT、refresh token 或完整会话 JSON。
- 绝不写回 Trae `storage.json`，不切换账号。
- 不导出 OS keychain 或 Credential Manager。
- 不提交或粘贴 token。
- 环境变量凭据模式下使用 `whoami` 或 `run` 诊断，不使用 `auth login`。

## 按需加载参考资料

| 需要处理的问题 | 加载内容 |
| --- | --- |
| 能力、范围和用法 | 先运行 `about`；失败时才读取 [about.md](references/about.md) |
| 首次配置、Python 或故障恢复 | [user-guide.md](references/user-guide.md) |
| 会话路径缺失或权限异常 | [platforms.md](references/platforms.md) |
| 环境变量、App ID、CLI 覆盖项 | [env-contract.md](references/env-contract.md) |
| 运行边界 | [security-and-limits.md](references/security-and-limits.md) |

措辞和设计说明不放进运行时 Skill。仓库工作区存在时，项目级材料见 `docs/traework-local-auth/`。
