---
name: feishu-base-snapshot-maintain
description: Use when checking or maintaining Feishu/Lark Base weekly snapshots, week-over-week comparisons or monthly closing snapshots, planning missing batches, or resuming a partially applied snapshot plan without rewriting history.
metadata:
  version: "0.1.2"
  updated: "2026-10-06"
---

# 飞书 Base 周月快照维护

将状态检查、计划、写入、恢复和验收分开。通用流程不内置 Base ID、业务字段、时区、脚本路径或历史记录数量；这些由调用方提供，并通过当前 Base 回读核对。本技能不依赖原始业务项目、专用 resource-map 文件或私有 Python 脚本。

## Router cooperation

This playbook can run directly. Consult `$feishu-next:feishu-workflow-router`
for missing verified context, unclear official capability selection, or a
user-requested cross-skill extension. Before business calls, establish or reuse
a matching verified `lark_execution` contract without redispatching this active
playbook. Revalidate changed targets, profile/identity, scope or write authority;
reuse is not blanket approval. Preserve `--profile '<profile>'` and
`--as '<identity>'`; do not ask an ordinary
user for a raw profile name or App ID.

For context checks or workflow handoffs, follow
[the shared rules](../feishu-workflow-router/references/playbook-handoff.md).
Load only required official guidance through the observed suite/separate/runtime
path; reuse already-current reads while retaining command and validation checks.

Return the frozen period, plan/evidence paths, verified batch results and remaining gaps to the caller; do not reinterpret a read-only check as permission to apply.

读取当前 `lark-shared`、`lark-base`，通过 `lark-cli skills list lark-base/references` 发现实际参考，再读所需字段、记录与批量写入说明。项目适配器必须保持同一执行上下文；不支持显式身份延续时停止，不静默使用 CLI 默认值。

## 前置契约

从本次目标、调用方配置和实际表结构确定输入；已有项目 SOP 或适配器时按需读取，但它们不是使用本技能的前置依赖。至少明确：

- 源表、周快照表、对比表、月快照表，以及各自真实字段映射。
- 稳定业务键、快照幂等键、业务时区、周标记、实际冻结日和月末结账定义。
- 新增、停用、改名、合并/拆分、空名称记录及已结账纠错策略。
- 计划与证据目录、授权范围；执行器为可选。没有适配器时按当前官方 `lark-base` 能力编排分页读取、计划与批量写入，不寻找或臆造原项目脚本。

本技能提供 Agent 可执行流程，不附带一键同步器。下表中的 status/plan/apply/validate 是意图模式，不是插件提供的 CLI 子命令。目标表或必需字段不存在时，仅报告缺口，不隐式创建 schema。

## 模式

| 模式 | 行为 |
| --- | --- |
| status | 只读检查记录、缺口、重复键和分页完整性 |
| weekly-plan / monthly-plan | 只读回源，生成差异与拟写入计划 |
| weekly-apply / monthly-apply | 仅执行用户确认的周期、范围及异常策略 |
| validate | 对原计划只读回读验收 |

“看看、检查、为什么”不授权 apply；“维护、刷新、结账”先生成计划，范围和异常口径明确后才能写入。

## 周度流程

1. 展示业务周标记、实际冻结日期和报告使用日期，不混为一个日期；按项目时区及周定义计算。
2. 完整分页读取源数据、前周和目标周；重复业务键、空关键字段、字段漂移或分页中断阻断计划。
3. 对新业务流使用契约指定策略。若契约采用 baseline-zero，则前周关联留空、基准进度为零，并标注“新增基准0”；不能把它误称为真实跨周提升。未定义策略时要求裁决，不自动排除。
4. 改名必须有显式映射；无法证明的合并/拆分不能伪装新增。空记录排除必须有精确 ID 与授权，且补名后旧计划失效。
5. 计划记录来源哈希、映射版本、周期、全部载荷、变更数、异常和排除项。目标周已有部分记录时优先核对原计划，不从当前主表另造一批冻结数据。
6. apply 前重读来源、字段与目标状态；漂移就停止。部分失败只续补同一计划中经回读证明缺失的记录，不能依旧累计计数跳过。
7. baseline-zero 契约下核对“本周快照数 = 常规跨周数 + 新增基准0数”，分别报告两类正增量候选；任何有意不完整的偏离都须明确标注。

## 月度流程

- 日期使用实际数据截至日，明确本次是月内刷新还是月末结账。
- 同月同业务键更新同一记录；新增只进入未结账月份，不自动回填历史。
- 已结账月份不随主表漂移；纠错须精确授权。保留无关键字段的建表空白行及不属本流程的人工字段。
- apply 前复核来源哈希和原计划，写后验证当前月份并检查其他月份未变。

## 安全与完成标准

所有写入先计划、按当前 CLI 支持做 dry-run、确认后小批次串行执行，并完整分页回读。遇到来源漂移、计划外目标记录、公式键重复、字段选项不兼容或部分失败时停止相关批次，保留证据用于续做。

不删除快照、历史或空白记录，不修改 schema、权限、Dashboard 或自动化。Dashboard 布局不属于数据验收。报告实际周期、变更数、恢复状态、完整性和排除口径；将计划及载荷留在私有任务目录，不提交公开仓库。
