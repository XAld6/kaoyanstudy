# presentation — 答辩展示

## 结构

```text
presentation/
├── ppt_rebuild/     # 重建后的 PPT 成品与预览
├── ppt_visuals/     # 单页视觉稿 / OCR 参考
└── tools/           # 从视觉稿生成 PPT 的脚本
```

## 成品位置

- 首页：`ppt_rebuild/slide01/slide01_zhizhua_rebuild.pptx`
- 第 2–12 页：`ppt_rebuild/slides02_12/huiyan_pages02_12_rebuild.pptx`
- 单页预览：`ppt_visuals/scheme_c_single_pages/slide_01.png` … `slide_12.png`

## 重新生成（可选）

```powershell
cd D:\xm\01_projects\dachaung\presentation
python tools\create_slide01_pptx.py
python tools\create_slides02_12_pptx.py
```

脚本以 `presentation/` 为根目录解析 `ppt_visuals` 与 `ppt_rebuild`。
