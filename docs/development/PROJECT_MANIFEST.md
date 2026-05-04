# MuGS Project Manifest

**Project Name**: MuGS (MuJoCo Gaussian Splatting)  
**Created**: 2026-05-01  
**Status**: Setup Complete, Ready for Implementation  
**Location**: `/home/ununtu/metabot-workspace/mugs/`

---

## Project Summary

**Goal**: Build the first scalable, photorealistic MuJoCo-based Vision-Language-Action (VLA) benchmark for humanoid robots using 3D Gaussian Splatting rendering.

**Core Innovation**: Two-stage rendering pipeline
- Stage 1: Low-res batched 3DGS (160×120 @ 5000-8000 FPS)
- Stage 2: Learned super-resolution to high quality (640×480)

**Target Publication**: RSS 2026 / CoRL 2026

---

## Documentation Index

### Essential Reading (in order)

1. **README.md** (5 min)
   - Quick overview and installation
   - Basic usage examples

2. **docs/design/TECHNICAL_DESIGN.md** (30 min)
   - Complete system architecture
   - Implementation details for all components
   - API specifications and data formats

3. **docs/RESEARCH_IDEAS.md** (20 min)
   - Research questions and hypotheses
   - Future extensions and wild ideas
   - Prioritization matrix

### Metamemory Documents (Shared Knowledge)

Located in metamemory server, Folder ID: `5f2b6991-35d1-4e00-85a7-516beb8b48c6`

1. **Project Vision** - High-level architecture and goals
2. **Implementation Roadmap** - Phase-by-phase milestones
3. **Project Setup Complete** - Initial setup summary

Access via:
```bash
mm search "MuGS"
mm list 5f2b6991-35d1-4e00-85a7-516beb8b48c6
```

---

## Quick Start for New Session

When starting a dedicated implementation session:

```bash
# 1. Navigate to project
cd /home/ununtu/metabot-workspace/mjlab-3dgs-vla

# 2. Read metamemory
mm search "mjlab 3dgs vla"

# 3. Review current phase
cat docs/design/TECHNICAL_DESIGN.md | grep "Phase 1" -A 20

# 4. Set up environment (if not done)
pip install -e .
pip install mjlab gsplat torch torchvision

# 5. Start implementation
# See docs/design/TECHNICAL_DESIGN.md Section 2 for GaussianSensor skeleton
```

---

## Project Structure

```
mjlab-3dgs-vla/
├── README.md                    # Project overview
├── PROJECT_MANIFEST.md          # This file
├── LICENSE                      # Apache 2.0
├── pyproject.toml              # Python package config
│
├── src/mjlab_3dgs/             # Main package
│   ├── __init__.py
│   ├── sensors/                # GaussianSensor implementation
│   │   ├── __init__.py
│   │   ├── gaussian_sensor.py       (~300 LOC, core)
│   │   └── camera_config.py
│   ├── utils/                  # SE(3) transforms, helpers
│   │   ├── __init__.py
│   │   ├── gaussian_transforms.py   (~100 LOC)
│   │   └── splat_utils.py
│   ├── assets/                 # Asset management
│   │   ├── __init__.py
│   │   ├── object_library.py        (~200 LOC)
│   │   └── scene_loader.py
│   ├── sr_models/              # Super-resolution
│   │   ├── __init__.py
│   │   ├── simawaresr.py            (~400 LOC)
│   │   └── inference.py
│   └── scene_gen/              # Procedural generation
│       ├── __init__.py
│       └── procedural_sampler.py    (~300 LOC)
│
├── assets/                     # 3DGS assets
│   ├── objects/                # Object-level .ply files
│   │   └── ycb_library.yaml         (to be created)
│   ├── scenes/                 # Background scenes
│   │   └── default.ply              (to be created)
│   └── configs/                # Asset metadata
│
├── configs/                    # Environment configs
│   ├── envs/                   # VLA task configs
│   │   └── humanoid_pick_cfg.yaml   (to be created)
│   ├── sensors/                # Camera/sensor configs
│   │   └── gaussian_sensor_cfg.yaml (to be created)
│   └── sr/                     # SR model configs
│       └── simawaresr.yaml          (to be created)
│
├── docs/                       # Documentation
│   ├── design/
│   │   ├── TECHNICAL_DESIGN.md      ✅ Created (8000+ words)
│   │   ├── ASSET_FORMAT.md          (todo)
│   │   └── API_REFERENCE.md         (todo)
│   ├── guides/
│   │   ├── INSTALLATION.md          (todo)
│   │   └── TUTORIAL.md              (todo)
│   └── RESEARCH_IDEAS.md            ✅ Created
│
├── examples/                   # Demo scripts
│   ├── basic/
│   │   ├── render_object.py         (Phase 1 deliverable)
│   │   └── procedural_scenes.py     (Phase 2 deliverable)
│   └── advanced/
│       └── vla_pick_place.py        (Phase 3 deliverable)
│
├── scripts/                    # Utility scripts
│   ├── data_collection/
│   │   ├── reconstruct_object.sh    (Phase 2)
│   │   ├── extract_mesh.py          (Phase 2)
│   │   └── align_assets.py          (Phase 2)
│   ├── training/
│   │   ├── train_gsplat.py          (Phase 2)
│   │   └── train_sr.py              (Phase 4)
│   └── evaluation/
│       └── benchmark.py             (Phase 5)
│
└── tests/                      # Tests
    ├── unit/
    │   ├── test_gaussian_transforms.py
    │   └── test_object_library.py
    └── integration/
        ├── test_gaussian_sensor.py
        └── test_performance.py
```

