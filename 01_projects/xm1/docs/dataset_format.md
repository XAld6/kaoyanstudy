# 外墙缺陷数据集格式说明

## 目录结构

真实数据按 YOLO 格式放入 `data/datasets/wall_defects/`：

```text
data/datasets/wall_defects/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
```

每张图片对应一个同名 `.txt` 标注文件。例如：

```text
images/train/wall_001.jpg
labels/train/wall_001.txt
```

## 类别编号

```text
0 crack
1 peeling
2 seepage
3 hollowing
```

## 标注格式

每一行表示一个目标框：

```text
class_id x_center y_center width height
```

坐标均为 0 到 1 之间的归一化值。

示例：

```text
0 0.512 0.438 0.083 0.421
1 0.332 0.685 0.214 0.180
```

## 标注建议

- 裂缝：框住可见裂缝主体和明显分支。
- 脱落：框住墙皮脱落或裸露基层区域。
- 渗水：框住水痕、霉斑或明显潮湿区域。
- 鼓包空鼓：框住鼓起、起壳、局部变形区域。
- 图片建议覆盖不同距离、光照、楼层、材质和天气。

## 训练命令

建议使用 Python 3.10 或 3.11 安装训练依赖：

```bash
pip install -r requirements-yolo.txt
```

```bash
python scripts\train.py --epochs 80 --imgsz 960 --batch 8
```

训练完成后，将最优权重复制到：

```text
data/models/best.pt
```
