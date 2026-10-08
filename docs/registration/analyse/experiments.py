"""Initial analysis of Module II.2: one experiment per question of the task plan.

Usage: python experiments.py [E1 E2 ...]   (all experiments when no argument)
Results: printed as markdown tables and saved in results/<experiment>.json
"""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import open3d as o3d

import harness as h

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)
ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]


def table(rows, cols):
    print("| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in rows:
        print("| " + " | ".join(f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")
    print()


def save(name, rows):
    (OUT / f"{name}.json").write_text(json.dumps(rows, indent=1, default=float))


def run_legacy(scan, bim, T, true_pts, voxel=0.2, thr=20.0):
    (reg, d, M), t = h.timed(h.legacy.obbp_icp_corrigido, scan, bim, voxel_size=voxel, icp_dist_thresh=thr)
    err, emax, rot = h.registration_error(M, T, true_pts)
    return dict(err_m=err, rot_err_deg=rot, d_avg=d, ok="✅" if err < h.SUCCESS_M else "❌", time_s=t)


def run_v1(scan, bim, T, true_pts, **kw):
    (best, cands), t = h.timed(h.obbp_v1, scan, bim, **kw)
    reg = copy.deepcopy(scan).transform(best["M"])
    err, emax, rot = h.registration_error(best["M"], T, true_pts)
    return dict(err_m=err, rot_err_deg=rot, d_avg=h.d_avg(reg, bim), ok="✅" if err < h.SUCCESS_M else "❌",
                time_s=t, fitness=best["fitness"])


# ---------------------------------------------------------------------------------------------

def E1():
    """Legacy code (as in make m2-2: voxel 0.2, ICP threshold 20 m) vs rotation and threshold."""
    rows = []
    for sym in (False, True):
        bim = h.make_bim(sym)
        for thr in (20.0, 5.0, 1.0):
            for a in ANGLES:
                scan, T, tp = h.make_scan(a, symmetric=sym)
                r = run_legacy(scan, bim, T, tp, thr=thr)
                rows.append(dict(bridge="symmetric" if sym else "asymmetric", thr_m=thr, angle=a, **r))
    print("## E1 legacy vs rotation / threshold")
    summary = []
    for sym in ("asymmetric", "symmetric"):
        for thr in (20.0, 5.0, 1.0):
            sel = [r for r in rows if r["bridge"] == sym and r["thr_m"] == thr]
            summary.append(dict(bridge=sym, thr_m=thr, success=f"{sum(r['ok'] == '✅' for r in sel)}/{len(sel)}",
                                failed_angles=",".join(str(r["angle"]) for r in sel if r["ok"] != "✅") or "-",
                                mean_time_s=float(np.mean([r["time_s"] for r in sel]))))
    table(summary, ["bridge", "thr_m", "success", "failed_angles", "mean_time_s"])
    save("E1", rows)


def E2():
    """Can fitness / D_avg tell the right candidate from the flipped one?"""
    rows = []
    for sym in (False, True):
        bim = h.make_bim(sym)
        scan, T, tp = h.make_scan(180, symmetric=sym)
        for thr in (20.0, 1.0):
            for i, c in enumerate(h.legacy_candidates(scan, bim, icp_dist_thresh=thr)):
                reg = copy.deepcopy(scan).transform(c["M"])
                err, _, rot = h.registration_error(c["M"], T, tp)
                rows.append(dict(bridge="symmetric" if sym else "asymmetric", thr_m=thr, cand=i,
                                 fitness=c["fitness"], rmse=c["rmse"], d_avg=h.d_avg(reg, bim),
                                 true_err_m=err, correct="✅" if err < h.SUCCESS_M else "❌ flipped"))
    print("## E2 candidate scores (scan rotated 180°)")
    table(rows, ["bridge", "thr_m", "cand", "fitness", "rmse", "d_avg", "true_err_m", "correct"])
    save("E2", rows)


def E3():
    """Georeferenced (UTM) coordinates: precision of the computation and of PLY storage."""
    rows = []
    off = np.array([680000.0, 7480000.0, 0.0])
    bim0 = h.make_bim()
    for label, o in (("local", np.zeros(3)), ("UTM", off)):
        bim = copy.deepcopy(bim0).translate(o)
        scan, T, tp = h.make_scan(90, translation=tuple(np.array([120.0, -45.0, 3.0]) + o))
        # the BIM is shifted by o, so the true scan -> BIM transform is T(o) . inv(T)
        Tb = np.eye(4)
        Tb[:3, 3] = -o
        for name, f in (("legacy, thr 1 m", lambda: h.legacy.obbp_icp_corrigido(scan, bim, voxel_size=0.2, icp_dist_thresh=1.0)[2]),
                        ("prototype v1 (offset)", lambda: h.obbp_v1(scan, bim)[0]["M"])):
            M = f()
            err, _, rot = h.registration_error(Tb @ M, T, tp)
            reg = copy.deepcopy(scan).transform(M)
            rows.append(dict(coords=label, test=name, err_m=err, rot_err_deg=rot, d_avg=h.d_avg(reg, bim),
                             ok="✅" if err < h.SUCCESS_M else "❌"))
    # storage: Open3D float64 PLY vs float32 PLY
    pts = np.asarray(bim0.points)[:2000] + off
    p = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts))
    o3d.io.write_point_cloud(str(OUT / "tmp64.ply"), p)
    back = np.asarray(o3d.io.read_point_cloud(str(OUT / "tmp64.ply")).points)
    (OUT / "tmp64.ply").unlink()
    f32 = pts.astype(np.float32).astype(np.float64)
    print("## E3 UTM coordinates")
    table(rows, ["coords", "test", "err_m", "rot_err_deg", "d_avg", "ok"])
    store = [dict(storage="Open3D write_point_cloud (PLY)", max_error_m=float(np.abs(back - pts).max())),
             dict(storage="float32 (e.g. CloudCompare/PDAL export as float)", max_error_m=float(np.abs(f32 - pts).max()))]
    table(store, ["storage", "max_error_m"])
    save("E3", rows + store)


def E4():
    """Tilted scan (R_z = identity in the legacy code) and the RANSAC-plane leveling prototype."""
    rows = []
    bim = h.make_bim()
    for axis in ("x", "y"):
      for tilt in (0, 5, 10, 20, 30):
        scan, T, tp = h.make_scan(45, tilt_deg=tilt, tilt_axis=axis)
        r = run_legacy(scan, bim, T, tp, thr=1.0)
        rows.append(dict(axis="roll (x)" if axis == "x" else "pitch (y)", tilt_deg=tilt, method="legacy (thr 1 m)", **r))
        r = run_v1(scan, bim, T, tp, level=True)
        rows.append(dict(axis="roll (x)" if axis == "x" else "pitch (y)", tilt_deg=tilt, method="prototype + level_z", **r))
        # leveling accuracy alone
        R = h.level_z(scan.voxel_down_sample(0.1))
        up = (R[:3, :3] @ (T[:3, :3] @ np.array([0, 0, 1.0])))
        rows[-1]["residual_tilt_deg"] = float(np.degrees(np.arccos(np.clip(up[2] / np.linalg.norm(up), -1, 1))))
    for r in rows:
        r.setdefault("residual_tilt_deg", "-")
    print("## E4 tilt")
    table(rows, ["axis", "tilt_deg", "method", "err_m", "rot_err_deg", "d_avg", "ok", "residual_tilt_deg"])
    save("E4", rows)


def E5():
    """Partially built bridge: only 30/50/70/100 % of the deck length is scanned."""
    rows = []
    bim = h.make_bim()
    for frac in (1.0, 0.7, 0.5, 0.3):
        for name, f in (("legacy thr 1 m", lambda s, T, tp: run_legacy(s, bim, T, tp, thr=1.0)),
                        ("prototype v1", lambda s, T, tp: run_v1(s, bim, T, tp)),
                        ("FPFH+RANSAC+ICP", None)):
            oks, errs = 0, []
            for a in (0, 90, 180, 270):
                scan, T, tp = h.make_scan(a, keep_fraction=frac)
                if f is None:
                    M = h.fpfh_ransac(scan, bim)
                    err = h.registration_error(M, T, tp)[0]
                else:
                    err = f(scan, T, tp)["err_m"]
                oks += err < h.SUCCESS_M
                errs.append(err)
            rows.append(dict(built=f"{int(frac * 100)} %", method=name, success=f"{oks}/4",
                             median_err_m=float(np.median(errs))))
    print("## E5 partial bridge")
    table(rows, ["built", "method", "success", "median_err_m"])
    save("E5", rows)


def E6():
    """Scale error (photogrammetry without control points)."""
    rows = []
    bim = h.make_bim()
    for s in (1.0, 0.98, 0.95, 1.05, 1.1):
        scan, T, tp = h.make_scan(45, scale=s)
        r = run_v1(scan, bim, T, tp)
        rows.append(dict(scale=s, d_avg=r["d_avg"], err_m=r["err_m"], ok=r["ok"]))
    print("## E6 scale (prototype v1, rigid ICP)")
    table(rows, ["scale", "d_avg", "err_m", "ok"])
    save("E6", rows)


def E7():
    """Raw scan (terrain, crane, vegetation) vs segmented scan - Table 1 of the paper."""
    rows = []
    bim = h.make_bim()
    clutter = h.make_clutter()
    for label, cl in (("segmented (bridge only)", None), ("raw (terrain + crane + trees)", clutter)):
        for name, f in (("legacy thr 20 m", lambda s, T, tp: run_legacy(s, bim, T, tp, thr=20.0)),
                        ("legacy thr 1 m", lambda s, T, tp: run_legacy(s, bim, T, tp, thr=1.0)),
                        ("prototype v1", lambda s, T, tp: run_v1(s, bim, T, tp))):
            res = [f(*h.make_scan(a, clutter=cl)) for a in (0, 90, 180, 270)]
            rows.append(dict(scan=label, method=name, success=f"{sum(r['ok'] == '✅' for r in res)}/4",
                             d_avg=float(np.mean([r["d_avg"] for r in res])),
                             time_s=float(np.mean([r["time_s"] for r in res]))))
    print("## E7 raw vs segmented")
    table(rows, ["scan", "method", "success", "d_avg", "time_s"])
    save("E7", rows)


def E8():
    """BIM density: 2000 points per element (current Module I) vs uniform density."""
    rows = []
    parts = []
    m = h.bridge_mesh()
    # rebuild the elements of the asymmetric bridge to sample them separately
    deck = o3d.geometry.TriangleMesh.create_box(60, 8, 1.5).translate((0, 0, 10))
    piers = [o3d.geometry.TriangleMesh.create_box(1.5, 1.5, 10).translate((x, 3.25, 0)) for x in (6, 18, 40)]
    abut = o3d.geometry.TriangleMesh.create_box(4, 10, 11.5).translate((60, -1, 0))
    elements = [deck, *piers, abut]
    per_elem = o3d.geometry.PointCloud()
    for i, e in enumerate(elements):
        o3d.utility.random.seed(i)
        per_elem += e.sample_points_uniformly(2000)
    uniform = h.sample(m, 60000, 0)
    for label, bim in (("2000 pts / element", per_elem), ("uniform (by area)", uniform)):
      for meth, f in (("legacy thr 20 m", lambda s, T, tp: run_legacy(s, bim, T, tp, thr=20.0)),
                      ("legacy thr 1 m", lambda s, T, tp: run_legacy(s, bim, T, tp, thr=1.0)),
                      ("prototype v1", lambda s, T, tp: run_v1(s, bim, T, tp))):
        res = [f(*h.make_scan(a)) for a in (0, 90, 180, 270)]
        rows.append(dict(bim=label, method=meth, points=len(bim.points),
                         success=f"{sum(r['ok'] == '✅' for r in res)}/4",
                         err_m=float(np.mean([r["err_m"] for r in res])),
                         d_avg=float(np.mean([r["d_avg"] for r in res]))))
    print("## E8 BIM density")
    table(rows, ["bim", "method", "points", "success", "err_m", "d_avg"])
    save("E8", rows)


def E9():
    """Main axes: legacy (OBB 3D columns 0 and 1) vs PCA on XY."""
    rows = []
    rng = np.random.default_rng(0)
    for name, dims in (("deck 60x8x1.5", (60, 8, 1.5)), ("tall pier 1.5x3x10", (1.5, 3, 10)),
                       ("square 20x20x2", (20, 20, 2)), ("tall square tower 4x4x30", (4, 4, 30))):
        for a in (0, 30, 75):
            pts = rng.uniform(0, 1, (20000, 3)) * dims
            R = h.rigid_transform(a, (0, 0, 0))
            p = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts @ R[:3, :3].T))
            res = {}
            for lab, f in (("legacy", h.legacy.get_2d_main_axes), ("pca", h.pca_axes_2d)):
                (ax, el), (_, es) = f(p)
                n = np.linalg.norm(ax)
                ang = np.degrees(np.arctan2(ax[1], ax[0])) % 180 if n > 1e-9 else float("nan")
                expected = a % 180 if dims[0] >= dims[1] else (a + 90) % 180
                diff = min(abs(ang - expected), 180 - abs(ang - expected)) if n > 1e-9 else float("nan")
                res[lab] = f"{diff:.1f}° (|axis|={n:.2f}, ext {el:.1f}/{es:.1f})"
            rows.append(dict(cloud=name, angle=a, legacy=res["legacy"], pca=res["pca"]))
    print("## E9 main axes: angle error of the long axis")
    table(rows, ["cloud", "angle", "legacy", "pca"])
    save("E9", rows)


