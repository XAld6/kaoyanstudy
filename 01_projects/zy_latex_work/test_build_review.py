import base64
import tempfile
import unittest
from pathlib import Path

from build_review import build_latex_document, parse_exam_file, scan_exam_files, latex_escape


SAMPLE = """<!doctype html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>样卷</title></head>
<body>
<header><h1>样卷</h1><div class="xy-print-subtitle">课程：桥梁工程</div></header>
<main>
<section class="xy-print-question">
  <h3>1. [单选题]</h3>
  <div class="xy-print-title"><div class="xy-print-rich-text">题干含 50% 与 $ 符号</div></div>
  <figure class="xy-print-image"><figcaption>题图</figcaption><img src="data:image/png;base64,QUJD" alt="题目图片"></figure>
  <div class="xy-print-options">
    <div class="xy-print-option"><div class="xy-print-option-letter">A.</div><div><div class="xy-print-rich-text">选项A</div></div></div>
    <div class="xy-print-option"><div class="xy-print-option-letter">B.</div><div><div class="xy-print-rich-text">选项B</div></div></div>
  </div>
  <div class="xy-print-answer"><strong>答案：</strong>B. 选项B</div>
</section>
</main>
</body></html>"""


class BuildReviewTests(unittest.TestCase):
    def test_parse_exam_file_extracts_question_answer_options_and_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sample.doc"
            src.write_text(SAMPLE, encoding="utf-8")
            exam = parse_exam_file(src, Path(tmp) / "figures")

            self.assertEqual(exam.title, "样卷")
            self.assertEqual(exam.course, "桥梁工程")
            self.assertEqual(len(exam.questions), 1)
            question = exam.questions[0]
            self.assertEqual(question.kind, "单选题")
            self.assertIn("50%", question.prompt)
            self.assertEqual(question.options[1].letter, "B")
            self.assertEqual(question.answer, "B. 选项B")
            self.assertEqual(len(question.images), 1)
            self.assertTrue((Path(tmp) / "figures" / question.images[0].filename).exists())
            self.assertEqual((Path(tmp) / "figures" / question.images[0].filename).read_bytes(), base64.b64decode("QUJD"))

    def test_scan_exam_files_uses_name_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.doc").write_text(SAMPLE.replace("样卷", "B卷"), encoding="utf-8")
            (root / "a.doc").write_text(SAMPLE.replace("样卷", "A卷"), encoding="utf-8")

            exams = scan_exam_files(root, root / "figures")

            self.assertEqual([exam.source_name for exam in exams], ["a.doc", "b.doc"])

    def test_latex_escape_preserves_cjk_and_escapes_specials(self):
        self.assertEqual(latex_escape("桥梁_50% & $"), r"桥梁\_50\% \& \$")

    def test_build_latex_document_can_place_answers_inline_or_appendix(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sample.doc"
            src.write_text(SAMPLE, encoding="utf-8")
            exam = parse_exam_file(src, Path(tmp) / "figures")

            inline_tex = build_latex_document([exam], "inline")
            appendix_tex = build_latex_document([exam], "appendix")

            self.assertIn(r"\begin{answerbox}", inline_tex)
            self.assertNotIn("答案汇总", inline_tex)
            self.assertIn("答案汇总", appendix_tex)
            self.assertIn(r"\begin{answerline}", appendix_tex)
            self.assertIn("figures/", inline_tex)

    def test_option_images_stay_with_options(self):
        html = SAMPLE.replace(
            '<div class="xy-print-rich-text">选项A</div>',
            '<figure class="xy-print-image"><figcaption>[图片]</figcaption><img src="data:image/png;base64,QUJD" alt="题目图片"></figure>',
        )
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sample.doc"
            src.write_text(html, encoding="utf-8")
            exam = parse_exam_file(src, Path(tmp) / "figures")

            self.assertEqual(len(exam.questions[0].images), 1)
            self.assertEqual(len(exam.questions[0].options[0].images), 1)
            self.assertEqual(exam.questions[0].options[0].text, "")


if __name__ == "__main__":
    unittest.main()
