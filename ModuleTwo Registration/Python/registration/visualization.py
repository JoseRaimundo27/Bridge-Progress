"""Open3D windows, only shown with --viz"""

import open3d as o3d


def show_before_after(
    scan_raw: o3d.geometry.PointCloud,
    scan_registered: o3d.geometry.PointCloud,
    bim: o3d.geometry.PointCloud,
) -> None:
    """Initial state (scan red, BIM blue), then result (scan green, BIM blue)"""
    raise NotImplementedError("T2.1")
