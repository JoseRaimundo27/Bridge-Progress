"""Data returned by the registration"""

from dataclasses import dataclass, field

import numpy as np
import open3d as o3d


@dataclass
class CandidateScore:
    """Score of one OBB candidate rotation after ICP"""

    index: int
    rotation_deg: float
    fitness: float
    inlier_rmse: float
    d_avg: float


@dataclass
class RegistrationResult:
    scan_registered: o3d.geometry.PointCloud
    transform: np.ndarray  # 4x4, from the raw scan to the BIM coordinates
    d_avg: float  # m, mean scan -> BIM distance (input of Module III)
    fitness: float
    inlier_rmse: float
    best_candidate: int
    candidates: list[CandidateScore] = field(default_factory=list)
    offset: np.ndarray | None = None  # common offset removed in preprocessing
    scale: float = 1.0
    runtime_s: float = 0.0
