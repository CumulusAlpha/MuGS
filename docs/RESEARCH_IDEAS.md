# Research Ideas & Future Directions

> **Advanced research questions and future extensions for MJLab-3DGS-VLA**

**Version**: 1.0  
**Last Updated**: 2026-05-01

---

## Core Research Questions

### 1. **Does 3DGS+SR beat traditional sim2real methods?**

**Hypothesis**: Photorealistic 3DGS rendering with learned SR will achieve better sim2real transfer than domain randomization or style transfer methods, at comparable compute cost.

**Experiment Design**:
- **Baseline 1**: DR (domain randomization) with OpenGL rendering
- **Baseline 2**: CycleGAN style transfer on OpenGL renders  
- **Baseline 3**: Isaac Sim ray-tracing (slow but high quality)
- **Ours**: Low-res 3DGS + SimAwareSR

**Metrics**:
- Zero-shot success rate on real robot
- Sample efficiency (episodes needed to reach 80% success)
- Visual quality (LPIPS, FID vs real images)
- Compute cost (FPS, memory, training time)

**Tasks**: Pick-and-place, object rearrangement, drawer opening

**Expected Outcome**: 3DGS+SR matches Isaac Sim quality at 10× speed, beats DR/CycleGAN by 15-20% success rate.

---

### 2. **What is the optimal low-res resolution for SR?**

**Question**: Is 160×120→640×480 the sweet spot, or should we go higher/lower?

**Ablation Study**:
| Low-res | High-res | SR scale | Rendering FPS | SR latency | Visual quality (LPIPS) |
|---------|----------|----------|---------------|------------|----------------------|
| 80×60 | 640×480 | 8× | 20k | ~100ms | ? |
| 120×90 | 640×480 | ~5× | 12k | ~80ms | ? |
| **160×120** | **640×480** | **4×** | **8k** | **~50ms** | **?** (baseline) |
| 240×180 | 960×720 | 4× | 3k | ~50ms | ? |
| 320×240 | 640×480 | 2× | 2k | ~30ms | ? |

**Hypothesis**: There's a knee in the curve around 160×120 where SR can still recover fine details needed for grasping (e.g., object edges, texture).

**Critical test**: Can the policy grasp thin objects (pens, cutlery) from low-res? If not, increase resolution.

---

### 3. **Object-level twins vs full-scene reconstruction**

**Two Paradigms**:
- **A. Object-centric** (current design): Reconstruct objects individually, compose procedurally
- **B. Scene-centric**: Reconstruct entire real scenes (room + objects together)

