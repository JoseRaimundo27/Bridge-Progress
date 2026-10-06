"""Point cloud-to-BIM registration (Module II.2) with the OBBP-ICP algorithm

Pipeline (Tang & Shi 2026, Algorithm 1):
    preprocessing -> coarse_alignment (OBB) -> fine_alignment (ICP) -> metrics

Public entry point: `register(scan, bim, config)`
"""

from registration.config import RegistrationConfig
from registration.obbp_icp import register
from registration.results import CandidateScore, RegistrationResult

__all__ = ["RegistrationConfig", "RegistrationResult", "CandidateScore", "register"]