---

## Implementation Status

### Phase 1: Foundation (Weeks 1-2) 🔄 CURRENT
- [x] Project structure created
- [x] Documentation written (README, TECHNICAL_DESIGN, RESEARCH_IDEAS)
- [x] Metamemory documents saved
- [ ] Dependencies installed
- [ ] gsplat PoC
- [ ] mjlab integration
- [ ] Performance validation

### Phase 2: Assets (Weeks 3-5) ⏳ PENDING
- [ ] 10 YCB objects as 3DGS
- [ ] Object library config
- [ ] Procedural scene sampler

### Phase 3: Core Pipeline (Weeks 6-7) ⏳ PENDING
- [ ] GaussianSensor complete
- [ ] VLA pick-and-place task
- [ ] 10k episodes generated

### Phase 4: Super-Resolution (Weeks 8-10) ⏳ PENDING
- [ ] Real robot data collected
- [ ] SimAwareSR trained
- [ ] Sim2real validation

### Phase 5: Benchmark Release (Weeks 11-12) ⏳ PENDING
- [ ] GitHub repo public
- [ ] arXiv paper submitted
- [ ] Community launch

---

## Key Design Decisions

1. **Physics**: MuJoCo Warp (10× faster than CPU)
2. **Rendering**: gsplat library (Apache-2.0, batched)
3. **Architecture**: Two-stage (low-res 3DGS + SR)
4. **Assets**: Object-level digital twins (modular)
5. **SR Model**: SwinIR-light (900K params, fast)

---

## Resource Requirements

- **Compute**: 1× A100 GPU (80GB) or 2× A6000
- **Storage**: ~1TB (episodes + assets)
- **Time**: 3 months (single PhD student full-time)
- **Budget**: ~$500-1000 (AWS for SR training, optional)

---

## Success Metrics

**Technical**:
- Rendering: ≥5000 FPS @ 4096 envs
- Visual quality: LPIPS < 0.15 vs real
- Sim2real: ≥70% zero-shot success

**Scientific**:
- Paper accepted at RSS/CoRL
- 100+ GitHub stars in 6 months
- 5+ external research groups adopt

---

## Important Files

| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Project overview | ✅ Done |
| `docs/design/TECHNICAL_DESIGN.md` | Complete spec | ✅ Done |
| `docs/RESEARCH_IDEAS.md` | Research questions | ✅ Done |
| `src/mjlab_3dgs/sensors/gaussian_sensor.py` | Core renderer | 🔄 Next |
| `examples/basic/render_object.py` | First demo | 🔄 Next |

---

## Next Actions (Priority Order)

1. **Read docs** (30 min)
   - TECHNICAL_DESIGN.md Sections 1-2
   - Understand GaussianSensor interface

2. **Environment setup** (30 min)
   ```bash
   pip install mjlab gsplat torch
   python -c "import gsplat; print(gsplat.__version__)"
   ```

3. **gsplat Hello World** (2 hours)
   - Download sample .ply (or create synthetic)
   - Render with gsplat
   - Display with matplotlib
   - Goal: Understand gsplat API

4. **mjlab Sensor skeleton** (2 hours)
   - Copy mjlab's CameraSensor as template
   - Modify for GaussianSensor
   - Stub out methods
   - Goal: Compiles and env runs (even if rendering is dummy)

5. **Integration PoC** (4 hours)
   - Load simple .ply in GaussianSensor.initialize()
   - Render in _compute_data()
   - Return RGB to env
   - Goal: See 3DGS image in env obs

**After Step 5**: Phase 1 is ~70% complete. Update metamemory with progress and blockers.

---

## Critical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low-res loses details | Medium | High | Test early on grasping task |
| SR doesn't generalize | Medium | Medium | Train on diverse scenes |
| Real robot unavailable | High | Medium | Use public datasets |
| FPS target not met | Low | High | Profile + optimize early |

---

## Contact & Collaboration

**Project Owner**: User (PhD student)  
**AI Assistant**: wusagi  
**Metamemory**: `/mjlab-3dgs-vla/` folder  
**Next Session**: Start Phase 1 implementation

---

## License

Apache 2.0 - See LICENSE file

---

**This manifest is a living document. Update as the project evolves.**
