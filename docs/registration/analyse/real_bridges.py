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

DATA = h.REPO / "ModuleTwo RandlaNET" / "DATASET" / "bridge-pointclouds"
OUT = Path(__file__).resolve().parent / "results"
ANGLES = (0, 90, 180, 270)
MAX_SCAN = 300_000
METHODS = ("legacy (thr 20 m)", "prototype v1", "FPFH+RANSAC+ICP")


def scenes(selector):
    """'source[:split[:sensor text]]' -> list of (source, scene, sensor) from scenes.csv."""
    source, split, sensor = (selector.split(":") + ["", ""])[:3]
    with open(DATA / source / "scenes.csv", newline="") as f:
        return [(source, r["scene"], r["sensor"]) for r in csv.DictReader(f)
                if (not split or r["split"] == split) and sensor in r["sensor"]]


def load(source, scene):
    v = PlyData.read(str(DATA / source / f"{scene}.ply"))["vertex"].data
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


def run(method, scan_pts, bim, T):
    scan = cloud(scan_pts).transform(T)
    if method == METHODS[0]:
        M = h.legacy.obbp_icp_corrigido(scan, bim, voxel_size=0.2, icp_dist_thresh=20.0)[2]
    elif method == METHODS[1]:
        M = h.obbp_v1(scan, bim)[0]["M"]
    else:
        M = h.fpfh_ransac(scan, bim)
    return h.registration_error(M, T, scan_pts)[0]


def main(selector):
    rng = np.random.default_rng(0)
    rows = []
    for source, scene, sensor in scenes(selector):
        pts, is_bridge = load(source, scene)
        bridge = pts[is_bridge]
        half = rng.random(len(bridge)) < 0.5
        bim = cloud(bridge[half]).voxel_down_sample(0.1)
        scan_bridge = bridge[~half] + rng.normal(0, 0.01, (int((~half).sum()), 3))
        cases = {
            "bridge only (perfect segmentation)": scan_bridge,
            "partial bridge (50 %)": keep_first_part(scan_bridge, 0.5),
            "raw scan (ground + vegetation)": np.vstack([scan_bridge, pts[~is_bridge]]),
        }
        for case, scan_pts in cases.items():
            if len(scan_pts) > MAX_SCAN:
                scan_pts = scan_pts[rng.choice(len(scan_pts), MAX_SCAN, replace=False)]
            for method in METHODS:
                errs = [run(method, scan_pts, bim, h.rigid_transform(a, (120.0, -45.0, 3.0))) for a in ANGLES]
                ok = sum(e < h.SUCCESS_M for e in errs)
                rows.append(dict(source=source, bridge=scene, sensor=sensor, case=case, method=method, success=ok,
                                 trials=len(ANGLES), median_err_m=float(np.median(errs))))
                print(f"{scene:18s} | {case:36s} | {method:18s} | {ok}/{len(ANGLES)} | median error "
                      f"{np.median(errs):7.3f} m", flush=True)
    name = selector.replace(":", "_").replace(" ", "")
    (OUT / f"real_bridges_{name}.json").write_text(json.dumps(rows, indent=1))

    n = len({r["bridge"] for r in rows})
    print(f"\n| Case | Method | Success ({n} bridges x {len(ANGLES)} rotations) |\n|---|---|---|")
    for case in dict.fromkeys(r["case"] for r in rows):
        for method in METHODS:
            sel = [r for r in rows if r["case"] == case and r["method"] == method]
            print(f"| {case} | {method} | {sum(r['success'] for r in sel)}/{sum(r['trials'] for r in sel)} |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "uav_lidar")
