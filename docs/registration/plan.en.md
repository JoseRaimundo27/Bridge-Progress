# Module II.2 — OBBP-ICP registration: work plan

**Team:** Oscar and Gabriel · **Branch:** `bridge-segmentation` · **Updated:** October 8, 2026

This document summarises the planned work on Module II.2. Each task is detailed in Jira. The figures come from the [initial analysis](initial-analysis.en.md).

---

## 1. Goal

Align the **as-built** point cloud of the bridge (drone scan, already cleaned by RandLA-Net) with the **as-planned** point cloud generated from the BIM.

The module outputs:
- the **registered scan**;
- the 4×4 **transform matrix**;
- the **mean distance `D_avg`**, which Module III uses to set its threshold `O_thr = D_avg + C`.

**Reference:** Tang & Shi (2026), *Module II*, Algorithm 1 (Fig. 4), Tables 1 and 2, Fig. 10.

## 2. Inputs and outputs

| Direction | With | Data |
|---|---|---|
| Input | Module I (BIM) | As-planned cloud `.ply`, in metres, with **uniform density** |
| Input | Module II.1 (RandLA-Net) | As-built scan `.ply`, bridge only |
| Output | Module III | `scan_registered.ply`, `transform.json`, `metrics.json` (with `D_avg`) |

## 3. Code layout

```
ModuleTwo Registration/
├── AsBuilt/  AsPlanned/        # input data (not in git)
├── outputs/                    # results (not in git)
└── Python/
    ├── run_registration.py     # entry point: load → register() → save
    ├── inspect_clouds.py       # data sheet (T0.3)
    ├── benchmark_rotations.py  # rotation benchmark (T3.2)
    ├── registration/           # module code, one function per step
    ├── tests/                  # pytest tests on synthetic bridges
    └── legacy/obbp_icp_v0.py   # old script, to delete at the end
```

Each function to write raises `NotImplementedError("Tx.y")`, where `Tx.y` is its Jira task. Tests to enable are marked `skip(reason="Tx.y")`.

## 4. Before we start

The analysis of October 8 found three things to fix first (two are done):

| Action | Who | Why |
|---|---|---|
| ✅ Pull Gabriel's commits and merge the October 2 fixes (Modules I and II.1) | Oscar | Done on October 8 |
| Regenerate the as-planned cloud with uniform density | Oscar | With 2000 points per element, registration always fails (E8). To do with the real IFC models |
| ✅ Set the git identity | Oscar | Done on October 8 |

## 5. Tasks

Size: **S** ≈ ½ day · **M** ≈ 1–2 days · **L** ≈ 3–5 days.
Priority after the analysis: 🔴 high · 🟠 normal · 🟡 depends on the data (T0.3).

**Current split (October 8):** Oscar takes all tasks for now. The "Who" columns (A / B) keep the split planned in Jira for later.

### Phase 0 — Setup

| Task | Size | Who | Priority | Expected result |
|---|---|---|---|---|
| T0.1 Data and baseline | S | Both | 🔴 | Baseline on D19: `D_avg`, matrix, runtime, screenshots. Check visually that the result is not flipped |
| T0.2 Clean the folder | S | A | ✅ done | — |
| T0.3 Data sheet | M | B | 🔴 | Table for D19 and S07. **Added after the analysis:** BIM density per element, float32 or float64, one known dimension to check the scale |

### Phase 1 — Fix the algorithm

| Task | Size | Who | Priority | Expected result |
|---|---|---|---|---|
| T1.1 Refactoring | M | A | 🔴 | One function per step. Same result as the baseline with the old parameters |
| T1.2 Recentering | S | A | 🟡 | Common float64 offset. Lower priority: Open3D already computes in float64 (E3) |
| T1.3 XY axes (2D PCA) | M | A | 🟠 | Angle found within ±1°, no NaN. The prototype reaches < 0.3° (E9) |
| T1.4 Z leveling | M | A | 🟡 | Only if T0.3 shows a tilt above ~10° (E4) |
| T1.5 Multi-scale ICP and candidate choice | M | B | 🔴 | No more flipped results. Prototype: 8/8 (E12) |
| T1.6 Point-to-plane | S | B | 🟠 | Comparison table. Point-to-plane is 2× faster on synthetic bridges (E10) |
| T1.7 Scale | S | B | 🟡 | Only if T0.3 finds a scale error. 2 % is enough to break the result (E6) |
| **T1.8 Failure check** *(proposed)* | S | to decide | 🟠 | Warn when the registration is doubtful, instead of reporting success |

