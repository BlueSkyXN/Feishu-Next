"""Generate synthetic SVG/HTML examples without network, browser or Feishu calls."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

from board_svg import Board, INK, wrap_text


def cards():
    b = Board()
    y = b.title("从材料到可复用方法：四个环节各有产出", "分组卡片｜每张卡回答做什么、何时与留下什么")
    rows = [
        [("A 记录事实", "做什么：记下条件、动作与结果。\n何时：阶段结束或出现关键变化。\n产出：可回查的原始记录。", "purple"),
         ("B 提炼经验", "做什么：选出值得复用的信息。\n何时：有结果或收到专业纠正。\n产出：带来源和适用条件的经验。", "purple")],
        [("C 核对适用", "做什么：确认当前问题是否适用。\n何时：进入相似任务或关键步骤。\n产出：采用、调整或暂缓的判断。", "teal"),
         ("D 持续修订", "做什么：结合来源变化与实际反馈更新。\n何时：信息变化或发现使用偏差。\n产出：有版本依据的修订内容。", "orange")],
    ]
    for row in rows:
        h = max(b.card_height(548, title, body) for title, body, _ in row)
        for col, (title, body, tone) in enumerate(row):
            b.card(40 + col * 572, y, 548, title, body, tone=tone, height=h)
        y += h + 24
    b.band(40, y, 1120, "读图方法", "前两张形成积累，后两张解释如何采用并保持有效。", tone="blue")
    return b


def swimlanes():
    b = Board()
    y = b.title("一次处理如何帮助下一次任务", "泳道与回流｜按阶段阅读，虚线表示反馈进入整理")
    y = b.rail(100, y, 1060, [
        {"key": "A", "label": "记录", "tone": "purple"},
        {"key": "B", "label": "整理", "tone": "orange", "badge": "人审"},
        {"key": "C", "label": "采用", "tone": "teal"},
        {"key": "D", "label": "推广", "tone": "blue", "active": False},
    ]).bottom + 30
    specs = [
        ("形成", "purple", "记录条件与结果", "保留问题、约束、尝试和实际结果。", "补充专业判断", "确认结果及适用范围，补充选择理由。"),
        ("整理", "orange", "形成可查的条目", "把来源、做法与适用范围整理在一起。", "核对重复与矛盾", "由维护者审阅共享内容，再更新入口。"),
        ("采用", "teal", "识别当前需要", "先核对条件，再查找对应的经验或方法。", "记录采用结果", "观察是否适用，将偏差和新条件反馈。"),
    ]
    anchors = []
    for label, tone, t1, c1, t2, c2 in specs:
        h = max(b.card_height(460, t1, c1), b.card_height(460, t2, c2))
        dark, light = b.palette[tone]
        b.box(40, y, 46, h, fill=light, stroke=dark)
        b.text(50, y + h / 2 - 32, 26, label, size=22, weight=700, color=dark)
        left = b.card(110, y, 460, t1, c1, tone=tone, height=h)
        right = b.card(660, y, 460, t2, c2, tone=tone, height=h)
        b.connector([(left.right + 8, left.cy), (right.x - 8, left.cy)], tone=tone)
        anchors.append((left, right))
        y += h + 48
    for first, second in zip(anchors, anchors[1:]):
        b.connector([(first[1].cx, first[1].bottom + 5),
                     (first[1].cx, first[1].bottom + 24),
                     (second[0].cx, first[1].bottom + 24),
                     (second[0].cx, second[0].y - 5)], tone="slate")
    b.connector([(anchors[2][1].right + 6, anchors[2][1].cy), (1144, anchors[2][1].cy),
                 (1144, anchors[1][1].cy), (anchors[1][1].right + 6, anchors[1][1].cy)],
                tone="orange", dashed=True)
    b.band(40, y, 1120, "反馈回流", "采用后的偏差回到整理环节，核实后再修订；推广阶段尚未展开。", tone="orange")
    return b


def comparison():
    b = Board()
    y = b.title("服务请求处理：按相同维度看改进", "比较矩阵｜现状与拟议做法的对照，使用合成内容演示版式")
    xs, widths = [40, 210, 550, 890], [146, 316, 316, 270]
    heads = [("比较维度", "slate"), ("当前情况", "slate"), ("改进动作", "blue"), ("如何检查", "teal")]
    for x, width, (label, tone) in zip(xs, widths, heads):
        dark, _ = b.palette[tone]
        b.box(x, y, width, 60, fill=dark)
        b.text(x + 16, y + 12, width - 32, label, size=22, weight=700, color="#FFFFFF")
    y += 76
    rows = [
        ("入口", "消息分散，缺少统一记录。", "统一登记请求，注明类型与责任人。", "请求是否都能找到对应记录。"),
        ("判断", "优先级依赖临时沟通。", "按影响范围与紧急程度决定次序。", "同类请求是否按相同标准处理。"),
        ("更新", "办理进度与变化通知脱节。", "记录状态变化，向相关方同步进度。", "状态变化是否及时送达。"),
    ]
    for row in rows:
        h = max(len(wrap_text(text, width - 32, 20)) * 29 + 32 for text, width in zip(row, widths))
        for index, (text, x, width) in enumerate(zip(row, xs, widths)):
            b.box(x, y, width, h, fill="#F2F4F7" if index == 0 else "#FFFFFF", stroke="#D0D3D9")
            b.text(x + 16, y + 16, width - 32, text, size=20, line_height=29,
                   weight=700 if index == 0 else 400, color=INK)
        y += h + 16
    b.band(40, y + 12, 1120, "验证方式", "用实际请求记录检查完整性、一致性与送达情况；本图只演示版式。", tone="blue")
    return b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    names = ["cards", "swimlanes", "comparison"]
    destinations = [args.output_dir / f"{name}.{ext}" for name in names for ext in ["svg", "html"]]
    if any(p.exists() for p in destinations):
        parser.error("Output already exists; choose a fresh task directory")
    for name, build in zip(names, [cards, swimlanes, comparison]):
        board = build()
        board.save(args.output_dir / f"{name}.svg")
        page = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
                f'<title>{escape(name)} — whiteboard design</title>'
                '<style>body{margin:0;background:#eef1f5;padding:24px}svg{display:block;'
                'background:white;width:1200px;max-width:100%;height:auto;margin:auto}</style>'
                + board.to_svg() + '</html>')
        (args.output_dir / f"{name}.html").write_text(page, encoding="utf-8")
        print(args.output_dir / f"{name}.svg")


if __name__ == "__main__":
    main()
