# Module II.2 (registration) — Initial analysis and tests

**Date:** Thursday, October 8, 2026 · **Branch:** `bridge-segmentation` (commit `84168a3`) · **Author:** Oscar (with Claude Code)
**Version française :** [analyse-initiale.fr.md](analyse-initiale.fr.md) (full details)

This document checks the state of Module II.2 **before** we start the tasks of the plan (T0.1 to T4.1). It answers three questions:
1. Do the current code and installation work?
2. Are the problems listed in the plan real? Which ones matter most?
3. Do the planned fixes work? Should the plan change?

## Key findings

| # | Finding | Severity | Task |
|---|---|---|---|
| 1 | **A partially built bridge makes registration fail every time** (scan covering 30–70 % of the bridge), even with the planned fixes. FPFH + RANSAC succeeds in 10 cases out of 12. | 🔴 | T3.4, move earlier |
| 2 | **The current BIM cloud (2000 points per element) makes registration fail** (0/4). A uniform density works (4/4). | 🔴 | Module I, T0.3 |
| 3 | The flipped result comes from a **tie on `fitness` (1.000)** between candidates with the 20 m threshold; the code keeps the first candidate. Multi-scale ICP fixes it: 8/8, including the near-symmetric bridge. | 🔴 | T1.5 confirmed |
| 4 | **`D_avg` mostly measures the BIM point spacing**: 0.085 m with a perfect scan. It is also very sensitive to outliers (4.7 m mean vs 0.14 m median). This affects the Module III threshold `O_thr = D_avg + C`. | 🟠 | T2.3, Module III |
| 5 | **A 2 % scale error moves points by more than 0.5 m**, but `D_avg` only goes from 0.085 to 0.135 m. | 🟠 | T0.3, T1.7 |
| 6 | The old axis computation gives **up to 74° error on a tall cloud** (single pier). 2D PCA gives less than 0.3°. | 🟠 | T1.3 confirmed |
| 7 | The old code handles a **tilt of up to 10°**; it fails from 20° of pitch. The planned leveling fixes it. | 🟡 | T1.4, depends on T0.3 |
| 8 | **UTM coordinates are not a problem during computation** (Open3D uses float64). The only risk is float32 storage (0.25 m error). | 🟡 | T1.2, lower priority |
| 9 | **Point-to-plane ICP: same accuracy, 2× faster** than point-to-point. | 🟢 | T1.6 |
| 10 | The current script prints "Alinhamento concluído!" **even when the result is flipped**, and its Open3D windows **block forever** without a screen. | 🟠 | T0.1, T2.1 |
| 11 | **With a realistic RandLA-Net segmentation (22 % clutter left), OBBP-ICP fails 4/4.** FPFH + RANSAC after outlier removal succeeds 4/4. | 🔴 | T3.3, T3.4 |

## 1. Method

- **Data:** the real data (D19, S07) is not in the repository. All tests use the **synthetic bridges of `tests/conftest.py`**: asymmetric and near-symmetric. Each scan is the same bridge with 1 cm noise, moved by a **known transform**.
- **Success:** because the transform is known, we measure the **real error**: the mean distance between each registered point and its true position. **Success = error < 20 cm.** This is more reliable than `D_avg`, which does not always detect a flipped result.
- **Code tested:**
  - **old code:** `legacy/obbp_icp_v0.py`, unchanged, with the `make m2-2` parameters (voxel 0.2 m, ICP threshold 20 m) unless stated otherwise;
  - **prototype:** a minimal version of the planned fixes (recentering, 2D PCA axes, optional leveling, multi-scale ICP 1 / 0.3 / 0.1 m, choice on fitness at the finest threshold then RMSE), written only for these tests;
  - **references:** ICP only, and FPFH + RANSAC + ICP.
- **Environment:** Ubuntu 26.04 on WSL2, Python 3.12, Open3D 0.20.0 (CPU), PyTorch 2.13.0 (CPU), installed like `make install` does. No GPU.

## 2. Repository state

- Gabriel's commits of Oct 5–6 are on `origin`. Oscar's local branch is 3 commits behind.
- Oscar's fixes of Oct 2 (Modules I and II.1, see [MODIFICATIONS.md](../../MODIFICATIONS.md), in French) are **not committed** yet.
- A test merge (in a separate copy) shows that the Module I and II.1 files apply cleanly. `Makefile`, `README.md`, `requirements.txt` and `.gitignore` conflict: we keep Gabriel's version and add only the WSL detection and the README notes. Oscar's path change in `obbp-icp.py` is dropped, because it would be wrong after the move to `legacy/`.
- ✅ **Done on October 8, after the analysis:** Gabriel's commits pulled, the October 2 fixes merged as above, git identity set. The merged code was re-checked (compilation, pytest, Module I, RandLA-Net dataset, Makefile); the test bench gives the same results.

