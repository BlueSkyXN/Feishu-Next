# Next 工作流与官方 suite 的分工

## 定位

**Feishu Next 把用户的一系列飞书操作串成完整工作流；官方 lark-suite 提供官方能力的统一入口。**

`feishu-workflow-router` 保留在 `plugins/feishu-next/skills/`，调用名仍是
`$feishu-next:feishu-workflow-router`。不再建设独立 Router 插件，不携带官方技能快照，不承担官方技能清单压缩。

| 层次 | 负责什么 |
| --- | --- |
| Next Router | 理解目标、选择或组合玩法、维护步骤依赖和执行上下文、导航到官方能力 |
| Next 具体工作流 | 个人经验沉淀、备份、证据、验证、恢复及交付标准 |
| 官方 lark-suite / 独立 lark-* | 官方领域选择、按需加载指南、原子操作和现成官方工作流 |
| 当前 lark-cli | 实际可执行命令、参数、身份、scope、风险标记和发行版能力边界 |

这些层次是指导职责，不要求新建远程调度服务、后台任务或子代理系统。

## 两类导航与平铺入口

Router 同时提供官方能力地图与 Next 玩法导航。能力地图按五类按需加载，说明能做什么、常见表达、领域边界和 Next 的额外价值；不复制参数表、执行脚本或完整官方教程。

- [云文档与知识库](../plugins/feishu-next/skills/feishu-workflow-router/references/capabilities-documents.md)
- [表格与数据](../plugins/feishu-next/skills/feishu-workflow-router/references/capabilities-data.md)
- [消息与协作](../plugins/feishu-next/skills/feishu-workflow-router/references/capabilities-collaboration.md)
- [演示、白板与应用](../plugins/feishu-next/skills/feishu-workflow-router/references/capabilities-visual-apps.md)
- [认证、事件与扩展](../plugins/feishu-next/skills/feishu-workflow-router/references/capabilities-platform.md)

Router 加七个玩法继续平铺为公开 Skill。每个玩法可以直接触发，正文都指向 Router 的共享协作规则：缺上下文或能力不明时按需查阅；已经在工作流中则复用仍匹配的验证上下文，保留当前步骤归属，回传真实产物与未解决问题。改变目标、身份或写入范围仍需复核，复用不是免除授权。

**归属按额外方法和交付要求判断，不按步骤数判断。** 官方的文档创作、权限治理、资料整理、会议汇总等已经可能是多步流程；完全覆盖时直接复用。能力咨询只回答能力，不要求用户先登录或提供链接。

## 不只是单次导航

以“归档聊天，整理文档，然后发送结果”为例：

1. Next 明确聊天范围、产物形式、目标文档/群、身份及允许的副作用。
2. IM 归档工作流完成分页与证据保存，得到可核验输入。
3. 只有前序产物通过检查，才开始整理文档；创建远程文档必须属于用户授权范围。
4. 只有产物真实存在且目标、发送内容和授权明确，才通过官方 IM 指南发送。
5. Next 汇总哪些步骤已验证、哪些被阻断、哪些写入结果不确定。

因此，导航到 suite 只是某一步获取官方方法，**不是放弃外层任务状态**。重试时不重复创建文档或发送消息；结果不确定先回读。不能把“做完这件事”解释为无限授权。

## 不为单点操作增加负担

如果用户只是查一条消息、读一篇文档，或者官方工作流已完整覆盖需求，可以直接导航到官方能力。
Next 不为简单任务强加一套台账，也不把每一种官方操作复制为自己的 Skill。
直接调用 Next 某个玩法时，Router 只返回所需上下文/能力信息，不重新分派同一个玩法造成循环。

## 安装布局与能力读取

- suite 可见时，读实际安装的入口和选中的 `references/<skill-name>/GUIDE.md`。
- separate 布局下，使用当前实际暴露的官方 `lark-*` 技能。
- 都不可见时，可用 CLI 内嵌文档；但必须承认其不包含全部脚本和 assets，缺少必需资源就报告依赖缺口。
- `lark-cli skills list` 是 CLI 内嵌目录，不是宿主技能安装清单；不能拿它证明 suite 已安装。
- 不自动转换布局，不遍历加载全部官方指南，不维护第二套官方内容。

官方源码的更新日志记录了 v1.0.88 引入 separate/suite 布局、v1.0.96 使用嵌套 `GUIDE.md`。
本项目复用这个职责分工，不把 suite 名称注册成自己的入口。

## 维护边界

更新只能由用户明确指挥 AI 发起。Next 不自动更新自身、CLI 或官方技能，不因发现版本提示就安装、移除或转换全局技能。
源码更新、客户端安装更新、公开发布是三种不同的动作，不相互授权。

## 本地验收场景

- “只规划归档聊天后整理成文档，不要访问远程。”应有两个有依赖的步骤，不执行 API，也不增加发送步骤。
- “读一下这个文档。”应直接导航官方能力，不强加跨步骤台账。
- suite 模式下仅加载目标领域及前置指南，不调用不存在的独立 Skill 工具。
- separate 或 runtime-only 模式下可以继续发现能力，但不宣称 suite 已安装。
- 前序导出失败，后续发送必须阻断；写入超时，先回读再决定重试。

规则检查和本地 help 验证不能替代新会话中的技能发现或真实业务端到端验收。
