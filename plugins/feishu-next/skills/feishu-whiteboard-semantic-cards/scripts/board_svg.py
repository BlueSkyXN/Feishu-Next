"""Small, local SVG layout components for editable Feishu whiteboard designs."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import math
from pathlib import Path
import re
import unicodedata


PALETTE = {
    "blue": ("#2F63E6", "#EDF2FF"),
    "purple": ("#6E55C2", "#F3EFFD"),
    "teal": ("#0F7C72", "#E6F4F1"),
    "orange": ("#D46B08", "#FFF4E6"),
    "red": ("#D83931", "#FDEDEC"),
    "green": ("#2EA121", "#EEF8EC"),
    "slate": ("#3B4452", "#F2F4F7"),
}
INK, SUB = "#1F2329", "#4E5969"


class LayoutError(ValueError):
    """The proposed geometry cannot fit the supplied content."""


def text_width(text: str, size: float) -> float:
    """Conservative estimate, not a measurement of the installed font."""
    return sum(
        0 if unicodedata.combining(c) else size * (
            1 if unicodedata.east_asian_width(c) in "WF" else 0.62
        ) for c in text
    )


def wrap_text(text: str, width: float, size: float) -> list[str]:
    if not math.isfinite(width) or not math.isfinite(size) or size <= 0 or width < size:
        raise LayoutError("Text needs positive font size and at least one full character of width")
    result = []
    for paragraph in str(text).split("\n"):
        paragraph_lines = []
        line = ""
        for token in re.findall(r"[A-Za-z0-9_./@%+\-]+|.", paragraph):
            pieces = list(token) if text_width(token, size) > width else [token]
            for piece in pieces:
                if line and text_width(line + piece, size) > width:
                    carry = ""
                    # Keep closing punctuation with preceding content, and
                    # opening punctuation with the content that follows it.
                    if piece in "，。；：、）】》」』！？,.!?:;)]}" and len(line) > 1:
                        carry, line = line[-1], line[:-1]
                    while len(line) > 1 and line[-1] in "（【《「『([{":
                        carry, line = line[-1] + carry, line[:-1]
                    paragraph_lines.append(line.rstrip())
                    line = carry
                    if text_width(line + piece, size) > width:
                        raise LayoutError("Text column is too narrow to keep punctuation with its content")
                line += piece if line else piece.lstrip()
        paragraph_lines.append(line.rstrip())
        if len(paragraph_lines) > 1 and text_width(paragraph_lines[-1], size) <= size * 2.1:
            previous = paragraph_lines[-2]
            if len(previous) > 1 and unicodedata.east_asian_width(previous[-1]) in "WF":
                moved = previous[-1] + paragraph_lines[-1]
                if text_width(moved, size) <= width:
                    paragraph_lines[-2], paragraph_lines[-1] = previous[:-1], moved
        result.extend(paragraph_lines)
    return result


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def cx(self):
        return self.x + self.width / 2

    @property
    def cy(self):
        return self.y + self.height / 2


class Board:
    def __init__(self, width=1200, margin=40, palette=None):
        if not math.isfinite(width) or not math.isfinite(margin) or margin < 0 or width <= margin * 2:
            raise LayoutError("Canvas width must exceed twice its nonnegative margin")
        self.width, self.margin = width, margin
        self.palette = {**PALETTE, **(palette or {})}
        for colors in self.palette.values():
            if len(colors) != 2 or any(not re.fullmatch(r"#[0-9a-fA-F]{6}", c) for c in colors):
                raise ValueError("Palette entries need two six-digit hexadecimal colors")
        self.elements = []
        self.bottom = 0

    def _bounds(self, x, y, width, height):
        values = (x, y, width, height)
        if not all(math.isfinite(v) for v in values) or min(values) < 0:
            raise LayoutError("Coordinates and dimensions must be finite and nonnegative")
        if x + width > self.width + 0.01:
            raise LayoutError(f"Element at x={x:g} exceeds canvas width {self.width:g}")
        self.bottom = max(self.bottom, y + height)
        return Box(x, y, width, height)

    def box(self, x, y, width, height, *, fill="#FFFFFF", stroke="none", radius=12, dashed=False):
        area = self._bounds(x, y, width, height)
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.elements.append(
            f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
            f'rx="{radius:g}" fill="{escape(fill, quote=True)}" '
            f'stroke="{escape(stroke, quote=True)}" stroke-width="1.5"{dash}/>'
        )
        return area

    def text(self, x, y, width, text, *, size=20, weight=400, color=INK, line_height=None,
             align="left", max_lines=None):
        lines = wrap_text(text, width, size)
        lh = line_height if line_height is not None else size * 1.45
        if not math.isfinite(lh) or lh < size:
            raise LayoutError("Line height must be finite and at least the font size")
        if max_lines is not None and len(lines) > max_lines:
            raise LayoutError(f"Text needs {len(lines)} lines; available: {max_lines}. Rework the layout")
        area = self._bounds(x, y, width, len(lines) * lh)
        if align not in {"left", "center", "right"}:
            raise ValueError("Text align must be left, center or right")
        anchor = {"left": "start", "center": "middle", "right": "end"}[align]
        xx = x if align == "left" else area.cx if align == "center" else area.right
        for index, line in enumerate(lines):
            self.elements.append(
                f'<text x="{xx:g}" y="{y + size + index * lh:g}" font-size="{size:g}" '
                f'font-weight="{weight}" fill="{escape(color, quote=True)}" '
                f'text-anchor="{anchor}">{escape(line)}</text>'
            )
        return area

    def title(self, title, subtitle="", *, tone="blue"):
        m = self.margin
        self.box(m, 30, 8, 42, fill=self.palette[tone][0], radius=4)
        heading = self.text(m + 24, 28, self.width - 2 * m - 24, title, size=34, weight=700)
        end = heading.bottom
        if subtitle:
            end = self.text(m + 24, end + 8, self.width - 2 * m - 24, subtitle,
                            size=18, color=SUB).bottom
        return end + 28

    @staticmethod
    def card_height(width, title, body, *, size=20):
        header = max(60, len(wrap_text(title, width - 40, 24)) * 31 + 24)
        return header + 40 + len(wrap_text(body, width - 40, size)) * size * 1.45

    def card(self, x, y, width, title, body, *, tone="blue", height=None, size=20):
        required = self.card_height(width, title, body, size=size)
        if height is not None and height + 0.01 < required:
            raise LayoutError(f"Card '{title}' needs height {required:g}, received {height:g}")
        h = required if height is None else height
        dark, light = self.palette[tone]
        area = self.box(x, y, width, h, fill="#FFFFFF", stroke=dark)
        header = max(60, len(wrap_text(title, width - 40, 24)) * 31 + 24)
        self.box(x, y, width, header, fill=dark)
        self.box(x, y + header - 12, width, 12, fill=dark, radius=0)
        self.text(x + 20, y + 12, width - 40, title, size=24, line_height=31,
                  weight=700, color="#FFFFFF")
        self.text(x + 20, y + header + 20, width - 40, body, size=size)
        return area

    def band(self, x, y, width, label, body, *, tone="slate"):
        dark, light = self.palette[tone]
        label_w = min(width * 0.32, max(84, text_width(label, 18) + 28))
        label_h = len(wrap_text(label, label_w - 24, 18)) * 26
        body_w = width - label_w - 48
        body_h = len(wrap_text(body, body_w, 20)) * 29
        h = max(label_h, body_h) + 32
        area = self.box(x, y, width, h, fill=light, stroke=dark)
        self.box(x + 12, y + 12, label_w, h - 24, fill=dark, radius=10)
        self.text(x + 24, y + (h - label_h) / 2, label_w - 24, label,
                  size=18, line_height=26, color="#FFFFFF", weight=700, align="center")
        self.text(x + label_w + 28, y + (h - body_h) / 2, body_w, body,
                  size=20, line_height=29)
        return area

    def rail(self, x, y, width, items, *, gap=10):
        if not items or gap < 0:
            raise LayoutError("Navigation needs items and a nonnegative gap")
        cw = (width - gap * (len(items) - 1)) / len(items)
        if cw < 88:
            raise LayoutError("Navigation is too dense; split it, shorten labels or omit it")
        label_lines = max(len(wrap_text(item["label"], cw - 16, 16)) for item in items)
        h = 40 + label_lines * 23 + 12
        area = self._bounds(x, y, width, h)
        for index, item in enumerate(items):
            xx = x + index * (cw + gap)
            dark, light = self.palette[item.get("tone", "blue")]
            active = item.get("active", True)
            self.box(xx, y, cw, h, fill=dark if active else "#FFFFFF",
                     stroke=dark if active else "#B4BAC2", radius=10)
            color = "#FFFFFF" if active else SUB
            self.text(xx + 8, y + 6, cw - 16, str(item["key"]), size=22,
                      weight=700, color=color, align="center", max_lines=1)
            self.text(xx + 8, y + 40, cw - 16, item["label"], size=16,
                      line_height=23, color=color, align="center")
            if item.get("badge"):
                badge = str(item["badge"])
                bw = text_width(badge, 12) + 16
                if bw > cw - 8 or y < 8:
                    raise LayoutError("Navigation badge needs a shorter label or more space")
                self.box(xx + cw - bw - 4, y - 8, bw, 22, fill="#FFFFFF", stroke=dark, radius=11)
                self.text(xx + cw - bw, y - 6, bw - 8, badge, size=12,
                          weight=700, color=dark, align="center", max_lines=1)
        return area

    def connector(self, points, *, tone="slate", dashed=False):
        if len(points) < 2:
            raise LayoutError("A connector needs at least two points")
        for x, y in points:
            self._bounds(x, y, 0, 0)
        x1, y1 = points[-2]
        x2, y2 = points[-1]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 12:
            raise LayoutError("The final connector segment needs at least 12 units for its arrowhead")
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        base_x, base_y = x2 - ux * 10, y2 - uy * 10
        arrow = [(base_x - uy * 5, base_y + ux * 5), (x2, y2),
                 (base_x + uy * 5, base_y - ux * 5)]
        for x, y in arrow:
            self._bounds(x, y, 0, 0)
        color = self.palette[tone][0]
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        path = " ".join(f"{x:g},{y:g}" for x, y in [*points[:-1], (base_x, base_y)])
        triangle = " ".join(f"{x:g},{y:g}" for x, y in arrow)
        self.elements.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="2.2"{dash}/>')
        self.elements.append(f'<polygon points="{triangle}" fill="{color}"/>')

    def to_svg(self):
        height = math.ceil(self.bottom + self.margin)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width:g}" height="{height}" '
                f'viewBox="0 0 {self.width:g} {height}" font-family="Noto Sans SC, PingFang SC, sans-serif">\n'
                f'<rect width="{self.width:g}" height="{height}" fill="#FFFFFF"/>\n'
                + "\n".join(self.elements) + "\n</svg>\n")

    def save(self, path, *, overwrite=False):
        target = Path(path)
        with target.open("w" if overwrite else "x", encoding="utf-8") as handle:
            handle.write(self.to_svg())
        return target
