import pytest


@pytest.mark.skip(reason="T1.2")
def test_offset_keeps_precision_with_utm_coordinates():
    """Clouds shifted by ~(500000, 8000000) m register as well as at the origin"""


@pytest.mark.skip(reason="T1.4")
def test_level_z_recovers_tilt():
    """A cloud tilted by 5-10 degrees is put back Z-up to within 0.5 degree"""


@pytest.mark.skip(reason="T1.4")
def test_level_z_keeps_upright_cloud():
    """An already Z-up cloud is left unchanged"""
