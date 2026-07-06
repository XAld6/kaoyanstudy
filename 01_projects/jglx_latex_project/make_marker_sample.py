from pathlib import Path
import fitz

src = Path(r"D:/xm/zy/jglx/6.作业&答案/结构力学基础与技巧班第1次作业（几何组成分析）.pdf")
out = Path(r"D:/xm/zy/jglx/marker_test")
out.mkdir(exist_ok=True)
doc = fitz.open(src)
new = fitz.open()
new.insert_pdf(doc, from_page=0, to_page=0)
new.save(out / "chapter01_problem_page1.pdf")
print(out / "chapter01_problem_page1.pdf")
