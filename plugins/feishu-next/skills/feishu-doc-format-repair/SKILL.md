---
name: feishu-doc-format-repair
description: Use when diagnosing and repairing misplaced headings, incorrect grouping of materials, numbering damage or confirmed paste residue in Feishu/Lark Docx. Applies to copied, imported or concatenated content from one or multiple sources. Examples include “标题挂错章节”, “粘贴后出现星号/CSS” and “多篇材料串在一起”. Apply a known reference style with feishu-doc-format-align.
metadata:
  version: "0.1.0"
  updated: "2026-11-07"
---

# 飞书文档格式修复

诊断并修复标题层级错位、材料边界混乱和粘贴残留，保留材料正文，逐项核对获准的结构与文本变化。单份内容的复制、导入也可能造成损伤，多份材料拼接是典型场景。

“格式乱了”先只读诊断：只有样式不统一、需要应用参考或明确规则时，转入 `$feishu-next:feishu-doc-format-align`。用户说“看看”只授权诊断。正文改写、材料合并与去重属于另行授权的内容任务。

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

Return the repaired range, per-batch block counts and revision to the caller; a structural repair does not authorize later content edits or publication.

复用当前 `lark-doc` 的已有文档编辑流程：读取前加载 fetch 参考，准备编辑时再加载 update 与 XML 参考，需要画像统计时读取 script 参考。按身份、输出契约或错误处理需要读取 `lark-shared` 对应参考。通过 [官方导航规则](../feishu-workflow-router/references/official-suite-navigation.md) 使用实际可用的 suite、独立技能或 runtime reads；命令、可回写属性和 revision 行为以当前 CLI 为准。

保留已验证的 profile、identity 和授权范围。Wiki 入口先确认底层对象为 Docx；Sheet/Base 内部数据、独立评论和画板编辑按对应官方领域指南处理。正文标题调整与 Drive 文件名称调整分别处理。

## 流程

1. **建立问题清单**：按 [修复 playbook](references/repair-playbook.md) 从基线清点标题层级、材料归属、编号及疑似残留。结合上下文识别损伤；区分导出标记、原文有意保留的字符和真正的误粘贴。
2. **确定修复方案**：逐项列出问题证据、拟修改块、结构目标和允许的文本差异，包括拟增补或拆分的标题、拟清理的残留。沿用用户已明确的范围和口径，不重复询问。用户指定 H1 时保持 H1；仅调整层级时保留标题原文。
3. **生成局部变换**：按 playbook 处理标题归属、编号、星号或图形残留，记录原块到修改后块的对应关系。证据不足或无法保真的项先保留；短标题加原段落的拆分按已获授权的范围执行。
4. **执行与验收**：按本技能的编辑与回读要求串行写入并回读。核对每项获准差异与未变化内容，完成一轮后重查材料边界和各材料内编号；不以残留计数归零代替正文与资源保真。
5. **交付或继续对齐**：返回已修复项、有意保留项和未解决项。用户同时要求按参考统一样式时，修复验收后将最新快照、revision、块映射和剩余问题交给 align，沿用仍有效的执行上下文；不要重复发现资源或用旧基线覆盖修复。

## 编辑与回读

### 完整编辑基线

- 先通过 outline 或已知锚点确定授权范围，用 `--detail full --doc-format xml` 读取；整体修复确需时才取全文。`with-ids` 可用于定位，不能作为缺少样式和引用的编辑基线。
- 保存完整 JSON 响应，包括同次响应的 XML、revision、block ID、`reference_map` 和提示信息。局部结果含 `excerpt` 时补读拟替换块的完整内容；不以节选重建容器。评论截断或资源降级影响保真时，先补读或暂留相关块。
- 快照、原文和逐次执行结果保存在本地任务目录。诊断清点基于快照，写前复核和写后验收再读取最新状态。

### 变换与写前比对

