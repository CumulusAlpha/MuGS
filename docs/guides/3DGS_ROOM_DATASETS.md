# 3DGS Room/Scene Datasets

完整房间场景资产获取指南

## 公开数据集

### 1. Mip-NeRF 360 Dataset (推荐)

**描述**: 室内外高质量场景，包含完整房间

**场景**:
- `room` - 办公室/房间
- `counter` - 厨房台面
- `kitchen` - 完整厨房
- `bonsai` - 盆景（室内）
- `garden`, `bicycle`, `stump` (户外)

**获取方式**:
```bash
# 下载脚本
wget http://storage.googleapis.com/gresearch/refraw360/360_v2.zip
unzip 360_v2.zip

# 或使用官方链接
# https://jonbarron.info/mipnerf360/
```

**格式**: 
- 多张RGB图片 + camera poses
- 需要训练3DGS模型（COLMAP → 3DGS training）

**优点**: 
- ✅ 高质量室内场景
- ✅ 完整房间布局
- ✅ 官方支持

**缺点**:
- ⚠️ 需要训练（~1-2小时/场景）
- ⚠️ 文件较大（~1-2GB/场景）

---

### 2. NeRF Synthetic Dataset

**描述**: 合成场景，包含简单物体

**场景**:
- `lego` - 乐高推土机
- `chair` - 椅子
- `drums` - 架子鼓
- `ficus` - 植物
- `hotdog` - 热狗
- `materials` - 材质球
- `mic` - 麦克风
- `ship` - 海盗船

**获取方式**:
```bash
wget http://cseweb.ucsd.edu/~viscomp/projects/LF/papers/ECCV20/nerf/nerf_synthetic.zip
unzip nerf_synthetic.zip
```

**优点**:
- ✅ 快速下载（~5GB）
- ✅ 已有camera poses
- ✅ 干净背景

**缺点**:
- ❌ 无完整房间场景
- ❌ 只有单个物体
- ⚠️ 需要转换为3DGS

---

### 3. Replica Dataset

**描述**: 高保真室内场景重建

**场景**:
- `office_0`, `office_1`, `office_2`, `office_3`
- `room_0`, `room_1`, `room_2`
- `apartment_0`, `apartment_1`, `apartment_2`
- `hotel_0`
- `frl_apartment_0`, ...

**获取方式**:
```bash
# 需要注册并下载
# https://github.com/facebookresearch/Replica-Dataset

# 或使用Habitat-Sim接口
pip install habitat-sim
```

**格式**: Mesh + textures

**优点**:
- ✅ 完整室内场景
- ✅ 多个房间类型
- ✅ 高质量mesh

**缺点**:
- ⚠️ 需要转换为3DGS
- ⚠️ 文件非常大（~50GB+）

---

### 4. ScanNet / ScanNet++

**描述**: 真实世界RGB-D扫描数据集

**内容**:
- 1500+ 室内场景
- 卧室、客厅、厨房、办公室等

**获取方式**:
```bash
# 需要申请访问权限
# http://www.scan-net.org/

# ScanNet++（更新版）
# https://kaldir.vc.in.tum.de/scannetpp/
```

**优点**:
- ✅ 真实场景
- ✅ 场景类型丰富
- ✅ 包含语义标注

**缺点**:
- ⚠️ 需要申请权限
- ⚠️ 数据量极大（1TB+）
- ⚠️ 需要预处理

---

### 5. 3DGS Pre-trained Models (最简单)

**直接下载已训练好的3DGS模型**

**来源**:
- Hugging Face: https://huggingface.co/models?search=gaussian+splatting
- GitHub: 搜索 "3dgs pretrained" / "gaussian splatting models"

**示例仓库**:
```bash
# 示例：3DGS官方Demo场景
git clone https://github.com/graphdeco-inria/gaussian-splatting
cd gaussian-splatting

# 下载示例场景
wget https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/input/tandt_db.zip
```

**优点**:
- ✅ 开箱即用（PLY文件）
- ✅ 无需训练
- ✅ 快速测试

**缺点**:
- ⚠️ 场景有限
- ⚠️ 质量不一

---

## 推荐获取流程

### 方案1: Mip-NeRF 360 (推荐用于演示)

