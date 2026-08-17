# Feishu Next

`Feishu Next` 是一个面向飞书 / Lark 常用工作流的 Codex 插件包。它采用
`Codex Is All You Need` 的 V2 plugin-first 形态：

```text
plugin package -> marketplace install -> skill workflow
```

它不是另一个飞书 OpenAPI SDK，也不复制官方 `lark-cli` 内置 skills。它的定位是把常见的
跨步骤飞书任务沉淀为可复用 Codex Skills，并始终以当前安装的 `lark-cli` 作为运行时真相源。

`Feishu Next 0.3.0` 已使用本机安装的 `lark-cli 1.0.83` 验证，并对照
`lark-cli 1.0.86` 源码审计，但不硬锁某个精确版本。源码审计不能替代安装态验证；router
会动态读取当前 skills、domain help、shortcut help 和 flags；旧版或新版 CLI
只要核心 runtime surface 校验通过即可使用。

## 迁移定位

`Feishu Next` 是插件化后的 Feishu 入口层，用来替代把 Feishu guide 单独放在
`~/.codex/skills` 的做法。安装插件后，默认从
`$feishu-next:feishu-workflow-router` 开始：

- router 负责识别飞书 URL / token / 用户意图，选择官方 `lark-*` skill 或本插件 sub-skill。
- 官方 `lark-*` skill 仍通过 `lark-cli skills read ...` 实时读取，不内置、不复制到本仓库。
- 本插件只沉淀跨步骤工作流、证据留存、备份回滚、验证门槛和安全边界。
- 旧的全局 `lark-cli-guide` 可以保留为过渡备份；插件安装并可发现后，常规使用不再需要它。

## 适合做什么

- 路由飞书任务到正确的官方 `lark-*` skill。
- 路由原生 Markdown、思维笔记、审批、Miaoda/Spark、应用 slash commands、
  会中能力和官方 meeting/standup workflows。
- 只读导出飞书文档、表格、多维表格和幻灯片。
- 盘点飞书文档中的图片、附件、画板和嵌入资源。
- 归档飞书 IM 聊天记录、消息搜索结果、线程和资源。
- 安全修改、重绘、恢复飞书文档内画板，并处理 `.drawio` / diagrams.net 到白板的发布同步边界。

## 仓库结构

```text
.agents/plugins/marketplace.json       # 本仓库自带 marketplace
plugins/feishu-next/                   # 默认工作流插件
  .codex-plugin/plugin.json
  README.md
  skills/
    feishu-workflow-router/
    feishu-readonly-doc-export/
    feishu-doc-asset-map/
    feishu-im-chat-archive/
    feishu-whiteboard-ops/
plugins/feishu-traework-local-auth/    # 可选：复用本机 TraeWork 飞书授权
docs/traework-local-auth/              # 上述可选插件的项目文档
```

## 安装

本地开发安装：

```bash
codex plugin marketplace add /path/to/Feishu-Next
codex plugin list --marketplace feishu-next --available --json
codex plugin add feishu-next@feishu-next
```

如果只想确认市场条目是否能被 Codex 看到，先运行前两条；安装到当前 Codex
运行环境时再执行 `codex plugin add`。

安装后建议从入口 skill 开始：

```text
$feishu-next:feishu-workflow-router
```

可选插件 `feishu-traework-local-auth` `0.2.1`：复用**本机已经完成**的 TraeWork 飞书授权（每人用自己的 Trae 登录，不要拷贝会话或 token）。它不是 Feishu Next 的默认鉴权。

```bash
codex plugin add feishu-traework-local-auth@feishu-next
```

```text
$feishu-traework-local-auth:feishu-traework-local-auth
```

Windows 上 `lark-cli` 一般是 `lark-cli.exe`；macOS / Linux 只有无后缀的 `lark-cli`，不要写 `.exe`。Windows GBK 控制台已用 `status` / `whoami` / 真实云空间搜索验收。详细安装、用词和验证记录见 [plugins/feishu-traework-local-auth/README.md](plugins/feishu-traework-local-auth/README.md) 与 [docs/traework-local-auth/](docs/traework-local-auth/)。

许可证是 `GPL-3.0-only`，原文见 <https://www.gnu.org/licenses/gpl-3.0.html>。

也可以直接调用具体工作流：

