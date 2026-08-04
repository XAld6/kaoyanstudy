from __future__ import annotations

import html
import math
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]  # presentation/
SRC = ROOT / "ppt_visuals" / "scheme_c_single_pages" / "slide_01.png"
OUT_DIR = ROOT / "ppt_rebuild" / "slide01"
ASSET_DIR = OUT_DIR / "assets"
PPTX = OUT_DIR / "slide01_zhizhua_rebuild.pptx"
PREVIEW = OUT_DIR / "slide01_zhizhua_rebuild_preview.png"

SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5
EMU = 914400
SLIDE_W_EMU = int(SLIDE_W_IN * EMU)
SLIDE_H_EMU = int(SLIDE_H_IN * EMU)

NAVY = "073F83"
NAVY_DARK = "04316F"
TEAL = "129C92"
BLUE_TEXT = "205E9F"
LIGHT_BLUE = "DCEBF7"
GRAY_TEXT = "6B7A8F"
BLACK = "111111"


def emu(v: float) -> int:
    return int(round(v * EMU))


def px_to_in_x(px: float) -> float:
    return px / 1672 * SLIDE_W_IN


def px_to_in_y(px: float) -> float:
    return px / 941 * SLIDE_H_IN


def crop_assets() -> dict[str, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SRC).convert("RGB")
    assets = {
        "right_visual": (730, 0, 1672, 864),
        "ai_motif": (0, 610, 355, 864),
        "circuit": (700, 75, 1140, 575),
    }
    paths: dict[str, Path] = {}
    for name, box in assets.items():
        p = ASSET_DIR / f"{name}.png"
        source.crop(box).save(p)
        paths[name] = p
    return paths


def clean_dir() -> Path:
    work = OUT_DIR / "_pptx"
    if work.exists():
        shutil.rmtree(work)
    (work / "_rels").mkdir(parents=True)
    (work / "docProps").mkdir()
    (work / "ppt" / "_rels").mkdir(parents=True)
    (work / "ppt" / "slides" / "_rels").mkdir(parents=True)
    (work / "ppt" / "media").mkdir(parents=True)
    (work / "ppt" / "theme").mkdir(parents=True)
    (work / "ppt" / "slideMasters" / "_rels").mkdir(parents=True)
    (work / "ppt" / "slideLayouts" / "_rels").mkdir(parents=True)
    return work


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


def solid_fill(color: str, alpha: int | None = None) -> str:
    if alpha is None:
        return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
    return f'<a:solidFill><a:srgbClr val="{color}"><a:alpha val="{alpha}"/></a:srgbClr></a:solidFill>'


def shape_rect(
    sid: int,
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    line: str | None = None,
    radius: bool = False,
) -> str:
    geom = "roundRect" if radius else "rect"
    ln = line if line is not None else '<a:ln><a:noFill/></a:ln>'
    return f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
    <a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>
    {fill}
    {ln}
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
</p:sp>"""


def line_shape(sid: int, name: str, x: float, y: float, w: float, color: str, width_pt: float = 3) -> str:
    return f"""
<p:cxnSp>
  <p:nvCxnSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="0"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="{int(width_pt * 12700)}" cap="sq"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>
  </p:spPr>
</p:cxnSp>"""


def tx_run(text: str, size: float, color: str, bold: bool = False, font: str = "Microsoft YaHei") -> str:
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
    paragraphs: list[list[tuple[str, float, str, bool]]],
    anchor: str = "t",
    align: str = "l",
    margin: float = 0,
) -> str:
    ps = []
    for paragraph in paragraphs:
        runs = "".join(tx_run(*run) for run in paragraph)
        ps.append(f'<a:p><a:pPr algn="{align}"/>{runs}<a:endParaRPr lang="zh-CN"/></a:p>')
    return f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/><a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" anchor="{anchor}" lIns="{emu(margin)}" tIns="{emu(margin)}" rIns="{emu(margin)}" bIns="{emu(margin)}"/>
    <a:lstStyle/>
    {"".join(ps)}
  </p:txBody>
</p:sp>"""


def pic(sid: int, name: str, rid: str, x: float, y: float, w: float, h: float, alpha: int | None = None) -> str:
    alpha_mod = f'<a:alphaModFix amt="{alpha}"/>' if alpha is not None else ""
    return f"""
<p:pic>
  <p:nvPicPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
  <p:blipFill><a:blip r:embed="{rid}">{alpha_mod}</a:blip><a:stretch><a:fillRect/></a:stretch></p:blipFill>
  <p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic>"""


