"""Shared tools for the initial analysis of Module II.2 (registration).

Uses the synthetic bridges of the repo's tests/conftest.py and the legacy script
legacy/obbp_icp_v0.py, unchanged. Nothing here modifies the repository.
"""

import copy
import importlib.util
import os
import sys
import time
from pathlib import Path

import numpy as np
import open3d as o3d

# repository root (docs/registration/analyse/ -> 3 levels up); REPO=... to test another copy
REPO = Path(os.environ.get("REPO", Path(__file__).resolve().parents[3]))
REG_PY = REPO / "ModuleTwo Registration" / "Python"
sys.path.insert(0, str(REG_PY / "tests"))
sys.path.insert(0, str(REG_PY))

from conftest import bridge_mesh, rigid_transform  # noqa: E402

o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)


def load_legacy():
    spec = importlib.util.spec_from_file_location("obbp_icp_v0", REG_PY / "legacy" / "obbp_icp_v0.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = load_legacy()

SUCCESS_M = 0.2  # a registration is "correct" when points end up < 20 cm from their true position


# ---------------------------------------------------------------- synthetic data

def sample(mesh, n, seed):
    o3d.utility.random.seed(seed)
    return mesh.sample_points_uniformly(n)


def make_bim(symmetric=False, n=60000):
    return sample(bridge_mesh(symmetric), n, 0)


def make_scan(angle_deg=0.0, translation=(120.0, -45.0, 3.0), noise=0.01, symmetric=False, n=50000,
              keep_fraction=1.0, tilt_deg=0.0, tilt_axis="x", scale=1.0, clutter=None, seed=1):
    """Scan of the bridge in its own frame, then moved by a known transform T_gt.
    Returns (scan, T_gt, true_points) where true_points are the scan points before T_gt
    (bridge frame) - used to measure the real registration error."""
    pts = np.asarray(sample(bridge_mesh(symmetric), n, seed).points)
    pts = pts + np.random.default_rng(seed).normal(0, noise, pts.shape)
    if keep_fraction < 1.0:  # partial bridge: only the first part along the deck is built
        pts = pts[pts[:, 0] <= pts[:, 0].min() + keep_fraction * np.ptp(pts[:, 0])]
    if clutter is not None:
        pts = np.vstack([pts, clutter])
    true_pts = pts.copy()
    T = np.eye(4)
    if scale != 1.0:
        S = np.eye(4)
        S[:3, :3] *= scale
        T = S @ T
    if tilt_deg:
        a = np.radians(tilt_deg)
        Rx = np.eye(4)  # roll about the deck axis (x) or pitch about the cross axis (y)
        i, j = (1, 2) if tilt_axis == "x" else (0, 2)
        Rx[np.ix_([i, j], [i, j])] = [[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]
        c = np.eye(4)
        c[:3, 3] = -true_pts.mean(0)
        T = np.linalg.inv(c) @ Rx @ c @ T
    T = rigid_transform(angle_deg, translation) @ T
    scan = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(true_pts))
    scan.transform(T)
    return scan, T, true_pts


def make_clutter(seed=3, ground=True, crane=True, vegetation=True, n_ground=40000):
    """Terrain, crane and vegetation around the bridge (bridge frame: deck x in [0, 64])."""
    rng = np.random.default_rng(seed)
    parts = []
    if ground:
        xy = rng.uniform([-30, -40], [95, 48], (n_ground, 2))
        z = 0.4 * np.sin(xy[:, 0] / 9) + 0.3 * np.cos(xy[:, 1] / 7) + rng.normal(0, 0.05, len(xy))
        parts.append(np.c_[xy, z])
    if crane:
        mast = rng.uniform([30, 15, 0], [32, 17, 30], (4000, 3))
        jib = rng.uniform([10, 15, 28], [55, 16, 29], (3000, 3))
        parts += [mast, jib]
    if vegetation:
        for _ in range(12):
            c = rng.uniform([-25, -35, 1], [90, 45, 3])
            parts.append(c + rng.normal(0, 1.2, (800, 3)))
    return np.vstack(parts)


# ---------------------------------------------------------------- error metrics

def registration_error(M, T_gt, true_pts):
    """Real error of an estimated transform M (scan -> BIM): mean and max displacement
    of the scan points from their true position, and rotation error in degrees."""
    E = M @ T_gt  # identity when M is exactly inv(T_gt)
    p = np.c_[true_pts, np.ones(len(true_pts))]
    disp = np.linalg.norm((p @ E.T)[:, :3] - true_pts, axis=1)
    cos = np.clip((np.trace(E[:3, :3]) - 1) / 2, -1, 1)
    return float(disp.mean()), float(disp.max()), float(np.degrees(np.arccos(cos)))


def d_avg(scan, bim):
    return float(np.mean(scan.compute_point_cloud_distance(bim)))


def timed(f, *a, **k):
    t = time.perf_counter()
    r = f(*a, **k)
    return r, time.perf_counter() - t


# ---------------------------------------------------------------- legacy with candidate scores

def legacy_candidates(scan_raw, bim_raw, voxel_size=0.2, square_tol=0.15, icp_dist_thresh=20.0):
    """Same steps as legacy.obbp_icp_corrigido, but returns the score of every candidate
    (the legacy function only returns the best one)."""
    scan_down = scan_raw.voxel_down_sample(voxel_size)
    bim_down = bim_raw.voxel_down_sample(voxel_size)
    T_align = np.eye(4)
    T_align[:3, 3] = bim_down.get_center() - scan_down.get_center()
    scan_z = copy.deepcopy(scan_down).transform(T_align)
    c = scan_z.get_center()
    (a_s, _), _ = legacy.get_2d_main_axes(scan_z)
    (a_bl, e_l), (a_bs, e_s) = legacy.get_2d_main_axes(bim_down)
    square = abs(e_l - e_s) / max(e_l, e_s) <= square_tol
    targets = [a_bl, a_bs, -a_bl, -a_bs] if square else [a_bl, -a_bl]
    crit = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=50)
    out = []
    for t in targets:
        R = legacy.rotation_matrix_2d_to_4x4(a_s, t)
        To, Tc = np.eye(4), np.eye(4)
        To[:3, 3], Tc[:3, 3] = -c, c
        R_i = Tc @ R @ To
        cand = copy.deepcopy(scan_z).transform(R_i)
        r = o3d.pipelines.registration.registration_icp(
            cand, bim_down, icp_dist_thresh, np.eye(4),
            o3d.pipelines.registration.TransformationEstimationPointToPoint(), crit)
        out.append(dict(M=r.transformation @ R_i @ T_align, fitness=r.fitness, rmse=r.inlier_rmse))
    return out


