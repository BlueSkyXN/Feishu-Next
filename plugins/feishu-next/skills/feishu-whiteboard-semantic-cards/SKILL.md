---
name: feishu-whiteboard-semantic-cards
description: Use when creating or restyling Feishu/Lark whiteboards with Semantic Card Diagrams (语义卡片图解), using semantic colors, modular cards and clear relationship layouts. Supports overviews, workflows, swimlanes and matrices; remote writes and recovery use feishu-whiteboard-ops.
metadata:
  version: "0.2.0"
  updated: "2026-11-10"
---

# 语义卡片图解

用稳定的语义配色、模块化卡片和清晰的关系布局，把材料设计成在目标文档中读得清楚、可继续编辑的画板。交付设计源和检查过的预览；先确定要表达的关系，再安排图形。

## 先确定改动范围

- **美化或匹配样式**：保留已有文案、对象、关系和状态，调整布局与视觉层级；需要删改文字或关系时先核对授权。
- **重组或从材料创作**：按读者要理解的问题组织内容，保留关键事实、条件与来源。用户要求一页、原文不变或局部调整时，把它作为设计约束。
- 已有图先看预览及本地源稿；线上对象的读取与基线导出交给 `$feishu-next:feishu-whiteboard-ops`。参考图可借用配色、组件和疏密，分类、编号和业务关系依据当前材料。
- 输入、读者和交付要求能从上下文推断时直接推进；只询问会改变设计的缺失信息。

## Router cooperation

This playbook can run directly. Consult `$feishu-next:feishu-workflow-router`
only for missing context, capability choices or requested composition,
without redispatching this active playbook. Follow the
[shared handoff rules](../feishu-workflow-router/references/playbook-handoff.md).
Local design and file generation need no CLI authentication. Before CLI business
calls, establish or reuse a matching `lark_execution` contract and preserve
`--profile '<profile>'` and `--as '<identity>'`. Revalidate changed target,
identity or scope; reuse is not blanket approval. Discover internal selectors;
do not ask an ordinary
user for a raw profile name or App ID. Return the design source, inspected preview, authorized scope
and unresolved issues to the caller or whiteboard-ops.

## 设计决策

- **组织内容**：确定读者要看懂的主线，列出必要的对象与关系。结构图呈现归属，流程图呈现动作和交付，比较图使用共同维度；只有材料支持顺序或依赖时才加箭头。
- **选择版式**：需要选择或重构布局时，读 [版式模式](references/layout-patterns.md)。复杂材料可用总图带分镜；一页要求优先，不能自行扩成多张。简单局部调整沿用现有结构。
- **形成视觉语法**：新建风格或统一多张图时，读 [视觉规范](references/design-system.md)。默认采用白底、彩色标题栏、细边框和浅底说明区；参考图与品牌要求优先。同组图让同一颜色、编号和状态标记表达同一含义。
- **控制密度**：先按实际显示宽度安排字号和列数，再处理长文。允许概括时压缩为判断所需的短句，细节下沉到正文或分镜；要求原文保留时增加空间或调整版式。
- **决定导航**：共同分类有助于跨图定位时才加导航条，高亮本图涉及项。项目阶段、能力维度或角色都可作为导航，数量和顺序取自材料。

## 制作与验收

有 `.drawio` 或其他可维护主稿时继续使用。需要 SVG 时，可用 [board_svg.py](scripts/board_svg.py) 的标准库组件，也可按任务生成合适的绘图代码。首次使用组件时读 [绘图与预览](references/svg-workflow.md)，其中提供可执行的起步示例、输出路径设置和可选离线渲染方法。

用实际输入生成源稿；[合成示例](scripts/render_examples.py) 用于学习组件和版式。通过代码绘图时保留生成脚本，方便后续改图。

预览检查两个尺度：整图看阅读路径、对齐和连线；按预期文档显示宽度看正文、标签、断行和对比度。字宽与外框检查不能代替实际渲染，字体替换和飞书转换都可能改变效果。

再与输入核对关键对象、关系、数字、条件和来源。纯美化核对文案与关系保留，重组核对概括后的事实。发现问题回到源稿修订；无法渲染时交付源稿并集中说明未完成视觉检查，先不进入线上写回。

## 交付与飞书写回

仅要求设计时交付源稿、可见预览和必要的读图说明；通过代码绘图时一并交付生成脚本。用户明确要求更新飞书时，将以下内容交给 `$feishu-next:feishu-whiteboard-ops`：

- 检查过的设计源与预览、目标文档/画板及有效上下文；
- 获准新增或替换的区域、应保留内容，以及未解决的问题。

whiteboard-ops 继续负责基线备份、合并/覆盖策略、dry-run、第三方转换工具检查和写后回读。飞书转换后核对显示与所需可编辑结构；接受的线上修订同步回设计源，保持后续修改有据可循。
