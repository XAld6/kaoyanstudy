from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUT_DIR = Path(__file__).resolve().parent
PDF_PATH = OUT_DIR / "顾诗渝_竞赛导向通用实习简历.pdf"
PORTRAIT_PATH = OUT_DIR / "assets" / "portrait.png"

FONT_REGULAR = "NotoSansSC"
FONT_BOLD = "NotoSansSCBold"

NAVY = colors.HexColor("#202b3c")
NAVY_2 = colors.HexColor("#334155")
BLUE = colors.HexColor("#0f6b8f")
GOLD = colors.HexColor("#c9963a")
INK = colors.HexColor("#20242c")
MUTED = colors.HexColor("#5d6675")
LINE = colors.HexColor("#d8dde5")
PAPER = colors.HexColor("#fffdf8")
PANEL = colors.HexColor("#f5f7f9")
WHITE = colors.white


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, r"C:\Windows\Fonts\NotoSansSC-VF.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\simhei.ttf"))


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def side_title(text: str) -> Paragraph:
    return para(text, S["side_title"])


def main_title(text: str) -> Paragraph:
    return para(f"<font color='#c9963a'>▌</font> {text}", S["main_title"])


def bullet(text: str, style_name: str = "bullet") -> Paragraph:
    return para(f"• {text}", S[style_name])


def side_row(label: str, value: str) -> Paragraph:
    return para(f"<b>{label}</b>{value}", S["side_text"])


def project(title: str, date: str, items: list[str]) -> KeepTogether:
    return KeepTogether(
        [
            Table(
                [[para(f"<b>{title}</b>", S["project_title"]), para(date, S["date"])]],
                colWidths=[96 * mm, 25 * mm],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                ),
            ),
            *[bullet(item) for item in items],
        ]
    )


