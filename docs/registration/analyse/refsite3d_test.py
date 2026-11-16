"""Registration on REAL construction-progress scans with their planned model: RefSite3D (RWTH Aachen, CC-BY 4.0).

RefSite3D (team dataset GETEC-UFBA/bridge-pointclouds, refsite3d/scan_vs_bim/) documents the assembly of a
modular building in 5 progress states (PM1: concrete only ... PM5: complete), scanned with laser scanners
(RIEGL, Leica), photogrammetry (Pix4D) and NeRF (Luma). Scans, planned models and synthetic as-planned
clouds share one coordinate system, so the true transform is known: we move each scan by a known
transform (4 rotations) and measure the real registration error.

- as-planned: synthetic point cloud of the full planned model of the phase;
- scan: "building extracted" (= well segmented) or "full scene" (= raw, with surroundings).

Not a bridge, but the same Scan-vs-BIM problem with real partial construction states.

Usage: python refsite3d_test.py
"""

import json
from pathlib import Path

import numpy as np
import open3d as o3d

import harness as h

ROOT = h.REPO / "ModuleTwo RandlaNET" / "DATASET" / "bridge-pointclouds-getec" / "refsite3d" / "scan_vs_bim" / "phases"
OUT = Path(__file__).resolve().parent / "results"
ANGLES = (0, 90, 180, 270)
MAX_POINTS = 300_000


def load(path, rng):
    pts = np.asarray(o3d.io.read_point_cloud(str(path)).points)
    if len(pts) > MAX_POINTS:
        pts = pts[rng.choice(len(pts), MAX_POINTS, replace=False)]
    return pts


def main():
    out = OUT / "refsite3d.json"
    rows = json.loads(out.read_text()) if out.exists() else []  # resume: results are saved after each scene
    done = {(r["scene"], r["case"]) for r in rows}
    rng = np.random.default_rng(0)
    for meta in sorted(ROOT.glob("phase_*/scans/scene_*/scene_*_metadata.json")):
        m = json.loads(meta.read_text())
        phase = meta.parents[2]
        bim = o3d.io.read_point_cloud(str(next((phase / "synthetic_pointclouds" / "full").glob("*.ply"))))
        info = m["scan_information"]
        for case, key, pattern in (("building extracted", "filename_target_extracted", "*_building_extracted_*.ply"),
                                   ("full scene (raw)", "filename_scene", "*_scene_ReStage_*.ply")):
            if (m["scene_id"], case) in done:
                continue
            path = meta.parent / info[key]
            if not path.exists():  # scene_006 metadata names "faro" files, the files are named "leica"
                path = next(meta.parent.glob(pattern))
            pts = load(path, rng)
            errs = {k: [] for k in h.METHODS}
            for a in ANGLES:
                T = h.rigid_transform(a, (120.0, -45.0, 3.0))
                scan = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts)).transform(T)
                for k, M in h.run_all_methods(scan, bim).items():
                    errs[k].append(h.registration_error(M, T, pts)[0])
            for k, e in errs.items():
                rows.append(dict(scene=m["scene_id"], state=m["progress_monitoring_state"], sensor=info["sensor"],
                                 case=case, points=len(pts), method=k, success=sum(x < h.SUCCESS_M for x in e),
                                 trials=len(ANGLES), median_err_m=float(np.median(e))))
            print(f"{m['scene_id']} {m['progress_monitoring_state']} {info['sensor'][:18]:18s} | {case:18s} | "
                  + " | ".join(f"{sum(x < h.SUCCESS_M for x in e)}/4 ({np.median(e):.3f} m)" for e in errs.values()), flush=True)
            out.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
