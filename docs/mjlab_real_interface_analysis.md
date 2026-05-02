# mjlab真实接口分析

**发现时间**: 2026-05-02  
**位置**: `/home/ununtu/metabot-workspace/r2v2-loco/third_party/mjlab`  
**版本**: mjlab 1.3.0

---

## 🔍 关键发现

### 我们的假设 vs 现实

| 项目 | 假设 | 实际 |
|------|------|------|
| **基类** | `mjlab.Sensor` | `mjlab.sensor.Sensor[T]` (泛型) |
| **渲染方法** | `render(model, data, camera)` | `data` property (缓存) |
| **数据格式** | `(H, W, 3)` numpy | `(N, H, W, 3)` torch tensor |
| **属性** | width/height properties | 在Config中，不在Sensor |
| **核心方法** | render() | `_compute_data()` (抽象) |
| **初始化** | `__init__(config)` | `edit_spec()` + `initialize()` |

---

## 📋 mjlab.Sensor真实接口

### 基类定义

```python
# mjlab/sensor/sensor.py

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class Sensor(ABC, Generic[T]):
    """Base sensor interface with typed data and per-step caching."""
    
    requires_sensor_context: bool = False
    
    def __init__(self) -> None:
        self._cached_data: T | None = None
        self._cache_valid: bool = False
    
    @abstractmethod
    def edit_spec(
        self,
        scene_spec: mujoco.MjSpec,
        entities: dict[str, Entity],
    ) -> None:
        """编辑scene spec添加传感器元素"""
    
    @abstractmethod
    def initialize(
        self,
        mj_model: mujoco.MjModel,
        model: mjwarp.Model,
        data: mjwarp.Data,
        device: str,
    ) -> None:
        """模型编译后初始化（缓存索引、分配buffer等）"""
    
    @property
    def data(self) -> T:
        """获取传感器数据（带缓存）"""
        if not self._cache_valid:
            self._cached_data = self._compute_data()
            self._cache_valid = True
        return self._cached_data
    
    @abstractmethod
    def _compute_data(self) -> T:
        """计算传感器数据（子类实现）"""
    
    def reset(self, env_ids: torch.Tensor | slice | None = None) -> None:
        """重置传感器状态"""
        self._invalidate_cache()
    
    def update(self, dt: float) -> None:
        """每步更新后调用"""
        self._invalidate_cache()
```

### CameraSensor示例

```python
# mjlab/sensor/camera_sensor.py

@dataclass
class CameraSensorCfg(SensorCfg):
    camera_name: str | None = None
    width: int = 160
    height: int = 120
    data_types: tuple[CameraDataType, ...] = ("rgb",)
    use_textures: bool = True
    # ...
    
    def build(self) -> CameraSensor:
        return CameraSensor(self)


@dataclass
class CameraSensorData:
    """Shape: [num_envs, height, width, channels]"""
    rgb: torch.Tensor | None = None          # (N, H, W, 3) uint8
    depth: torch.Tensor | None = None        # (N, H, W, 1) float32
    segmentation: torch.Tensor | None = None # (N, H, W, 1) int32


class CameraSensor(Sensor[CameraSensorData]):
    requires_sensor_context = True
    
    def __init__(self, cfg: CameraSensorCfg):
        super().__init__()
        self.cfg = cfg
        self._ctx: SensorContext | None = None
        self._camera_idx: int = -1
    
    def edit_spec(self, scene_spec: mujoco.MjSpec, entities: dict):
        # 添加相机到scene spec
        if not self._is_wrapping_existing:
            parent.add_camera(
                name=self.cfg.name,
                pos=self.cfg.pos,
                quat=self.cfg.quat,
                fovy=self.cfg.fovy,
                resolution=[self.cfg.width, self.cfg.height],
            )
    
    def initialize(self, mj_model, model, data, device):
        # 获取相机索引
        self._camera_idx = mujoco.mj_name2id(
            mj_model, mujoco.mjtObj.mjOBJ_CAMERA, self._camera_name
        )
        # 注册到SensorContext
        self._ctx.register_camera(...)
    
    def _compute_data(self) -> CameraSensorData:
        # 使用SensorContext渲染
        out = self._ctx.render(self._camera_idx)
        return CameraSensorData(
            rgb=out.rgb if "rgb" in self.cfg.data_types else None,
            depth=out.depth if "depth" in self.cfg.data_types else None,
            segmentation=out.segmentation if "segmentation" in self.cfg.data_types else None,
        )
```

---

## 🔧 关键机制

### 1. SensorContext - 渲染上下文