register_fonts()
base = getSampleStyleSheet()
S = {
    "name": ParagraphStyle(
        "name",
        parent=base["Normal"],
        fontName=FONT_BOLD,
        fontSize=25,
        leading=28,
        alignment=1,
        textColor=colors.HexColor("#f7c96b"),
    ),
    "tagline": ParagraphStyle(
        "tagline",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.8,
        leading=10.5,
        alignment=1,
        textColor=colors.HexColor("#dce5ef"),
    ),
    "side_title": ParagraphStyle(
        "side_title",
        parent=base["Normal"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=12,
        textColor=WHITE,
        spaceBefore=8,
        spaceAfter=4,
    ),
    "side_text": ParagraphStyle(
        "side_text",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.5,
        leading=10.1,
        textColor=colors.HexColor("#e7edf5"),
        spaceAfter=1.6,
    ),
    "side_bullet": ParagraphStyle(
        "side_bullet",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.3,
        leading=9.9,
        leftIndent=6,
        firstLineIndent=-6,
        textColor=colors.HexColor("#e7edf5"),
        spaceAfter=1.4,
    ),
    "pill": ParagraphStyle(
        "pill",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=6.8,
        leading=8.4,
        alignment=1,
        textColor=WHITE,
    ),
    "hero_title": ParagraphStyle(
        "hero_title",
        parent=base["Normal"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=16,
        textColor=NAVY,
        spaceAfter=3,
    ),
    "hero": ParagraphStyle(
        "hero",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8.05,
        leading=11.7,
        textColor=colors.HexColor("#3c4656"),
    ),
    "main_title": ParagraphStyle(
        "main_title",
        parent=base["Normal"],
        fontName=FONT_BOLD,
        fontSize=10.2,
        leading=12.4,
        textColor=BLUE,
        spaceBefore=6.5,
        spaceAfter=4,
    ),
    "project_title": ParagraphStyle(
        "project_title",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8.2,
        leading=10.2,
        textColor=NAVY,
    ),
    "date": ParagraphStyle(
        "date",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.2,
        leading=9,
        alignment=2,
        textColor=MUTED,
    ),
    "bullet": ParagraphStyle(
        "bullet",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.45,
        leading=10.4,
        leftIndent=6,
        firstLineIndent=-6,
        textColor=colors.HexColor("#414a59"),
    ),
    "award": ParagraphStyle(
        "award",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=6.85,
        leading=9.3,
        textColor=colors.HexColor("#3d4654"),
    ),
    "campus": ParagraphStyle(
        "campus",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.1,
        leading=9.6,
        textColor=colors.HexColor("#404958"),
    ),
}


def build_sidebar() -> list:
    flow: list = []
    if PORTRAIT_PATH.exists():
        img = Image(str(PORTRAIT_PATH), width=29 * mm, height=38.7 * mm)
        img.hAlign = "CENTER"
        flow.append(img)
        flow.append(Spacer(1, 5))
    flow.append(para("顾诗渝", S["name"]))
    flow.append(para("土木工程本科 ｜ 竞赛与项目执行型候选人", S["tagline"]))
    flow.append(Spacer(1, 5))

    flow.append(side_title("基本信息"))
    for label, value in [
        ("电话：", "13013936376"),
        ("邮箱：", "gsy1193@outlook.com"),
        ("学校：", "宁夏理工学院"),
        ("专业：", "土木工程 本科"),
        ("政治面貌：", "中共预备党员"),
        ("意向城市：", "徐州"),
        ("求职类型：", "实习 / 校园实践"),
    ]:
        flow.append(side_row(label, value))

    flow.append(side_title("求职定位"))
    for item in [
        "通用实习、项目助理、工程资料与申报材料支持",
        "工程建模、数据处理、图像识别项目协作",
        "适合需要执行力、文档能力和跨角色沟通的岗位",
    ]:
        flow.append(bullet(item, "side_bullet"))

    flow.append(side_title("技能标签"))
    pills = [
        "数学建模",
        "Python",
        "OpenCV",
        "Pandas",
        "NumPy",
        "YOLO",
        "OpenClaw",
        "AutoCAD",
        "Revit",
        "MATLAB",
        "Word",
        "Excel",
        "PPT",
        "商业计划书",
    ]
    rows = []
    for i in range(0, len(pills), 2):
        rows.append([para(pills[i], S["pill"]), para(pills[i + 1] if i + 1 < len(pills) else "", S["pill"])])
    flow.append(
        Table(
            rows,
            colWidths=[21.5 * mm, 21.5 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#3b485b")),
                    ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#566579")),
                    ("INNERGRID", (0, 0), (-1, -1), 1.8, NAVY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.3),
                ]
            ),
        )
    )

    flow.append(side_title("证书"))
    for item in ["普通话二级甲等", "计算机二级", "日语 N2", "驾驶证"]:
        flow.append(bullet(item, "side_bullet"))

    flow.append(side_title("教育背景"))
    for line in [
        "<b>2023.08 - 2027.06</b>",
        "宁夏理工学院 ｜ 土木工程",
        "主修：混凝土结构、理论力学、材料力学、结构力学、流体力学",
    ]:
        flow.append(para(line, S["side_text"]))

    return flow


def award_card(text: str) -> Paragraph:
    return para(text, S["award"])


def build_main() -> list:
    flow: list = []
    flow.append(para("个人优势", S["hero_title"]))
    flow.append(
        para(
            "中共预备党员，土木工程本科在读，具备数学建模、工程图像识别、科创项目统筹和材料撰写经验。曾获全国大学生数学建模竞赛全国二等奖、APMCM 亚太地区大学生数学建模竞赛二等奖、节能减排竞赛一等奖等荣誉；能够在数据处理、模型训练、项目申报、商业计划书撰写和团队协作中承担执行型任务。",
            S["hero"],
        )
    )

    flow.append(main_title("竞赛 / 项目经历"))
    for item in [
        project(
            "慧眼识裂 - 基于 OpenClaw 的基础设施裂缝全链路智能诊断与闭环处置系统",
            "2026.01 - 至今",
            [
                "规划项目技术路线与实施步骤，推进数据集构建、模型适配、性能测试和系统闭环设计。",
                "负责核心技术工作，围绕裂缝识别效率与准确率优化算法流程，支撑项目展示与申报材料形成。",
                "结合土木工程安全检测场景，梳理“识别 - 诊断 - 处置 - 反馈”的项目表达逻辑。",
            ],
        ),
        project(
            "智眼识蚜 - 枸杞蚜虫精准防控引领者",
            "2024.11 - 2025.09",
            [
                "制定项目实施计划，明确数据采集、处理、模型训练各阶段时间节点并推进落地。",
                "负责全流程数据处理与模型搭建，协调解决样本标注、参数调优等问题。",
                "参与项目材料整理与成果表达，支持团队完成竞赛申报和展示准备。",
            ],
        ),
        project(
            "智井卫士 - 城市智能监测井盖项目",
            "2025.11 - 至今",
            [
                "独立完成商业计划书撰写，覆盖市场定位、商业模式、运营策略、风险管控等内容。",
                "梳理项目应用场景与落地路径，将工程问题转化为可展示、可申报的项目方案。",
            ],
        ),
    ]:
        flow.append(item)
        flow.append(Spacer(1, 3.5))

    flow.append(main_title("获奖荣誉"))
    awards = [
        "2025 年全国大学生数学建模竞赛全国二等奖",
        "2025 年第十五届 APMCM 亚太地区大学生数学建模竞赛二等奖",
        "2024 年全国大学生数学建模竞赛宁夏赛区一等奖",
        "第二届宁夏大学生节能减排社会实践与科技竞赛一等奖",
        "宁夏第十一届大学生数学建模竞赛暨全国选拔赛二等奖",
        "宁夏第十届大学生数学建模竞赛暨全国选拔赛三等奖",
        "中国国际大学生创新大赛宁夏回族自治区铜奖",
        "第七届中青杯全国大学生数学建模竞赛三等奖",
        "第八届中华职业教育创新创业大赛宁夏选拔赛二等奖",
        "2026 年第十一届全国大学生统计建模大赛校级一等奖",
        "2023-2024、2024-2025 学年校级优秀学生干部",
        "2025-2026 学年校级优秀共青团员",
    ]
    award_rows = []
    for i in range(0, len(awards), 2):
        award_rows.append([award_card(awards[i]), award_card(awards[i + 1] if i + 1 < len(awards) else "")])
    flow.append(
        Table(
            award_rows,
            colWidths=[60 * mm, 60 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                    ("BOX", (0, 0), (-1, -1), 0.25, LINE),
                    ("INNERGRID", (0, 0), (-1, -1), 2.2, PAPER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            ),
        )
    )

    flow.append(main_title("校内经历"))
    campus = [
        "<b>土木工程 23101 班副班长：</b>配合完成班级日常管理，推进学风建设和师生沟通，统筹班级事务协调。",
        "<b>建筑与环境学院团委办公室干事 / 委员：</b>负责团务材料整理归档、团学活动筹备执行，锻炼公文处理与多任务统筹能力。",
        "<b>建筑与环境学院学生党支部督察组委员：</b>负责支部督查相关工作，带动同学参与理论学习。",
    ]
    rows = [[para(text, S["campus"])] for text in campus]
    flow.append(
        Table(
            rows,
            colWidths=[121 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.25, LINE),
                    ("INNERGRID", (0, 0), (-1, -1), 1.5, PAPER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )
    return flow


def build_pdf() -> None:
    page_width, page_height = A4
    doc = BaseDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=0,
        rightMargin=0,
        topMargin=0,
        bottomMargin=0,
    )
    frame = Frame(0, 0, page_width, page_height, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="full", frames=[frame])])

    sidebar = build_sidebar()
    main = build_main()

    side_cell = Table(
        [[sidebar]],
        colWidths=[57 * mm],
        rowHeights=[277 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 12 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8 * mm),
            ]
        ),
    )

    main_cell = Table(
        [[main]],
        colWidths=[133 * mm],
        rowHeights=[277 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 11 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9 * mm),
            ]
        ),
    )

    page = Table(
        [[side_cell, main_cell]],
        colWidths=[63 * mm, 147 * mm],
        rowHeights=[page_height],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )
    doc.build([page])


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