## 3. Installation and module skeleton

| Check | Result |
|---|---|
| `make install`, CPU build | ✅ `import open3d.ml.torch` works |
| `make install`, GPU build | ⚠️ Not checked (no GPU) |
| System packages | `libusb-1.0-0` is required. `libgomp1` is not needed with Open3D 0.20. **`make` was missing** on the test machine: add it to the README requirements |
| `pytest tests` | ✅ 15 tests collected, 15 skipped, as expected |
| `run_registration.py --help` | ✅ |
| `make m2-2` (old script) | ✅ Runs in 1.7 s. ⚠️ On a scan rotated by 180°, the result is **flipped** but the script reports success |
| `make m2-2` without a screen | ❌ **Blocks forever** (`draw_geometries` waits for a window) |
| Missing `.ply` file | Open3D returns an **empty cloud without an error**; the old code then crashes with an unclear qhull error. `load_point_cloud` (T2.1) must check this |

**Notes on the skeleton:**
- `icp_thresholds = [1.0, 0.3, 0.1]` is fixed **in metres**. The plan says "10×, 3×, 1× `voxel_size`", so with `--voxel 0.2` the thresholds do not follow. Compute them from the voxel, or document it.
- For the T1.1 regression test, the config must be able to reproduce the old behaviour: voxel 0.2, thresholds `[20.0]`, no recentering, no leveling.
- The "symmetric" bridge of `conftest.py` is **not perfectly symmetric** (its piers are 25 cm off-centre). This is why the prototype can still register it. A perfectly symmetric bridge cannot be solved by geometry alone.

## 4. Results

| Exp. | Question | Result |
|---|---|---|
| E1 | Old code vs rotation and threshold | Asymmetric bridge: **3/8** with 20 m, 8/8 with 5 m or 1 m. Near-symmetric: 4/8 whatever the threshold |
| E2 | Why the wrong candidate wins | With 20 m, both candidates have `fitness` = 1.000; the first one (flipped) is kept. The RMSE (1.88 vs 0.11 m) would pick the right one. Near-symmetric: `D_avg` 0.088 (flipped) vs 0.078 (correct), so **`D_avg` alone cannot detect a flip** |
| E3 | UTM coordinates | Same error in UTM and local coordinates (0.012 m old code, 0.001 m prototype). Only **float32 storage** loses precision (0.25 m) |
| E4 | Tilted scan | Old code OK up to 10° (roll or pitch); fails at 20° pitch (2.0 m) and 30° (4.2 m). Leveling prototype: residual tilt < 0.02°, always succeeds |
| E5 | Partially built bridge | 70 %, 50 % or 30 % built: **0/12** for the old code and the prototype (≈ 25 m error). **FPFH + RANSAC: 10/12** |
| E6 | Scale error | Scale 0.98 → points moved by 0.56 m, but `D_avg` only 0.135 m. Scale 1.10 → 1.9 m |
| E7 | Raw vs segmented scan | Raw scan (terrain, crane, trees): old code **0/4**; prototype 4/4, but its `D_avg` = 12 m, which is meaningless. Segmented: 4/4 |
| E8 | BIM density | 2000 points per element: **0/4** (old code with 1 m and prototype). Uniform density: 4/4 |
| E9 | Main axes | Tall pier: old code **7°–74°** error (projected axis length 0.02, almost zero). 2D PCA: < 0.3° |
| E10 | Methods vs rotation | Old code 3/8 · ICP only 5/8 · FPFH + RANSAC 8/8 · prototype point-to-point 8/8 (1.7 s) · prototype **point-to-plane 8/8 (0.8 s)** |
| E11 | What `D_avg` measures | Perfect scan: **0.085 m** (BIM point spacing). Noise 10 cm: 0.126 m. Leftover crane and trees: **4.7 m** mean, 0.14 m median |
| E12 | Prototype on all rotations | **8/8** on both bridges, max rotation error 0.01°, mean error 0.001–0.002 m |

### AI test: RandLA-Net

**Goal:** check that the Module II.1 AI chain works with the current installation, and measure how a **realistic, imperfect** segmentation affects registration (preview of T3.3).

**Setup:** 5 synthetic scenes (bridge + terrain, crane, trees, noisy colours): 3 for training, 1 for validation, 1 unseen test scene. Two classes: bridge / not bridge. The repo's `PonteDataset` and the `train_ponte.py` settings, on **CPU**, 12 epochs of 15 iterations.

| Segmentation of the test scene | Value |
|---|---|
| Training time (CPU) | 26 min (≈ 8 s per iteration) |
| Inference time (117,000 points) | 20 s |
| Accuracy / **mIoU** | 0.85 / **0.74** |
| Bridge points kept | 60,000 / 60,000 |
| Clutter points left | **17,088** (22 % of the segmented cloud) |