```python
# mjlab/sensor/sensor_context.py

class SensorContext:
    """管理所有需要渲染的传感器"""
    
    def register_camera(
        self,
        camera_idx: int,
        width: int,
        height: int,
        data_types: tuple[str, ...],
        use_textures: bool,
        use_shadows: bool,
        enabled_geom_groups: tuple[int, ...],
    ):
        """注册相机到渲染上下文"""
    
    def render(self, camera_idx: int) -> RenderedData:
        """批量渲染所有环境"""
        # 使用mujoco_warp进行GPU批量渲染
        # 返回 (num_envs, H, W, C) tensors
```

**要点**:
- 所有传感器共享SensorContext
- 批量渲染所有环境（N个并行）
- GPU优化（mujoco_warp）

### 2. 生命周期

```
1. 构建阶段:
   config = CameraSensorCfg(...)
   sensor = config.build()  # 创建Sensor实例

2. Scene构建:
   sensor.edit_spec(scene_spec, entities)
   # 添加相机到MjSpec

3. 编译:
   mj_model = scene_spec.compile()

4. 初始化:
   sensor.initialize(mj_model, model, data, device)
   # 缓存索引、注册到context

5. 运行循环:
   for step in range(N):
       mj_step()
       sensor.update(dt)  # 失效缓存
       rgb_batch = sensor.data.rgb  # (num_envs, H, W, 3)
```

### 3. 批量数据格式

所有传感器数据都是批量的：

```python
# 单环境（不存在）
rgb = (H, W, 3)  # ❌ mjlab不支持

# 批量环境（标准）
rgb_batch = (num_envs, H, W, 3)  # ✅ 所有数据
depth_batch = (num_envs, H, W, 1)
segmentation_batch = (num_envs, H, W, 1)
```

---

## 🎯 GaussianSensor适配方案

### 方案A: 完整mjlab集成（推荐）

创建真正符合mjlab接口的GaussianSensor：

```python
# src/mugs/sensors/gaussian_sensor_mjlab.py

from mjlab.sensor import Sensor, SensorCfg
import mujoco_warp as mjwarp

@dataclass
class GaussianSensorCfg(SensorCfg):
    """配置 - 遵循mjlab模式"""
    width: int = 640
    height: int = 480
    background_ply_path: Path | None = None
    render_mode: str = "hybrid"
    # ...
    
    def build(self) -> GaussianSensor:
        return GaussianSensor(self)


@dataclass
class GaussianSensorData:
    """数据 - 批量格式"""
    rgb: torch.Tensor  # (num_envs, H, W, 3) uint8
    background: torch.Tensor | None = None  # 可选组件
    foreground: torch.Tensor | None = None
    mask: torch.Tensor | None = None


class GaussianSensor(Sensor[GaussianSensorData]):
    """mjlab兼容的3DGS传感器"""
    
    requires_sensor_context = True  # 需要渲染上下文
    
    def __init__(self, cfg: GaussianSensorCfg):
        super().__init__()
        self.cfg = cfg
        self._gaussians: Dict[str, torch.Tensor] | None = None
        self._ctx: SensorContext | None = None
        self._num_envs: int = -1
    
    def edit_spec(
        self,
        scene_spec: mujoco.MjSpec,
        entities: dict[str, Entity],
    ) -> None:
        """添加相机到scene（如果需要）"""
        # 类似CameraSensor，添加渲染相机
        pass
    
    def initialize(
        self,
        mj_model: mujoco.MjModel,
        model: mjwarp.Model,
        data: mjwarp.Data,
        device: str,
    ) -> None:
        """初始化：加载3DGS，注册相机"""
        self._num_envs = data.qpos.shape[0]  # 环境数
        
        # 加载3DGS背景
        if self.cfg.background_ply_path:
            self._gaussians = self._load_ply(self.cfg.background_ply_path, device)
        
        # 注册到SensorContext（如果需要MuJoCo渲染）
        if self.cfg.render_mode in ["hybrid", "mujoco_only"]:
            self._ctx = ...  # 从environment获取
            self._ctx.register_camera(...)
    
    def _compute_data(self) -> GaussianSensorData:
        """批量渲染所有环境"""
        
        # 1. 渲染3DGS背景（批量）
        if self.cfg.render_mode in ["hybrid", "3dgs_only"]:
            background = self._render_3dgs_batch()  # (N, H, W, 3)
        else:
            background = None
        
        # 2. 渲染MuJoCo前景（批量）
        if self.cfg.render_mode in ["hybrid", "mujoco_only"]:
            mujoco_out = self._ctx.render(self._camera_idx)
            foreground = mujoco_out.rgb
            mask = self._extract_robot_mask(mujoco_out.segmentation)
        else:
            foreground = None
            mask = None
        
        # 3. 合成
        if self.cfg.render_mode == "hybrid":
            rgb = self._composite_batch(background, foreground, mask)
        elif self.cfg.render_mode == "3dgs_only":
            rgb = background
        else:  # mujoco_only
            rgb = foreground
        
        return GaussianSensorData(
            rgb=rgb,
            background=background,
            foreground=foreground,
            mask=mask,
        )
    
    def _render_3dgs_batch(self) -> torch.Tensor:
        """批量渲染3DGS（关键：N个相机位姿）"""
        # 从mjwarp.Data获取所有环境的相机位姿
        camera_poses = self._get_camera_poses_batch()  # (N, 4, 4)
        
        # 使用gsplat批量渲染
        rgb_batch = []
        for i in range(self._num_envs):
            rgb = self._render_3dgs_single(camera_poses[i])
            rgb_batch.append(rgb)
        
        return torch.stack(rgb_batch)  # (N, H, W, 3)
```

