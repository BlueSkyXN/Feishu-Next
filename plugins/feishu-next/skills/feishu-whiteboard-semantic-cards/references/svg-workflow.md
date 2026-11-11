# SVG 绘图与预览

## 路径与组件

先将 `SKILL_DIR` 设为本轮读取的 `SKILL.md` 所在目录，`TASK_DIR` 设为已确定并创建的本次产物目录。下面的命令使用这两个实际路径；不依赖当前工作目录或其他项目的脚本。

`scripts/board_svg.py` 只依赖 Python 标准库，提供可组合的绘图组件。它保留独立文字和简单图形，估算字宽与外框尺寸，不自动避让连线或检测图形重叠。

## 从实际材料生成图

以下是起步代码，保存为任务目录里的 `draw_diagram.py`，再按输入修改对象、文字和关系。同排卡片先取最长内容的高度，连线使用卡片返回的几何位置。

```python
import sys
from board_svg import Board

board = Board(width=1200)
y = board.title("从材料到可复用方法", "说明形成、检查与采用之间的关系")
items = [
    ("形成记录", "保存问题、条件、动作与结果。", "purple"),
    ("检查适用", "核对来源与适用范围，再决定是否采用。", "teal"),
]
height = max(board.card_height(520, title, body) for title, body, _ in items)
cards = [
    board.card(x, y, 520, title, body, tone=tone, height=height)
    for x, (title, body, tone) in zip((40, 640), items)
]
a, b = cards
board.connector([(a.right + 6, a.cy), (b.x - 6, a.cy)], tone="slate")
board.save(sys.argv[1])
```

从任意任务工作目录运行，显式提供模块位置与产物路径：

```bash
PYTHONPATH="$SKILL_DIR/scripts" python3 "$TASK_DIR/draw_diagram.py" "$TASK_DIR/diagram.svg"
```

- 坐标单位与 SVG 画布一致，`text()` 的 y 为文字框顶部。
- `text(..., max_lines=...)` 和过小的固定卡片会抛出 `LayoutError`；调整空间，或在获准概括时精炼内容。
- `rail()` 接受任意数量的 `{key, label, tone, active, badge}` 项。空间不足时拆行、简化或省略导航，不自动缩成小字。
- `box()`、`text()` 可组成矩阵；`connector()` 接受折线坐标，可设置虚线。
- `Board(palette=...)` 可覆盖色系，值为 `(主色, 浅底)` 的十六进制颜色对。
- `save()` 根据内容确定高度，默认拒绝覆盖已有文件；迭代使用任务内的新文件名或明确指定 `overwrite=True`。

需要更多组件用法时看 `scripts/render_examples.py`；下面命令生成分组卡片、泳道回流、比较矩阵三种合成 SVG 和对应 HTML，仅作为绘图参考：

```bash
python3 "$SKILL_DIR/scripts/render_examples.py" --output-dir "$TASK_DIR/component-examples"
```

## 选择现有预览能力

使用宿主允许的浏览器预览或已安装的离线 SVG 渲染器。浏览器适合检查实际字体和缩放；离线渲染适合直接产生可查看图片。按环境选可用路径，不为预览自动安装软件。

例如环境已提供 PyMuPDF 时，可将以下代码存为任务目录里的 `preview_svg.py`：

```python
import sys
import fitz

with fitz.open(sys.argv[1]) as document:
    document[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(sys.argv[2])
```

```bash
python3 "$TASK_DIR/preview_svg.py" "$TASK_DIR/diagram.svg" "$TASK_DIR/diagram.png"
```

打开生成的图像，核对中文、符号、断行和连线，并按最终显示宽度检视。离线字体可能与浏览器及飞书不同；后续仍以目标画板的实际结果核对保真。缺少渲染能力时说明未完成视觉检查。

## 进入飞书

保留 SVG 和生成脚本作为后续修改的入口，将源稿、已检查的预览、目标和获准范围交给 `feishu-whiteboard-ops`。文字、矩形、折线等简单元素有利于转换；复杂滤镜、外链资源或字体效果可能导致局部图像化，按实际转换结果调整源稿。
