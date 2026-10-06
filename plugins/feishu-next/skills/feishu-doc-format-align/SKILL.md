---
name: feishu-doc-format-align
description: Use when aligning Feishu/Lark docx or Wiki section formatting to a reference document, fixing inconsistent table widths, headers or callouts, or changing layout without changing the original text.
metadata:
  version: "0.1.1"
  updated: "2026-10-06"
---

# 飞书文档格式对齐

只改排版，不改正文。输入是目标文档、参考文档或明确的样式要求，以及要修改的章节范围；“看看哪里乱了”只授权诊断。

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

Return the changed range, revision and text/resource comparison result to the caller; a formatting result does not authorize later content edits or publication.

读取当前 `lark-shared`、`lark-doc` 及其 fetch、update、XML 参考；Wiki 入口按当前运行时解析底层对象。API 参数和颜色枚举以当前 CLI 为准，不把本技能当静态 API 文档。

## 流程

1. 按用户范围读取目标与参考的 XML、revision、block ID 和资源引用。使用 `docs +fetch --detail full --doc-format xml`；大文档先定位章节，不默认读取或修改全文。
2. 比较表头加粗/对齐/底色、列宽比例、单元格底色、callout 语义、强调色和空段落。以参考文档为准，不套用某位作者的个人模板或固定像素总宽。
3. 列出格式差异及拟修改块。用户已明确目标、样式和范围时无需重复询问；否则先确认范围。保存私有写前 XML、revision 和文本基线。
4. 从原始 XML 做结构化变换，不手工重打长单元格。多行合并单元格的占位状态跨行传递；逐行核对实际列数、rowspan 和 colspan。不要用自动缩进给单元格注入空白文本。
5. 写前逐段、逐单元格比较文本与资源引用。不得以整表拼接文本相等掩盖错列；不得用删除标点、前缀或数字的“归一化”掩盖正文变化。新增项目符号、改标点或加说明属于内容编辑，须另行授权。
6. 重读目标 revision 和内容；有并发变化时重基变换，不覆盖新内容。对精确 block 操作先执行相同参数的 `--dry-run`，实际写入绑定 `--revision-id`。含无法保真资源的块不整块重建。
7. 同一文档串行更新。每次结构变化后重新定位 block ID，不沿用旧 ID。回读受影响范围，核对文本、顺序、合并单元格、资源和样式。

## 验收

- 默认逐段、逐格正文字符完全一致，资源 token、链接、人员提及和相邻内容保留。
- 用户明确允许分行时，单独记录换行差异；不能据此忽略其他空白或正文变化。
- 纯格式变换失败、`partial_success`、资源降级或并发冲突均不能报完成。回滚同样须使用当前 revision 并遵守写入授权，不盲目覆盖。
- 返回修改范围、样式变化、文本与结构对比结果；仅 CLI 回读不能证明视觉效果已验收。默认不启动浏览器，必要时遵守 Router 的能力缺口与 UI 授权规则。
