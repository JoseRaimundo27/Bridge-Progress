"""Data sheet of the input clouds (T0.3)

Example:
    python inspect_clouds.py ../AsBuilt/scan.ply ../AsPlanned/bim.ply
"""

import argparse
from pathlib import Path

import open3d as o3d


def describe(pcd: o3d.geometry.PointCloud) -> dict:
    """Point count, min/max/extent, coordinate magnitude, probable unit,
    density (mean nearest-neighbour distance), colours/normals, Z-up or not"""
    raise NotImplementedError("T0.3")


def print_table(rows: dict[str, dict]) -> None:
    """Markdown table, one column per cloud"""
    raise NotImplementedError("T0.3")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Describe point clouds before registration"
    )
    parser.add_argument("clouds", type=Path, nargs="+", help=".ply files")
    args = parser.parse_args()

    rows = {
        path.name: describe(o3d.io.read_point_cloud(str(path))) for path in args.clouds
    }
    print_table(rows)


if __name__ == "__main__":
    main()
