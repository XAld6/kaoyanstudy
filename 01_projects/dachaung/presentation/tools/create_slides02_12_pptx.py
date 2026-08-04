from __future__ import annotations

import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]  # presentation/
SRC_DIR = ROOT / "ppt_visuals" / "scheme_c_single_pages"
OUT_DIR = ROOT / "ppt_rebuild" / "slides02_12"
PPTX = OUT_DIR / "huiyan_pages02_12_rebuild.pptx"
PREVIEW_DIR = OUT_DIR / "previews"
WORK_DIR = OUT_DIR / "_pptx"

SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5
EMU = 914400
SLIDE_W_EMU = int(SLIDE_W_IN * EMU)
SLIDE_H_EMU = int(SLIDE_H_IN * EMU)

NAVY = "073F83"
NAVY_DARK = "04316F"
BLUE_TEXT = "205E9F"
TEAL = "129C92"
BLACK = "111111"

PROJECT = "慧眼识裂"
PROJECT_FULL = "基于 OpenClaw 多智能体工作流的基础设施病害智能诊断系统"


SLIDES = [
    {
        "num": 2,
        "title": "项目缘起：基础设施巡检从人工经验走向智能辅助",
        "subtitle": "",
        "mask": (395, 28, 1170, 74),
        "title_pos": (414, 36, 720, 34),
        "title_size": 16,
    },
    {
        "num": 3,
        "title": "现状痛点",
        "subtitle": "基础设施病害识别存在四大共性难题",
        "mask": (405, 22, 820, 78),
        "title_pos": (416, 34, 190, 34),
        "title_size": 18,
    },
    {
        "num": 4,
        "title": "时代机遇：智能巡检正当时",
        "subtitle": "",
        "mask": (405, 22, 820, 78),
        "title_pos": (416, 34, 500, 34),
        "title_size": 18,
    },
    {
        "num": 5,
        "title": "研究内容",
        "subtitle": "构建从图像上传到报告导出的完整闭环",
        "mask": (405, 22, 760, 78),
        "title_pos": (416, 35, 220, 34),
        "title_size": 18,
    },
    {
        "num": 6,
        "title": "技术路线图",
        "subtitle": "从“单点识别”升级为“闭环诊断工作流”",
        "mask": (405, 22, 1100, 78),
        "title_pos": (416, 34, 230, 34),
        "title_size": 18,
    },
    {
        "num": 7,
        "title": "项目创新点",
        "subtitle": "用轻量化方案实现可解释、可复核、可落地的 AI 巡检",
        "mask": (405, 22, 1100, 78),
        "title_pos": (416, 34, 230, 34),
        "title_size": 18,
    },
    {
        "num": 8,
        "title": "进度安排",
        "subtitle": "六阶段递进式实施，稳步推进系统落地",
        "mask": (405, 22, 980, 78),
        "title_pos": (416, 34, 210, 34),
        "title_size": 18,
    },
    {
        "num": 9,
        "title": "预期成果",
        "subtitle": "形成可演示、可复用、可推广的智能巡检原型",
        "mask": (405, 22, 1130, 78),
        "title_pos": (416, 34, 210, 34),
        "title_size": 18,
    },
    {
        "num": 10,
        "title": "经费预算",
        "subtitle": "精准投入，支撑系统开发、测试与展示",
        "mask": (405, 22, 980, 78),
        "title_pos": (416, 34, 210, 34),
        "title_size": 18,
    },
    {
        "num": 11,
        "title": "未来展望",
        "subtitle": "从本地原型走向多场景智能巡检平台",
        "mask": (405, 22, 1120, 78),
        "title_pos": (416, 34, 210, 34),
        "title_size": 18,
    },
    {
        "num": 12,
        "title": "感谢聆听\n敬请指正",
        "subtitle": "AI 初筛，人工把关，闭环留痕",
        "mask": (0, 70, 1020, 535),
        "title_pos": (235, 130, 520, 150),
        "title_size": 31,
        "center": True,
    },
]


def emu(v: float) -> int:
    return int(round(v * EMU))


def px_to_in_x(px: float) -> float:
    return px / 1672 * SLIDE_W_IN


