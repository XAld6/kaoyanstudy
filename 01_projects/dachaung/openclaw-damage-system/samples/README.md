# 演示样例包 samples/

用于答辩演示、回归验证和 `scripts/demo_run.py` 批量跑通。

| 文件 | 场景 | 建议讲解点 |
|------|------|------------|
| `01_plain_surface.png` | 正常表面 | 无显著病害 → 低风险/自动通过 |
| `02_crack_synthetic.png` | 合成裂缝 | 线状候选、红色标注 |
| `03_spalling_synthetic.png` | 合成剥落 | 块状亮斑、橙色标注 |
| `04_stain_synthetic.png` | 合成渗水/色差 | 暗湿斑、蓝色标注 |
| `05_mixed_damage.png` | 混合病害 | 多类型 metrics + 较高风险 |
| `06_sample_crack.png` | 内置裂缝样例 | 快速上传验证 |
| `07_demo_concrete_crack.png` | 混凝土展示图 | 标注图 + PDF 报告演示 |

重新生成合成图：

```powershell
python scripts/build_samples.py
```
