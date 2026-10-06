import pytest


@pytest.mark.skip(reason="T3.1")
@pytest.mark.parametrize("angle_deg", [0, 45, 90, 135, 180])
def test_register_recovers_known_transform(angle_deg, bim_cloud, make_scan):
    """Asymmetric bridge: rotation error < 0.5 degree, translation error < 2 x voxel_size"""


@pytest.mark.skip(reason="T1.5")
def test_best_candidate_is_not_flipped(bim_cloud, make_scan):
    """At 180 degrees, the chosen candidate is the right one, not the flipped one"""


@pytest.mark.skip(reason="T3.4")
@pytest.mark.parametrize("fraction", [0.3, 0.5, 0.7])
def test_partial_bridge(fraction, bim_cloud, make_scan):
    """Scan containing only part of the bridge still registers"""