def px_to_in_y(px: float) -> float:
    return px / 941 * SLIDE_H_IN


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def rels(items: list[tuple[str, str, str]]) -> str:
    body = "\n".join(
        f'<Relationship Id="{rid}" Type="{typ}" Target="{escape(target)}"/>'
        for rid, typ, target in items
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        f"{body}\n"
        "</Relationships>"
    )


def solid_fill(color: str) -> str:
    return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'


def rect(sid: int, name: str, x: float, y: float, w: float, h: float, fill: str, radius: bool = False) -> str:
    geom = "roundRect" if radius else "rect"
    return f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
    <a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>
    {fill}<a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
</p:sp>"""


def line(sid: int, name: str, x: float, y: float, w: float, color: str, width_pt: float = 1) -> str:
    return f"""
<p:cxnSp>
  <p:nvCxnSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="0"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="{int(width_pt * 12700)}" cap="sq"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>
  </p:spPr>
</p:cxnSp>"""


def run(text: str, size: float, color: str, bold: bool = False, font: str = "Microsoft YaHei") -> str:
    b = ' b="1"' if bold else ""
    return (
        f'<a:r><a:rPr lang="zh-CN" sz="{int(size * 100)}"{b}>'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="{escape(font)}"/><a:ea typeface="{escape(font)}"/><a:cs typeface="{escape(font)}"/>'
        f'</a:rPr><a:t>{escape(text)}</a:t></a:r>'
    )


def text_box(
    sid: int,
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    lines: list[tuple[str, float, str, bool]],
    align: str = "l",
) -> str:
    ps = []
    for text, size, color, bold in lines:
        ps.append(f'<a:p><a:pPr algn="{align}"/>{run(text, size, color, bold)}<a:endParaRPr lang="zh-CN"/></a:p>')
    return f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/><a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0"/><a:lstStyle/>{"".join(ps)}</p:txBody>
</p:sp>"""


def pic(sid: int, name: str, rid: str) -> str:
    return f"""
<p:pic>
  <p:nvPicPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
  <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
  <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W_EMU}" cy="{SLIDE_H_EMU}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic>"""


def title_shapes(info: dict, sid: int) -> list[str]:
    num = info["num"]
    shapes = []
    if info["num"] != 12:
        mx1, my1, mx2, my2 = (0, 0, 1672, 108)
    else:
        mx1, my1, mx2, my2 = info["mask"]
    shapes.append(rect(sid, "title cleanup mask", px_to_in_x(mx1), px_to_in_y(my1), px_to_in_x(mx2 - mx1), px_to_in_y(my2 - my1), solid_fill("FFFFFF")))
    sid += 1
    tx, ty, tw, th = info["title_pos"]
    title_lines = info["title"].split("\n")
    lines = [(t, info["title_size"], NAVY_DARK, True) for t in title_lines]
    align = "c" if info.get("center") else "l"
    shapes.append(text_box(sid, "editable title", px_to_in_x(tx), px_to_in_y(ty), px_to_in_x(tw), px_to_in_y(th), lines, align=align))
    sid += 1
    if info.get("subtitle"):
        sub_x = tx + (0 if not info.get("center") else -20)
        sub_y = ty + th + (3 if not info.get("center") else 8)
        sub_w = 760 if not info.get("center") else 520
        sub_h = 24
        shapes.append(text_box(sid, "editable subtitle", px_to_in_x(sub_x), px_to_in_y(sub_y), px_to_in_x(sub_w), px_to_in_y(sub_h), [(info["subtitle"], 8.8 if not info.get("center") else 13, BLACK if not info.get("center") else NAVY_DARK, False)], align=align))
        sid += 1
    if num != 12:
        # rebuild the small left page number tile as editable.
        shapes.append(rect(sid, "page tile mask", px_to_in_x(18), px_to_in_y(23), px_to_in_x(65), px_to_in_y(58), solid_fill(NAVY), radius=True))
        sid += 1
        shapes.append(text_box(sid, "editable top number", px_to_in_x(24), px_to_in_y(33), px_to_in_x(50), px_to_in_y(36), [(f"{num:02d}", 18, "FFFFFF", True)], align="c"))
    return shapes