A first run with only 3 epochs predicted "not bridge" everywhere (mIoU 0.24): training needs enough iterations to converge.

| Scan given to registration | Old code (20 m) | OBBP-ICP prototype | FPFH + RANSAC + ICP | Median distance after registration |
|---|---|---|---|---|
| raw (terrain, crane, trees) | 0/4 | 0/4 | — | — |
| perfect segmentation (ground truth) | 2/4 | **4/4** | — | 0.08 m |
| RandLA-Net segmentation | 0/4 | **0/4** | 3/4 | 0.72 m |
| RandLA-Net + statistical outlier removal | — | 0/4 | **4/4** | 0.09 m (`D_avg` = 1.83 m) |
| RandLA-Net + largest DBSCAN cluster | — | 0/4 | 3/4 | 0.11 m |

**Conclusions:**
- **The installation works for the AI part:** training, checkpoint save/load and inference all run with Open3D-ML 0.20 + PyTorch 2.13. CPU training is possible but slow; real data needs a GPU.
- **The training log is empty by default:** Open3D-ML reports loss, accuracy and mIoU through Python `logging`. Add `logging.basicConfig(level=logging.INFO)` to `train_ponte.py` (Module II.1).
- **A realistic segmentation is enough to break OBBP-ICP:** with 22 % clutter left, it fails 4 times out of 4, even with the Phase 1 fixes.
- **FPFH + RANSAC after outlier removal succeeds 4 times out of 4.** This is a second reason, after E5, to implement T3.4 strategy (c) early.
- **`D_avg` stays inflated (1.83 m) even when registration succeeds**; the median is correct (0.09 m).

⚠️ These are simple synthetic scenes and a very short training. They do not predict RandLA-Net's real performance on D19; they only show **how sensitive registration is to segmentation errors**.

## 5. Impact on the task plan

| Task | Verdict | Proposed change |
|---|---|---|
| T0.1 | ✅ | Run `make m2-2` **with a screen**. Check visually that the result is not flipped: the success message cannot be trusted |
| T0.3 | ✅ high priority | Also measure: **BIM density per element** (E8), **float32/float64** in the PLY header (E3), a **known dimension** to check the scale (E6). Fail clearly on empty or missing files |
| T1.1 | ✅ | Allow an "old behaviour" config for the regression test |
| T1.2 | 🟡 lower priority | No precision loss inside Open3D. Keep it: cheap, and protects against float32 files |
| T1.3 | ✅ confirmed | Add a "tall pier" test |
| T1.4 | 🟡 depends on T0.3 | Not needed under ~10° tilt. Level **after** segmentation, otherwise the dominant plane is the ground |
| T1.5 | ✅ confirmed, high priority | Root cause found (fitness tie). Compute the thresholds from the voxel |
| T1.6 | ✅ | Point-to-plane is a good default (2× faster), to confirm on D19 |
| T1.7 | 🟡 depends on T0.3 | A 2 % scale error is enough to break results: check the scale carefully |
| T2.1 | ✅ | `--viz` off by default is **required** (blocks without a screen). Check empty or missing files |
| T2.2 | ✅ | Write the BIM point spacing in `metrics.json` |
| T2.3 | ✅ important | Median and p95 are required; add distance to the BIM mesh; agree on `D_avg` with the Module III team |
| T3.1 | ✅ | Add tests: tall pier, sparse BIM, empty cloud |
| T3.2 | ✅ | Define success by **comparing with the known transform**, not by `D_avg` |
| T3.3 | ✅ | Also show that `D_avg` is meaningless on a raw scan. Report segmentation quality (mIoU, clutter left) with each result; test FPFH + RANSAC on the RandLA-Net output |
| Module II.1 | ✅ | Add `logging.basicConfig(level=logging.INFO)` to `train_ponte.py` to see loss and mIoU during training |
| T3.4 | 🔴 **move earlier** | This is the normal case during construction: 0/12 with OBBP-ICP, 10/12 with FPFH + RANSAC. The same method also handles the clutter left by RandLA-Net. Start strategy (c) in Phase 1 |
| Module I | 🔴 prerequisite | Merge the uniform-density fix (`geometriaEnuvem.py`) and regenerate the as-planned clouds |
| **New task** | — | **Automatic failure check**: warn when the result is doubtful (low fitness at the finest threshold, small gap between candidates, high median distance) |

## 6. Reproduce

Scripts are in [`docs/registration/analyse/`](analyse/). They do not change the repository.

```bash
cd docs/registration/analyse
../../../.venv/bin/python experiments.py          # E1 to E12 (about 10 min on CPU)
../../../.venv/bin/python randlanet_test.py 12    # RandLA-Net, 12 epochs (about 30 min on CPU)
../../../.venv/bin/python randla_followup.py      # cleaning of the RandLA-Net output (after randlanet_test.py)
```

Raw results are saved in `analyse/results/*.json`.
