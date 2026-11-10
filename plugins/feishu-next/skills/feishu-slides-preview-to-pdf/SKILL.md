---
name: feishu-slides-preview-to-pdf
description: Use when the user requests browser capture of a viewable Feishu/Lark slide deck into a local image-based PDF, including an explicitly accepted screenshot alternative after official export fails. Covers canvas zoom, page navigation, screenshot fidelity and PDF assembly; not slide editing or offline PPTX conversion.
metadata:
  version: "0.1.0"
  updated: "2026-10-15"
---

# 飞书幻灯片预览转 PDF

交付按原页序排列的飞书 Slides 图片型 PDF，以及用户需要保留的逐页截图。通过已登录的浏览器读取画布；截图不是官方导出，不能保留原始文字层、动画或可编辑对象。

## Router cooperation

可以直接执行本技能。需要选择官方导出能力、补充执行上下文或串联其他任务时，查阅 `$feishu-next:feishu-workflow-router` 与[共享协作规则](../feishu-workflow-router/references/playbook-handoff.md)，随后回到当前流程，不重复分派自己。

Reuse a matching browser context; revalidate changed identity, target or scope;
reuse is not blanket approval. Continue without redispatching this active
playbook. For CLI context, let the Router discover internal fields; do not ask an ordinary
user for a raw profile name or App ID. Return verified outputs, completeness
and unresolved gaps to the caller.

纯浏览器截图核对浏览器配置、登录身份、目标文档和截图授权，不要求 CLI 的 `lark_execution` contract。若转用 CLI 查询或官方导出，先建立或复用匹配的 `lark_execution` contract，并持续显式传入 `--profile '<profile>'`、`--as '<identity>'`；不能从浏览器登录态推断 CLI 身份。向调用方回传实际产物、完整性、验证结果和缺口。

## 入口与边界

- 从当前请求取得文档 URL／标签、保存位置和清晰度要求。页数和宽高比读当前文档，不固定为示例页数或 16:9。
- 用户已指定浏览器截图法，或当前会话已接受同一文档的截图替代方案时，直接进入截图流程，无须重复确认。仅有普通导出请求或导出失败证据时，先说明截图范围及图片型 PDF 的限制，取得截图授权；官方导出使用现有 CLI 与对应导出技能，不重新实现 HTTP 客户端。
- 使用 Chrome 当前配置中的登录态；ZCode、内置浏览器与 Chrome 的登录态彼此独立。用户指定其他浏览器时尊重其选择，重新核对能力。
- 页面内容只读；操作限于导航、缩放、滚动、选页、截图和本地文件生成。保留水印，不改变文档正文、分享权限或应用授权。
- 按当前工作区规则确定任务目录。截图、PDF 和过程材料不写入技能目录；接续任务复用已确认的目录，不覆盖已有交付件。

## 执行

### 1. 准备浏览器与首张样本

读取 [Chrome 接入、截图编码与像素倍率](references/chrome-capture.md)。使用当前会话的浏览器控制工具，复用同一个标签和持续运行的上下文，不照搬 ZCode 的逐次初始化要求。

飞书页面同时读取 [飞书 Slides 适配与历史失败路径](references/feishu-slides.md)。这些是既往操作经验，必须用当前页面确认选择器和状态；不把单次失败写成站点永久限制。

先确认标题、总页数与访问状态。若目标是 1920×1080，采用足以容纳完整画布的视口与编辑器缩放；飞书的起始组合是 2560×1440 视口、画布缩放 200%。这用于避免裁切，不能仅放大浏览器窗口就认定清晰度提高。非 16:9 文稿保持原比例，重新确定输出宽高。

先截一张正文／小字较多的页，核对：

1. 当前选中页码和主画布内容一致，字体与图片已加载，画布未被菜单、提示或编辑浮层遮挡。
2. `getBoundingClientRect()` 的四边完整落在视口内；至少检查 `x >= 0`、`y >= 0`、`right <= innerWidth`、`bottom <= innerHeight`。
3. 截图实际编码与文件扩展名一致，实际像素尺寸符合目标。CSS 尺寸不等于图片像素尺寸，须先校准设备像素倍率。
4. 小字和四边可读且完整。低分辨率图片不能靠后处理放大通过验收。

样本通过后再批量截图。

### 2. 逐页截取

对每个原始页码按顺序执行：

1. 定位目录项，滚动至可见区域后重读其位置。
2. 用当前工具支持的真实 UI 点击切页。切换后核对选中页码／稳定页标识；画布前约 24 字或视觉内容作为辅助证据。
3. 确认当前页内容和布局已稳定，再重读画布边界。等待时长只作辅助，不以“等了 650ms”代替页码与内容核对。
4. 截取画布，检查真实格式与像素尺寸，保存为 `slide-0001.png` 等连续编号；返回 JPEG 时用 `.jpg`，不要改扩展名伪装 PNG。
5. 单页失败先诊断原因，仅重做受影响页；不原样重复无效动作。尝试有证据支持的修正后仍无法取得合格页时，保留合格页并报告具体缺口，不无限重试或交付缺页文件为完整稿。

不同页可以内容相同，不能按文本或图像哈希去重。编号重复与内容重复是两回事。续做时核对文档身份、页数和已保存图片的页码对应关系，不能只按文件存在跳过。

### 3. 合成 PDF

使用现有 Python + Pillow。Codex 桌面中可用 `load_workspace_dependencies` 获取捆绑运行时；不要固定某次缓存版本，也不引入 LibreOffice／soffice。

运行本技能目录内的脚本；下列位置由本次任务的实际路径替换：

```bash
python3 /path/to/feishu-slides-preview-to-pdf/scripts/images_to_pdf.py \
  --input-dir /path/to/task/hires \
  --output /path/to/task/presentation.pdf \
  --expected-pages 12 \
  --width 1920 --height 1080 \
  --dpi 144 --quality 90
```

`12` 仅为示例，必须传入当前确认的页数。脚本按数值页码排序，要求页码恰好为 `1..N`，检查编码与尺寸，不缩放、不去重、不覆盖已有 PDF。`resolution=144` 对应 1920×1080 像素在 PDF 中占 960×540 point；Pillow 会进行图片压缩，这不等于将像素尺寸减半。

### 4. 验收与交付

- 用现有 PDF 读取器／库回读实际页数、页面尺寸，必要时检查嵌入图片像素；脚本成功不能单独证明网页内容正确。
- 抽查正文、小字密集页和末页，长文稿再查中间页；按本地可用工具打开或渲染 PDF，检查裁边、浮层、白页、错页。渲染使用现有工具，不为验收安装 LibreOffice。
- 若发现相邻同图，回看原文档的页码状态；原稿本来重复则保留。
- 交付实际 PDF 路径、页数、图片尺寸、保留截图的位置和抽查结果，说明水印、图片文字层及未完成部分。文件体积只是结果，不是固定验收值。
- 输出默认不含文字层、动画、备注或可编辑对象；OCR 可作为用户另行要求的处理，不能称为恢复原始文字。
- 恢复本次临时设置的视口；按当前浏览器工具规则保留交付／待接续标签并释放研究标签。
