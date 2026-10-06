"""Steps 3 and 4 of OBBP-ICP: ICP refinement of each candidate and choice of the best one"""

import numpy as np
import open3d as o3d

from registration.config import RegistrationConfig
from registration.results import CandidateScore


def refine_icp(
    scan: o3d.geometry.PointCloud,
    bim: o3d.geometry.PointCloud,
    config: RegistrationConfig,
) -> o3d.pipelines.registration.RegistrationResult:
    """Multi-scale ICP over `config.icp_thresholds` (T1.5), point-to-point or point-to-plane (T1.6)"""
    raise NotImplementedError("T1.5")


def select_best(scores: list[CandidateScore]) -> int:
    """Index of the best candidate: highest fitness at the finest threshold, then lowest rmse (T1.5)"""
    raise NotImplementedError("T1.5")


def estimate_scale(
    scan: o3d.geometry.PointCloud, bim: o3d.geometry.PointCloud
) -> float:
    """Scale factor for unscaled photogrammetry (T1.7)"""
    raise NotImplementedError("T1.7")
