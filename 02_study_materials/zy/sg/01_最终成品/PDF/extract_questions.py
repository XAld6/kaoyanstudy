import os, re, json

base = r'D:\xm\02_study_materials\zy\sg\01_最终成品\PDF'

chapters = []
current_chapter = None
current_question = None
all_questions = []
i = 0

for p in range(3, 101):
    path = os.path.join(base, f'extracted_page_{p:03d}.txt')
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    lines = text.split('\n')
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        i += 1
        
        # Save last question before switching chapters
        if current_question and current_question.get('qnum'):
            current_chapter['questions'].append(current_question)
            all_questions.append(current_question)
            current_question = None
        
        # Chapter header: "第一章土方工程章节测试"
        if '章' in line and '测试' in line:
            ch_match = re.search(r'(\d+)\s*(.+?)章节测试', line)
            if ch_match:
                current_chapter = {'num': ch_match.group(1), 'name': ch_match.group(2).strip(), 'questions': []}
                chapters.append(current_chapter)
                continue
        
        # Question header: "第1 题单选题" or "第2 题多选题"
        q_match = re.match(r'^第(\d+)\s*题(?:单选|多选|不定项)', line)
        if q_match and current_chapter:
            current_question = {
                'page': p,
                'ch_num': current_chapter['num'],
                'ch_name': current_chapter['name'],
                'qnum': q_match.group(1),
                'qtype': line,
                'text': '',
                'options': [],
            }
            continue
        
        if current_question:
            # Single letter on its own line followed by option text on next line
            if re.match(r'^[A-E]$', line) and i < n:
                letter = line
                opt_text = ''
                # Collect option text - might span multiple lines
                while i < n:
                    next_line = lines[i].strip()
                    i += 1
                    # Stop if we hit a new option letter, question header, page number, or special marker
                    if re.match(r'^[A-E]$', next_line):
                        # Put back - this is next option letter
                        i -= 1
                        break
                    if re.match(r'^第\d+\s*题', next_line):
                        i -= 1
                        break
                    if re.match(r'^\d+$', next_line) or re.match(r'^第\d+页', next_line) or next_line in ['作答区', '', '章节数', '题目数']:
                        i -= 1
                        break
                    if opt_text == '':
                        opt_text = next_line
                    else:
                        opt_text += ' ' + next_line
                
                if opt_text:
                    current_question['options'].append({'letter': letter, 'text': opt_text})
                continue
            
            # Question body text
            if line and line not in ['作答区', ''] and not re.match(r'^第\d+题', line) and not re.match(r'^\d+$', line) and not re.match(r'^[A-E]$', line):
                if len(current_question['text']) == 0:
                    current_question['text'] = line
                else:
                    current_question['text'] += ' ' + line

# Save last question
if current_question and current_question.get('qnum'):
    if current_chapter:
        current_chapter['questions'].append(current_question)
    all_questions.append(current_question)

print('Total chapters:', len(chapters))
for ch in chapters:
    print(f"  Chapter {ch['num']}: {ch['name']} - {len(ch['questions'])} questions")
print('Total questions:', len(all_questions))

# Save
with open(os.path.join(base, 'all_questions.json'), 'w', encoding='utf-8') as f:
    json.dump(all_questions, f, ensure_ascii=False, indent=2)
print('Saved to all_questions.json')
