import sys
from pypdf import PdfReader
for path in sys.argv[1:]:
    print(f'=== {path} ===')
    reader = PdfReader(path)
    print('pages=', len(reader.pages))
    for i in range(min(3, len(reader.pages))):
        text = reader.pages[i].extract_text() or ''
        print(f'--- page {i+1} ---')
        print(text[:2500])
