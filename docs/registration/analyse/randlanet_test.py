"""AI test: RandLA-Net (repo's PonteDataset, Open3D-ML 0.20, CPU) on synthetic bridge scenes,
then registration of the raw / ground-truth-segmented / RandLA-Net-segmented scan.

Labels: 0 = not bridge (terrain, crane, trees), 1 = bridge.
Usage: python randlanet_test.py [epochs]
"""

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import open3d as o3d
from plyfile import PlyData, PlyElement

import harness as h

HERE = Path(__file__).resolve().parent
DATA = HERE / "randla_data"
sys.path.insert(0, str(h.REPO / "ModuleTwo RandlaNET" / "Python"))


def scene(seed, symmetric=False):
    """Bridge + clutter, coloured, in the bridge frame."""
    rng = np.random.default_rng(seed)
    bridge = np.asarray(h.sample(h.bridge_mesh(symmetric), 60000, seed).points)
    bridge += rng.normal(0, 0.01, bridge.shape)
    clutter = h.make_clutter(seed=seed + 100)
    pts = np.vstack([bridge, clutter])
    lab = np.r_[np.ones(len(bridge), int), np.zeros(len(clutter), int)]
    col = np.where(lab[:, None] == 1, [150, 150, 145], [110, 95, 70]).astype(float)
    col += rng.normal(0, 25, col.shape)  # noisy colours so geometry matters too
    return pts, np.clip(col, 0, 255).astype(np.uint8), lab


def write_ply(path, pts, col, lab):
    v = np.zeros(len(pts), dtype=[("x", "f8"), ("y", "f8"), ("z", "f8"), ("red", "u1"), ("green", "u1"),
                                  ("blue", "u1"), ("label", "i4")])
    v["x"], v["y"], v["z"] = pts.T
    v["red"], v["green"], v["blue"] = col.T
    v["label"] = lab
    path.parent.mkdir(parents=True, exist_ok=True)
    PlyData([PlyElement.describe(v, "vertex")]).write(str(path))


def main(epochs):
    # Open3D-ML reports loss / accuracy / mIoU through logging (silent if not configured)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for split, seeds in (("train", (10, 11, 12)), ("val", (20,)), ("test", (30,))):
        for s in seeds:
            write_ply(DATA / split / f"scene_{s}.ply", *scene(s, symmetric=(s == 11)))

    import torch
    import open3d.ml.torch as ml3d
    import dataset_ponte

    # fewer repetitions than the repo's x100 so that CPU training stays short
    dataset_ponte.PonteSplit.__len__ = lambda self: len(self.files) * 10
    dataset = dataset_ponte.PonteDataset(str(DATA))
    model = ml3d.models.RandLANet(num_points=40960, num_classes=2, in_channels=6, ignored_label_inds=[])
    pipeline = ml3d.pipelines.SemanticSegmentation(
        model=model, dataset=dataset, max_epoch=epochs, batch_size=2, val_batch_size=2,
        optimizer={"lr": 1e-3}, scheduler_gamma=0.95, num_workers=0,
        main_log_dir=str(HERE / "randla_logs"), device="cpu", save_ckpt_freq=epochs)
    t = time.perf_counter()
    pipeline.run_train()
    train_s = time.perf_counter() - t

    # inference on the unseen test scene
    pts, col, lab = scene(30)
    data = {"point": (pts - pts.min(0)).astype(np.float32), "feat": col.astype(np.float32) / 255,
            "label": np.zeros(len(pts), np.int32)}
    t = time.perf_counter()
    pred = pipeline.run_inference(data)["predict_labels"]
    infer_s = time.perf_counter() - t
    tp = np.sum((pred == 1) & (lab == 1))
    iou_b = tp / np.sum((pred == 1) | (lab == 1))
    iou_n = np.sum((pred == 0) & (lab == 0)) / np.sum((pred == 0) | (lab == 0))
    seg = dict(epochs=epochs, train_s=train_s, infer_s=infer_s, accuracy=float(np.mean(pred == lab)),
               iou_bridge=float(iou_b), iou_not_bridge=float(iou_n), miou=float((iou_b + iou_n) / 2),
               bridge_points_kept=f"{tp}/{np.sum(lab == 1)}", clutter_points_left=int(np.sum((pred == 1) & (lab == 0))))
    print("## RandLA-Net segmentation (unseen test scene)")
    print(json.dumps(seg, indent=1))

    # registration of the three versions of the scan (Table 1 of the paper)
    bim = h.make_bim()
    rows = []
    for name, mask in (("raw", np.ones(len(pts), bool)), ("ground truth segmentation", lab == 1),
                       ("RandLA-Net segmentation", pred == 1)):
        res = []
        for a in (0, 90, 180, 270):
            T = h.rigid_transform(a, (120.0, -45.0, 3.0))
            scan = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts[mask])).transform(T)
            if mask.sum() < 100:
                res.append(dict(method="legacy thr 20 m", err=float("inf"), d_avg=float("nan")))
                res.append(dict(method="prototype v1", err=float("inf"), d_avg=float("nan")))
                continue
            for meth, f in (("legacy thr 20 m", lambda s: h.legacy.obbp_icp_corrigido(s, bim, voxel_size=0.2, icp_dist_thresh=20.0)[2]),
                            ("prototype v1", lambda s: h.obbp_v1(s, bim)[0]["M"])):
                M = f(scan)
                err = h.registration_error(M, T, pts[mask])[0]
                reg = o3d.geometry.PointCloud(scan).transform(M)
                res.append(dict(method=meth, err=err, d_avg=h.d_avg(reg, bim)))
        for meth in ("legacy thr 20 m", "prototype v1"):
            sel = [r for r in res if r["method"] == meth]
            rows.append(dict(scan=name, points=int(mask.sum()), method=meth,
                             success=f"{sum(r['err'] < h.SUCCESS_M for r in sel)}/4",
                             d_avg=float(np.mean([r["d_avg"] for r in sel]))))
    print("## Registration of raw / segmented scans")
    for r in rows:
        print(r)
    (HERE / "results" / "randlanet.json").write_text(json.dumps(dict(segmentation=seg, registration=rows), indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
