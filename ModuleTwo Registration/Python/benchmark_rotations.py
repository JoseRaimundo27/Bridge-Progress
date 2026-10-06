"""Robustness to the initial rotation, as in Table 2 of the paper (T3.2)

Each method registers the scan rotated by 0, 45, 90, 135 and 180 degrees

Example:
    python benchmark_rotations.py --scan ../AsBuilt/scan.ply --bim ../AsPlanned/bim.ply --out ../outputs/benchmark
"""

import argparse
from pathlib import Path

import numpy as np
import open3d as o3d

ANGLES_DEG = [0, 45, 90, 135, 180]
METHODS = ["obbp_icp", "icp", "ransac_fpfh"]


def rotate_about_z(
    pcd: o3d.geometry.PointCloud, angle_deg: float
) -> o3d.geometry.PointCloud:
    """Copy of the cloud rotated about Z around its center"""
    raise NotImplementedError("T3.2")


def run_method(
    method: str, scan: o3d.geometry.PointCloud, bim: o3d.geometry.PointCloud
) -> np.ndarray:
    """4x4 transform found by `method`"""
    raise NotImplementedError("T3.2")


def is_success(d_avg: float, voxel_size: float) -> bool:
    """Success criterion of a trial"""
    raise NotImplementedError("T3.2")


def summarize(results: list[dict], out_dir: Path) -> None:
    """Success rate, mean and standard deviation of D_avg per method -> CSV"""
    raise NotImplementedError("T3.2")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark registration methods against initial rotations."
    )
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--bim", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise NotImplementedError("T3.2")


if __name__ == "__main__":
    main()
