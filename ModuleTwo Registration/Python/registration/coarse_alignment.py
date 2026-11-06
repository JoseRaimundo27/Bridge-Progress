"""Step 2 of OBBP-ICP: oriented bounding box alignment in the XY plane"""

import numpy as np
import open3d as o3d


def main_axes_2d(
    pcd: o3d.geometry.PointCloud,
) -> tuple[np.ndarray, float, np.ndarray, float]:
    """Long axis, long extent, short axis, short extent of the cloud projected on XY (T1.3)"""
    raise NotImplementedError("T1.3")


def is_square(long_extent: float, short_extent: float, square_tol: float) -> bool:
    """True when the footprint is close to a square (4 candidates instead of 2)"""
    raise NotImplementedError("T1.1")


def rotation_z_between(
    v_source: np.ndarray, v_target: np.ndarray, center: np.ndarray
) -> np.ndarray:
    """4x4 rotation about the Z axis, around `center`, that aligns v_source with v_target"""
    raise NotImplementedError("T1.1")


def generate_candidates(
    scan: o3d.geometry.PointCloud, bim: o3d.geometry.PointCloud, square_tol: float
) -> list[np.ndarray]:
    """2 candidate rotations (non-square) or 4 (square), as 4x4 matrices"""
    raise NotImplementedError("T1.1")
