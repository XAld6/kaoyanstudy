from pathlib import Path
HERE = Path(__file__).resolve().parent


from pypdf import PdfReader


PDF_PATH = Path(r"C:\Users\Administrator\Downloads\双创2026-[07]号  关于2026年大学生创新创业训练计划项目立项的通知 .pdf")
OUT_PATH = HERE / "notice_requirements.txt"


def main() -> None:
    reader = PdfReader(str(PDF_PATH))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        pages.append(f"===== PAGE {i} =====\n{text.strip()}\n")

    content = "\n".join(pages)
    OUT_PATH.write_text(content, encoding="utf-8")
    print(f"pages={len(reader.pages)}")
    print(f"chars={len(content)}")
    print(f"output={OUT_PATH}")
    print(content[:4000])


if __name__ == "__main__":
    main()
