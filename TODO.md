# MuGS Development TODO

**Last Updated**: 2026-05-02  
**Current Phase**: Phase 0 - Setup Complete ✅  
**Next Phase**: Phase 1 - gsplat PoC

---

## Phase 1: gsplat Proof-of-Concept (Weeks 1-2)

### 1.1 Environment Setup
- [ ] Install gsplat library (`pip install gsplat>=1.5.0`)
- [ ] Verify CUDA/GPU setup (test gsplat basic rendering)
- [ ] Set up MuJoCo Warp environment
- [ ] Create development branch `phase-1-gsplat-poc`

### 1.2 Core Rendering Tests
- [ ] Implement basic gsplat rendering script
  - [ ] Load sample 3DGS model (PLY format)
  - [ ] Render single view at 640×480
  - [ ] Benchmark FPS on single GPU
- [ ] Test batched rendering (4096 parallel environments)
  - [ ] Implement batched camera pose generation
  - [ ] Measure throughput at different resolutions
  - [ ] Profile GPU memory usage
- [ ] Validate rendering quality
  - [ ] Compare with ground truth images (LPIPS/PSNR)
  - [ ] Test view interpolation quality

### 1.3 MuJoCo Integration Spike
- [ ] Create minimal MuJoCo scene (single object + camera)
- [ ] Extract camera pose from MuJoCo simulation
- [ ] Drive gsplat renderer with MuJoCo camera
- [ ] Synchronize physics step with rendering

**Success Criteria:**
- ✅ Batched rendering achieves >5000 FPS @ 160×120
- ✅ Single-view LPIPS < 0.15 vs ground truth
- ✅ MuJoCo camera integration working

---

## Phase 2: GaussianSensor Core (Weeks 3-5)

### 2.1 Sensor API Design
- [ ] Implement `GaussianSensorCfg` dataclass
  - [ ] Resolution, FPS, batch size configs
  - [ ] Camera intrinsics/extrinsics
  - [ ] Asset loading parameters
- [ ] Implement `GaussianSensor` class
  - [ ] `__init__`: Load 3DGS asset, setup renderer
  - [ ] `update(poses)`: Batched rendering
  - [ ] `get_images()`: Retrieve RGB tensors
  - [ ] `reset()`: Clear cache

### 2.2 SE(3) Transform Utilities
- [ ] Implement `se3_to_view_matrix()` (MuJoCo → OpenGL)
- [ ] Implement `compute_intrinsics()` (FOV → K matrix)
- [ ] Add coordinate system tests (unit tests)

### 2.3 Asset Management
- [ ] Implement `ObjectLibrary` class
  - [ ] Load/cache 3DGS PLY files
  - [ ] Asset metadata (YAML configs)
  - [ ] Memory-efficient asset sharing
- [ ] Create sample object assets
  - [ ] 3-5 simple objects (cube, sphere, mug, etc.)
  - [ ] Capture 3DGS models (COLMAP → 3DGS training)

### 2.4 Integration Tests
- [ ] Test multi-object scenes (5+ objects per scene)
- [ ] Test dynamic objects (moving poses frame-to-frame)
- [ ] Benchmark full pipeline latency

**Success Criteria:**
- ✅ Sensor API complete with documentation
- ✅ End-to-end latency < 10ms for 4096 envs
- ✅ 5+ object assets ready

---

## Phase 3: Object Library & Procedural Scenes (Weeks 6-8)

### 3.1 Asset Acquisition
- [ ] Capture 20+ household object 3DGS models
  - [ ] Kitchen items (5 objects)
  - [ ] Tools (5 objects)
  - [ ] Containers (5 objects)
  - [ ] Misc (5 objects)
- [ ] Document capture pipeline (COLMAP workflow)
- [ ] Optimize asset file sizes (compression)

### 3.2 Procedural Scene Generation
- [ ] Implement `SceneGenerator` class
  - [ ] Random object placement (physics-valid)
  - [ ] Object orientation sampling
  - [ ] Collision avoidance
  - [ ] Diversity metrics
- [ ] Implement scene templates
  - [ ] Tabletop manipulation
  - [ ] Kitchen counter
  - [ ] Floor cleanup
- [ ] Add scene export (HDF5 format)

### 3.3 Asset Quality Validation
- [ ] Visual inspection script (render grid view)
- [ ] Quality metrics (coverage, sharpness)
- [ ] Fix problematic assets

**Success Criteria:**
- ✅ 20+ production-quality 3DGS assets
- ✅ Scene generator creates diverse scenes
- ✅ Asset library documented

---

## Phase 4: Super-Resolution Training (Weeks 9-10)

### 4.1 Data Collection
- [ ] Generate training dataset
  - [ ] 10k low-res rendered images (160×120)
  - [ ] Ground truth high-res images (640×480)
  - [ ] Paired LR-HR dataset (HDF5)
