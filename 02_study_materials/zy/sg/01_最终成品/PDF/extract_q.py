import fitz
import json
import re

pdf_path = r'D:\xm\02_study_materials\zy\sg\01_最终成品\PDF\施工章节测试_刷题版_答案在最后_新版排版.pdf'
doc = fitz.open(pdf_path)

all_questions = []
chapters = []
current_chapter = None
current_q = None

for page_idx in range(2, 100):
    text = doc[page_idx].get_text()
    page_num = page_idx + 1
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if current_q and current_q.get('qnum') is not None:
            if current_chapter:
                current_chapter['questions'].append(current_q)
            all_questions.append(current_q)
            current_q = None
        if '章' in line and '测试' in line and '第' in line:
            m = re.search(r'(\d+)\s*(.+?)章节测试', line)
            if m:
                current_chapter = {'num': m.group(1), 'name': m.group(2).strip(), 'questions': []}
                chapters.append(current_chapter)
                i += 1
                continue
        q_match = re.match(r'^第(\d+)\s*题(?:单选|多选|不定项)', line)
        if q_match and current_chapter:
            current_q = {'page': page_num, 'ch_num': current_chapter['num'], 'ch_name': current_chapter['name'], 'qnum': q_match.group(1), 'qtype': line, 'text': '', 'options': []}
            i += 1
            continue
        if current_q:
            if re.match(r'^[A-E]$', line):
                letter = line
                opt_text = ''
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if re.match(r'^[A-E]$', next_line):
                        i -= 1
                        break
                    if re.match(r'^第\d+\s*题', next_line):
                        i -= 1
                        break
                    if re.match(r'^\d+$', next_line) or re.match(r'^第\d+页', next_line):
                        i -= 1
                        break
                    if next_line in ['作答区', ''] or '章节数' in next_line or '题目数' in next_line:
                        i -= 1
                        break
                    if next_line:
                        opt_text = opt_text + ' ' + next_line if opt_text else next_line
                    i += 1
                if opt_text:
                    current_q['options'].append({'letter': letter, 'text': opt_text.strip()})
                continue
            if line and line != '作答区' and not re.match(r'^\d+$', line) and not re.match(r'^[A-E]$', line) and '第' + '页' not in line and '章节数' not in line:
                if not current_q['text']:
                    current_q['text'] = line
                else:
                    current_q['text'] += ' ' + line
        i += 1

if current_q and current_q.get('qnum') is not None and current_chapter:
    current_chapter['questions'].append(current_q)
    all_questions.append(current_q)

doc.close()

print(f"Chapters: {len(chapters)}")
for ch in chapters:
    print(f"  Ch{ch['num']}: {ch['name']} - {len(ch['questions'])} questions")
print(f"Total questions: {len(all_questions)}")

with open('all_questions.json', 'w', encoding='utf-8') as f:
    json.dump(all_questions, f, ensure_ascii=False, indent=2)
print("Saved to all_questions.json")
