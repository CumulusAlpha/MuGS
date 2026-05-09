# 3DGS 场景采集教程

End-to-end 教程：自己拍摄 → COLMAP 位姿恢复 → 3DGS 训练 → 落地到 MuGS。

> **何时读这份文档**
> - 现有公开数据集（mip-NeRF 360 / DISCOVERSE / GS-Playground）满足不了你的场景需求
> - 想给 MuGS 加入实验室、家居、工位等自有场景
> - 想了解 MuGS 期望的 PLY + `cameras.json` 数据布局，调试导入失败问题
>
> 只需要现成场景的话，先看 [3DGS_ROOM_DATASETS.md](3DGS_ROOM_DATASETS.md) 和 [ASSET_ACQUISITION.md](ASSET_ACQUISITION.md)。

**Last Updated**: 2026-05-09

---

## 目录

1. [总览：从拍照到 MuGS 的 5 步](#总览)
2. [Step 0 — 决策：自己拍 or 用公开数据](#step-0--决策)
3. [Step 1 — 拍摄：手机 / 相机 / 视频](#step-1--拍摄)
4. [Step 2 — 抽帧（仅视频路线）](#step-2--抽帧)
5. [Step 3 — COLMAP 位姿恢复](#step-3--colmap-位姿恢复)
6. [Step 4 — 3DGS 训练](#step-4--3dgs-训练)
7. [Step 5 — 落地到 MuGS](#step-5--落地到-mugs)
8. [质量检查与常见问题](#质量检查与常见问题)
9. [参考：MuGS 期望的目录结构](#参考-mugs-期望的目录结构)

---

## 总览

```
   拍 50–300 张照片 / 1–3 分钟视频
            │
            ▼
   (视频路线) ffmpeg 抽帧
            │
            ▼
   COLMAP SfM            ─→  sparse/0/{cameras,images,points3D}.bin
            │
            ▼
   3DGS Training         ─→  point_cloud/iteration_30000/point_cloud.ply
            │              + cameras.json + cfg_args
            ▼
   data/custom/<scene>/
            │
            ▼
   GaussianSensorConfig(background_ply_path=...)
```

整套流程在单卡 RTX 3090/4090 上对一个房间场景大约：
- 拍摄 + 整理：**20–40 分钟**
- COLMAP：**10–60 分钟**（视图数和 GPU 而定）
- 3DGS 训练 30k iter：**30–90 分钟**

---

## Step 0 — 决策

| 需求 | 推荐路径 |
|------|---------|
| 复现已有论文 / 跑通 pipeline | 用 mip-NeRF 360 现成场景 |
| 论文 demo 用的标志性场景 | mip-NeRF 360 + 自己拍 1–2 个补充 |
| 实验室自己的桌面 / 工作台 | **本教程**，自己拍 |
| 大批量采集（>20 个场景） | 写 batch 脚本 + 雇人拍，超出本教程范围 |

自采的两个常见误区：
1. **拍得太快太少** — 50 张以下、覆盖不到 360°，COLMAP 注册不上一半图片，训出来全是空洞。
2. **场景里有动态物体** — 风扇、人、屏幕画面、玻璃反光会让 SfM 直接崩。开拍前关掉它们。

---

## Step 1 — 拍摄

### 推荐参数（手机即可）

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 数量 | 100–300 张 | 太少 → 漏洞；太多 → COLMAP 慢 |
| 分辨率 | 1080p–4K | 手机原图就行，不要降采样 |
| 曝光 | **锁定 AE/AF/WB** | 避免每帧自动调亮度，破坏一致性 |
| ISO / 快门 | 固定 ISO，快门 ≥ 1/100s | 避免动态模糊 |
| 重叠率 | 相邻照片 70%+ 视野重叠 | SfM 靠匹配特征点 |
| 距离 | 1–3 m | 太近边缘畸变重 |
| 角度 | 三圈高度 + 仰俯 | 见下图 |

### 推荐拍摄轨迹

```
  视图：俯视场景中心
     高 ●─────●─────●─────●     ← 高位环（举高拍）
        │     │     │     │
     中 ●─────●──★──●─────●     ← 中位环（与目标齐平）★ = 场景中心
        │     │     │     │
     低 ●─────●─────●─────●     ← 低位环（蹲下拍）
```

- **三圈环绕**：高、中、低 三个高度各拍一圈，每圈 20–30 张
- **关键面补拍**：桌面、显示器等关键观察面，多走几步多拍 10–20 张
- **尽量不要原地转动相机** —— 平移比纯旋转有用得多（SfM 靠平移恢复深度）

### 视频路线（懒人版）

如果觉得拍照繁琐，可以**录视频**：
- 用手机以 **1080p 30fps** 录一段 60–120 秒
- 走位同上：三圈环绕 + 关键面贴近
- 全程缓慢平移，**避免快速摇晃**（动态模糊会让 SfM 失败）

视频版到 Step 2 抽帧，照片版直接跳到 Step 3。

### 场景准备 checklist

- [ ] 关掉风扇、空调出风口（防止帘子动）
- [ ] 关掉屏幕，或让屏幕显示静态画面
- [ ] 移走会被人碰到的椅子
- [ ] 光照一致（窗帘拉一致，主光不动）
- [ ] 拍摄期间不让人走进画面

---

## Step 2 — 抽帧

仅视频路线需要。照片路线直接跳到 Step 3。

```bash
# 假设视频在 ~/Downloads/lab.mp4
mkdir -p data/custom/lab/input
ffmpeg -i ~/Downloads/lab.mp4 -qscale:v 2 -vf fps=2 \
    data/custom/lab/input/frame_%04d.jpg
```

参数解释：
- `-qscale:v 2` JPEG 高质量
- `-vf fps=2` 每秒抽 2 帧 → 60s 视频得 120 张，正合适
- 抽完 `ls data/custom/lab/input | wc -l` 确认数量在 100–300 区间

---

## Step 3 — COLMAP 位姿恢复

COLMAP 用 SfM (Structure-from-Motion) 给每张照片估算相机位姿和稀疏点云，是 3DGS 训练的输入。

### 安装

```bash
# Ubuntu
sudo apt install colmap            # 含 GUI + CLI
# 或者 conda
conda install -c conda-forge colmap
```

> 如果有 GPU，COLMAP 默认会调用 SiftGPU 加速。`colmap -h` 应显示 `with CUDA`.

### 一键自动重建

3DGS 官方推荐用 `convert.py`（来自 [graphdeco-inria/gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting)）：

```bash
# 准备数据
DATA=/home/ununtu/metabot-workspace/mugs/data/custom/lab
ls $DATA/input/*.jpg | head -3   # 确认照片在 input/ 下

# 跑 COLMAP（首次需要 clone 一下 3dgs 工具仓库）
git clone https://github.com/graphdeco-inria/gaussian-splatting \
    /home/ununtu/code/gaussian-splatting
cd /home/ununtu/code/gaussian-splatting
python convert.py -s $DATA --no_gpu       # 没 GPU 加 --no_gpu，否则去掉
```

跑完会生成：

```
data/custom/lab/
├── input/                 # 你的原始照片
├── images/                # COLMAP undistort 后的图（训练用）
├── sparse/0/              # SfM 输出
│   ├── cameras.bin
│   ├── images.bin
│   └── points3D.bin
└── stereo/                # 可忽略
```

### 验证 COLMAP 结果

```bash
# 看注册了多少张图（应当 ≥ 输入的 80%）
colmap model_analyzer --path $DATA/sparse/0

# 输出关键指标：
# Cameras: 1
# Images: 142          ← 注册成功的图
# Points: 38291        ← 稀疏点云规模
# Mean track length: 4.83
# Reprojection error: 0.61 px
```

| 指标 | 健康值 | 不健康时 |
|------|--------|---------|
| Images 注册率 | ≥ 80% | < 50%：拍摄重叠不够，重拍 |
| Reprojection error | < 1 px | > 2 px：模糊/动态物体污染 |
| Points | ≥ 10k | 太少：纹理不足，加补光或换背景 |

---

## Step 4 — 3DGS 训练

### 选 backend

| Backend | 用途 | 优点 | 缺点 |
|---------|------|------|------|
| **graphdeco-inria/gaussian-splatting** (官方) | 跑论文复现 / 出 PLY | 输出最稳定，MuGS 直接吃 | CUDA 编译麻烦 |
| **nerfstudio + splatfacto** | 可视化、调参 | 自带 viewer，方便 debug | 输出格式需转换 |
| **gsplat** (Nerfstudio team) | 训练 + 推理库 | 速度快，MuGS 内部用 | 单纯训练入口少 |

新手 / MuGS 路线 **推荐官方仓库**。

### 训练

```bash
cd /home/ununtu/code/gaussian-splatting
pip install -r requirements.txt    # 首次需要

DATA=/home/ununtu/metabot-workspace/mugs/data/custom/lab
OUT=/home/ununtu/metabot-workspace/mugs/data/custom/lab/output

python train.py \
    -s $DATA \
    -m $OUT \
    --iterations 30000 \
    --eval                # 留 1/8 测试集，用来看 PSNR
```

显存占用：
- 1080p, ~150 张 → ~6–8 GB
- 4K, ~150 张 → ~12–16 GB

不够就降分辨率：
```bash
python train.py -s $DATA -m $OUT --resolution 2     # 降一半
```

### 训练产物

```
data/custom/lab/output/
├── cameras.json                       ← MuGS 需要 ★
├── cfg_args
├── input.ply                          ← 初始稀疏点云
└── point_cloud/
    ├── iteration_7000/point_cloud.ply
    └── iteration_30000/point_cloud.ply ← MuGS 需要 ★
```

只有打 ★ 的两个文件 MuGS 真正会用。

### 监控训练

```bash
# 训练日志显示 L1, PSNR, num_gaussians
# PSNR > 25 视为合格；> 30 是好场景
# 高斯数从 ~10k 涨到 1–5M

# 用官方 viewer 看实时效果
./SIBR_viewers/install/bin/SIBR_gaussianViewer_app -m $OUT
```

---

## Step 5 — 落地到 MuGS

MuGS 期望每个场景在 `data/custom/<scene_name>/` 下，目录结构和 `data/pretrained/kitchen/` 完全一致。

### 拷贝产物

```bash
SCENE=lab
SRC=/home/ununtu/metabot-workspace/mugs/data/custom/$SCENE/output
DST=/home/ununtu/metabot-workspace/mugs/data/custom/$SCENE

mkdir -p $DST/point_cloud/iteration_30000
cp $SRC/point_cloud/iteration_30000/point_cloud.ply \
   $DST/point_cloud/iteration_30000/
cp $SRC/cameras.json $DST/
cp $SRC/cfg_args $DST/
cp $SRC/input.ply $DST/      # 可选，方便 debug
```

落地后：

```
data/custom/lab/
├── cameras.json
├── cfg_args
├── input.ply
└── point_cloud/iteration_30000/point_cloud.ply
```

### 在代码里加载

```python
from pathlib import Path
from mugs.sensors import GaussianSensor, GaussianSensorConfig

scene = Path("data/custom/lab")
config = GaussianSensorConfig(
    width=960,
    height=640,
    background_ply_path=scene / "point_cloud" / "iteration_30000" / "point_cloud.ply",
)
sensor = GaussianSensor(config)

# 仿真循环里：
rgb = sensor.render(model, data, camera_name="head_cam")
```

### 与 MuJoCo 世界对齐

3DGS 场景在 COLMAP 世界系下，与 MuJoCo 世界没有先验关系。MuGS 用 **训练相机锚点 + 头摄相对位姿** 的方式对齐（详见主 README *AndroidTwin × MuGS* 章节和 [`CAMERA_ALIGNMENT_FIX.md`](../CAMERA_ALIGNMENT_FIX.md)）。

要点：
1. 在 `cameras.json` 里挑一个**初始视角合适**的训练相机作为锚点（默认用 `id=0`）
2. 启动时让 MuJoCo 头摄初始 pose ≈ 锚点 pose
3. 后续帧用 MuJoCo 头摄相对锚点的 delta，叠加到 GS 锚点上

如果你的 MuJoCo 世界尺度和 COLMAP 不一致（COLMAP 没有真实尺度），需要做一次手动 scale 标定。

---

## 质量检查与常见问题

### 训练完先做 5 项检查

```bash
PLY=data/custom/lab/point_cloud/iteration_30000/point_cloud.ply

# 1. 文件大小 — 健康场景 30–500 MB
ls -lh $PLY

# 2. 高斯数量
python -c "from plyfile import PlyData; \
  print(len(PlyData.read('$PLY')['vertex']))"
# → 应在 500k – 5M

# 3. 用 MuGS 自带 demo 渲一张图
python scripts/demos/render_pretrained.py \
    --ply $PLY \
    --cameras data/custom/lab/cameras.json \
    --out /tmp/check.png

# 4. 肉眼检查 /tmp/check.png 不是糊成一团
# 5. 对比 cameras.json 第 0 个 cam 的视角和原图 input/ 里对应那张
```

### 常见症状

| 症状 | 原因 | 解决 |
|------|------|------|
| COLMAP 注册率 < 50% | 拍摄重叠不够 / 模糊 | 重拍，加大重叠率，固定 ISO |
| 训练 loss 不降 | COLMAP 错误 / 相机参数烂 | 重跑 SfM，查 reprojection error |
| 渲染全是空洞 | 视角覆盖不全 | 补拍漏掉的角度 |
| 渲染像浮云 | 高斯过分裂 | 调 `--densify_grad_threshold` 增大 |
| 训练 OOM | 分辨率太高 | `--resolution 2` 或 4 |
| `cameras.json` 视角错位 | 锚点没选好 | 在 cameras.json 手挑一个朝向接近的 |

### 进阶：mask 掉动态区域

如果场景里实在有不能避免的动态区域（如窗外车流），可以用 [Segment Anything](https://github.com/facebookresearch/segment-anything) 生成 alpha mask，然后用 `--use_alpha_mask` 训练。详见 [`docs/SUPER_RESOLUTION.md`](../SUPER_RESOLUTION.md) 同目录的 mask 方案讨论。

---

## 参考: MuGS 期望的目录结构

> 这套结构兼容 INRIA 官方 3DGS 输出，所以从官方 repo 跑出来的任何场景都能直接用。

```
data/
├── pretrained/
│   └── kitchen/                      ← 已有 mip-NeRF 360 kitchen 作为参考
│       ├── cameras.json
│       ├── cfg_args
│       ├── input.ply
│       └── point_cloud/
│           └── iteration_30000/point_cloud.ply
└── custom/
    └── <your_scene>/                 ← 自己拍的放这里
        ├── cameras.json              ← 训练相机内外参（锚点用）
        ├── cfg_args                  ← 训练超参（可选）
        ├── input.ply                 ← SfM 稀疏点云（可选，debug 用）
        └── point_cloud/
            └── iteration_30000/point_cloud.ply  ← 主资产
```

### `cameras.json` 字段速查

```json
[
  {
    "id": 0,
    "img_name": "DSCF0656",
    "width": 3115, "height": 2078,
    "position": [-3.50, 1.91, -0.73],         // 相机在 COLMAP 世界系下的位置
    "rotation": [[...], [...], [...]],        // 3x3 旋转矩阵 (camera-from-world)
    "fx": 3231.58, "fy": 3240.81              // 焦距（像素）
  },
  ...
]
```

`GaussianSensor` 用这个文件确定锚点相机和初始内参。挑哪一个 `id` 当锚点取决于你 MuJoCo 头摄的初始视角，参考主 README 的 AndroidTwin 例子。

---

## 相关文档

- [3DGS_ROOM_DATASETS.md](3DGS_ROOM_DATASETS.md) — 公开数据集获取
- [ASSET_ACQUISITION.md](ASSET_ACQUISITION.md) — 物体级 PLY 获取
- [QUICK_START.md](QUICK_START.md) — MuGS 15 分钟上手
- [`../CAMERA_ALIGNMENT_FIX.md`](../CAMERA_ALIGNMENT_FIX.md) — GS↔MuJoCo 坐标系对齐细节
- [`../session_9_camera_poses.md`](../session_9_camera_poses.md) — 相机选择实验记录

外部参考：

- [graphdeco-inria/gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting) — 官方实现
- [COLMAP docs](https://colmap.github.io/) — SfM 工具
- [Nerfstudio splatfacto](https://docs.nerf.studio/nerfology/methods/splat.html) — 备选训练 backend
