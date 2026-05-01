# Phase 1 优化计划

**目标**: 完成Phase 1，达到production-ready状态

---

## 优先级1: GPU加速 (估时: 2-4小时)

### 问题
当前使用CPU光栅化渲染，速度慢（~18 FPS）

### 目标
- gsplat GPU编译成功
- 达到5000+ FPS @ 160×120

### 方案

#### 方案A: 修复CUDA架构 (推荐)
```bash
# 设置兼容架构
export TORCH_CUDA_ARCH_LIST="8.6"

# 修复cudart路径
export LD_LIBRARY_PATH=/usr/local/cuda-11.6/lib64:$LD_LIBRARY_PATH

# 清除缓存重新编译
rm -rf ~/.cache/torch_extensions/
python -c "from gsplat import rasterization; print('OK')"
```

**优点**: 快速，无需升级  
**缺点**: 性能可能略低于native compute_89

#### 方案B: 升级CUDA Toolkit
```bash
# 下载CUDA 12.1
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run

# 安装
sudo sh cuda_12.1.0_530.30.02_linux.run

# 更新环境变量
export PATH=/usr/local/cuda-12.1/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH
```

**优点**: 原生支持RTX 4090  
**缺点**: 时间较长，可能影响其他项目

#### 方案C: 预编译wheel
```bash
# 查找预编译版本
pip install gsplat --find-links https://github.com/nerfstudio-project/gsplat/releases
```

**优点**: 最简单  
**缺点**: 可能版本不匹配

### 测试

```python
# benchmark_gsplat.py
import torch
from gsplat import rasterization
import time

# Create test data
means = torch.randn(10000, 3, device='cuda')
quats = torch.randn(10000, 4, device='cuda')
quats = quats / quats.norm(dim=-1, keepdim=True)
scales = torch.ones(10000, 3, device='cuda') * 0.01
opacities = torch.ones(10000, device='cuda') * 0.9
colors = torch.rand(10000, 3, device='cuda')

viewmat = torch.eye(4, device='cuda')[None, ...]
K = torch.tensor([[500, 0, 80], [0, 500, 60], [0, 0, 1]], device='cuda')[None, ...]

# Warmup
for _ in range(10):
    rendered, _, _ = rasterization(
        means, quats, scales, opacities, colors,
        viewmat, K, 160, 120, packed=False
    )

# Benchmark
torch.cuda.synchronize()
start = time.time()
n_iters = 100

for _ in range(n_iters):
    rendered, _, _ = rasterization(
        means, quats, scales, opacities, colors,
        viewmat, K, 160, 120, packed=False
    )

torch.cuda.synchronize()
elapsed = time.time() - start

fps = n_iters / elapsed
print(f"✅ gsplat GPU: {fps:.0f} FPS @ 160×120")
print(f"   Target: 5000+ FPS")
print(f"   {'PASS' if fps > 5000 else 'FAIL'}")
```

---

## 优先级2: 真实房间场景 (估时: 1-2小时)

### 任务
下载并集成完整厨房场景

### 方案

#### 快速方案: 下载预训练模型
```bash
# 1. 搜索Hugging Face
# https://huggingface.co/models?search=gaussian+splatting+kitchen

# 2. 或使用3DGS官方示例
git clone https://github.com/graphdeco-inria/gaussian-splatting
cd gaussian-splatting

# 下载示例场景（如果有kitchen）
# wget <kitchen_scene_url>
```

#### 完整方案: Mip-NeRF 360
```bash
# 1. 下载数据集
cd /home/ununtu/metabot-workspace/mugs/data/
wget http://storage.googleapis.com/gresearch/refraw360/360_v2.zip
unzip 360_v2.zip

# 2. 训练3DGS
cd ../external/gaussian-splatting/
python train.py \
    -s ../../data/360_v2/kitchen \
    -m ../../outputs/kitchen_trained \
    --iterations 30000

# 3. 复制PLY
cp ../../outputs/kitchen_trained/point_cloud/iteration_30000/point_cloud.ply \
   ../../assets/scenes/kitchen_real.ply
```

**时间**: ~1-2小时训练（RTX 4090）

### 集成

```python
# 更新demo脚本
def load_room_scene(scene_path):
    """加载完整房间场景（单个PLY）"""
    gaussians = load_ply_gaussians(scene_path)
    
    # 房间场景不需要transform（已在世界坐标）
    return {'kitchen_room': gaussians}

# 使用
room_gaussians = load_room_scene('assets/scenes/kitchen_real.ply')
gs_rgb = render_3dgs(room_gaussians, camera_params)
```

---

## 优先级3: 代码整理 (估时: 30分钟)

### 任务
- 合并重复代码
- 统一接口
- 添加文档

