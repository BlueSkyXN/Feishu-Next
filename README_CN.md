# Feishu Next

`Feishu Next` 是一个面向飞书 / Lark 常用工作流的 Codex 插件包。它采用
`Codex Is All You Need` 的 V2 plugin-first 形态：

```text
plugin package -> marketplace install -> skill workflow
```

**Next 是飞书工作流能力层：把你的一系列飞书操作串成完整任务，而不是只调用一次官方 skill。**
它沉淀个人玩法和经验，管理步骤依赖、输入输出、执行身份、授权、证据、验证和失败恢复。
官方 `lark-suite` 负责官方能力整合与技能清单压缩；Next 支持导航到 suite，但保留整个工作流的状态。
它不是另一个 OpenAPI SDK，不复制官方正文或资源快照，始终以当前安装的 `lark-cli` 为运行时真相源。

当前源码版本为 **0.11.0**，包含 **11 个 Skill**（Router 加 10 个具体工作流）；加上独立鉴权插件，全仓 **12 个 Skill**。
`feishu-workflow-router` 保留在 Next，不另建独立 Router 插件。从工作区提炼的公共能力保留文档格式对齐、思维笔记大纲和通用 Base 快照；5 个业务专用技能及项目快照实现仍在原项目维护，详见 [迁移说明](docs/skill-migration.md)。

历史 `Feishu Next 0.3.0` 已使用本机安装的 `lark-cli 1.0.83` 验证，并对照
`lark-cli 1.0.86` 源码审计，但不硬锁某个精确版本。源码审计不能替代安装态验证；router
会动态读取当前 skills、domain help、shortcut help 和 flags；旧版或新版 CLI
只要核心 runtime surface 校验通过即可使用。

## 迁移定位

安装插件后，从 `$feishu-next:feishu-workflow-router` 组织完整任务，也可以直接选择具体玩法：

- Router 既介绍官方“能做什么”，也导航你的工作流；按需读取云文档与知识库、表格数据、消息协作、演示应用、认证扩展五类能力地图。
- 判断依据是能力和附加方法，不是单步/多步：官方已有完整文档创作、权限治理等流程时直接复用，需要 Next 的保真、证据、恢复或跨任务状态时再用 Next。
- 11 个技能继续平铺。每个玩法都提到 Router：缺执行上下文、能力不明或用户要求串联任务时按需使用；已处于流程中则沿用有效上下文，交回真实产物，不重复分派自己。身份、目标或授权改变仍需复核。
- 对多步任务，Next 保持步骤依赖、经过验证的产物、授权检查点和部分失败状态；不会把整个任务转给 suite 后就结束。
- 当前客户端确实暴露 `lark-suite` 时，导航到其入口，再按需读取 `references/<skill-name>/GUIDE.md`。不把内部指南当独立技能调用。
- 仍兼容独立 `lark-*` 技能，以及 `lark-cli skills read ...`。CLI 的技能清单不是客户端安装清单，不据此声称 suite 已安装。
- 只有用户明确指挥 AI 时才更新插件、CLI 或技能布局。普通任务不安装 suite、不自动更新、不移除全局技能。
- 旧的全局 `lark-cli-guide` 可以保留为过渡备份；Next 不会擅自修改 `~/.codex/skills` 等用户目录。

例如“归档聊天、据此整理文档、最后发送结果”，Next 负责串起这几个步骤；官方指南分别提供 IM、Doc 等具体操作方法。
只读或草稿请求不会自动扩大成创建、发布或发送。详细分工见 [工作流架构](docs/workflow-architecture.md)。

## 适合做什么

