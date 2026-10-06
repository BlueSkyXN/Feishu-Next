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

当前 Feishu Next 工作流插件为 0.7.0，含 Router 加七个平铺工作流，共 8 个 Skill；加上独立鉴权插件全仓共 9 个。此前未发布的 Router 独立拆分已取消，原调用名 `$feishu-next:feishu-workflow-router` 保持不变。Router 0.7.0 增加官方能力地图，导航官方基础使用、Next 玩法或组合任务，不内嵌官方技能。其余工作流对 Router 的引用改为按需协作与上下文复用，各自提升 PATCH，版本详见 metadata 与 CHANGELOG。五个已撤下名称不回到公共清单或 Router，项目快照旧名也不登记为公共别名。

源码提交与 PR 不等于安装更新或版本发布。保持现有 Codex marketplace 协议与名称；本次没有更新客户端安装或执行飞书业务写入。
