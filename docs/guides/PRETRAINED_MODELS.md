# Mip-NeRF 360 Kitchen预训练模型资源

## 🎯 已确认可用资源

### 1. INRIA官方预训练模型 ⭐⭐⭐ 强烈推荐

**来源**: [graphdeco-inria/gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting)

**下载地址**: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/pretrained/models.zip

**特点**:
- 官方发布的预训练3DGS模型
- 14GB zip压缩包
- 包含Tanks & Temples等标准benchmark场景
- 可直接用于inference，无需训练

**使用方法**:
```bash
# 下载预训练模型
wget -O data/pretrained_models.zip \
  https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/pretrained/models.zip

# 解压
unzip data/pretrained_models.zip -d data/pretrained/

# 检查包含的场景
ls data/pretrained/
```

**注意**: 需要验证是否包含kitchen场景。如果不包含，可以使用NerfBaselines训练。

---

### 2. NerfBaselines工具 ⭐⭐ 推荐用于训练

**来源**: [nerfbaselines/nerfbaselines](https://github.com/nerfbaselines/nerfbaselines)

**特点**:
- 专业的NeRF/3DGS评估和训练框架
- 统一接口，支持多种方法
- 支持gaussian-splatting方法
- 可重现的评估结果

**安装**:
```bash
pip install nerfbaselines
```

**训练kitchen场景**:
```bash
# 使用已下载的Mip-NeRF 360数据
nerfbaselines train \
  --method gaussian-splatting \
  --data data/kitchen \
  --output experiments/kitchen_gs \
  --eval-few-iters 1000::1000 \
  --eval-all-iters -1

# 训练时间：约1-2小时（RTX 4090）
```

**渲染已训练模型**:
```bash
nerfbaselines render \
  --checkpoint experiments/kitchen_gs/checkpoint.ckpt \
  --output renders/kitchen/
```

---

### 3. Hugging Face数据集

**来源**: [mileleap/mipnerf360](https://huggingface.co/datasets/mileleap/mipnerf360)

**特点**:
- 完整的Mip-NeRF 360数据集
- 包含kitchen场景的多视角图像
- 可能包含其他用户上传的预训练模型

**使用方法**:
```bash
# 安装Hugging Face CLI
pip install -U huggingface_hub

# 浏览数据集文件
huggingface-cli repo-files mileleap/mipnerf360

# 下载kitchen场景
huggingface-cli download mileleap/mipnerf360 \
  --include "kitchen/*" \
  --local-dir ./data/mipnerf360_hf
```

---

### 4. 其他研究项目

以下项目在论文中使用了Mip-NeRF 360 kitchen场景，可能提供预训练模型：

**FastGS** (CVPR 2026 Highlight)
- GitHub: https://github.com/fastgs/FastGS
- 特点：100秒训练3DGS
- 可能提供预训练checkpoint

**Matryoshka Gaussian Splatting**
- GitHub: https://github.com/ZhilinGuo/matryoshka-gaussian-splatting
- Checkpoint路径：`../checkpoint/mipnerf360/kitchen/ckpts/`
- 需联系作者或查看repo的releases

**Mip-Splatting** (CVPR 2024 Best Student Paper)
- GitHub: https://github.com/autonomousvision/mip-splatting
- 3DGS + Mip-NeRF的结合
- 可能提供预训练模型

---

## 🚀 快速开始方案

### 方案1: 使用INRIA官方预训练模型（最快）

```bash
cd /home/ununtu/metabot-workspace/mugs

# 1. 下载官方预训练模型（14GB，正在后台下载中）
# wget已在后台运行

# 2. 等待下载完成后解压
unzip data/pretrained_models.zip -d data/pretrained/

# 3. 列出包含的场景
ls data/pretrained/

# 4. 如果有kitchen场景，转换为.ply格式供gsplat使用
python scripts/utils/convert_3dgs_to_ply.py \
  --input data/pretrained/kitchen/ \
  --output assets/scenes/kitchen_pretrained.ply
```

**优势**: 无需训练，开箱即用  
**时间**: ~30分钟（主要是下载时间）

---

### 方案2: 使用NerfBaselines训练（最可靠）

```bash
cd /home/ununtu/metabot-workspace/mugs

# 1. 安装nerfbaselines（已完成）
# pip install nerfbaselines

# 2. 训练kitchen场景
nerfbaselines train \
  --method gaussian-splatting \
  --data data/kitchen \
  --output experiments/kitchen_gs \
  --logger tensorboard

# 3. 训练完成后，提取PLY
python scripts/utils/extract_gaussians_from_nerfbaselines.py \
  --checkpoint experiments/kitchen_gs/checkpoint.ckpt \
  --output assets/scenes/kitchen_trained.ply
```

**优势**: 完全可控，质量有保证  
**时间**: 1-2小时训练 + 5分钟转换

---

### 方案3: 继续使用程序生成场景（已可用）

```bash
# 当前已有的kitchen场景
# - 位置: assets/scenes/kitchen.ply
# - 高斯数量: 6,180
# - 性能: 8,920 FPS
# - 质量: 程序生成，适合Phase 1-2开发

# 可以直接使用现有场景继续开发
python examples/basic/render_scene.py --scene kitchen
```

**优势**: 无需等待，立即可用  
**时间**: 0分钟

---

## 📊 资源对比

| 来源 | 训练时间 | 质量 | 易用性 | 推荐度 |
|------|---------|------|--------|--------|
| **INRIA官方** | 0（预训练） | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **NerfBaselines** | 1-2小时 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Hugging Face** | 0（如有checkpoint） | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **程序生成** | 0 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 💡 建议操作流程

### Step 1: 等待INRIA官方模型下载完成（后台进行中）

```bash
# 检查下载进度
tail -f /tmp/claude-1000/-home-ununtu-metabot-workspace/*/tasks/bv2440x1a.output

# 下载完成后解压并检查
unzip data/pretrained_models.zip -d data/pretrained/
ls data/pretrained/
```

如果包含kitchen场景 → 转换为PLY并使用 ✅  
如果不包含 → 继续Step 2

### Step 2: 使用NerfBaselines训练（1-2小时）

```bash
nerfbaselines train \
  --method gaussian-splatting \
  --data data/kitchen \
  --output experiments/kitchen_gs
```

### Step 3: 继续使用程序生成场景开发（当前可用）

```bash
# Phase 1-2开发不受影响
# 等训练完成后替换为真实场景即可
```

---

## 🔧 转换工具（待开发）

需要创建以下转换脚本：

1. **convert_3dgs_to_ply.py**
   - 从官方3DGS checkpoint转换为gsplat兼容的PLY格式
   - 输入：`point_cloud/iteration_30000/point_cloud.ply`
   - 输出：`assets/scenes/kitchen.ply`

2. **extract_gaussians_from_nerfbaselines.py**
   - 从NerfBaselines checkpoint提取高斯参数
   - 保存为标准PLY格式

这些脚本将在需要时创建。

---

## 📌 当前状态

**✅ 已完成**:
- Mip-NeRF 360 kitchen数据集下载（279张图像，1.5GB）
- NerfBaselines工具安装和测试
- INRIA官方预训练模型下载启动（14GB，后台进行中）

**🔄 进行中**:
- 等待官方预训练模型下载完成
- 验证是否包含kitchen场景

**📋 待定**:
- 如果官方模型包含kitchen → 转换为PLY
- 如果不包含 → 使用NerfBaselines训练1-2小时

---

## 📚 参考资源

- [Official 3D Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting)
- [NerfBaselines](https://nerfbaselines.github.io/)
- [Hugging Face Dataset](https://huggingface.co/datasets/mileleap/mipnerf360)
- [Mip-Splatting](https://github.com/autonomousvision/mip-splatting)
- [FastGS](https://github.com/fastgs/FastGS)
- [Matryoshka GS](https://github.com/ZhilinGuo/matryoshka-gaussian-splatting)

---

**最后更新**: 2026-05-02  
**维护者**: MuGS Team
