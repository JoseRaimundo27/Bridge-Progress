"""Parameters of the registration, with the default values of the paper"""

from dataclasses import dataclass, field


@dataclass
class RegistrationConfig:
    # Step 1: preprocessing
    voxel_size: float = 0.1  # m, grid size used in the paper
    recenter: bool = True  # subtract a common offset before computing (T1.2)
    level_z: bool = False  # estimate R_z so the scan is Z-up (T1.4)

    # Step 2: bounding box alignment
    square_tol: float = (
        0.15  # |long - short| / long under which the footprint is "square"
    )

    # Step 3: ICP refinement (T1.5, T1.6)
    icp_thresholds: list[float] = field(
        default_factory=lambda: [1.0, 0.3, 0.1]
    )  # m, coarse to fine
    icp_max_iteration: int = 50
    point_to_plane: bool = False

    # Optional scale estimation for unscaled photogrammetry (T1.7)
    estimate_scale: bool = False
