# 架构与验证（项目级）

配合 [wording.md](wording.md) 阅读。实现脚本见插件 `scripts/traework_local_auth.py`。

## 分层

| 层 | 说明 |
| --- | --- |
| 飞书 OAuth 同意 | 用户在 TraeWork 流程中已完成 |
| Trae 云端 | 托管第三方（飞书）令牌 |
| 本机 Trae 会话 | 客户端为当前 OS 用户保存的登录态 |
| 本插件脚本 | 只读会话 → 请求短时飞书用户令牌 → 注入环境变量 |
| `lark-cli` | 官方环境凭据模式消费 `LARKSUITE_CLI_*` |

```text
本机 Trae 会话（只读）
  → Trae 产品接口：第三方令牌（feishu/lark）
  → Feishu user access token（绑定 TraeWork 应用）
  → LARKSUITE_CLI_APP_ID
     LARKSUITE_CLI_USER_ACCESS_TOKEN
     LARKSUITE_CLI_BRAND
  → lark-cli whoami / OpenAPI
```

## JWT / 会话来源策略

| 优先级 | 来源 | 说明 |
| --- | --- | --- |
| 默认 | 本地 `storage.json` 会话 | 登录后通常存在 |
| 备用 | 主目录下可选 JWT 文件 | 仅当客户端写出时存在；无稳定用户开关 |
| 覆盖 | `TRAEWORK_JWT_SOURCE` / `TRAE_STORAGE_JSON` | 见 skill `platforms` / `user-guide` |

## 跨平台路径

见 skill 内 [platforms.md](../../plugins/feishu-traework-local-auth/skills/feishu-traework-local-auth/references/platforms.md) 与 [reference-cockpit-tools.md](reference-cockpit-tools.md)。

主脚本启动只依赖标准库；加密依赖惰性导入。缺库时 `status` 仍能报告当前 Python 和安装 argv。`run` 不捕获业务输出。

## lark-cli 二进制解析

默认不绑死当前 `PATH` 的第一个 `lark-cli`。脚本会收集：

- 当前 `PATH`（含智能体/fnm/nvm 会话）
- 常见系统路径（`/usr/local/bin`、Homebrew、`~/.local/bin`、Windows `%APPDATA%\npm`）
- 当前 agent/node 环境（`FNM_MULTISHELL_PATH`、`FNM_DIR`、`NVM_BIN`、`NVM_SYMLINK`、`PNPM_HOME`、`npm prefix -g`）

然后按 `newest_version` 选择可运行副本。Windows 在同版本时优先 `lark-cli.exe`，而不是 `.cmd` / `.bat`；macOS/Linux 只扫描无后缀的 `lark-cli`。再其次才按 `PATH` 优先。`TRAEWORK_LARK_CLI` / `LARK_CLI` 可强制指定文件，不再比版本。

用 token 的方式是 `run -- <lark-cli args>`：取短时 UAT，注入到这一次子进程，不打印 token。这仍不是 `lark-cli auth/profile` 集成，也不是改 PATH 的常驻 shim。

## 环境契约

见 skill 内 [env-contract.md](../../plugins/feishu-traework-local-auth/skills/feishu-traework-local-auth/references/env-contract.md)。

TraeWork client id（非 secret）：

| 区域 | client id | brand |
| --- | --- | --- |
| CN | `cli_a965abcba6fadbd3` | `feishu` |
| 国际 | `cli_a96598a589b89dba` | `lark` |

## 验证记录

命令（插件脚本真相源）：

```bash
python3 plugins/feishu-traework-local-auth/skills/feishu-traework-local-auth/scripts/traework_local_auth.py status
python3 .../traework_local_auth.py decrypt-check
python3 .../traework_local_auth.py fetch-uat
python3 .../traework_local_auth.py resolve-lark-cli
python3 .../traework_local_auth.py whoami
python3 .../traework_local_auth.py run -- whoami --json
```

| 项 | 状态（2026-08-14，macOS + TRAE SOLO CN） |
| --- | --- |
| `status` 读到本机会话 | 通过（scheme B / storage） |
| `decrypt-check` | 通过 |
| `fetch-uat` | HTTP 200，`Type=feishu`，有 open_id / expire_at |
| `whoami` | returncode 0；`appId=cli_a965abcba6fadbd3`；`identity=user`；`available=true`；`tokenStatus=ready` |
| Windows | 2026-08-17 在默认 GBK、Python 3.10.11、未启用 `PYTHONUTF8`、`lark-cli` 1.0.68 下通过 `status`、`whoami` 和真实云空间搜索 |
| Linux 路径生成 | mock 与 cockpit-tools 约定一致；目标 OS 请再跑 `status`/`whoami` |
| `lark-cli` 多路径 / 新版本优先 | 2026-08-17 本机解析到 agent `1.0.87`；纯函数单测覆盖“更新版本优先” |
| `run` 消费 token | 取票后注入子进程；禁止 `auth login` / profile / config 变更；不打印 token |

## 明确边界

- 不写回 Trae 会话、不切号  
- 不把 TraeWork 宣称为官方公共共享 App  
- 不并入 `feishu-next` 默认鉴权  
- 私有产品接口与本地会话格式可能随版本变化  
- 令牌短命；scope 受 TraeWork 授权页约束  

## 与 skill 文档的分工

| 问题 | 去哪看 |
| --- | --- |
| 怎么跑命令？ | skill `SKILL.md` + `user-guide.md` |
| 路径在哪？ | skill `platforms.md` |
| 用词对不对？ | 本文档目录 `wording.md` |
| 参考了谁？ | `reference-cockpit-tools.md` |
| 为什么这样设计？ | 本文 |
