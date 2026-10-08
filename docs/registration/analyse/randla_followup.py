"""Follow-up of randlanet_test.py: can simple post-processing make the RandLA-Net output usable?"""
import json, sys, logging
from pathlib import Path
import numpy as np, open3d as o3d
import harness as h
import randlanet_test as rt
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(h.REPO / "ModuleTwo RandlaNET" / "Python"))
import open3d.ml.torch as ml3d, dataset_ponte
dataset = dataset_ponte.PonteDataset(str(rt.DATA))
model = ml3d.models.RandLANet(num_points=40960, num_classes=2, in_channels=6, ignored_label_inds=[])
pipe = ml3d.pipelines.SemanticSegmentation(model=model, dataset=dataset, device="cpu")
pipe.load_ckpt(str(sorted((HERE / "randla_logs").rglob("ckpt_*.pth"))[-1]))
pts, col, lab = rt.scene(30)
pred = pipe.run_inference({"point": (pts - pts.min(0)).astype(np.float32), "feat": col.astype(np.float32) / 255,
                           "label": np.zeros(len(pts), np.int32)})["predict_labels"]
seg = pts[pred == 1]

def largest_cluster(p, eps=1.0):
    pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(p))
    l = np.asarray(pc.cluster_dbscan(eps=eps, min_points=10))
    return p[l == np.bincount(l[l >= 0]).argmax()]

def sor(p):
    pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(p))
    return np.asarray(pc.remove_statistical_outlier(20, 2.0)[0].points)

bim = h.make_bim()
rows = []
for name, cloud in (("RandLA-Net", seg), ("RandLA-Net + statistical outlier removal", sor(seg)),
                    ("RandLA-Net + largest DBSCAN cluster", largest_cluster(seg))):
    is_bridge = np.isin(cloud.view([('', cloud.dtype)] * 3), pts[lab == 1].view([('', pts.dtype)] * 3)).ravel()
    for meth in ("prototype v1", "FPFH+RANSAC+ICP"):
        ok, ds = 0, []
        for a in (0, 90, 180, 270):
            T = h.rigid_transform(a, (120.0, -45.0, 3.0))
            scan = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(cloud)).transform(T)
            M = h.obbp_v1(scan, bim)[0]["M"] if meth == "prototype v1" else h.fpfh_ransac(scan, bim)
            ok += h.registration_error(M, T, cloud)[0] < h.SUCCESS_M
            reg = o3d.geometry.PointCloud(scan).transform(M)
            d = np.asarray(reg.compute_point_cloud_distance(bim)); ds.append((d.mean(), np.median(d)))
        rows.append(dict(scan=name, points=len(cloud), clutter_left=int((~is_bridge).sum()), method=meth,
                         success=f"{ok}/4", d_avg=float(np.mean([x[0] for x in ds])), median=float(np.mean([x[1] for x in ds]))))
        print(rows[-1], flush=True)
(HERE / "results" / "randlanet_followup.json").write_text(json.dumps(rows, indent=1))