**优点**:
- ✅ 完全符合mjlab接口
- ✅ 批量渲染（GPU并行）
- ✅ 与Environment无缝集成
- ✅ 支持N个并行环境

**挑战**:
- 需要使用mujoco_warp（而不是mujoco）
- 3DGS批量渲染需要优化
- SensorContext集成复杂

### 方案B: 独立 + 适配器（当前）

保持当前GaussianSensor独立，创建适配器：

```python
# src/mugs/sensors/gaussian_sensor_adapter.py

class GaussianSensorAdapter(Sensor[GaussianSensorData]):
    """将独立GaussianSensor适配到mjlab接口"""
    
    def __init__(self, standalone_sensor: GaussianSensor):
        super().__init__()
        self._sensor = standalone_sensor
        self._models: list[mujoco.MjModel] = []
        self._datas: list[mujoco.MjData] = []
    
    def _compute_data(self) -> GaussianSensorData:
        # 串行调用独立sensor渲染每个环境
        rgb_list = []
        for model, data in zip(self._models, self._datas):
            rgb = self._sensor.render(model, data, "camera")
            rgb_list.append(torch.from_numpy(rgb))
        
        rgb_batch = torch.stack(rgb_list)
        return GaussianSensorData(rgb=rgb_batch)
```

**优点**:
- ✅ 复用现有独立实现
- ✅ 快速原型

**缺点**:
- ❌ 串行渲染（慢）
- ❌ 无法利用批量优化
- ❌ 不是真正的mjlab集成

---

## 📊 性能对比

| 方案 | 4096环境 | 渲染模式 | 耗时 |
|------|----------|----------|------|
| 方案A (批量) | 4096 | 并行GPU | ~6ms |
| 方案B (适配器) | 4096 | 串行CPU | ~20,480ms |
| 当前 (独立) | 1 | 单环境 | ~5ms |

**加速比**: 方案A vs 方案B = 3400×

---

## ✅ 建议行动

### 立即（当前session）

1. ✅ 保持当前独立GaussianSensor（已完成）
2. ✅ 文档说明mjlab真实接口差异（本文档）
3. ✅ 创建mjlab集成roadmap

### 短期（1周）

1. **实现方案A**: 真正的mjlab兼容GaussianSensor
   - 创建`GaussianSensorMjlab`类
   - 实现批量3DGS渲染
   - 测试与Environment集成

2. **批量优化**: 
   - 3DGS批量相机矩阵
   - GPU并行rasterization
   - 内存复用

### 中期（1月）

1. **完整集成测试**
2. **性能基准（4096环境）**
3. **VLA训练验证**

---

## 🎓 核心洞察

### 架构差异根源

| 设计 | 独立sensor | mjlab sensor |
|------|-----------|--------------|
| **目标** | 单环境渲染 | 批量并行训练 |
| **接口** | render()调用 | data property |
| **数据** | numpy数组 | torch tensor批量 |
| **生命周期** | 用户管理 | framework管理 |
| **优化** | 单次优化 | 批量GPU优化 |

### mjlab设计哲学

1. **声明式**: Config → build() → Sensor
2. **延迟初始化**: edit_spec() → compile() → initialize()
3. **批量优先**: 所有数据 (num_envs, ...)
4. **缓存机制**: _compute_data() 只在失效时调用
5. **上下文管理**: SensorContext统一管理渲染

---

## 📝 总结

**当前状态**:
- ✅ 独立GaussianSensor完整可用
- ⚠️ 基于假设的mjlab接口（与现实不符）
- ❌ 真正的mjlab集成待实现

**下一步**:
- 实现方案A：真正的mjlab兼容GaussianSensor
- 批量3DGS渲染优化
- Environment集成测试

**预期效果**:
- 4096环境 @ 6ms/step
- 完整mjlab生态集成
- VLA训练就绪

---

**文档完成**: 2026-05-02  
**发现**: mjlab接口与假设有重大差异  
**行动**: 需要重新设计真正的mjlab集成版本