# ---------------------------------------------------------------- prototypes of the planned fixes

def pca_axes_2d(pcd):
    """T1.3 prototype: main axes of the XY projection (never vertical, never NaN)."""
    xy = np.asarray(pcd.points)[:, :2]
    w, v = np.linalg.eigh(np.cov((xy - xy.mean(0)).T))
    long_ax, short_ax = v[:, 1], v[:, 0]
    proj = (xy - xy.mean(0)) @ v
    return (long_ax, float(np.ptp(proj[:, 1]))), (short_ax, float(np.ptp(proj[:, 0])))


def multiscale_icp(src, tgt, thresholds, point_to_plane=False, max_iter=50, init=np.eye(4)):
    """T1.5/T1.6 prototype: ICP with decreasing thresholds; scores at the finest one."""
    est = (o3d.pipelines.registration.TransformationEstimationPointToPlane() if point_to_plane
           else o3d.pipelines.registration.TransformationEstimationPointToPoint())
    T = init
    for th in thresholds:
        r = o3d.pipelines.registration.registration_icp(
            src, tgt, th, T, est, o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iter))
        T = r.transformation
    return r


def obbp_v1(scan_raw, bim_raw, voxel=0.1, thresholds=(1.0, 0.3, 0.1), square_tol=0.15,
            axes="pca", point_to_plane=False, level=False):
    """Prototype of the planned algorithm: offset, (leveling), OBB/PCA candidates,
    multi-scale ICP, choice on fitness at the finest threshold then rmse."""
    offset = np.asarray(bim_raw.get_center())
    To = np.eye(4)
    To[:3, 3] = -offset
    scan = copy.deepcopy(scan_raw).transform(To).voxel_down_sample(voxel)
    bim = copy.deepcopy(bim_raw).transform(To).voxel_down_sample(voxel)
    if point_to_plane:
        bim.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=3 * voxel, max_nn=30))
    R_z = level_z(scan) if level else np.eye(4)
    T_align = np.eye(4)
    T_align[:3, 3] = bim.get_center() - (R_z @ np.r_[scan.get_center(), 1])[:3]
    s = copy.deepcopy(scan).transform(T_align @ R_z)
    f = pca_axes_2d if axes == "pca" else legacy.get_2d_main_axes
    (a_s, _), _ = f(s)
    (a_bl, e_l), (a_bs, e_s) = f(bim)
    targets = [a_bl, a_bs, -a_bl, -a_bs] if abs(e_l - e_s) / max(e_l, e_s) <= square_tol else [a_bl, -a_bl]
    c = s.get_center()
    cands = []
    for t in targets:
        R = legacy.rotation_matrix_2d_to_4x4(a_s, t)
        Tc, Tm = np.eye(4), np.eye(4)
        Tm[:3, 3], Tc[:3, 3] = -c, c
        R_i = Tc @ R @ Tm
        r = multiscale_icp(copy.deepcopy(s).transform(R_i), bim, thresholds, point_to_plane)
        M = r.transformation @ R_i @ T_align @ R_z
        cands.append(dict(M=np.linalg.inv(To) @ M @ To, fitness=r.fitness, rmse=r.inlier_rmse))
    best = max(range(len(cands)), key=lambda i: (round(cands[i]["fitness"], 3), -cands[i]["rmse"]))
    return cands[best], cands