def icon_group(start_id: int) -> str:
    labels = ["上传巡检图像", "生成识别", "评估", "复核", "归档", "报告导出"]
    glyphs = ["□", "◇", "◎", "✓", "▣", "▤"]
    parts = []
    x0, y = 0.86, 4.14
    gap = 0.61
    for i, (g, lab) in enumerate(zip(glyphs, labels)):
        x = x0 + i * gap
        parts.append(text_box(start_id + i * 3, f"cap icon {i+1}", x, y, 0.24, 0.19, [[(g, 10.5, TEAL, True)]], align="c"))
        parts.append(text_box(start_id + i * 3 + 1, f"cap label {i+1}", x - 0.16, y + 0.23, 0.58, 0.18, [[(lab, 4.4, BLACK, False)]], align="c"))
        if i < len(labels) - 1:
            parts.append(line_shape(start_id + i * 3 + 2, f"cap line {i+1}", x + 0.25, y + 0.09, 0.22, "6EAFCB", 0.7))
    return "\n".join(parts)


def build_pptx() -> None:
    assets = crop_assets()
    work = clean_dir()
    shutil.copy2(assets["right_visual"], work / "ppt" / "media" / "right_visual.png")
    shutil.copy2(assets["ai_motif"], work / "ppt" / "media" / "ai_motif.png")
    shutil.copy2(assets["circuit"], work / "ppt" / "media" / "circuit.png")

    created = datetime.now(timezone.utc).isoformat()
    write(work / "[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>""")
    write(work / "_rels" / ".rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "ppt/presentation.xml"),
        ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
        ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties", "docProps/app.xml"),
    ]))
    write(work / "docProps" / "core.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>智爪识损 第1页复刻</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>
</cp:coreProperties>""")
    write(work / "docProps" / "app.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex OpenXML Builder</Application><PresentationFormat>Wide</PresentationFormat><Slides>1</Slides>
</Properties>""")

    write(work / "ppt" / "presentation.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>
  <p:sldSz cx="{SLIDE_W_EMU}" cy="{SLIDE_H_EMU}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>""")
    write(work / "ppt" / "_rels" / "presentation.xml.rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "slideMasters/slideMaster1.xml"),
        ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", "slides/slide1.xml"),
        ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "theme/theme1.xml"),
    ]))

    write(work / "ppt" / "theme" / "theme1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Zhizhua Clean">
  <a:themeElements>
    <a:clrScheme name="Office"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F4E79"/></a:dk2><a:lt2><a:srgbClr val="EAF4FB"/></a:lt2><a:accent1><a:srgbClr val="073F83"/></a:accent1><a:accent2><a:srgbClr val="129C92"/></a:accent2><a:accent3><a:srgbClr val="2C7CC9"/></a:accent3><a:accent4><a:srgbClr val="F6A21A"/></a:accent4><a:accent5><a:srgbClr val="6EAFCB"/></a:accent5><a:accent6><a:srgbClr val="93A9C4"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="YaHei"><a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface="Arial"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface="Arial"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Clean"><a:fillStyleLst><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:srgbClr val="D9E8F4"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>""")
    write(work / "ppt" / "slideMasters" / "slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>""")
    write(work / "ppt" / "slideMasters" / "_rels" / "slideMaster1.xml.rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
        ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "../theme/theme1.xml"),
    ]))
    write(work / "ppt" / "slideLayouts" / "slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
</p:sldLayout>""")
    write(work / "ppt" / "slideLayouts" / "_rels" / "slideLayout1.xml.rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "../slideMasters/slideMaster1.xml"),
    ]))

    shapes = []
    shapes.append(shape_rect(2, "white background", 0, 0, SLIDE_W_IN, SLIDE_H_IN, solid_fill("FFFFFF")))
    shapes.append(pic(3, "center circuit texture", "rId3", px_to_in_x(700), px_to_in_y(75), px_to_in_x(440), px_to_in_y(500), 42000))
    shapes.append(pic(4, "bottom-left AI circuit texture", "rId2", px_to_in_x(0), px_to_in_y(610), px_to_in_x(355), px_to_in_y(254), 52000))
    shapes.append(pic(5, "right infrastructure photo collage", "rId1", px_to_in_x(730), 0, px_to_in_x(942), px_to_in_y(864)))
    shapes.append(shape_rect(6, "subtitle cleanup mask", px_to_in_x(680), px_to_in_y(398), px_to_in_x(210), px_to_in_y(92), solid_fill("FFFFFF")))
    shapes.append(shape_rect(7, "top page number tile", px_to_in_x(22), px_to_in_y(26), px_to_in_x(108), px_to_in_y(94), solid_fill(NAVY), radius=True))
    shapes.append(text_box(8, "top page number", px_to_in_x(37), px_to_in_y(48), px_to_in_x(78), px_to_in_y(54), [[("01", 31, "FFFFFF", True)]], align="c"))
    shapes.append(text_box(9, "main title", px_to_in_x(106), px_to_in_y(156), px_to_in_x(590), px_to_in_y(132), [[("智爪识损", 55, NAVY_DARK, True)]], align="l"))
    shapes.append(line_shape(10, "teal title underline", px_to_in_x(108), px_to_in_y(326), px_to_in_x(42), TEAL, 4.2))
    shapes.append(text_box(11, "subtitle", px_to_in_x(108), px_to_in_y(360), px_to_in_x(650), px_to_in_y(115), [[("基于 OpenClaw 的", 23, BLACK, True)], [("基础设施巡检图像智能识别系统", 23, BLACK, True)]], align="l"))
    shapes.append(icon_group(20))
    shapes.append(shape_rect(60, "footer white band", 0, px_to_in_y(864), SLIDE_W_IN, px_to_in_y(77), solid_fill("FFFFFF")))
    shapes.append(line_shape(61, "footer top hairline", 0, px_to_in_y(864), SLIDE_W_IN, "E4EFF7", 0.8))
    shapes.append(text_box(62, "footer brand", px_to_in_x(42), px_to_in_y(888), px_to_in_x(130), px_to_in_y(26), [[("智爪识损", 15.5, NAVY, True)]], align="l"))
    shapes.append(line_shape(63, "footer divider", px_to_in_x(178), px_to_in_y(892), 0, "AFCBE3", 0.9))
    shapes.append(text_box(64, "footer description", px_to_in_x(200), px_to_in_y(891), px_to_in_x(520), px_to_in_y(24), [[("基于 OpenClaw 的基础设施巡检图像智能识别系统", 11.5, BLUE_TEXT, False)]], align="l"))
    shapes.append(text_box(65, "bottom page number", px_to_in_x(1588), px_to_in_y(879), px_to_in_x(62), px_to_in_y(45), [[("01", 23, NAVY, True)]], align="c"))

    slide = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {"".join(shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""
    write(work / "ppt" / "slides" / "slide1.xml", slide)
    write(work / "ppt" / "slides" / "_rels" / "slide1.xml.rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "../media/right_visual.png"),
        ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "../media/ai_motif.png"),
        ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "../media/circuit.png"),
        ("rId4", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
    ]))

    if PPTX.exists():
        PPTX.unlink()
    with zipfile.ZipFile(PPTX, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(work.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(work).as_posix())


def draw_preview() -> None:
    assets = crop_assets()
    scale = 1
    canvas = Image.new("RGB", (1672, 941), "white")
    draw = ImageDraw.Draw(canvas)

    def font(name: str, size: int) -> ImageFont.FreeTypeFont:
        candidates = [
            Path("C:/Windows/Fonts/msyhbd.ttc") if "bold" in name else Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ]
        for c in candidates:
            if c.exists():
                return ImageFont.truetype(str(c), size)
        return ImageFont.load_default()

    ai = Image.open(assets["ai_motif"]).convert("RGB")
    canvas.paste(ai, (0, 610))
    circuit = Image.open(assets["circuit"]).convert("RGB")
    circuit = Image.blend(Image.new("RGB", circuit.size, "white"), circuit, 0.42)
    canvas.paste(circuit, (700, 75))
    right = Image.open(assets["right_visual"]).convert("RGB")
    canvas.paste(right, (730, 0))
    draw.rectangle((680, 398, 890, 490), fill="white")

    draw.rounded_rectangle((22, 26, 130, 120), 8, fill=f"#{NAVY}")
    draw.text((42, 45), "01", font=font("bold", 52), fill="white")
    draw.text((106, 150), "智爪识损", font=font("bold", 110), fill=f"#{NAVY_DARK}")
    draw.line((108, 326, 150, 326), fill=f"#{TEAL}", width=7)
    draw.text((108, 358), "基于 OpenClaw 的", font=font("bold", 43), fill="black")
    draw.text((108, 418), "基础设施巡检图像智能识别系统", font=font("bold", 43), fill="black")

    labels = ["上传巡检图像", "生成识别", "评估", "复核", "归档", "报告导出"]
    glyphs = ["□", "◇", "◎", "✓", "▣", "▤"]
    x0, y = 108, 520
    for i, (g, lab) in enumerate(zip(glyphs, labels)):
        x = x0 + i * 76
        draw.text((x, y), g, font=font("bold", 21), fill=f"#{TEAL}")
        tw = draw.textlength(lab, font=font("regular", 13))
        draw.text((x + 10 - tw / 2, y + 31), lab, font=font("regular", 13), fill="black")
        if i < len(labels) - 1:
            draw.line((x + 29, y + 10, x + 55, y + 10), fill="#6EAFCB", width=1)

    draw.rectangle((0, 864, 1672, 941), fill="white")
    draw.line((0, 864, 1672, 864), fill="#E4EFF7", width=1)
    draw.text((42, 888), "智爪识损", font=font("bold", 28), fill=f"#{NAVY}")
    draw.line((178, 890, 178, 919), fill="#AFCBE3", width=1)
    draw.text((200, 891), "基于 OpenClaw 的基础设施巡检图像智能识别系统", font=font("regular", 24), fill=f"#{BLUE_TEXT}")
    draw.text((1588, 879), "01", font=font("bold", 42), fill=f"#{NAVY}")
    canvas.save(PREVIEW)


if __name__ == "__main__":
    build_pptx()
    draw_preview()
    print(PPTX)
    print(PREVIEW)
