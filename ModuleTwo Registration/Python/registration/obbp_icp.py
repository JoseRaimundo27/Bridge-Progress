"""OBBP-ICP orchestration: chains the steps of Algorithm 1"""

import open3d as o3d

from registration.config import RegistrationConfig
from registration.results import RegistrationResult


def register(
    scan: o3d.geometry.PointCloud,
    bim: o3d.geometry.PointCloud,
    config: RegistrationConfig,
) -> RegistrationResult:
    """Register the as-built scan onto the as-planned cloud

    1. preprocessing: offset, downsample, T_align, R_z
    2. coarse_alignment: candidate rotations from the OBB axes
    3. fine_alignment: ICP on each candidate
    4. fine_alignment: best candidate
    5. M_total = M_icp * R_best * R_z * T_align, applied to the raw scan; D_avg
    """
    raise NotImplementedError("T1.1")
