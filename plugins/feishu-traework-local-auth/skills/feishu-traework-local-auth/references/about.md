# Feishu TraeWork 本地授权

可选本机助手（插件 `0.2.1`）：在**同一台电脑、同一个 OS 用户**上，复用你已经在 Trae / TraeWork 里完成的飞书授权，把它交给官方 `lark-cli` 使用。每次运行按需换取短时用户访问令牌，不把短时令牌长期保存到本地。

它不是 Feishu Next 的默认鉴权，也不是给别人用的公共飞书应用。没有 Trae 登录、或多用户/服务器场景，请改用自己的飞书应用。发给别人时，对方必须在自己的电脑上完成 Trae 登录和 TraeWork 飞书同意；不要拷贝会话文件或 token。

## TraeWork 相关

- 你先在本机 Trae 客户端登录，并在 TraeWork 流程里完成飞书同意。
- 助手只读当前用户的 Trae 会话（默认 `storage.json`，方案 B），向 Trae 云端换取你已授权给 TraeWork 的短时飞书用户令牌。
- 国内 TraeWork 应用身份是 `cli_a965abcba6fadbd3`（client id，不是 secret），品牌 `feishu`。国际版走另一套 id + `lark`。
- 权限范围以 TraeWork 授权页为准，不会扩展为授权范围之外的 scope。
- 令牌寿命短。正确用法是每次业务命令前重新取票，而不是长期保存。
- 默认 JWT 文件通常不存在；日志里的 `JWT token refresh is disabled` 不表示本助手不可用。

## Windows 支持

| 项 | 状态 |
| --- | --- |
| Windows 会话路径 | 已实现：`%APPDATA%\<Trae产品名>\User\globalStorage\storage.json` |
| 解密 | 便携 AES / byteCrypto，不读 Credential Manager |
| PowerShell 命令 | `status` / `whoami` / `run` 可用 |
| 终端编码 | 捕获的 CLI 输出按 UTF-8 解码；不要求修改 `chcp` |
| `lark-cli` 发现 | 会看 `PATH`、npm/pnpm、fnm/nvm 和当前 agent/node 环境，默认选更新版本。Windows 优先 `lark-cli.exe`；macOS/Linux 只认无后缀的 `lark-cli` |
| 实机验收 | Windows GBK + Python 3.10.11 + `lark-cli` 1.0.68 已通过 `status`、`whoami` 和真实云空间搜索；macOS + TRAE SOLO CN 也已验证 |
| `export-env` | 输出的是 bash `export`，PowerShell 不要直接用 |

Linux 路径按 `$XDG_CONFIG_HOME` 或 `~/.config` 设计，同样未做独立实机验收。

## 使用方法

先确认本机 Trae 已登录且 TraeWork 飞书授权完成，本机有 `lark-cli` 和 Python 3.10+。缺 `pycryptodome` 时，用即将跑脚本的那个 Python 安装 `scripts/requirements.txt`。脚本本身不会自动运行 `pip`。

```bash
SCRIPT="<skill-dir>/scripts/traework_local_auth.py"
python3 "$SCRIPT" about
python3 "$SCRIPT" status
python3 "$SCRIPT" resolve-lark-cli
python3 "$SCRIPT" whoami
python3 "$SCRIPT" run -- whoami --json
python3 "$SCRIPT" run -- drive +search --as user --page-size 3
```

PowerShell 把 `python3` 换成 `python`；没有可用的 `python` 时改用 `py -3`。路径使用反斜杠；消费 token 同样用 `run`，不要 `export-env`。

成功标准：`whoami` 里是 TraeWork `appId`，`identity=user`，`available=true`。

覆盖项：`TRAE_STORAGE_JSON`、`TRAEWORK_LARK_CLI` / `LARK_CLI`、`TRAE_API_HOST`。

## 用例

- 本机 Agent 要读你刚在 TraeWork 里授权过的飞书文档、知识库、云盘或多维表格。
- 你不想为同一台电脑再走一遍自建飞书应用的 OAuth。
- 智能体环境和系统里各有一份 `lark-cli` 时，让助手选更新的那份，再带着 TraeWork 用户身份发只读查询。
- 诊断本机 Trae 会话在不在、能不能换成 `lark-cli` 用户身份。

## 不要用它做这些

- 不要打印、提交或转发 JWT / UAT。
- 不要 `run -- auth login`，也不要改 `profile` / `config` 来“修”环境凭据。
- 不要写回 Trae `storage.json`、不要切号、不要导出钥匙串。
- 不要拿到另一台机器、另一个人或服务器上用。
- 不要把它当成飞书自动化平台（妙搭）的官方授权通道。