def footer_shapes(num: int, sid: int) -> list[str]:
    y = px_to_in_y(866)
    shapes = [
        rect(sid, "footer cleanup", 0, y, SLIDE_W_IN, px_to_in_y(75), solid_fill("FFFFFF")),
        line(sid + 1, "footer top line", 0, y, SLIDE_W_IN, "E4EFF7", 0.7),
        text_box(sid + 2, "footer project", px_to_in_x(42), px_to_in_y(890), px_to_in_x(132), px_to_in_y(26), [(PROJECT, 12.3, NAVY, True)]),
        line(sid + 3, "footer divider", px_to_in_x(179), px_to_in_y(892), 0, "AFCBE3", 0.8),
        text_box(sid + 4, "footer full project", px_to_in_x(199), px_to_in_y(893), px_to_in_x(610), px_to_in_y(24), [(PROJECT_FULL, 7.3, BLUE_TEXT, False)]),
        text_box(sid + 5, "footer page number", px_to_in_x(1585), px_to_in_y(881), px_to_in_x(62), px_to_in_y(45), [(f"{num:02d}", 21, NAVY, True)], align="c"),
    ]
    return shapes


def slide_xml(info: dict, slide_index: int) -> str:
    shapes = [pic(2, f"slide {info['num']:02d} visual asset", "rId1")]
    shapes += title_shapes(info, 10)
    shapes += footer_shapes(info["num"], 40)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    {"".join(shapes)}
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def build_package() -> None:
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    for p in [
        WORK_DIR / "_rels",
        WORK_DIR / "docProps",
        WORK_DIR / "ppt" / "_rels",
        WORK_DIR / "ppt" / "slides" / "_rels",
        WORK_DIR / "ppt" / "media",
        WORK_DIR / "ppt" / "theme",
        WORK_DIR / "ppt" / "slideMasters" / "_rels",
        WORK_DIR / "ppt" / "slideLayouts" / "_rels",
    ]:
        p.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for idx, info in enumerate(SLIDES, 1):
        src = SRC_DIR / f"slide_{info['num']:02d}.png"
        shutil.copy2(src, WORK_DIR / "ppt" / "media" / f"slide_{info['num']:02d}.png")
        write(WORK_DIR / "ppt" / "slides" / f"slide{idx}.xml", slide_xml(info, idx))
        write(WORK_DIR / "ppt" / "slides" / "_rels" / f"slide{idx}.xml.rels", rels([
            ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", f"../media/slide_{info['num']:02d}.png"),
            ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
        ]))

    slide_overrides = "\n".join(
        f'  <Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, len(SLIDES) + 1)
    )
    write(WORK_DIR / "[Content_Types].xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
{slide_overrides}
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>""")
    write(WORK_DIR / "_rels" / ".rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "ppt/presentation.xml"),
        ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
        ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties", "docProps/app.xml"),
    ]))
    now = datetime.now(timezone.utc).isoformat()
    write(WORK_DIR / "docProps" / "core.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>慧眼识裂 第2-12页复刻</dc:title><dc:creator>Codex</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>""")
    write(WORK_DIR / "docProps" / "app.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex OpenXML Builder</Application><PresentationFormat>Wide</PresentationFormat><Slides>{len(SLIDES)}</Slides>
</Properties>""")
    slide_ids = "\n".join(f'    <p:sldId id="{256+i}" r:id="rId{2+i}"/>' for i in range(len(SLIDES)))
    write(WORK_DIR / "ppt" / "presentation.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>
{slide_ids}
  </p:sldIdLst>
  <p:sldSz cx="{SLIDE_W_EMU}" cy="{SLIDE_H_EMU}" type="wide"/><p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>""")
    rel_items = [("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "slideMasters/slideMaster1.xml")]
    rel_items += [(f"rId{2+i}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", f"slides/slide{i+1}.xml") for i in range(len(SLIDES))]
    rel_items.append((f"rId{2+len(SLIDES)}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "theme/theme1.xml"))
    write(WORK_DIR / "ppt" / "_rels" / "presentation.xml.rels", rels(rel_items))
    write(WORK_DIR / "ppt" / "theme" / "theme1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Huiyan Clean"><a:themeElements><a:clrScheme name="Huiyan"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="073F83"/></a:dk2><a:lt2><a:srgbClr val="EAF4FB"/></a:lt2><a:accent1><a:srgbClr val="073F83"/></a:accent1><a:accent2><a:srgbClr val="129C92"/></a:accent2><a:accent3><a:srgbClr val="2C7CC9"/></a:accent3><a:accent4><a:srgbClr val="F6A21A"/></a:accent4><a:accent5><a:srgbClr val="6EAFCB"/></a:accent5><a:accent6><a:srgbClr val="93A9C4"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="YaHei"><a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface="Arial"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface="Arial"/></a:minorFont></a:fontScheme><a:fmtScheme name="Clean"><a:fillStyleLst><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:srgbClr val="D9E8F4"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>""")
    write(WORK_DIR / "ppt" / "slideMasters" / "slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>""")
    write(WORK_DIR / "ppt" / "slideMasters" / "_rels" / "slideMaster1.xml.rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
        ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "../theme/theme1.xml"),
    ]))
    write(WORK_DIR / "ppt" / "slideLayouts" / "slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld></p:sldLayout>""")
    write(WORK_DIR / "ppt" / "slideLayouts" / "_rels" / "slideLayout1.xml.rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "../slideMasters/slideMaster1.xml"),
    ]))
    if PPTX.exists():
        PPTX.unlink()
    with zipfile.ZipFile(PPTX, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(WORK_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(WORK_DIR).as_posix())


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc") if bold else Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def draw_preview(info: dict) -> Path:
    im = Image.open(SRC_DIR / f"slide_{info['num']:02d}.png").convert("RGB")
    d = ImageDraw.Draw(im)
    if info["num"] != 12:
        mx1, my1, mx2, my2 = (0, 0, 1672, 108)
    else:
        mx1, my1, mx2, my2 = info["mask"]
    d.rectangle((mx1, my1, mx2, my2), fill="white")
    tx, ty, tw, th = info["title_pos"]
    if info.get("center"):
        for j, t in enumerate(info["title"].split("\n")):
            twidth = d.textlength(t, font=font(56, True))
            d.text((tx + (tw - twidth) / 2, ty + j * 64), t, font=font(56, True), fill=f"#{NAVY_DARK}")
        st = info["subtitle"]
        twidth = d.textlength(st, font=font(22, False))
        d.text((tx + (tw - twidth) / 2, ty + 138), st, font=font(22, False), fill=f"#{NAVY_DARK}")
    else:
        d.text((tx, ty), info["title"], font=font(34 if info["num"] == 2 else 36, True), fill=f"#{NAVY_DARK}")
        if info.get("subtitle"):
            d.text((tx + 245, ty + 12), info["subtitle"], font=font(18, False), fill="#222222")
        d.rounded_rectangle((18, 23, 83, 81), radius=7, fill=f"#{NAVY}")
        d.text((26, 33), f"{info['num']:02d}", font=font(33, True), fill="white")
    d.rectangle((0, 866, 1672, 941), fill="white")
    d.line((0, 866, 1672, 866), fill="#E4EFF7", width=1)
    d.text((42, 890), PROJECT, font=font(24, True), fill=f"#{NAVY}")
    d.line((179, 892, 179, 920), fill="#AFCBE3", width=1)
    d.text((199, 893), PROJECT_FULL, font=font(14, False), fill=f"#{BLUE_TEXT}")
    d.text((1585, 881), f"{info['num']:02d}", font=font(40, True), fill=f"#{NAVY}")
    out = PREVIEW_DIR / f"slide_{info['num']:02d}_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return out


def build_previews() -> None:
    if PREVIEW_DIR.exists():
        shutil.rmtree(PREVIEW_DIR)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for info in SLIDES:
        draw_preview(info)
    thumbs = []
    for p in sorted(PREVIEW_DIR.glob("slide_*_preview.png")):
        im = Image.open(p).convert("RGB")
        im.thumbnail((420, 236))
        can = Image.new("RGB", (440, 276), "white")
        can.paste(im, ((440 - im.width) // 2, 28))
        ImageDraw.Draw(can).text((12, 8), p.name, fill=(0, 0, 0))
        thumbs.append(can)
    sheet = Image.new("RGB", (3 * 440, 4 * 276), (245, 245, 245))
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % 3) * 440, (i // 3) * 276))
    sheet.save(OUT_DIR / "pages02_12_preview_contact_sheet.jpg", quality=92)


if __name__ == "__main__":
    build_package()
    build_previews()
    print(PPTX)
    print(PREVIEW_DIR)
