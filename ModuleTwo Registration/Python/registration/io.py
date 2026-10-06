"""Reading the input clouds and writing the outputs used by Module III"""

from pathlib import Path

import open3d as o3d

from registration.config import RegistrationConfig
from registration.results import RegistrationResult


def load_point_cloud(path: Path) -> o3d.geometry.PointCloud:
    """Read a .ply file and fail with a clear message if it is missing or empty"""
    raise NotImplementedError("T2.1")


def save_results(
    result: RegistrationResult, config: RegistrationConfig, out_dir: Path
) -> None:
    """Write the outputs for Module III (T2.2):

    - scan_registered.ply
    - transform.json: 4x4 matrix, offset, scale
    - metrics.json: D_avg, fitness, rmse, every candidate's score, parameters, runtime
    """
    raise NotImplementedError("T2.2")