**Trade-offs**:
| Aspect | Object-centric (A) | Scene-centric (B) |
|--------|-------------------|------------------|
| Diversity | Infinite (procedural) | Limited (# real scenes) |
| Reconstruction effort | Medium (per-object) | High (per-scene) |
| Physical accuracy | High (objects movable) | Medium (baked together) |
| Real-world alignment | Medium (scene mismatch) | High (exact replica) |

**Hybrid approach**: Use both! Object-centric for training diversity, scene-centric for final sim2real validation (exact twin of real lab).

**Research question**: Does training on 1000 procedural scenes generalize better than training on 10 exact scene twins?

---

### 4. **Can we close the loop: Real→Sim→Real?**

**Real2Sim Pipeline** (reverse direction):
1. Robot performs task in real world, records RGB-D + trajectory
2. Reconstruct scene as 3DGS from robot's ego-centric views
3. Replay trajectory in sim with reconstructed scene
4. Measure replay error (pose deviation, contact forces)
5. Use error to refine 3DGS or physics parameters

**Use case**: Debugging real-robot failures in sim (like NVIDIA Isaac Sim's "Digital Twin" feature).

**Technical challenge**: Ego-centric 3DGS reconstruction is harder than multi-view turntable. Need SLAM-like tracking.

**Potential solution**: Integrate with [NeRF-SLAM](https://github.com/ToniRV/NeRF-SLAM) or use robot's onboard odometry.

---

### 5. **Differentiable 3DGS + Differentiable Physics**

**Motivation**: Enable gradient-based optimization through the entire sim stack.

**Use cases**:
- **System ID**: Optimize 3DGS colors/geometry AND MuJoCo contact params to match real trajectories
- **Policy gradient through rendering**: Backprop policy loss through SR model and 3DGS renderer
- **Inverse graphics**: Given real RGB, optimize 3DGS to match

**Technical requirements**:
- gsplat is already differentiable ✅
- MuJoCo Warp is **NOT differentiable** ❌ (vs MJX-JAX which is)
- SR model is differentiable ✅

**Feasibility**:
- **Short-term**: Differentiable SR only (freeze physics) — useful for domain adaptation
- **Long-term**: Switch to MJX-JAX backend for full differentiability — but lose 10× speed

**Research question**: Is end-to-end differentiability worth the speed trade-off for VLA training? Probably not for pure RL, but maybe for imitation learning with real demo matching.

---

### 6. **Language-conditioned procedural scenes**

**Problem**: How to generate language annotations for procedurally generated scenes?

**Current VLA datasets**: Human-annotated ("pick up the red mug")

**Our challenge**: 100k procedural scenes × human annotation = infeasible

**Solutions**:

**A. Template-based**:
```python
def generate_instruction(scene):
    obj = random.choice(scene.objects)
    color = obj.metadata['color']
    category = obj.metadata['category']
    
    templates = [
        f"pick up the {color} {category}",
        f"grasp the {category} on the left",
        f"move the {color} object to the bin"
    ]
    return random.choice(templates)
```
✅ Cheap, but limited diversity

**B. LLM-based**:
- Feed scene graph to GPT-4: `scene_graph_to_language(objects, spatial_relations)`
- LLM generates diverse phrasings
- Cost: ~$0.001/scene, so 100k scenes = $100 (acceptable)

**C. Vision-language model**:
- Render scene from 3rd-person view
- Feed to CLIP/LLaVA: `generate_instruction(image)`
- More grounded, but may hallucinate

**Recommended**: Hybrid of A+B. Templates for common tasks, LLM for diversity.

---

### 7. **Multi-modal observations beyond RGB**

**Current**: RGB-only

**Extensions**:
- **Depth**: 3DGS can render depth (from splat distances) — nearly free
- **Segmentation**: Per-object masks (from splat_to_body_idx) — free
- **Normals**: From Gaussian orientations — cheap
- **Optical flow**: Temporal difference of splat projections — cheap

**Research question**: Do VLA policies trained on RGB+depth+seg outperform RGB-only? How much?

**Hypothesis**: Depth helps for 3D manipulation (grasping), seg helps for object-centric attention. But RGB-only should work if resolution is high enough (like human vision).

**Practical benefit**: Depth is free with 3DGS, while Isaac Sim needs extra ray-tracing pass.

---

### 8. **Temporal consistency and video prediction**

**Observation**: Our rendering is temporally consistent (Gaussians bound to rigid bodies), but SR model is per-frame.

**Problem**: Per-frame SR can flicker (inconsistent upsampling across time).

**Solutions**:

**A. Temporal SR model**:
- Input: (T, H, W, 3) low-res video
- Output: (T, H', W', 3) high-res video
- Architecture: 3D conv or temporal transformer

**B. Optical flow guidance**:
- Compute flow from 3DGS motion
- Use flow to warp previous high-res frame
- SR model only fills in residuals

**Research question**: Does temporal consistency matter for RL? Probably not (policies are frame-wise), but matters for video generation / dataset visualization.

**Recommended**: Start with per-frame SR (simpler), add temporal if needed later.

---

### 9. **Scaling to 10k+ environments**

**Current target**: 4096 envs on single A100

**Question**: Can we scale to 10k+ envs for internet-scale VLA training?

**Bottlenecks**:
- GPU memory: 3DGS assets must fit in VRAM
- Compute: Rasterization scales O(N_env × N_splat)

**Solutions**:

**A. Multi-GPU**:
- Split envs across 4-8 GPUs
- Each GPU: 2k envs, communicate via NCCL for policy updates
- Near-linear scaling if SR model is replicated

**B. Gaussian pruning**:
- Current: 90% pruning (GS-Playground level)
- Aggressive: 95% pruning (5% of splats kept)
- Trade-off: quality vs memory

**C. Level-of-detail (LOD)**:
- Distant objects: fewer splats
- Close objects: full detail
- Dynamic pruning based on camera distance

**Expected outcome**: 10k envs feasible on 8×A100 with aggressive pruning.

---

### 10. **Integration with Foundation Models**

**VLA models are getting huge**: OpenVLA (7B), RT-2-X (55B)

**Question**: How to integrate our sim with these models?

**Use cases**:

**A. Data generation**:
- Generate 1M episodes in sim
- Format as OpenVLA training data
- Fine-tune OpenVLA on sim data
- Zero-shot transfer to real robot

**B. Policy distillation**:
- Train large VLA in sim (leveraging our scale)
- Distill to small policy for real-robot deployment
- Sim2real gap reduced because sim is photorealistic

**C. Sim-in-the-loop RL**:
- VLA policy initialized from pretrained weights
- Fine-tune with RL in our sim (cheap exploration)
- Transfer to real (warm-start)

**Technical requirement**: Our observation format must match OpenVLA/RT-2 specs (224×224 RGB, language tokens).

**Action item**: Add `OpenVLAWrapper` that resizes our 640×480 outputs to 224×224.

---

## Future Extensions

### Short-term (3-6 months)

1. **More tasks**: Beyond pick-and-place
   - Drawer opening (contact-rich)
   - Liquid pouring (needs particle sim — out of scope for 3DGS)
   - Multi-object rearrangement (tests generalization)

2. **More robots**: Beyond humanoid
   - Mobile manipulators (quadruped + arm)
   - Dual-arm humanoid (bimanual tasks)
   - Dexterous hands (fine manipulation)

3. **Better SR models**:
   - Diffusion-based SR (slower but higher quality)
   - Test newer architectures (SwinIR v2, HAT, etc.)

### Medium-term (6-12 months)

4. **Real robot integration**:
   - Partner with lab that has humanoid (Unitree H1, Tesla Optimus, etc.)
   - Run 1000-episode sim2real validation
   - Publish sim2real benchmark results

5. **Benchmark standardization**:
   - Define evaluation protocol (tasks, metrics, baselines)
   - Open leaderboard (like RoboMimic, Robosuite)
   - Community adoption (10+ papers using our sim)

6. **Interactive humans**:
   - 3DGS avatars of humans (from video capture)
   - Human-robot collaboration tasks
   - Language instructions from real human demonstrators

### Long-term (12+ months)

7. **Embodied AI beyond manipulation**:
   - Navigation + manipulation (mobile humanoids)
   - Long-horizon tasks (make coffee, clean room)
   - Generalization to unseen scenes (zero-shot)

8. **Foundation model co-evolution**:
   - Co-train VLA and 3DGS jointly (end-to-end)
   - Use VLA attention maps to improve 3DGS sampling (where to add detail)
   - Sim→Real→Sim loop: VLA guides scene reconstruction

9. **Open-source ecosystem**:
   - Integrate with IsaacLab (they add 3DGS support using our code)
   - Contribute back to mjlab (GaussianSensor upstreamed)
   - Asset marketplace (community-contributed 3DGS objects)

---

## Wild Ideas (Speculative)

### 1. **Neural Physics via 3DGS**

Instead of MuJoCo physics, learn physics directly from 3DGS:
- Each Gaussian has velocity, mass
- Collision detection via splat overlap
- Learned dynamics model (GNN or transformer)
- **Crazy?** Yes. **Cool?** Also yes.

### 2. **Generative Scene Synthesis**

Instead of procedural placement, generate scenes with diffusion:
- Text → 3D scene (like Shap-E, but with 3DGS)
- "A kitchen with a toaster and coffee mug" → full 3DGS scene
- Infinite diversity, language-grounded

**Challenge**: Current 3D diffusion models are slow, low-res. Wait 2-3 years.

### 3. **Sim2Real2Sim GAN**

Train a CycleGAN but for full scenes:
- Sim 3DGS scene → render → Real image style
- Real image → 3DGS reconstruction → Sim physics
- Adversarial training to match distributions
- End result: "sim that looks real" AND "real that has physics"

**Why?** Best of both worlds: real visual diversity + perfect sim physics.

---

## Prioritization Matrix

| Idea | Impact | Feasibility | Timeline | Priority |
|------|--------|-------------|----------|----------|
| 3DGS+SR vs baselines (Q1) | High | High | 3 months | **P0** |
| Object-level twins (Q3) | High | High | 2 months | **P0** |
| Optimal resolution (Q2) | Medium | High | 1 month | **P1** |
| Language annotation (Q6) | High | Medium | 2 months | **P1** |
| Multi-modal obs (Q7) | Medium | High | 1 month | **P1** |
| Real2Sim (Q4) | High | Medium | 6 months | **P2** |
| Differentiable stack (Q5) | Low | Low | 6 months | **P3** |
| Scaling 10k envs (Q9) | Medium | Medium | 4 months | **P2** |
| Foundation model integration (Q10) | High | High | 3 months | **P1** |

**Phase 1 focus**: P0 and P1 items (get core working + validate hypotheses).

---

## Collaboration Opportunities

### With OpenVLA Team
- Use their model as VLA backbone
- Contribute sim data to their training set
- Co-publish benchmark results

### With mjlab Maintainers
- Upstream GaussianSensor to official mjlab
- Collaborate on MuJoCo Warp optimizations

### With GS-Playground Authors
- Share 3DGS asset datasets
- Cross-validate rendering performance
- Potentially merge codebases if they open-source

### With Robotics Labs
- Berkeley, Stanford, CMU, etc.
- Provide them with free sim tool
- Get real robot validation data
- Co-author sim2real paper

---

## Success Criteria (12 months)

**Technical**:
- ✅ 5000 FPS rendering @ 4096 envs
- ✅ LPIPS < 0.15 vs real images
- ✅ 70%+ sim2real zero-shot success

**Scientific**:
- 📄 1 RSS/CoRL paper accepted
- 🌟 100+ GitHub stars
- 👥 5+ external research groups using it
- 📊 1M+ VLA episodes generated

**Community**:
- 📝 10+ tutorial blog posts / videos
- 💬 Active Discord/Slack channel
- 🎓 Course adoption (at least 1 university)

---

**Document Status**: Brainstorm  
**Next Review**: After Phase 1 completion  
**Contributors**: Add your ideas!