### Phase 2 — Inputs, outputs, integration

| Task | Size | Who | Priority | Expected result |
|---|---|---|---|---|
| T2.1 Arguments and paths | S | A | 🟠 | `make m2-2` and the command line work without editing the code. `--viz` off by default (otherwise it blocks without a screen) |
| T2.2 Export for Module III | S | A | 🟠 | `scan_registered.ply`, `transform.json`, `metrics.json` written at each run |
| T2.3 Metrics | M | B | 🟠 | Median, 95th percentile, BIM→scan distance, heat map. Agree on `D_avg` with Module III (E11) |

### Phase 3 — Validation

| Task | Size | Who | Priority | Expected result |
|---|---|---|---|---|
| T3.1 Synthetic tests | M | A | 🟠 | All tests pass; error < 0.5° and < 2 × voxel |
| T3.2 Rotation benchmark | L | B | 🟠 | Table like Table 2 of the paper. Success measured against the known transform |
| T3.3 Effect of segmentation | M | B | 🟠 | Table like Table 1 of the paper (raw / manual / RandLA-Net). With 22 % clutter left by RandLA-Net, OBBP-ICP fails 4/4 on synthetic data |
| T3.4 Partial bridge | L | Both | 🔴 **move earlier** | Normal case during construction: 0/12 today, 10/12 with FPFH + RANSAC (E5). FPFH + RANSAC also handles the noisy RandLA-Net output |
| T3.5 Second bridge (S07) | S | Both | 🟠 | Same metrics as D19, same parameters |

### Phase 4 — Delivery

| Task | Size | Who | Expected result |
|---|---|---|---|
| T4.1 Documentation and PR | S | Both | Module README, docstrings, PR `bridge-segmentation` → `main` with the T3.2 and T3.3 results |

## 6. Work order

```
Before we start (merge, regenerated BIM cloud)
        │
T0.1 → T0.3 ─┬─► T1.1 ─► T1.3 ─► T1.2 ─► (T1.4) ──────────────┐
             │                                                 ├─► T2.1 ─► T2.2 ─► T3.1 ─► T3.2 ─► T3.5 ─► T4.1
             └─► T1.5 ─► T1.8 ─► T1.6 ─► (T1.7) ─► T2.3 ───────┤
                                                               │
             T3.4 (FPFH + RANSAC strategy), right after T1.1   ┤
             T3.3 (when the II.1 team delivers the RandLA-Net scan) ┘
```

**Changes from the first plan:**
- T3.4 starts earlier: it is the main risk of the module.
- T1.2 moves after T1.3: it is less urgent.
- T1.8 is added.

**Important rule:** T1.1 fills every file of the package. **Merge it before** person B works on `fine_alignment.py` (T1.5), to avoid conflicts.

## 7. How we work

- **One task = one or more commits** whose message names the task, e.g. `feat(T1.3): main axes by 2D PCA`.
- **Before pushing:**
  - tests pass: `cd "ModuleTwo Registration/Python" && python -m pytest tests`;
  - the other person has reviewed the code.
- **At the end of each task:** update its status in Jira, with the measured result.
- **Measure before and after:** compare each improvement with the baseline (T0.1) or with the [initial analysis](initial-analysis.en.md).

## 8. When is a task done?

1. The code is written; no `NotImplementedError` is left for this task.
2. The task's tests are enabled (no `skip`) and pass.
3. The result is measured and logged.
4. The other person has reviewed the code.

## 9. Glossary

| Term | Meaning |
|---|---|
| As-built | What is actually built: the site scan |
| As-planned | What is planned: the cloud generated from the BIM |
| Registration | Finding the motion (rotation + translation) that puts the scan on the BIM |
| OBB | Oriented bounding box: gives the long axis of the bridge for a first alignment |
| ICP | Iterative Closest Point: refines the alignment by matching each point to its nearest neighbour |
| `fitness` | Share of scan points with a BIM neighbour closer than the threshold |
| RMSE | Root mean square error of the matched points |
| `D_avg` | Mean distance from each scan point to the nearest BIM point |
| FPFH + RANSAC | Alignment from local shape descriptors; robust to partial clouds |
| Voxel | Grid cell used to downsample the cloud |