def E10():
    """Methods vs initial rotation (preview of T3.2): legacy, ICP only, FPFH+RANSAC, prototype."""
    rows = []
    bim = h.make_bim()
    methods = {
        "legacy (thr 20 m)": lambda s, T, tp: h.registration_error(
            h.legacy.obbp_icp_corrigido(s, bim, voxel_size=0.2, icp_dist_thresh=20.0)[2], T, tp)[0],
        "ICP only (centroids + multi-scale)": None,
        "FPFH+RANSAC+ICP": lambda s, T, tp: h.registration_error(h.fpfh_ransac(s, bim), T, tp)[0],
        "prototype v1 (point-to-point)": lambda s, T, tp: run_v1(s, bim, T, tp)["err_m"],
        "prototype v1 (point-to-plane)": lambda s, T, tp: run_v1(s, bim, T, tp, point_to_plane=True)["err_m"],
    }

    def icp_only(s, T, tp):
        init = np.eye(4)
        init[:3, 3] = bim.get_center() - s.get_center()
        r = h.multiscale_icp(s.voxel_down_sample(0.1), bim.voxel_down_sample(0.1), (5.0, 1.0, 0.3, 0.1), init=init)
        return h.registration_error(r.transformation, T, tp)[0]

    methods["ICP only (centroids + multi-scale)"] = icp_only
    for name, f in methods.items():
        errs, times = [], []
        for a in ANGLES:
            scan, T, tp = h.make_scan(a)
            e, t = h.timed(f, scan, T, tp)
            errs.append(e)
            times.append(t)
        ok = [e < h.SUCCESS_M for e in errs]
        rows.append(dict(method=name, success=f"{sum(ok)}/{len(ok)}",
                         failed_angles=",".join(str(a) for a, o in zip(ANGLES, ok) if not o) or "-",
                         mean_err_ok_m=float(np.mean([e for e, o in zip(errs, ok) if o])) if any(ok) else float("nan"),
                         mean_time_s=float(np.mean(times))))
    print("## E10 methods vs rotation (asymmetric bridge)")
    table(rows, ["method", "success", "failed_angles", "mean_err_ok_m", "mean_time_s"])
    save("E10", rows)