### 重构

#### 1. 提取公共函数
```python
# src/mugs/utils/rendering.py

def load_ply_gaussians(ply_path: Path) -> dict:
    """Load 3DGS from PLY (unified)"""
    ...

def render_mujoco_rgb(model, data, camera_name, width, height):
    """MuJoCo RGB rendering (unified)"""
    ...

def create_robot_mask(seg_ids, model, robot_geom_names):
    """Extract robot mask (generalized)"""
    ...

def composite_images(mujoco_rgb, gs_rgb, mask):
    """Hybrid compositing (unified)"""
    ...
```

#### 2. 统一Demo接口
```python
# examples/demo/render_scene.py (统一入口)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', choices=['objects', 'room'], default='objects')
    parser.add_argument('--camera', default='overview')
    parser.add_argument('--output', default='outputs/demo')
    args = parser.parse_args()
    
    # Load scene (objects or room)
    if args.scene == 'objects':
        gaussians = load_multi_objects('assets/scenes/kitchen/')
    else:
        gaussians = load_room_scene('assets/scenes/kitchen_real.ply')
    
    # Render
    render_hybrid_scene(gaussians, args.camera, args.output)
```

#### 3. 文档
```python
# 添加docstring (Google style)
def render_hybrid_scene(gaussians: dict, camera_name: str, output_dir: Path):
    """Render hybrid scene with MuJoCo robot and 3DGS objects.
    
    Args:
        gaussians: Dict of object_id -> gaussian parameters
        camera_name: MuJoCo camera name
        output_dir: Where to save outputs
    
    Returns:
        Composite RGB image (H, W, 3)
    
    Example:
        >>> gaussians = load_multi_objects('assets/scenes/kitchen/')
        >>> img = render_hybrid_scene(gaussians, 'overview', 'outputs/')
    """
    ...
```

---

## 优先级4: 性能基准测试 (估时: 30分钟)

### 任务
完整的性能测试报告

### 测试脚本

```python
# scripts/evaluation/benchmark_pipeline.py

def benchmark_full_pipeline():
    """完整pipeline性能测试"""
    
    results = {}
    
    # Test 1: MuJoCo rendering
    times = []
    for _ in range(100):
        start = time.time()
        mujoco_rgb = render_mujoco_rgb(...)
        seg_ids = render_mujoco_segmentation(...)
        times.append(time.time() - start)
    
    results['mujoco'] = {
        'mean_ms': np.mean(times) * 1000,
        'std_ms': np.std(times) * 1000,
    }
    
    # Test 2: 3DGS rendering (CPU)
    # Test 3: 3DGS rendering (GPU)
    # Test 4: Compositing
    # Test 5: End-to-end
    
    # Generate report
    print("="*60)
    print("Performance Benchmark")
    print("="*60)
    for stage, metrics in results.items():
        print(f"{stage:20s}: {metrics['mean_ms']:.2f} ± {metrics['std_ms']:.2f} ms")
    
    total_ms = sum(m['mean_ms'] for m in results.values())
    fps = 1000 / total_ms
    print(f"\nTotal: {total_ms:.2f} ms ({fps:.1f} FPS)")
```

### 目标指标

| Stage | Target | Current |
|-------|--------|---------|
| MuJoCo RGB | < 30ms | ~30ms ✅ |
| Segmentation | < 30ms | ~30ms ✅ |
| Mask extraction | < 1ms | ~1ms ✅ |
| 3DGS (GPU) | < 5ms | TBD ⚠️ |
| 3DGS (CPU) | N/A | ~300ms |
| Composite | < 1ms | ~1ms ✅ |
| **Total (GPU)** | **< 70ms** | **TBD** |
| **Total (CPU)** | N/A | ~360ms |

---

## 执行顺序

1. **Week 1 Day 1-2**: GPU加速 (优先级1)
   - 修复gsplat编译
   - 验证性能达标

2. **Week 1 Day 3-4**: 真实场景 (优先级2)
   - 下载/训练kitchen场景
   - 集成到demo

3. **Week 1 Day 5**: 代码整理 (优先级3)
   - 重构公共代码
   - 统一接口

4. **Week 2 Day 1**: 基准测试 (优先级4)
   - 完整性能报告
   - 文档更新

5. **Week 2 Day 2-5**: Phase 2准备
   - 设计GaussianSensor API
   - 规划集成方案

---

## 完成标准

Phase 1视为完成当:
- ✅ GPU渲染工作 (>5000 FPS)
- ✅ 至少1个真实房间场景
- ✅ 代码整洁，有文档
- ✅ 完整性能报告
- ✅ Demo可运行，效果好

**预计完成时间**: 1-2周
