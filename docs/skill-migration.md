# 工作区 Skills 公共／私有划分

2026-10-06 的初次 0.4.0 本地源码曾提炼 8 个工作流；经用途复核，0.5.0 只保留其中 **3 个公共能力**，另外 **5 个业务专用技能恢复原项目**。项目快照的专用实现也恢复原位，与公共快照方法分开维护。这两个版本均未因本次操作发布或安装。

## 当前归属

| 原项目技能 | 公共技能 | 当前维护边界 |
| --- | --- | --- |
| feishu-doc-format-align | feishu-doc-format-align | 公共：保真格式变换；原项目只保留调用入口与个人风格参考 |
| feishu-mindnote-outline | feishu-mindnote-outline | 公共：已有思维笔记的节点与层级维护；原项目保留调用入口 |
| maintain-ai-project-snapshots | feishu-base-snapshot-maintain | 双层独立：原项目维护业务规则和执行脚本；公共包仅提供通用快照流程，二者不是别名 |
| analyze-quality-ai-usage | 已撤下 feishu-ai-usage-analyze | 原项目完整维护，不随 Next 分发 |
| maintain-major-project-data | 已撤下 feishu-project-data-maintain | 原项目完整维护，不随 Next 分发 |
| insight-background-evidence | 已撤下 feishu-insight-evidence | 原项目完整维护，不随 Next 分发 |
| job-ai-transition-evidence | 已撤下 feishu-job-ai-transition | 原项目完整维护，不随 Next 分发 |
| weekly-ai-weekly-report | 已撤下 feishu-ai-weekly-report | 原项目完整维护，不随 Next 分发 |
| ppt-preview-to-pdf | feishu-slides-preview-to-pdf | 飞书 Slides 截图转 PDF 的公共方法与合成脚本；旧独立入口归档，本地调用可链接公共源码 |

## 为什么这样划分

- 文档格式对齐有逐格正文保真、合并单元格和修订保护等飞书特有难点。
- Mindnote 大纲有隐式根、父子引用、节点复用和内容/结构更新边界。
- 通用 Base 快照保留冻结、幂等、差异计划、部分失败恢复及历史保护；不携带某个项目的字段、资源、部门和脚本。
- 用量、重大项目、洞察、岗位评估和周报的主体分别是统计、业务模型、写作、公司规则和报告模板。飞书只是其中的来源或存储，不因此单独注册公共 Skill。

## 恢复与保全

5 个业务技能加项目快照实现，共 6 个原件目录已恢复到源项目正常技能入口；SKILL.md、references、scripts、tests 及其他原有文件保持逐字一致，不再通过薄入口引用被撤下的公共版本。

撤下的 5 份公共提炼稿与退役薄入口保留在源项目的非发现归档区；未直接删除，也未复制私有原件进入本仓库。哈希、私有路径与恢复记录只留在源项目。两项公共能力的本地兼容入口仍有效。

公共快照不要求原项目 resource-map、维护 SOP 或 Python 文件。调用方提供目标、真实 schema、周期、业务键和异常策略后，按当前官方 lark-base 能力执行；status/plan/apply/validate 是流程模式，不是本插件提供的命令，也不意味着附带一键同步器。

## 离线验收场景

以下是规则走查，不是飞书业务端到端验收：

1. “按参考文档统一这个表的样式，一个字也别改。”选择 `feishu-doc-format-align`，保持逐格文本、资源和 revision 保护。
2. “更新这份已有思维笔记的大纲。”选择 `feishu-mindnote-outline`，复用节点并区分内容与关系变化，不自动新建笔记。
3. “看看本周快照为什么少了一条，先别改。”选择 `feishu-base-snapshot-maintain` 的只读模式，读取调用方输入与实际字段，不寻找原项目私有脚本。
4. “按我们公司的模板填岗位评估或写周报。”不路由到已撤下的 Next 技能；只使用当前实际可用的项目技能，原子飞书操作交给官方运行时。

## 兼容与版本

当前 Feishu Next 工作流插件为 0.11.0，含 Router 加十个平铺工作流，共 11 个 Skill；加上独立鉴权插件全仓共 12 个。语义卡片图解 `feishu-whiteboard-semantic-cards` 为 0.2.0，保留 `feishu-doc-format-repair` 0.1.0 和 0.8.0 加入的 `feishu-slides-preview-to-pdf` 0.1.0；旧独立名称 `ppt-preview-to-pdf` 仅记录迁移映射，客户端不会自动提供别名，插件调用名为 `$feishu-next:feishu-slides-preview-to-pdf`。原件哈希与归档定位保留在本地迁移记录，不进入公共包。

画板风格 Skill 由 `feishu-whiteboard-design` 改名为 `feishu-whiteboard-semantic-cards`，调用方将旧调用替换为 `$feishu-next:feishu-whiteboard-semantic-cards`。清单的 `legacy_names` 记录旧名用于追溯；客户端不自动提供旧名别名，公共包只保留新目录。此次命名迁移保留绘图组件与设计流程。

此前未发布的 Router 独立拆分已取消，原调用名 `$feishu-next:feishu-workflow-router` 保持不变。Router 0.7.0 增加的官方能力地图与按需上下文协作继续保留，0.8.0 增加显式浏览器截图路由，0.9.0 增加文档格式修复入口，格式对齐升为 0.1.2；两者区分样式对齐与损伤修复，各自包含完整的文档编辑与验收规则。0.10.0 新增画板设计入口，画板运维升为 0.3.2 说明设计稿交接；其余工作流版本不变，详见 metadata 与 CHANGELOG。五个已撤下名称不回到公共清单或 Router，项目快照旧名也不登记为公共别名。

源码提交与 PR 不等于安装更新或版本发布。保持现有 Codex marketplace 协议与名称；本次没有更新客户端安装或执行飞书业务写入。
