# Initial analysis test bench

Scripts used for the [initial analysis](../initial-analysis.en.md) of October 8, 2026, extended until November 5. They test the old code (`legacy/obbp_icp_v0.py`) and a prototype of the planned fixes on the synthetic bridges of `tests/conftest.py`. They do not change the repository and are not part of the `registration/` package.

| File | Content |
|---|---|
| `harness.py` | Synthetic scans (rotation, tilt, partial bridge, scale, clutter), real-error metric, prototype of the planned fixes, FPFH + RANSAC |
| `experiments.py` | Experiments E1 to E12 |
| `randlanet_test.py` | RandLA-Net (repo's `PonteDataset`) on synthetic scenes, then registration of raw / segmented scans |
| `real_bridges.py` | Registration on real bridges of the team datasets (complete, partial, raw). Selector `source[:split[:sensor]]`, results in `results/registration_<selector>.json` |
| `ifc_bridge.py` | Scan vs BIM: Module I as-planned cloud from the buildingSMART IFC4.3 bridge, scans at 3 construction stages |
| `generated_bridges.py` | Random IFC 4.3 girder bridges, Module I as-planned cloud, scans at each construction stage |
| `refsite3d_test.py` | Real construction scans with their planned model (RefSite3D, private team dataset) |
| `results/` | Raw results (JSON) |

```bash
cd docs/registration/analyse
../../../.venv/bin/python experiments.py          # all experiments, ~10 min on CPU
../../../.venv/bin/python experiments.py E5 E8    # some experiments only
../../../.venv/bin/python randlanet_test.py 12    # RandLA-Net, 12 epochs, ~30 min on CPU
../../../.venv/bin/python real_bridges.py uav_lidar               # one dataset; also rc_bridges_japan, brpcd
../../../.venv/bin/python real_bridges.py semanticbridge:test:BLK2GO   # one split and sensor
../../../.venv/bin/python generated_bridges.py 10 # 10 generated bridges
../../../.venv/bin/python refsite3d_test.py       # RefSite3D
```

`real_bridges.py`, `generated_bridges.py` and `refsite3d_test.py` run for hours on CPU. They save after each bridge or scene: run the same command again to resume. `harness.METHODS` lists the methods they compare.

Requires Gabriel's commits of October 5–6 (`legacy/` and `tests/conftest.py`). `REPO=/path/to/copy` runs the scripts against another copy of the repository.
