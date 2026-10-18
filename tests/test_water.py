import pytest

from homebrew_as_code.water import mineral_profile, split_salts


def test_christmas_ale_added_ions():
    profile = mineral_profile(28.0, 5.0, 3.0)
    assert profile.calcium_mg_l == pytest.approx(73.65, abs=0.2)
    assert profile.chloride_mg_l == pytest.approx(86.13, abs=0.2)
    assert profile.sulfate_mg_l == pytest.approx(59.78, abs=0.2)


def test_split_salts_preserves_total():
    mash, sparge = split_salts(5.0, 23.0, 5.0)
    assert mash == pytest.approx(4.107142857)
    assert mash + sparge == pytest.approx(5.0)


def test_reject_invalid_input():
    with pytest.raises(ValueError):
        mineral_profile(0, 5, 3)
    with pytest.raises(ValueError):
        split_salts(-1, 23, 5)