- [ ] Split train/val/test (80/10/10)

### 4.2 Model Training
- [ ] Implement `SimAwareSR` model
  - [ ] SwinIR-light backbone (900K params)
  - [ ] Simulation-aware features (depth, segmentation)
  - [ ] Perceptual loss (LPIPS + L1)
- [ ] Training pipeline
  - [ ] Hyperparameter sweep (LR, batch size)
  - [ ] Multi-GPU training (DDP)
  - [ ] Checkpoint best model (val LPIPS)

### 4.3 Model Optimization
- [ ] Export to TorchScript/ONNX
- [ ] Benchmark inference latency (target: <2ms)
- [ ] Profile memory usage

### 4.4 Evaluation
- [ ] Quantitative metrics (LPIPS, PSNR, SSIM)
- [ ] Qualitative comparison (visual grid)
- [ ] Ablation studies (w/o sim features, etc.)

**Success Criteria:**
- ✅ SR model LPIPS < 0.10 on test set
- ✅ Inference latency < 2ms per image
- ✅ Ablation results documented

---

## Phase 5: Benchmarking & Paper (Weeks 11-12)

### 5.1 Benchmark Suite
- [ ] Implement standard VLA tasks
  - [ ] Pick-and-place (3 variants)
  - [ ] Bimanual manipulation (2 tasks)
  - [ ] Mobile manipulation (1 task)
- [ ] Baseline evaluations
  - [ ] Domain randomization baseline
  - [ ] Isaac Sim baseline (if feasible)
- [ ] Performance benchmarks
  - [ ] Rendering FPS vs. batch size
  - [ ] End-to-end training throughput
  - [ ] GPU memory scaling

### 5.2 Paper Writing
- [ ] Draft paper structure (RSS/CoRL template)
- [ ] Write methodology section
- [ ] Generate all figures
  - [ ] System architecture diagram
  - [ ] Rendering pipeline visualization
  - [ ] Performance comparison plots
  - [ ] Qualitative results grid
- [ ] Write results section
- [ ] Write related work & discussion
- [ ] Internal review & revision

### 5.3 Code Release Preparation
- [ ] Clean up code & documentation
- [ ] Add installation guide
- [ ] Create demo scripts
- [ ] Add unit tests (target: >80% coverage)
- [ ] License compliance check
- [ ] Create release branch

**Success Criteria:**
- ✅ Paper draft complete
- ✅ Benchmark results published
- ✅ Code ready for public release

---

## Ongoing Tasks (Throughout All Phases)

### Documentation
- [ ] Update technical design doc as we learn
- [ ] Document all design decisions
- [ ] Keep README.md up-to-date
- [ ] Write API documentation (docstrings)

### Testing & Quality
- [ ] Add unit tests for each module
- [ ] Integration tests for end-to-end pipeline
- [ ] Performance regression tests
- [ ] Code review before merging

### Infrastructure
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Set up experiment tracking (wandb/mlflow)
- [ ] Set up compute cluster access
- [ ] Backup strategy for assets

---

## Research Questions to Explore (Parallel Track)

These are exploratory items that can run alongside the main implementation:

1. **How much does SR model help vs. direct high-res rendering?**
   - [ ] Ablation study comparing approaches

2. **Can we use NeRF instead of 3DGS for certain objects?**
   - [ ] Benchmark NeRF vs 3DGS speed/quality

3. **What's the sim2real transfer gap?**
   - [ ] Collect real-world images for comparison
   - [ ] Measure domain gap metrics

4. **Can we learn 3DGS from simulation + real images?**
   - [ ] Hybrid training pipeline experiment

5. **What's the minimal asset quality threshold?**
   - [ ] Downsample assets, measure policy performance

---

## Blockers & Dependencies

### Current Blockers
- None (Phase 0 complete)

### External Dependencies
- [ ] MuJoCo Warp access (verify licensing)
- [ ] GPU cluster access (for SR training)
- [ ] COLMAP environment (for asset capture)

---

## Next Session Action Items

When starting next session:
1. Read `docs/design/TECHNICAL_DESIGN.md` (Phase 1 section)
2. Check out Phase 1 development branch
3. Start with `1.1 Environment Setup` checklist
4. Update this TODO.md as you complete items

---

**Progress Tracking:**
- Phase 0 (Setup): ✅ Complete
- Phase 1 (gsplat PoC): 🔄 Not started
- Phase 2 (GaussianSensor): ⏸️ Waiting
- Phase 3 (Object Library): ⏸️ Waiting
- Phase 4 (Super-Resolution): ⏸️ Waiting
- Phase 5 (Benchmarking): ⏸️ Waiting