def E11():
    """Scan noise vs D_avg (D_avg feeds the Module III threshold O_thr = D_avg + C)."""
    rows = []
    bim = h.make_bim()
    for noise in (0.0, 0.01, 0.03, 0.05, 0.1):
        scan, T, tp = h.make_scan(90, noise=noise)
        r = run_v1(scan, bim, T, tp)
        reg = copy.deepcopy(scan).transform(h.obbp_v1(scan, bim)[0]["M"])
        d = np.asarray(reg.compute_point_cloud_distance(bim))
        rows.append(dict(noise_sigma_m=noise, d_avg=float(d.mean()), median=float(np.median(d)),
                         p95=float(np.percentile(d, 95)), true_err_m=r["err_m"]))
    # outliers left by an imperfect segmentation
    scan, T, tp = h.make_scan(90, clutter=h.make_clutter(ground=False, crane=True, vegetation=True))
    reg = copy.deepcopy(scan).transform(h.obbp_v1(scan, bim)[0]["M"])
    d = np.asarray(reg.compute_point_cloud_distance(bim))
    rows.append(dict(noise_sigma_m="0.01 + crane/trees left", d_avg=float(d.mean()), median=float(np.median(d)),
                     p95=float(np.percentile(d, 95)), true_err_m=h.registration_error(
                         h.obbp_v1(scan, bim)[0]["M"], T, tp)[0]))
    print("## E11 noise and outliers vs D_avg")
    table(rows, ["noise_sigma_m", "d_avg", "median", "p95", "true_err_m"])
    save("E11", rows)