- 将多项飞书操作组成有步骤依赖、证据和完成检查的工作流。
- 导航到官方 suite、独立技能或运行时说明；直接复用匹配的官方工作流，不重复包装原子 API。
- 只读导出飞书文档、表格、多维表格和幻灯片。
- 按用户明确要求，通过 Chrome 逐页截取可查看的飞书幻灯片并合成图片型 PDF，核对画布、页序、图片编码和像素尺寸。
- 盘点飞书文档中的图片、附件、画板和嵌入资源。
- 归档飞书 IM 聊天记录、消息搜索结果、线程和资源。
- 把研究或业务材料设计成统一的卡片、流程、泳道、矩阵或前后对照图，生成可编辑 SVG 并检查视觉效果；提供零第三方 Python 依赖的组件和合成示例。
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
    feishu-slides-preview-to-pdf/
    feishu-doc-asset-map/
    feishu-im-chat-archive/
    feishu-whiteboard-ops/
    feishu-whiteboard-semantic-cards/
    feishu-doc-format-align/
    feishu-doc-format-repair/
    feishu-mindnote-outline/
    feishu-base-snapshot-maintain/
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
$feishu-next:feishu-slides-preview-to-pdf
$feishu-next:feishu-doc-asset-map
$feishu-next:feishu-im-chat-archive
$feishu-next:feishu-whiteboard-ops
$feishu-next:feishu-whiteboard-semantic-cards
```

## 运行时依赖

使用官方 API 的工作流需要已安装并配置飞书官方 CLI：

```bash
command -v lark-cli
lark-cli --version
lark-cli skills list
```

显式调用 `feishu-slides-preview-to-pdf` 的纯浏览器路径使用 Chrome 已有的飞书登录态；不要求先安装或登录 CLI。若转用 CLI 查询或官方导出，再建立对应的执行上下文。截图结果保留水印，不含原始文字层、动画或可编辑对象。

`feishu-whiteboard-semantic-cards` 使用“语义卡片图解”风格，根据本地材料完成设计与预览，无需飞书认证；读取线上参考或写回时，再复用 Router 上下文并交给 `feishu-whiteboard-ops` 执行。它负责版式、视觉层级和设计源，后者负责目标定位、备份、写入与恢复。

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

## Skills 清单

| Skill | 用途 |
| --- | --- |
| `feishu-workflow-router` | 选择与编排多步任务，保持执行上下文，并导航到官方 suite |
| `feishu-readonly-doc-export` | 只读导出 doc/docx/sheet/bitable/slides |
| `feishu-slides-preview-to-pdf` | 通过浏览器逐页截取飞书幻灯片，校验并合成图片型 PDF |
| `feishu-doc-asset-map` | 盘点文档图片、附件、画板、内嵌表格和 Base |
| `feishu-im-chat-archive` | 分页归档 IM 消息、线程、资源和 evidence 字段 |
| `feishu-whiteboard-ops` | 安全查看、修改、重绘、恢复画板，含 `.drawio` 同步边界 |
| `feishu-whiteboard-semantic-cards` | 用“语义卡片图解”风格设计总览、流程、泳道与矩阵，生成 SVG、预览检查后交接画板写回 |
| `feishu-doc-format-align` | 按参考文档或明确样式规则统一排版，默认保留材料划分与正文，逐段逐格验证 |
| `feishu-doc-format-repair` | 诊断并修复标题错位、材料边界混乱和粘贴残留，逐项核对获准的结构与文本变化 |
| `feishu-mindnote-outline` | 维护已有思维笔记的大纲和父子关系 |
| `feishu-base-snapshot-maintain` | 周月快照、跨周比较与部分失败续做 |

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
make validate-privacy
make validate-privacy-history
make validate-runtime
make validate-all
```

`validate` 先执行本地隐私检查，再运行静态/plugin/skill 校验与回归测试。隐私检查覆盖 Git 候选文件和暂存区，要求本机 Gitleaks；缺失时默认失败，不自动安装。`validate-privacy-history` 另外检查本地可达历史。`/local/` 由仓库级忽略保护；发布不能压缩整个目录，必须按审核提交清单生成并检查最终 ZIP，详见 [隐私与发布规则](docs/privacy-and-release.md)。

`validate-runtime` 只执行本地
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

## 命名与版本

详见 [命名与版本规则](docs/skill-governance.md)、[技能清单与旧名映射](skill-catalog.json) 和 [变更记录](CHANGELOG.md)。插件版本存 manifest，单技能版本存 `metadata.version`，均采用完整 SemVer；技能名称保持稳定的 `feishu-*` kebab-case，不带 `-v2` 等版本后缀。Router 为 `0.11.0`，语义卡片图解为 `0.2.0`，幻灯片预览转 PDF 和格式修复为 `0.1.0`；格式对齐为 `0.1.2`、思维笔记为 `0.1.1`、通用快照为 `0.1.2`、资产盘点为 `0.3.2`、白板运维为 `0.3.3`，导出与聊天归档为 `0.3.1`。

5 个业务专用技能和项目快照实现已恢复原项目正常目录，前两项公共能力保留本地兼容入口。公开收录以可复用飞书操作能力为标准，不因业务流程读写飞书就纳入；通用快照不依赖原项目脚本，也不提供一键同步器。源码提交与 PR 不代表已更新安装缓存或发布版本；本次未执行远端业务操作。

## 维护原则

- 新增 workflow 先判断是否已经被官方 `lark-*` skill 覆盖；只把跨步骤、可复用、有证据或安全边界的流程放进本插件。
- 每个 skill 保持一个清晰触发场景，正文控制在可快速读取的执行步骤内。
- 涉及命令参数、scope、身份时，不从记忆或源码猜，先读当前 `lark-cli skills read ...` 输出。
- 公开仓库不提交真实导出物、聊天归档、二维码、token、私有 URL 或私有文档内容。
