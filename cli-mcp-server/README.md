# Feishu Next CLI MCP Server

这个子包把本机已安装的 `lark-cli` 包装成 MCP server，供其他 MCP client 调用。它不替代官方
`lark-mcp`，也不链接或修改 `lark-cli` 源码；所有飞书能力仍通过受控白名单调用本机
`lark-cli` 二进制。

更完整的可行性、架构边界和后续路线见 [DESIGN.md](./DESIGN.md)。

## Transport

默认监听 `127.0.0.1:3000`：

```text
POST   http://127.0.0.1:3000/mcp
GET    http://127.0.0.1:3000/mcp
DELETE http://127.0.0.1:3000/mcp

GET    http://127.0.0.1:3000/sse
POST   http://127.0.0.1:3000/messages?sessionId=...

GET    http://127.0.0.1:3000/health
```

- 新 MCP client 优先使用 Streamable HTTP：`/mcp`。
- 旧 MCP client 使用 legacy HTTP+SSE：`/sse` + `/messages`。
- 两个 transport 共享同一组工具，但 session 独立管理。

## Start

```bash
npm ci
npm run start
```

覆盖 host/port：

```bash
LARK_CLI_MCP_HOST=127.0.0.1 LARK_CLI_MCP_PORT=3017 npm run start
```

调整内部 `lark-cli` 子进程调度：

```bash
LARK_CLI_MCP_MAX_CONCURRENCY=4 LARK_CLI_MCP_MAX_QUEUE=64 npm run start
```

Streamable HTTP session 默认最多 128 个、空闲 15 分钟自动回收；可分别通过
`LARK_CLI_MCP_MAX_SESSIONS` 和 `LARK_CLI_MCP_SESSION_IDLE_TTL_MS` 调整。

需要 Node.js 18 或更高版本。所有需要调用 `lark-cli` 的 MCP tool 都会先进入本地 scheduler，再由
scheduler 调用 `spawn("lark-cli", args, { shell: false })`。
`lark_runtime_status` 和 `/health` 会返回当前 active / pending / completed 计数。

如需让其他本机进程或内网进程调用，建议加本地 bearer token：

```bash
LARK_CLI_MCP_BEARER_TOKEN='<local-secret>' npm run start
```

这个 server 继承本机 `lark-cli` 的登录态和权限。默认只绑 `127.0.0.1`；如果暴露到非本机地址，
server 会强制要求 `LARK_CLI_MCP_BEARER_TOKEN`；仍建议同时使用反向代理 ACL 或其他访问控制。
设置 token 后，`/mcp`、legacy SSE 和 `/health` 都需要同一个 bearer token。

## Tools

- `lark_auth_status`
- `lark_auth_login_start`
- `lark_auth_login_complete`
- `lark_doctor_offline`
- `lark_runtime_status`
- `lark_profile_list`
- `lark_skills_list`
- `lark_skill_read`
- `lark_drive_inspect`
- `lark_drive_search`
- `lark_docs_fetch`
- `lark_event_list`
- `lark_event_schema`
- `lark_event_consume_bounded`
- `lark_api_dry_run`

`lark_profile_list`、skills 和 event catalog 属于 bootstrap discovery，不要求业务执行 contract。Auth、doctor、
Drive、Docs、event consume 和 raw API dry-run 都要求 caller 明确传入 `context`、`profile`、独立锚定的
`expectedAppId` 与 `identity`。wrapper 会先运行 profile-qualified `config show`、`whoami`、
`auth status --json --verify`；App/profile/identity 不一致时停止，不会用环境变量猜选目标。

`lark_auth_login_start` 使用 `lark-cli auth login --no-wait --json` 启动设备授权。server 不把
`device_code` 暴露给 MCP client，而是短期保存在内存中，只返回 `authorizationHandle`、原样
`verificationUrl`、`userCode` 和可选 ASCII QR。用户完成授权后，caller 以相同 execution contract 和
`authorizationHandle` 调用 `lark_auth_login_complete`；handle 最长有效 10 分钟，成功后即失效，失败时可在
TTL 内重试，server 重启后失效。

wrapper 不暴露任意 shell/argv，不允许外部 caller 传 `--yes`。错误 envelope 不返回 raw argv、stdout
或 stderr；`lark-cli` 失败只给固定提示和 request ID。公开文档、日志和测试也不写入真实 token、app secret、
cookie、私有文档内容或聊天归档。

## Validation

```bash
npm run check
npm run contract
npm run smoke
npm run smoke:mcp
npm run smoke:streamable
npm run smoke:scheduler
npm run smoke:auth
npm run smoke:transport
```

- `contract` 直接测试 execution preflight、schema、argv 拼接、OAuth handle、脱敏和 forbidden args。
- `smoke` 只检查 server 启动和 `/health`。
- `smoke:mcp` 通过 legacy SSE MCP transport 连接，执行 `tools/list` 和 `lark_skills_list`。
- `smoke:streamable` 通过 Streamable HTTP `/mcp` 连接，执行同样的 MCP 链路检查。
- `smoke:scheduler` 用临时 fake `lark-cli` 验证并发/队列上限，以及忽略 `SIGTERM` 时升级到 `SIGKILL`。
- `smoke:auth` 用临时 fake `lark-cli` 验证 bearer/Host 防护、preflight、一次性 OAuth handle 和脱敏。
- `smoke:transport` 验证 legacy session 关闭清理、unknown session 和 invalid body 不回显。

仓库级验证前删除本地依赖目录，避免项目 validator 扫描第三方包内容：

```bash
rm -rf cli-mcp-server/node_modules
python3 scripts/validate_project.py
```
