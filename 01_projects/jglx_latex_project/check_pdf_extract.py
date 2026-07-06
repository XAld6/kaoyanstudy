import fitz
from pathlib import Path
samples = [
    Path('6.作业&答案/结构力学基础与技巧班第1次作业（几何组成分析）.pdf'),
    Path('6.作业&答案/结构力学基础与技巧班第1次作业答案（几何组成分析）.pdf'),
    Path('6.作业&答案/结构力学基础与技巧班第12次作业及答案（位移法）.pdf'),
    Path('7.作业讲解笔记/【第11次作业笔记】—位移法.pdf'),
]
for pdf in samples:
    doc = fitz.open(pdf)
    print('---', pdf, 'pages', doc.page_count)
    for i in range(min(2, doc.page_count)):
        page = doc[i]
        text = page.get_text('text')
        print('page', i+1, 'text_len', len(text.strip()), 'images', len(page.get_images(full=True)))
        print(text[:800].replace('\n',' | '))