```text
$feishu-next:feishu-readonly-doc-export
$feishu-next:feishu-doc-asset-map
$feishu-next:feishu-im-chat-archive
$feishu-next:feishu-whiteboard-ops
```

## 运行时依赖

需要已安装并配置飞书官方 CLI：

```bash
command -v lark-cli
lark-cli --version
lark-cli skills list
```

飞书访问、身份、scope、权限错误和高风险确认规则都以当前 `lark-cli` 内嵌 skill 为准：

```bash
lark-cli skills read lark-shared
lark-cli skills read <lark-domain-skill>
lark-cli whoami
lark-cli auth status --json --verify
```

只有诊断本地配置或 runtime 健康状态时才运行 `lark-cli doctor --offline`。
像 `application` 这样没有独立 embedded skill 的 domain，以当前
`lark-cli application --help` 和 shortcut help 为准，不猜造 skill 名称。

## 设计边界

- 插件只打包 reusable skills，不打包本机 token、应用密钥、私有文档内容或运行时配置。
- 写入、删除、发送消息、权限变更、发布和 `--yes` 操作不在默认路径里，必须单独确认。
- `feishu-*` skills 是组合工作流层；具体 API 细节优先读取官方 `lark-*` skills。
- 遇到没有 matching skill 的能力时，先检查 domain/shortcut help；正式 command
  也不存在时，再读 `lark-openapi-explorer` 并通过 `schema` / `api` 探索。

## 首批 Skills

| Skill | 用途 |
| --- | --- |
| `feishu-workflow-router` | 根据 URL、资源类型和用户意图选择正确 workflow |
| `feishu-readonly-doc-export` | 只读导出 doc/docx/sheet/bitable/slides |
| `feishu-doc-asset-map` | 盘点文档图片、附件、画板、内嵌表格和 Base |
| `feishu-im-chat-archive` | 分页归档 IM 消息、线程、资源和 evidence 字段 |
| `feishu-whiteboard-ops` | 安全查看、修改、重绘、恢复画板，含 `.drawio` 同步边界 |

可选独立插件：

| 插件 | 用途 |
| --- | --- |
| `feishu-traework-local-auth` `0.2.1` | 复用本机 TraeWork 飞书授权，按需换取短时用户令牌并驱动官方 `lark-cli` |

## 本地校验

```bash
python3 scripts/validate_project.py
python3 scripts/validate_lark_runtime.py
```

或使用 Make：

```bash
make validate
make validate-runtime
make validate-all
```

`validate` 保持确定性的静态/plugin/skill 校验；`validate-runtime` 只执行本地
`lark-cli skills read` 和 `--help` 探测，不认证、不调用飞书 API、不写远端资源；
它验证核心 skill/reference，并把其他 Router skill 的“已读取且非空”与 catalog
的“已发现”数量分开报告；裁剪发行版缺少的非核心 skill 只告警，不假装成 scope
错误；`validate-all` 顺序运行二者。静态校验底层会继续调用 Codex 的插件和 skill
校验器；缺少这些 validator 时默认失败，避免发布门禁假绿。只做非发布态的
降级静态检查时可显式运行
`python3 scripts/validate_project.py --allow-missing-codex-validators`。

## CLI MCP Server

`cli-mcp-server/` 提供独立的本机 MCP wrapper，通过白名单工具调用已安装的
`lark-cli`，支持 Streamable HTTP 和 legacy SSE。它不属于 Codex plugin 包，
不会复制或修改官方 CLI；使用、transport、安全边界和验证命令见
[`cli-mcp-server/README.md`](cli-mcp-server/README.md)。运行 `make validate-all`
时会同时验证 plugin/runtime 与 MCP wrapper。

需要单独验证时：

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/feishu-next

python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/feishu-next/skills/feishu-workflow-router
```

其余 skill 目录同样用 `quick_validate.py` 校验。

## 维护原则

- 新增 workflow 先判断是否已经被官方 `lark-*` skill 覆盖；只把跨步骤、可复用、有证据或安全边界的流程放进本插件。
- 每个 skill 保持一个清晰触发场景，正文控制在可快速读取的执行步骤内。
- 涉及命令参数、scope、身份时，不从记忆或源码猜，先读当前 `lark-cli skills read ...` 输出。
- 公开仓库不提交真实导出物、聊天归档、二维码、token、私有 URL 或私有文档内容。
