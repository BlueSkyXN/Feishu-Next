# Skill 命名与版本规则

本规则适用于仓库 marketplace 中的插件和公共 Skills。保留现有 Codex V2 `.codex-plugin/plugin.json` 与 `.agents/plugins/marketplace.json`，不因开发客户端不同而改换插件协议。

## 1. 稳定名称

- 插件和 Skill 使用小写 kebab-case，长度不超过 64；不得含空格、下划线、连续连字符或中文。
- 公共 Skill 使用 `feishu-<对象或领域>-<动作或目的>`，如 `feishu-doc-format-align`。官方 `lark-*` 名称保留给官方运行时，不复制同名技能。
- 目录名与 `SKILL.md` 的 `name` 必须一致。调用形式为 `$<plugin>:<skill>`；`agents/openai.yaml` 的默认提示使用完整命名空间。
- 名称不带版本或日期，不新增 `-v2`、`-v3`、`-20261006` 等目录。升级在原目录进行。
- 已分发且合法的名字优先稳定；改名属于兼容性变更，必须记录旧名映射与迁移方式，不能悄悄改名。
- [skill-catalog.json](../skill-catalog.json) 是公共技能清单和旧名映射，不存版本副本。旧名映射用于文档与本地适配，不代表客户端自动提供别名。

## 2. 两级版本

所有版本使用严格 SemVer：`MAJOR.MINOR.PATCH`，可选 `-prerelease` 和 `+build`，数值段不能带前导零。

| 对象 | 唯一版本来源 | 本次基线 |
| --- | --- | --- |
| 插件发布包 | `.codex-plugin/plugin.json` 的 version | 主插件 0.7.0；鉴权插件保持既有版本 |
| 单个公共 Skill | `SKILL.md` 的 `metadata.version`，字符串 | Router 0.7.0，格式/大纲 0.1.1，快照 0.1.2，资产盘点 0.3.2；导出/归档/白板 0.3.1 |

Skill 还保留 `metadata.updated: "YYYY-MM-DD"`。不使用顶层 version，以兼容现有 Codex Skill schema。项目本地兼容入口仍只含 name/description，公共方法的版本以所引用插件为准。

- PATCH：不改变输入输出契约的错误修复、措辞澄清、补充校验。
- MINOR：向后兼容的新能力、Skill、可选分支或字段。
- MAJOR：移除/重命名既有公共能力，改变输入输出、授权边界或默认副作用，且不再兼容。
- 0.x 阶段不兼容变化至少提升 MINOR，并明确迁移说明；兼容新增也提升 MINOR，修复提升 PATCH。
- 只改某个 Skill 时升级该 Skill，不给所有 Skill 跟随插件集体涨版本；包含内容变化的插件包同时升级发布版本。
- 从缺失版本开始建立 0.1.0 基线；将历史 0.3 补成 0.3.0 仅是表示法规范化，不宣称功能变更。
- 既有 `+codex.YYYYMMDDHHMMSS` 元数据可保留；它不参与 SemVer 优先级，不能仅改时间戳冒充一次更新。新常规版本优先使用纯 `X.Y.Z`。
- 版本赋值表示源码状态，不证明已 tag、发布、安装或运行验收。本次源码变更记录见 [CHANGELOG.md](../CHANGELOG.md)。

## 3. 发布与命名约定

发布本身必须另行获得用户授权，本规则不创建 tag 或发布包：

- 多插件 tag：`<plugin>/v<version>`，例如 `feishu-next/v0.4.0`。
- 压缩包：`<plugin>-<version>.zip`，存放经忽略的 `dist/`，不混入 `skills/`。只能从审核提交的插件文件及 LICENSE 清单生成；扫描最终 ZIP，不直接压缩工作目录。详见 [隐私与发布规则](privacy-and-release.md)。
- `SKILL.md` 只放执行步骤；references 放按需方法细节，scripts 放可独立复用的代码，agents 放展示与调用提示，测试使用合成数据。
- description 必须同时说明能力与触发场景；本仓库以 `Use when` 为可校验标记，正文可用中文。

## 4. 公共收录门槛与私有边界

不能把“用到了飞书”当成公共收录标准。去掉公司规则、固定模板和历史案例后，仍有独立可复用的飞书操作方法，才适合成为公共 Skill；泛化后只剩一般写作、统计或核对清单的流程留在业务项目。

公共包不包含人员名单、部门专属默认值、内部 URL、真实文档/表/字段标识、token、凭据、历史业务金额、真实导出物或私人绝对路径。

提炼或撤回 Skill 时：

1. 先盘点整个目录及跨目录依赖，不能只改 SKILL.md 的标题。
2. 项目专用 Skill 与其脚本在原项目正常技能目录维护；仅独立提炼满足公共门槛的能力，不因提炼方法就强制搬走整套业务实现。
3. 公共能力不得依赖原项目绝对路径、专用配置文件或未分发脚本。输入契约可以由调用方提供，执行器是可选的；纯 Agent 流程须明确不附带一键执行程序。
4. 本地只需要调用公共方法时可以保留薄入口及私有风格参考；仍承担业务执行的技能不改成薄入口。项目快照实现与通用快照方法等不同职责，不登记为旧名别名。
5. 移动前核对哈希；撤下的公共稿和本轮退役入口放回私有归档，不直接删除。恢复后核对原始文件及脚本路径；历史迁移记录保留并补充当前状态。
6. 不将私有原件复制进公开仓库的 local/、示例、测试、日志或提交。公开迁移表只记录名称、归属与能力，不公布私有定位信息。

## 5. 工作流与官方能力

`feishu-workflow-router` 属于 Next 的工作流层，负责选择/组合玩法、状态和证据传递，并按需导航到官方 `lark-suite`。官方负责能力目录与清单压缩，Next 不复制官方技能，也不注册独立 Router 插件。直接原子任务可以导航官方而不强制构建多步流程。

Router 与七个工作流保持独立公开入口；特殊分支和能力地图作为按需参考，不新增公开 Skill。每个工作流正文都说明何时借助 Router、何时复用上下文及如何回传结果，避免循环分派。官方已有多步流程可以直接复用，不以步骤数量划分归属。

更新插件、CLI 或技能布局只由用户明确指挥 AI 发起，不自动执行。源码检查不安装套件或移除全局技能。详见 [工作流架构](workflow-architecture.md)。

## 6. 验证门禁

```bash
python3 scripts/validate_privacy.py
python3 scripts/validate_project.py
python3 -m unittest discover -s scripts/tests -v
python3 scripts/validate_lark_runtime.py
```

项目校验检查清单与实际目录一致、名称/目录/namespace、SemVer/日期、路由覆盖、manifest 路径和公共包敏感绑定。外部 Codex 校验器缺失时默认失败；仅做非发布检查可显式加 `--allow-missing-codex-validators`，并报告这一降级。

这些检查不执行飞书业务请求，不替代人工授权、端到端能力验证或公开发布前的数据审查。名称/格式校验不能证明版本升级幅度合理，变更语义和兼容说明仍需维护者审查。
