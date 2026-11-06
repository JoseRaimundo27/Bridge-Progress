"""Synthetic bridges shared by the tests: no real data needed"""

import sys
from pathlib import Path

import numpy as np
import open3d as o3d
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def bridge_mesh(symmetric: bool = False) -> o3d.geometry.TriangleMesh:
    """60 m deck on piers. The asymmetric version has irregular piers and one abutment,
    so only one orientation fits"""
    mesh = o3d.geometry.TriangleMesh.create_box(60, 8, 1.5).translate((0, 0, 10))
    piers = (8, 22, 36, 50) if symmetric else (6, 18, 40)
    for x in piers:
        mesh += o3d.geometry.TriangleMesh.create_box(1.5, 1.5, 10).translate(
            (x, 3.25, 0)
        )
    if not symmetric:
        mesh += o3d.geometry.TriangleMesh.create_box(4, 10, 11.5).translate((60, -1, 0))
    return mesh


def rigid_transform(angle_deg: float, translation) -> np.ndarray:
    """4x4 rotation about Z followed by a translation"""
    a = np.radians(angle_deg)
    transform = np.eye(4)
    transform[:2, :2] = [[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]
    transform[:3, 3] = translation
    return transform


@pytest.fixture
def bim_cloud() -> o3d.geometry.PointCloud:
    o3d.utility.random.seed(0)
    return bridge_mesh().sample_points_uniformly(60000)


@pytest.fixture
def make_scan():
    """Factory: scan of the same bridge, with noise, moved by a known transform
    Returns (scan, applied 4x4 transform)"""

    def _make(
        angle_deg=0.0, translation=(120.0, -45.0, 3.0), noise=0.01, symmetric=False
    ):
        o3d.utility.random.seed(1)
        points = np.asarray(
            bridge_mesh(symmetric).sample_points_uniformly(50000).points
        )
        points = points + np.random.default_rng(0).normal(0, noise, points.shape)
        scan = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
        transform = rigid_transform(angle_deg, translation)
        return scan.transform(transform), transform

    return _make