- 操作清单记录当前 block ID、基准 revision、原 XML、修改后的 XML、依据及允许差异；同一块的多处修改合成一次操作。保留旧块到新块的对应关系，拆分或合并时明确原文去向。
- 从 XML 节点做局部变换，保留未获准修改的块属性、行内样式、链接、人员提及、资源引用和评论锚点。含无法保真资源的块暂不重建；不得转成纯文本或替换为占位内容。
- 按当前 XML 指南检查原始 XML 语法、可回写属性与父容器约束。例如 callout 内不能直接写入标题或 pre；多块替换限同一直接父节点的连续区间。需要调整位置时先确认它属于已授权范围。
- 序列化时保留文本节点、换行和块边界，不手工重打长正文，不对整段 XML 再转义，也不以自动缩进注入空白。逐段、逐格比较完整文本及属性，仅接受本技能列明的获准变化。
- `docs +script parse` 可辅助画像与统计；它会在内存修复部分畸形 XML，`assessment.status=passed` 不能替代原始语法、父容器规则及保真检查。`--dry-run` 用于检查请求参数，实际接受情况仍须写后核对。

### 串行写入与版本复核

每次写前以 `full` 复核目标和必要相邻范围。revision 或内容与基线不符时，读取最新状态并重新生成变换；超出原授权范围的变化再请用户确定。所有替换、插入、删除或恢复均显式传入基准 `--revision-id`，不省略或使用 `-1`。

以下是单块替换的 dry-run 模板；命令和参数先与当前 help 核对：

```bash
lark-cli --profile '<profile>' docs +update --doc '<doc>' --as '<identity>' \
  --command block_replace --block-id '<current-block-id>' \
  --revision-id '<base-revision>' --doc-format xml --content @patch.xml --dry-run
```

payload 使用原响应的临时引用时，按当前参考加 `--reference-map @reference-map.json`；文件内容取自同次基线响应的 `data.document.reference_map`。已有写入授权、dry-run 参数正确且基线仍匹配时，以相同 payload 和参数去掉 `--dry-run` 执行；其间版本变化则重新生成并验证。

同一文档串行更新，批次按可验收范围划分，不硬编码块数。每次结构变化后按旧 ID 已失效处理，写后回读取得当前 revision 和 block ID，再定位后续块；不整批重放旧 ID，也不以调用次数推算 revision 或判断并发。

### 结果、异常与回读

- 按当前 `lark-shared` 输出契约分别保存退出码、stdout 成功信封和 stderr 错误信封。写入需检查 `ok`、`data.result`、实际更新块数、warnings 和 tips；即使 `result=success` 也核对降级提示。日志前缀和顶层 `code` 不作为成功依据。
- 退出码 10 且错误为 `confirmation_required` 时，按官方高风险确认流程处理，不静默追加确认参数。`partial_success`、错误、超时或响应不明时停止后续依赖操作，回读区分已经生效、尚未执行和被外部修改的部分，只为仍获授权的未完成项生成新操作。
- 持续冲突或确认用户正编辑同一区域时暂停该范围写入。回滚也须先核对当前状态并绑定当前 revision；被用户删除的内容只在用户要求恢复时回补。
- 每次写后以 `full` 核对全部修改块及相邻内容。逐段、逐格检查正文字符、换行、顺序与获准差异，同时比较未修改的属性、样式、链接目标、人员提及、资源 token/引用映射与位置、评论锚点。抽样、字数相同或整表拼接文本相等均不足以验收。
- 按本技能的样式目标或修复清单验收，返回已经验证的修改范围、逐批成功/失败块数、最终 revision 和遗留项。局部成功、资源降级及未解决冲突不能报全部完成。
- CLI 回读与视觉验收分别记录。默认不启动浏览器；必要时遵守 Router 的能力缺口与 UI 授权规则，未核验的版式项目交付时列明。

## 验收

- 标题归属、材料边界和编号符合用户口径；无错误挂接或跳级。无既定口径时可建议材料 h1、章 h2、节 h3、小节 h4；允许独立材料重新起号。
- 每项标题增补、拆分、编号或标记清理均与获准清单对应。全部修改块的其余正文、换行和顺序保持一致，资源与相邻内容按本技能的编辑与回读要求核验。
- 已确认且获准修复的问题完成处理；有意保留、证据不足、转换失败和未验证的视觉项目分别列明。是否合并材料、删重或采用某版结论由用户决定。
