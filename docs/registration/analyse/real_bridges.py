"""Registration tests on real bridges (team dataset Gabl26/bridge-pointclouds), complementing E1, E5 and E7.

There is no BIM for these bridges, so the "as-planned" cloud is a random half of the bridge points
(label 1) and the scan is the other half (plus 1 cm noise), moved by a known transform.

Data: https://huggingface.co/datasets/Gabl26/bridge-pointclouds, downloaded to
ModuleTwo RandlaNET/DATASET/bridge-pointclouds/ (scenes listed in each <source>/scenes.csv).

Usage:
    python real_bridges.py uav_lidar                     # the 6 UAV LiDAR bridges
    python real_bridges.py semanticbridge:test           # SemanticBridge test bridges (TLS + MLS)
    python real_bridges.py semanticbridge:test:BLK2GO    # ... only the MLS scans
"""

import csv
import json
import sys
from pathlib import Path

import numpy as np
import open3d as o3d
from plyfile import PlyData

import harness as h

_DATASETS = h.REPO / "ModuleTwo RandlaNET" / "DATASET"
# private team dataset (GETEC-UFBA, more sources) if downloaded, else the public one (Gabl26)
DATA = next((d for d in (_DATASETS / "bridge-pointclouds-getec", _DATASETS / "bridge-pointclouds") if d.exists()),
            _DATASETS / "bridge-pointclouds")
OUT = Path(__file__).resolve().parent / "results"
ANGLES = (0, 90, 180, 270)
MAX_SCAN = 300_000


def scenes(selector):
    """'source[:split[:sensor text]]' -> list of (source, scene, sensor) from scenes.csv."""
    source, split, sensor = (selector.split(":") + ["", ""])[:3]
    folder = DATA / source / "processed" if (DATA / source / "processed").exists() else DATA / source
    with open(folder / "scenes.csv", newline="") as f:
        return [(source, r["scene"], r["sensor"]) for r in csv.DictReader(f)
                if (not split or r["split"] == split) and sensor in r["sensor"]]


def load(source, scene):
    folder = DATA / source / "processed" if (DATA / source / "processed").exists() else DATA / source
    v = PlyData.read(str(folder / f"{scene}.ply"))["vertex"].data
    pts = np.c_[v["x"], v["y"], v["z"]].astype(np.float64)
    return pts - pts.mean(0), np.asarray(v["label"]) == 1  # label: -1 unlabeled, 0 not bridge, 1 bridge


def cloud(p):
    return o3d.geometry.PointCloud(o3d.utility.Vector3dVector(p))


def keep_first_part(pts, frac):
    """Partial bridge: keep the first part along the main horizontal axis."""
    xy = pts[:, :2] - pts[:, :2].mean(0)
    axis = np.linalg.eigh(np.cov(xy.T))[1][:, 1]
    s = xy @ axis
    return pts[s <= s.min() + frac * np.ptp(s)]


def main(selector):
    name = selector.replace(":", "_").replace(" ", "")
    out = OUT / f"registration_{name}.json"
    rows = json.loads(out.read_text()) if out.exists() else []  # resume: results are saved after each bridge
    done = {r["bridge"] for r in rows}
    for source, scene, sensor in scenes(selector):
        if scene in done:
            continue
        rng = np.random.default_rng(abs(hash_name(scene)))
        pts, is_bridge = load(source, scene)
        bridge = pts[is_bridge]
        half = rng.random(len(bridge)) < 0.5
        bim = cloud(bridge[half]).voxel_down_sample(0.1)
        scan_bridge = bridge[~half] + rng.normal(0, 0.01, (int((~half).sum()), 3))
        cases = {
            "bridge only (perfect segmentation)": scan_bridge,
            "partial bridge (50 %)": keep_first_part(scan_bridge, 0.5),
        }
        if (~is_bridge).sum() > 0.05 * len(pts):  # some sources contain the bridge only
            cases["raw scan (ground + vegetation)"] = np.vstack([scan_bridge, pts[~is_bridge]])
        for case, scan_pts in cases.items():
            if len(scan_pts) > MAX_SCAN:
                scan_pts = scan_pts[rng.choice(len(scan_pts), MAX_SCAN, replace=False)]
            errs = {m: [] for m in h.METHODS}
            for a in ANGLES:
                T = h.rigid_transform(a, (120.0, -45.0, 3.0))
                for m, M in h.run_all_methods(cloud(scan_pts).transform(T), bim).items():
                    errs[m].append(h.registration_error(M, T, scan_pts)[0])
            for m, e in errs.items():
                rows.append(dict(source=source, bridge=scene, sensor=sensor, case=case, method=m,
                                 success=sum(x < h.SUCCESS_M for x in e), trials=len(ANGLES),
                                 median_err_m=float(np.median(e))))
            print(f"{scene:18s} | {case:36s} | " + " | ".join(f"{sum(x < h.SUCCESS_M for x in e)}/4" for e in errs.values()),
                  flush=True)
        out.write_text(json.dumps(rows, indent=1))

    n = len({r["bridge"] for r in rows})
    print(f"\n| Case | " + " | ".join(h.METHODS) + f" |  ({n} bridges x {len(ANGLES)} rotations)\n|---|" + "---|" * len(h.METHODS))
    for case in dict.fromkeys(r["case"] for r in rows):
        print(f"| {case} | " + " | ".join(
            f"{sum(r['success'] for r in rows if r['case'] == case and r['method'] == m)}/"
            f"{sum(r['trials'] for r in rows if r['case'] == case and r['method'] == m)}" for m in h.METHODS) + " |")


def hash_name(text):
    """Stable seed per bridge (Python's hash() changes between runs), so a resumed run gives the same results."""
    return int.from_bytes(text.encode()[:8].ljust(8, b"0"), "little") % (2**31)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "uav_lidar")
