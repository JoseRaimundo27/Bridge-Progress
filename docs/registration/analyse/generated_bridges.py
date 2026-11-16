"""Scan-vs-BIM tests on generated IFC 4.3 bridges, through realistic construction sequences.

No public dataset pairs a bridge under construction with its BIM, so this script builds them:
- random girder bridges (2 to 6 spans, 15-40 m spans, piers 5-15 m, deck 8-14 m wide, unequal spans),
  written as IFC 4.3 files with ifcopenshell (footings, piers, pier caps, abutments, one deck slab per span);
- as-planned cloud: Module I (geometriaEnuvem.py) on the full IFC, as in production;
- scans of the elements built at each stage: foundations, + piers, deck span by span, complete;
- methods: see harness.METHODS ("combined" = best of wide-ICP prototype and FPFH + RANSAC, by the fitness
  of the scan on the as-planned cloud at 0.2 m).

Usage: python generated_bridges.py [number_of_bridges]
"""

import json
import sys
import tempfile
from pathlib import Path

import ifcopenshell
import ifcopenshell.api as api
import numpy as np
import open3d as o3d

import harness as h

sys.path.insert(0, str(h.REPO / "ModuleOne BIMtoPC" / "Python"))
import geometriaEnuvem  # noqa: E402

OUT = Path(__file__).resolve().parent / "results"
ANGLES = (0, 90, 180, 270)


# ------------------------------------------------------------------ IFC generation

def box(f, body, container, ifc_class, name, size, center, stage):
    """Box element: rectangle profile extruded along Z, bottom face at center[2]."""
    e = api.run("root.create_entity", f, ifc_class=ifc_class, name=name)
    profile = f.createIfcRectangleProfileDef("AREA", None, None, float(size[0]), float(size[1]))
    rep = api.run("geometry.add_profile_representation", f, context=body, profile=profile, depth=float(size[2]))
    api.run("geometry.assign_representation", f, product=e, representation=rep)
    m = np.eye(4)
    m[:3, 3] = center
    api.run("geometry.edit_object_placement", f, product=e, matrix=m)
    api.run("spatial.assign_container", f, products=[e], relating_structure=container)
    pset = api.run("pset.add_pset", f, product=e, name="Pset_Construction")
    api.run("pset.edit_pset", f, pset=pset, properties={"Stage": stage})
    return e


def make_bridge(path, rng):
    n_spans = int(rng.integers(2, 7))
    spans = rng.uniform(15, 40, n_spans)
    width = rng.uniform(8, 14)
    height = rng.uniform(5, 15)
    deck_t = 1.2
    f = ifcopenshell.file(schema="IFC4X3")
    project = api.run("root.create_entity", f, ifc_class="IfcProject", name="generated")
    api.run("unit.assign_unit", f, length={"is_metric": True, "raw": "METERS"})  # default would be millimetres
    ctx = api.run("context.add_context", f, context_type="Model")
    body = api.run("context.add_context", f, context_type="Model", context_identifier="Body",
                   target_view="MODEL_VIEW", parent=ctx)
    site = api.run("root.create_entity", f, ifc_class="IfcSite")
    bridge = api.run("root.create_entity", f, ifc_class="IfcBridge", name="girder bridge")
    api.run("aggregate.assign_object", f, products=[site], relating_object=project)
    api.run("aggregate.assign_object", f, products=[bridge], relating_object=site)

    xs = np.r_[0, np.cumsum(spans)]  # support positions along the deck axis
    for k, x in enumerate(xs):
        end = k in (0, len(xs) - 1)
        box(f, body, bridge, "IfcFooting", f"footing {k}", (6, width, 1.5), (x, 0, -1.5), "foundations")
        if end:
            box(f, body, bridge, "IfcWall", f"abutment {k}", (2.5, width + 1, height), (x, 0, 0), "foundations")
        else:
            for y in ((-width / 4, width / 4) if width > 11 else (0,)):
                box(f, body, bridge, "IfcColumn", f"pier {k}", (1.6, 1.6, height - 1.0), (x, y, 0), "piers")
            box(f, body, bridge, "IfcBeam", f"pier cap {k}", (2.0, width, 1.0), (x, 0, height - 1.0), "piers")
    for s in range(n_spans):
        box(f, body, bridge, "IfcSlab", f"deck span {s + 1}", (spans[s], width, deck_t),
            ((xs[s] + xs[s + 1]) / 2, 0, height), f"deck {s + 1}")
    f.write(str(path))
    return dict(spans=[round(float(x), 1) for x in spans], width=round(float(width), 1), height=round(float(height), 1))


