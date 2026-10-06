"""Quality of the registration (T2.3)"""

import numpy as np
import open3d as o3d


def distances(
    source: o3d.geometry.PointCloud, target: o3d.geometry.PointCloud
) -> np.ndarray:
    """Distance from each source point to its nearest target point"""
    raise NotImplementedError("T2.3")


def d_avg(scan: o3d.geometry.PointCloud, bim: o3d.geometry.PointCloud) -> float:
    """Mean scan -> BIM distance, as defined in the paper"""
    raise NotImplementedError("T1.1")


def distance_stats(dist: np.ndarray) -> dict[str, float]:
    """Mean, median, 95th percentile and standard deviation"""
    raise NotImplementedError("T2.3")


def deviation_cloud(
    scan: o3d.geometry.PointCloud, dist: np.ndarray
) -> o3d.geometry.PointCloud:
    """Copy of the scan coloured by its distance to the BIM (heat map)"""
    raise NotImplementedError("T2.3")
