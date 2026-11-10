#!/usr/bin/env python3
"""校验逐页截图并合成图片型 PDF；不缩放、不去重、不覆盖。"""

import argparse
import math
import os
from pathlib import Path
import re
import sys
import tempfile


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("必须是正整数")
    return number


def positive_float(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("必须是有限正数")
    return number


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-pages", type=positive_int, required=True)
    parser.add_argument("--width", type=positive_int, default=1920)
    parser.add_argument("--height", type=positive_int, default=1080)
    parser.add_argument("--dpi", type=positive_float, default=144.0)
    parser.add_argument("--quality", type=int, choices=range(1, 101), default=90,
                        metavar="1..100")
    return parser.parse_args()


def collect_pages(root, expected):
    if not root.is_dir():
        raise ValueError(f"截图目录不存在：{root}")
    pages = {}
    for path in root.iterdir():
        if not path.name.startswith("slide-"):
            continue
        match = re.fullmatch(r"slide-([0-9]+)\.(png|jpg|jpeg)", path.name)
        if not match or not path.is_file():
            raise ValueError(f"截图命名或类型不合法：{path.name}")
        number = int(match.group(1))
        if number in pages:
            raise ValueError(f"重复页码 {number}：{pages[number].name}、{path.name}")
        pages[number] = path
    wanted = set(range(1, expected + 1))
    missing, extra = sorted(wanted - pages.keys()), sorted(pages.keys() - wanted)
    if missing or extra:
        raise ValueError(f"页码必须恰好为 1..{expected}；缺页={missing}，多余页={extra}")
    return [pages[number] for number in range(1, expected + 1)]


def build_pdf(args):
    from PIL import Image

    output = args.output.absolute()
    if output.suffix.lower() != ".pdf":
        raise ValueError("输出文件必须使用 .pdf 扩展名")
    if output.exists() or output.is_symlink():
        raise ValueError(f"拒绝覆盖已有输出：{output}")
    paths = collect_pages(args.input_dir, args.expected_pages)
    images = []
    temporary = None
    try:
        for path in paths:
            with Image.open(path) as source:
                expected_format = "PNG" if path.suffix == ".png" else "JPEG"
                if source.format != expected_format:
                    raise ValueError(f"编码与扩展名不符：{path.name} 实际为 {source.format}")
                if source.size != (args.width, args.height):
                    raise ValueError(f"尺寸不符：{path.name} 为 {source.size}，"
                                     f"要求 {(args.width, args.height)}")
                source.load()
                if "A" in source.getbands() or "transparency" in source.info:
                    # PDF 统一白底，避免透明区域变黑；不改变像素尺寸。
                    with source.convert("RGBA") as rgba:
                        rgb = Image.new("RGB", source.size, "white")
                        with rgba.getchannel("A") as alpha:
                            rgb.paste(rgba, mask=alpha)
                else:
                    rgb = source.convert("RGB")
                images.append(rgb)

        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".ppt-pdf-", suffix=".pdf",
                                         dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
        images[0].save(temporary, format="PDF", save_all=True,
                       append_images=images[1:], resolution=args.dpi,
                       quality=args.quality)
        # 同目录链接只在目标不存在时成功，避免并发创建时覆盖交付件。
        os.link(temporary, output)
    finally:
        for image in images:
            image.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    print(f"已生成：{output}")
    print(f"页数：{len(paths)}；图片：{args.width}×{args.height} px；"
          f"页面：{args.width / args.dpi * 72:g}×{args.height / args.dpi * 72:g} pt；"
          f"文件：{output.stat().st_size} bytes")
    print("本脚本未验证截图是否对应原文页码；交付前仍需核对内容和裁切。")


def main():
    args = parse_args()
    try:
        build_pdf(args)
    except (OSError, ValueError, ImportError) as error:
        print(f"失败：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
