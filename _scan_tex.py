from pathlib import Path
p = Path(r'D:\xm\latex_review\main.tex')
text = p.read_text(encoding='utf-8')
print('chars', len(text))
print('sections', text.count('\\section{'))
print('subsections', text.count('\\subsection{'))
print('figures', text.count('\\begin{figure}'))
print('tables', text.count('\\begin{table}'))
print('placeholders', text.count('\\placeholder{'))
print('newpages', text.count('\\newpage'))
for s in ['附录','参考文献','摘要','关键词','abstract','bibliography','thebibliography']:
    print(s, text.count(s))