```bash
# Step 1: 下载数据
cd /home/ununtu/metabot-workspace/mugs/data/
wget http://storage.googleapis.com/gresearch/refraw360/360_v2.zip
unzip 360_v2.zip

# Step 2: 安装3DGS训练工具
git clone https://github.com/graphdeco-inria/gaussian-splatting
cd gaussian-splatting
pip install -r requirements.txt

# Step 3: 训练kitchen场景
python train.py -s ../data/360_v2/kitchen -m output/kitchen

# Step 4: 提取PLY
cp output/kitchen/point_cloud/iteration_30000/point_cloud.ply \
   /home/ununtu/metabot-workspace/mugs/data/pretrained/kitchen/point_cloud/iteration_30000/point_cloud.ply
```

**时间**: ~1-2小时（取决于GPU）

---

### 方案2: 使用现成的Kitchen场景

**在线搜索关键词**:
- "3dgs kitchen scene"
- "gaussian splatting kitchen model"
- "nerf kitchen dataset"

**推荐网站**:
1. **PolyHaven** (https://polyhaven.com/)
   - 高质量3D场景
   - 可转换为3DGS

2. **Sketchfab** (https://sketchfab.com/)
   - 搜索 "kitchen 3d model"
   - 下载 → 转换为3DGS

3. **TurboSquid** (https://www.turbosquid.com/)
   - 免费模型区
   - 下载mesh → NeRF → 3DGS

---

### 方案3: 自己捕获（最灵活）

完整的端到端教程见 **[GS_DATA_COLLECTION.md](GS_DATA_COLLECTION.md)** —— 拍摄技巧、COLMAP、3DGS 训练、落地到 MuGS 都在那里展开。简版命令：

```bash
# 1. 拍摄 100–300 张照片（三圈环绕，锁定 AE/AF/WB）
# 2. COLMAP + 3DGS 一条龙
git clone https://github.com/graphdeco-inria/gaussian-splatting
cd gaussian-splatting
python convert.py -s data/custom/<scene>           # COLMAP SfM
python train.py   -s data/custom/<scene> -m out/<scene> --iterations 30000
```

**优点**:
- ✅ 完全自定义
- ✅ 符合实际需求

**缺点**:
- ⚠️ 需要高质量拍摄
- ⚠️ 训练时间长

---

## 快速开始：下载示例Kitchen场景

```python
# /scripts/data_collection/download_kitchen_scene.py

import requests
from pathlib import Path

def download_kitchen_scene():
    """下载预训练的kitchen场景"""
    
    # 示例URL（需要替换为实际URL）
    urls = {
        "kitchen_mipnerf360": "https://example.com/kitchen.ply",  # TODO
        "kitchen_replica": "https://example.com/replica_kitchen.ply",  # TODO
    }
    
    output_dir = Path("assets/scenes/")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    for name, url in urls.items():
        print(f"Downloading {name}...")
        output_path = output_dir / f"{name}.ply"
        
        # TODO: 实际下载逻辑
        # response = requests.get(url)
        # output_path.write_bytes(response.content)
        
        print(f"✅ Saved to {output_path}")

if __name__ == "__main__":
    download_kitchen_scene()
```

---

## 使用场景PLY的修改

当前代码需要小幅修改以支持完整场景：

```python
# 当前：加载多个物体PLY
gaussians_dict = {
    'mug': load_ply('mug.ply'),
    'plate': load_ply('plate.ply'),
}

# 改为：加载单个场景PLY
kitchen_scene = load_ply('kitchen_scene.ply')
gaussians_dict = {'kitchen': kitchen_scene}

# 渲染时不需要transform（场景已在世界坐标）
gs_rgb = render_3dgs(gaussians_dict, camera_params)
```

---

## 对比：物体 vs 场景

| 特性 | 当前（多物体） | 完整场景 |
|------|--------------|----------|
| **文件数** | 12个PLY | 1个PLY |
| **高斯数** | 6,180 | 50,000-500,000 |
| **文件大小** | 1.6MB | 10-100MB |
| **渲染速度** | 快 | 较慢 |
| **灵活性** | 高（可移动物体） | 低（固定场景） |
| **真实感** | 中等 | 很高 |

---

## 建议

**Phase 1-2 (当前)**:
- ✅ 使用多物体方案
- ✅ 验证pipeline
- ✅ 快速迭代

**Phase 3+ (后续)**:
- 🎯 下载Mip-NeRF 360 kitchen场景
- 🎯 训练或使用预训练模型
- 🎯 演示完整房间渲染

**立即可用的最简单方案**:
1. 先用当前的12个物体验证流程
2. 并行下载Mip-NeRF 360数据集
3. 训练kitchen场景（1-2小时）
4. 替换为完整场景

---

**需要帮助下载/训练吗？**