def level_z(scan, dist=0.05):
    """T1.4 prototype: normal of the dominant RANSAC plane brought onto +Z."""
    n = np.asarray(scan.segment_plane(dist, 3, 1000)[0][:3])
    n = n if n[2] >= 0 else -n
    v = np.cross(n, [0, 0, 1])
    s, c = np.linalg.norm(v), n[2]
    if s < 1e-9:
        return np.eye(4)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    R = np.eye(3) + K + K @ K * ((1 - c) / s**2)
    ctr = np.asarray(scan.get_center())
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = ctr - R @ ctr
    return T


def fpfh_ransac(scan_raw, bim_raw, voxel=0.5, refine=(1.0, 0.3, 0.1)):
    """T3.2 baseline: FPFH features + RANSAC, then multi-scale ICP."""
    reg = o3d.pipelines.registration
    s, b = scan_raw.voxel_down_sample(voxel), bim_raw.voxel_down_sample(voxel)
    for p in (s, b):
        p.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=2 * voxel, max_nn=30))
    fs, fb = (reg.compute_fpfh_feature(p, o3d.geometry.KDTreeSearchParamHybrid(radius=5 * voxel, max_nn=100))
              for p in (s, b))
    r = reg.registration_ransac_based_on_feature_matching(
        s, b, fs, fb, True, 1.5 * voxel, reg.TransformationEstimationPointToPoint(False), 3,
        [reg.CorrespondenceCheckerBasedOnEdgeLength(0.9), reg.CorrespondenceCheckerBasedOnDistance(1.5 * voxel)],
        reg.RANSACConvergenceCriteria(100000, 0.999))
    fine = multiscale_icp(scan_raw.voxel_down_sample(0.1), bim_raw.voxel_down_sample(0.1), refine,
                          init=r.transformation)
    return fine.transformation
