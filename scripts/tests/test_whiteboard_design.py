"""Check observable layout and file behavior with synthetic content only."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


SCRIPTS = (Path(__file__).resolve().parents[2] / "plugins/feishu-next/skills"
           / "feishu-whiteboard-semantic-cards/scripts")
spec = importlib.util.spec_from_file_location("board_svg", SCRIPTS / "board_svg.py")
svg = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = svg
spec.loader.exec_module(svg)


class WhiteboardDesignTests(unittest.TestCase):
    def test_wrap_preserves_content_and_fits_cjk_and_long_english(self):
        text = "核对 InteroperabilityAndConfiguration 与版本"
        lines = svg.wrap_text(text, 150, 20)
        self.assertEqual("".join(text.split()), "".join("".join(lines).split()))
        self.assertTrue(all(svg.text_width(line, 20) <= 150.01 for line in lines))

    def test_text_escaping_and_content_driven_canvas(self):
        b = svg.Board()
        b.text(40, 500, 800, 'A < B & C > D "校验"')
        root = ET.fromstring(b.to_svg())
        self.assertGreater(float(root.get("height")), 500)
        self.assertIn('A < B & C > D "校验"', "".join(root.itertext()))

    def test_chinese_wrap_avoids_orphaned_punctuation_and_single_character_tail(self):
        text = "用索引组织主题，保留原始来源。"
        lines = svg.wrap_text(text, 284, 20)
        self.assertEqual(text, "".join(lines))
        self.assertTrue(all(not line.startswith(tuple("，。；：、）！？")) for line in lines))
        self.assertGreater(len(lines[-1].rstrip("，。；：、）！？")), 1)
        self.assertTrue(all(svg.text_width(line, 20) <= 284 for line in lines))

    def test_fixed_card_overflow_fails_before_truncating(self):
        b = svg.Board()
        body = "保留来源、条件和动作。" * 15
        with self.assertRaises(svg.LayoutError):
            b.card(40, 100, 260, "说明", body, height=100)
        area = b.card(40, 100, 260, "说明", body)
        self.assertGreater(area.height, 100)
        text = "".join(ET.fromstring(b.to_svg()).itertext())
        self.assertIn(body, text.replace("\n", ""))

    def test_dense_navigation_and_text_line_limit_fail(self):
        b = svg.Board()
        with self.assertRaises(svg.LayoutError):
            b.rail(40, 100, 1120, [{"key": str(i), "label": "阶段"} for i in range(20)])
        with self.assertRaises(svg.LayoutError):
            b.text(40, 100, 120, "详细说明" * 10, max_lines=2)

    def test_navigation_accepts_non_numeric_keys_and_custom_palette(self):
        b = svg.Board(palette={"phase": ("#123456", "#F0F2F4")})
        b.rail(40, 100, 1120, [
            {"key": "A", "label": "形成", "tone": "phase"},
            {"key": "B", "label": "采用", "active": False},
        ])
        source = b.to_svg()
        self.assertIn("#123456", source)
        self.assertIn("形成", "".join(ET.fromstring(source).itertext()))

    def test_invalid_geometry_and_degenerate_connector_fail(self):
        b = svg.Board()
        for args in [(1190, 0, 100, 20), (40, -1, 10, 10), (40, 10, float("nan"), 20)]:
            with self.assertRaises(svg.LayoutError):
                b.box(*args)
        with self.assertRaises(svg.LayoutError):
            b.connector([(40, 50), (40, 50)])

    def test_save_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "design.svg"
            svg.Board().save(path)
            with self.assertRaises(FileExistsError):
                svg.Board().save(path)

    def test_examples_generate_parseable_local_artifacts_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            argv = [sys.executable, str(SCRIPTS / "render_examples.py"), "--output-dir", folder]
            result = subprocess.run(argv, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            files = sorted(Path(folder).glob("*.svg"))
            self.assertEqual(3, len(files))
            for path in files:
                ET.parse(path)
                self.assertTrue(path.with_suffix(".html").exists())
            before = {p: p.read_bytes() for p in Path(folder).iterdir()}
            result = subprocess.run(argv, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(before, {p: p.read_bytes() for p in Path(folder).iterdir()})


if __name__ == "__main__":
    unittest.main()
