# MuGS Project Memory & Context

This file records project context, key decisions, and links to memory systems for AI assistants working across sessions.

---

## Quick Access

### Metamemory (Shared Knowledge Store)
```bash
# Search for MuGS documents
mm search "MuGS"

# List all project documents in MuGS folder
mm list 5f2b6991-35d1-4e00-85a7-516beb8b48c6

# Get specific document
mm get <doc_id>
```

**Metamemory Folder ID**: `5f2b6991-35d1-4e00-85a7-516beb8b48c6`

**Documents Saved**:
1. **"MuGS Project Vision"** - High-level architecture, goals, two-stage rendering design
2. **"MuGS Implementation Roadmap"** - 5-phase development plan (12 weeks)
3. **"MuGS Project Setup Complete"** - Phase 0 completion summary

### Auto-Memory (Workspace Memory)
Location: `/home/ununtu/.claude/projects/-home-ununtu-metabot-workspace/memory/`

**Relevant Files**:
- `project_mjlab_3dgs_vla.md` - Project goals, architecture, research value, timeline
- `reference_mjlab_3dgs_vla.md` - Documentation paths, quick retrieval commands

---

## Project Summary

**Full Name**: MuGS (MuJoCo Gaussian Splatting)  
**Short Description**: Photorealistic VLA benchmark using MuJoCo + 3D Gaussian Splatting  
**Status**: Phase 0 Complete ✅, Ready for Phase 1  
**Target**: RSS/CoRL 2026 publication

### Core Innovation
Two-stage rendering pipeline for speed + quality:
1. **Stage 1**: Low-res 3DGS (160×120 @ 5000-8000 FPS)
2. **Stage 2**: Learned super-resolution (→ 640×480 photorealistic)

**Result**: 10× faster than Isaac Sim with similar visual quality

---

## Key Design Decisions

### 1. Project Name: "MuGS"
**Date**: 2026-05-02  
**Reason**: Short, memorable, technical (MuJoCo + Gaussian Splatting)  
**Previous name**: MJLab-3DGS-VLA  
**Impact**: Renamed all docs, package name, directory

### 2. Two-Stage Rendering Architecture
**Date**: 2026-05-01  
**Why**: Direct high-res 3DGS too slow (500 FPS vs 5000 FPS target)  
**Trade-off**: Added SR model complexity, but 10× speed gain  
**Validation**: Phase 4 will measure quality vs speed empirically

### 3. gsplat as Rendering Backend
**Date**: 2026-05-01  
**Alternatives**: Original 3DGS repo, Nerfstudio  
**Chosen**: gsplat - Apache-2.0 license, batched rendering, PyTorch native  
**Why**: Research-friendly license, better for parallelization

### 4. Object-Level (not Scene-Level) Assets
**Date**: 2026-05-01  
**Why**: Modularity - can compose new scenes from library  
**Trade-off**: More assets to manage, but better for procedural generation  
**Implementation**: Each object = PLY file + YAML metadata

---

## Documentation Map

All documentation is in this repository:

```
/home/ununtu/metabot-workspace/mugs/

Essential Reading:
├── TODO.md                      ← Current phase tasks & progress
├── PROJECT_MANIFEST.md          ← Full project index
├── README.md                    ← Quick overview
└── docs/
    ├── design/TECHNICAL_DESIGN.md   ← 8000+ word implementation guide
    └── RESEARCH_IDEAS.md            ← Research questions & experiments

Context & Memory:
└── .context/
    └── MEMORY.md                ← This file
```

---

## Research Context

### Problem
- Photorealistic simulators (Isaac Sim) too slow: 100 FPS
- Fast rendering (domain randomization) too low quality
- No scalable photorealistic MuJoCo benchmark exists

### Our Solution
- 3DGS rendering: photorealistic + fast
- Two-stage pipeline: low-res batch → SR upscale
- MuJoCo Warp: GPU physics (10× faster)
- Object library: modular, reusable assets

### Expected Contribution
1. First 3DGS + SR two-stage rendering for robotics simulation
2. First photorealistic MuJoCo VLA benchmark
3. 10× speedup vs Isaac Sim, 5× quality vs domain randomization
4. Open-source asset library + tools

---

## Performance Targets

| Metric | Target | Baseline | Notes |
|--------|--------|----------|-------|
| Rendering FPS | 5000-8000 | Isaac Sim: 100 | @ 160×120, 4096 parallel envs |
| SR Latency | <2ms | - | Per image |
| Image Quality | LPIPS <0.10 | DR: ~0.30 | vs ground truth |
| Object Assets | 20+ | - | Phase 3 deliverable |

---

## Development Timeline

**Created**: 2026-05-01  
**Phase 0 Complete**: 2026-05-02  
**Expected Phase 1 Start**: 2026-05-03  
**Target Paper Submission**: 2026-09 (RSS) or 2026-02 (CoRL)

### Phase Breakdown
- **Phase 0**: Setup (✅ Complete)
- **Phase 1**: gsplat PoC (Weeks 1-2)
- **Phase 2**: GaussianSensor Core (Weeks 3-5)
- **Phase 3**: Object Library (Weeks 6-8)
- **Phase 4**: Super-Resolution (Weeks 9-10)
- **Phase 5**: Benchmarking & Paper (Weeks 11-12)

---

## Important Notes for Future Sessions

### When Starting a New Session
1. Read `TODO.md` first - check current phase
2. Retrieve latest context from metamemory: `mm list 5f2b6991`
3. Read relevant section of `TECHNICAL_DESIGN.md`
4. Update TODO.md as you complete tasks

### When Making Key Decisions
1. Document in this file (`.context/MEMORY.md`)
2. Update `TECHNICAL_DESIGN.md` if architecture changes
3. Save to metamemory if valuable for other projects

### When Completing a Phase
1. Update TODO.md phase status
2. Create metamemory document summarizing learnings
3. Update auto-memory if timeline/goals shift

---

## Git Repository

**Initialized**: 2026-05-02  
**Remote**: TBD (will add GitHub remote later)  
**Main Branch**: `main`  
**Development Branch**: Create per-phase (e.g., `phase-1-gsplat-poc`)

### Commit Convention
Using conventional commits:
- `feat(component):` - New feature
- `fix(component):` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions
- `refactor:` - Code refactoring
- `perf:` - Performance improvements

---

## Contact & Collaboration

**Primary Researcher**: User (hqyseller@gmail.com)  
**AI Assistants**: Claude Code (various bots via MetaBot)  
**Collaboration Mode**: Asynchronous via metamemory & auto-memory

---

## Changelog

### 2026-05-02
- Created `.context/MEMORY.md` file
- Initialized git repository
- Created comprehensive TODO.md (5 phases)
- Renamed project from "MJLab-3DGS-VLA" to "MuGS"
- Updated all documentation with new name
- Saved project context to auto-memory
- Phase 0 (Setup) marked complete

### 2026-05-01
- Initial project setup
- Created 12k+ words of documentation
- Saved vision & roadmap to metamemory (folder `5f2b6991`)
- Scaffolded Python package structure

---

**Last Updated**: 2026-05-02
