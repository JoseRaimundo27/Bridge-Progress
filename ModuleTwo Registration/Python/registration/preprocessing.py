"""Step 1 of OBBP-ICP: downsampling, recentering and Z-axis leveling"""

import numpy as np
import open3d as o3d


def downsample(
    pcd: o3d.geometry.PointCloud, voxel_size: float
) -> o3d.geometry.PointCloud:
    """Voxel grid downsampling"""
    raise NotImplementedError("T1.1")


def compute_offset(bim: o3d.geometry.PointCloud) -> np.ndarray:
    """Common offset (float64) subtracted from both clouds to avoid precision loss
    with georeferenced coordinates (T1.2)"""
    raise NotImplementedError("T1.2")


def translation_to_center(
    scan: o3d.geometry.PointCloud, bim: o3d.geometry.PointCloud
) -> np.ndarray:
    """4x4 matrix T_align that moves the scan's center onto the BIM's center"""
    raise NotImplementedError("T1.1")


def estimate_z_leveling(scan: o3d.geometry.PointCloud) -> np.ndarray:
    """4x4 matrix R_z that brings the scan's vertical onto the Z axis (T1.4)"""
    raise NotImplementedError("T1.4")
