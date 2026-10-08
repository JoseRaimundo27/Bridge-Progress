# Initial analysis test bench

Scripts used for the [initial analysis](../initial-analysis.en.md) of October 8, 2026. They test the old code (`legacy/obbp_icp_v0.py`) and a prototype of the planned fixes on the synthetic bridges of `tests/conftest.py`. They do not change the repository and are not part of the `registration/` package.

| File | Content |
|---|---|
| `harness.py` | Synthetic scans (rotation, tilt, partial bridge, scale, clutter), real-error metric, prototype of the planned fixes, FPFH + RANSAC |
| `experiments.py` | Experiments E1 to E12 |
| `randlanet_test.py` | RandLA-Net (repo's `PonteDataset`) on synthetic scenes, then registration of raw / segmented scans |
| `results/` | Raw results (JSON) |

```bash
cd docs/registration/analyse
../../../.venv/bin/python experiments.py          # all experiments, ~10 min on CPU
../../../.venv/bin/python experiments.py E5 E8    # some experiments only
../../../.venv/bin/python randlanet_test.py 12    # RandLA-Net, 12 epochs, ~30 min on CPU
```

Requires Gabriel's commits of October 5–6 (`legacy/` and `tests/conftest.py`). `REPO=/path/to/copy` runs the scripts against another copy of the repository.