def E12():
    """Prototype v1 on all rotations, both bridges (what T1.3 + T1.5 should achieve)."""
    rows = []
    for sym in (False, True):
        bim = h.make_bim(sym)
        res = []
        for a in ANGLES:
            scan, T, tp = h.make_scan(a, symmetric=sym)
            res.append(run_v1(scan, bim, T, tp))
        ok = [r["ok"] == "✅" for r in res]
        rows.append(dict(bridge="symmetric" if sym else "asymmetric", success=f"{sum(ok)}/{len(ok)}",
                         failed_angles=",".join(str(a) for a, o in zip(ANGLES, ok) if not o) or "-",
                         max_rot_err_ok_deg=float(max([r["rot_err_deg"] for r, o in zip(res, ok) if o], default=float("nan"))),
                         mean_err_ok_m=float(np.mean([r["err_m"] for r, o in zip(res, ok) if o])),
                         mean_time_s=float(np.mean([r["time_s"] for r in res]))))
    print("## E12 prototype v1 (PCA axes + multi-scale ICP 1/0.3/0.1 m + fitness then rmse)")
    table(rows, ["bridge", "success", "failed_angles", "max_rot_err_ok_deg", "mean_err_ok_m", "mean_time_s"])
    save("E12", rows)


if __name__ == "__main__":
    names = sys.argv[1:] or [n for n in dir() if n.startswith("E") and n[1:].isdigit()]
    for n in sorted(names, key=lambda s: int(s[1:])):
        globals()[n]()
        sys.stdout.flush()
