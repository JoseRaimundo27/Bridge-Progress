"""Scan-vs-BIM test from a real IFC bridge model: Module I output -> registration (T3.4 preview).

Model: buildingSMART sample "Infra-Bridge.ifc" (IFC4X3_ADD2, 3 bridges, 44 elements), from
https://github.com/buildingSMART/Sample-Test-Files (IFC 4.3.2.0 / Simple-Scene), saved in ModuleOne BIMtoPC/Modelos/.

As-planned: the full model, sampled by Module I (geometriaEnuvem.py, uniform density).
Scan: an independent sampling of the elements already built at a construction stage, + 1 cm noise,
moved by a known transform (4 rotations). Stages follow the IFC classes:
    foundations: IfcFooting, IfcWall, IfcEarthworksFill
    substructure: + IfcColumn
    complete: all elements

Usage: python ifc_bridge.py
"""

import json
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import numpy as np
import open3d as o3d

import harness as h

MODULE1 = h.REPO / "ModuleOne BIMtoPC" / "Python"
sys.path.insert(0, str(MODULE1))
import geometriaEnuvem  # noqa: E402
from ifc_utils import elementos_construidos  # noqa: E402

IFC = h.REPO / "ModuleOne BIMtoPC" / "Modelos" / "Infra-Bridge.ifc"
OUT = Path(__file__).resolve().parent / "results"
STAGES = {
    "foundations only": {"IfcFooting", "IfcWall", "IfcEarthworksFill"},
    "foundations + piers": {"IfcFooting", "IfcWall", "IfcEarthworksFill", "IfcColumn"},
    "complete bridge": None,
}
METHODS = ("legacy (thr 20 m)", "prototype v1", "FPFH+RANSAC+ICP")
ANGLES = (0, 90, 180, 270)


def element_meshes():
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    meshes = []
    model = ifcopenshell.open(str(IFC))  # keep a reference: elements are invalid once the file is freed
    for e in elementos_construidos(model):
        if not e.Representation:
            continue
        s = ifcopenshell.geom.create_shape(settings, e)
        m = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(np.array(s.geometry.verts).reshape(-1, 3)),
                                      o3d.utility.Vector3iVector(np.array(s.geometry.faces).reshape(-1, 3)))
        meshes.append((e.is_a(), m))
    return meshes


def scan_of(meshes, classes, rng, density=30):
    """Independent uniform sampling (different from Module I's Poisson sampling) + 1 cm noise."""
    parts = []
    for i, (cls, m) in enumerate(meshes):
        if classes is None or cls in classes:
            o3d.utility.random.seed(1000 + i)
            n = max(50, int(m.get_surface_area() * density))
            parts.append(np.asarray(m.sample_points_uniformly(n).points))
    pts = np.vstack(parts)
    return pts + rng.normal(0, 0.01, pts.shape)


def main():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:  # Module I writes its outputs next to the script: redirect them
        geometriaEnuvem.PASTA_SCRIPT = Path(tmp)
        bim = geometriaEnuvem.extrair_geometria_e_gerar_nuvem(IFC)
    meshes = element_meshes()
    rng = np.random.default_rng(0)
    rows = []
    for stage, classes in STAGES.items():
        pts = scan_of(meshes, classes, rng)
        for method in METHODS:
            errs = []
            for a in ANGLES:
                T = h.rigid_transform(a, (120.0, -45.0, 3.0))
                scan = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts)).transform(T)
                if method == METHODS[0]:
                    M = h.legacy.obbp_icp_corrigido(scan, bim, voxel_size=0.2, icp_dist_thresh=20.0)[2]
                elif method == METHODS[1]:
                    M = h.obbp_v1(scan, bim)[0]["M"]
                else:
                    M = h.fpfh_ransac(scan, bim)
                errs.append(h.registration_error(M, T, pts)[0])
            ok = sum(e < h.SUCCESS_M for e in errs)
            rows.append(dict(stage=stage, scan_points=len(pts), method=method, success=ok, trials=len(ANGLES),
                             median_err_m=float(np.median(errs))))
            print(f"{stage:20s} | {len(pts):7d} pts | {method:18s} | {ok}/{len(ANGLES)} | median error {np.median(errs):7.3f} m",
                  flush=True)
    (OUT / "ifc_bridge.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
