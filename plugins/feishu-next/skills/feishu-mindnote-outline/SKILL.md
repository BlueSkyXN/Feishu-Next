---
name: feishu-mindnote-outline
description: Use when writing or updating an outline in an existing Feishu/Lark mindnote, fixing duplicate title levels or parent-child relationships, or reconciling a revised chapter tree while preserving existing nodes and notes.
metadata:
  version: "0.1.1"
  updated: "2026-10-06"
---

# 飞书思维笔记大纲维护

在用户指定的同一份思维笔记中维护大纲，不另建笔记、改成画板或改写原文。询问“能访问吗”“结构是否合理”只做只读检查。

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

Return verified node IDs, hierarchy changes and incomplete operations to the caller; do not present a planned move or deletion as completed.

```bash
lark-cli skills read lark-shared
lark-cli skills read lark-doc
lark-cli skills read lark-doc references/lark-doc-mindnote.md
lark-cli mindnotes nodes create --help
lark-cli schema mindnotes.nodes.create
```

需要解析 Wiki 或文件标题时读取当前 `lark-drive`。Wiki token 不是 mindnote token；先确认底层类型。命令/schema 与旧经验冲突时以运行时为准，不猜不存在的删除、排序或主题参数。

## 层级映射

| 大纲对象 | 落位 |
| --- | --- |
| 整份大纲题目 | 文件元数据标题，是界面的隐式根 |
| 章节 | 第一层内容节点，不重复创建题目节点 |
| 小节 | 父引用指向对应章节 |
| 章节说明 | 该节点的 notes，不再创建虚假章节 |

数据是扁平节点数组与父引用，不是嵌套 children。备注可能直接显示，不能承诺默认隐藏。文字高亮不等于分支主题、布局或节点形状。

## 差异更新

1. 读取现有节点与目标大纲；按章节编号、标题及父路径匹配，不按数组位置或全局同名文本盲配。空节点列表不等于文件不存在。
2. 区分原位内容更新、新增、移动与删除。保留未涉及节点的 ID、图片、高亮和完成状态。大纲装饰符不写入，编排指令不作为节点。
3. 有写入时才在任务私有目录保存节点基线和请求；写前比较当前状态，存在并发修改就重算差异。
4. 更新复用已有 node_id；新增先创建父节点再用返回 ID 创建子节点。只传需要改变的字段。相同请求重试复用 client_token，内容或对象变化则换新标识。
5. 内容更新与层级调整分开。省略 parent_id 不代表清空父关系；若当前运行时没有明确清父级语义，停止该结构变更，不用猜测值试错。操作前确认顺序与受影响子树。
6. 对支持的命令用相同请求先 dry-run，按授权执行后只回读必要范围。报错或超时先检查是否部分生效，不盲目重复新增。
7. 删除节点、改文件标题或布局若仍无 CLI 能力，报告精确缺口。只有按 Router 取得对应 UI 动作授权才可使用当前可用浏览器工具；不把网页操作作为默认步骤，也不通过 raw API 绕过拒绝。

## 验收

核对标题/备注与原文、受影响节点数量、父子关系及顺序，确认未涉及属性保留。删除未完成时明确列出，不能清空正文后宣称删除。纯内容更新不做多轮截图；只有看过实际效果才报告视觉验收，内容、层级、元数据与布局是不同结果。