# ------------------------------------------------------------------ scans and registration

def element_clouds(path, density=30):
    """Independent uniform sampling of each element (different from Module I's), keyed by stage."""
    import ifcopenshell.geom
    import ifcopenshell.util.element as ue
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    model = ifcopenshell.open(str(path))
    out = []
    for i, e in enumerate(model.by_type("IfcBuiltElement")):
        s = ifcopenshell.geom.create_shape(settings, e)
        m = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(np.array(s.geometry.verts).reshape(-1, 3)),
                                      o3d.utility.Vector3iVector(np.array(s.geometry.faces).reshape(-1, 3)))
        o3d.utility.random.seed(2000 + i)
        pts = np.asarray(m.sample_points_uniformly(max(50, int(m.get_surface_area() * density))).points)
        out.append((ue.get_psets(e)["Pset_Construction"]["Stage"], pts))
    return out


def stages(clouds):
    """Cumulative construction stages: foundations, + piers, deck span by span (complete = last)."""
    decks = sorted({s for s, _ in clouds if s.startswith("deck")}, key=lambda s: int(s.split()[1]))
    order = [("foundations", {"foundations"}), ("+ piers", {"foundations", "piers"})]
    for k in range(1, len(decks) + 1):
        name = "complete" if k == len(decks) else f"+ deck {k}/{len(decks)} spans"
        order.append((name, {"foundations", "piers", *decks[:k]}))
    return order


def main(n_bridges):
    out = OUT / "generated_bridges.json"
    rows = json.loads(out.read_text()) if out.exists() else []  # resume: results are saved after each bridge
    done = {r["bridge"] for r in rows}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        geometriaEnuvem.PASTA_SCRIPT = tmp  # Module I writes next to its script: redirect its outputs
        for b in range(n_bridges):
            rng = np.random.default_rng(1000 + b)  # one seed per bridge, so a resumed run gives the same bridges
            ifc = tmp / f"bridge_{b}.ifc"
            info = make_bridge(ifc, rng)
            if b in done:
                continue
            bim = geometriaEnuvem.extrair_geometria_e_gerar_nuvem(ifc)
            clouds = element_clouds(ifc)
            print(f"\n== bridge {b}: spans {info['spans']} m, width {info['width']} m, piers {info['height']} m, "
                  f"as-planned {len(bim.points)} pts", flush=True)
            for stage, keep in stages(clouds):
                pts = np.vstack([p for s, p in clouds if s in keep])
                pts = pts + rng.normal(0, 0.01, pts.shape)
                errs = {m: [] for m in h.METHODS}
                for a in ANGLES:
                    T = h.rigid_transform(a, (120.0, -45.0, 3.0))
                    scan = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts)).transform(T)
                    for m, M in h.run_all_methods(scan, bim).items():
                        errs[m].append(h.registration_error(M, T, pts)[0])
                for m, e in errs.items():
                    rows.append(dict(bridge=b, **info, stage=stage, method=m, success=sum(x < h.SUCCESS_M for x in e),
                                     trials=len(ANGLES), median_err_m=float(np.median(e))))
                print(f"   {stage:22s} " + " | ".join(f"{sum(x < h.SUCCESS_M for x in e)}/4" for e in errs.values()), flush=True)
            out.write_text(json.dumps(rows, indent=1))

    def group(stage):
        return stage if stage in ("foundations", "+ piers", "complete") else "deck partly built"
    print("\n| Stage | " + " | ".join(h.METHODS) + " |\n|---|" + "---|" * len(h.METHODS))
    for g in ("foundations", "+ piers", "deck partly built", "complete"):
        sel = [r for r in rows if group(r["stage"]) == g]
        print(f"| {g} | " + " | ".join(f"{sum(r['success'] for r in sel if r['method'] == m)}/"
                                       f"{sum(r['trials'] for r in sel if r['method'] == m)}" for m in h.METHODS) + " |")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
