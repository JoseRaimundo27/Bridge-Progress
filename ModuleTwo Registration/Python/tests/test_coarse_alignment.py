import pytest


@pytest.mark.skip(reason="T1.3")
def test_main_axes_2d_recovers_known_angle():
    """A rectangle rotated by a known angle gives its long axis to within 1 degree"""


@pytest.mark.skip(reason="T1.3")
def test_main_axes_2d_never_returns_nan():
    """Tall clouds (vertical OBB axis) still give horizontal axes, without NaN"""


@pytest.mark.skip(reason="T1.1")
def test_generate_candidates_count():
    """2 candidates for a long footprint, 4 for a square one"""
