"""Deterministic mineral additions for near-zero-mineral RO water.

Masses assume pure CaCl2·2H2O and CaSO4·2H2O. This module does not
predict mash pH and does not account for residual ions in RO water.
"""

from dataclasses import dataclass

# Ion mass fractions based on molar masses (g/mol).
_CACL2_2H2O = 147.014
_CASO4_2H2O = 172.171
_CA = 40.078
_CL2 = 2 * 35.453
_SO4 = 96.06


@dataclass(frozen=True)
class IonProfile:
    calcium_mg_l: float
    chloride_mg_l: float
    sulfate_mg_l: float


def mineral_profile(volume_l: float, calcium_chloride_dihydrate_g: float,
                    calcium_sulfate_dihydrate_g: float) -> IonProfile:
    """Return *added* ion concentrations, excluding source-water minerals."""
    if volume_l <= 0:
        raise ValueError("Water volume must be positive")
    if min(calcium_chloride_dihydrate_g, calcium_sulfate_dihydrate_g) < 0:
        raise ValueError("Salt masses must not be negative")
    ca_from_chloride = calcium_chloride_dihydrate_g * _CA / _CACL2_2H2O
    ca_from_sulfate = calcium_sulfate_dihydrate_g * _CA / _CASO4_2H2O
    chloride = calcium_chloride_dihydrate_g * _CL2 / _CACL2_2H2O
    sulfate = calcium_sulfate_dihydrate_g * _SO4 / _CASO4_2H2O
    return IonProfile(
        calcium_mg_l=(ca_from_chloride + ca_from_sulfate) * 1000 / volume_l,
        chloride_mg_l=chloride * 1000 / volume_l,
        sulfate_mg_l=sulfate * 1000 / volume_l,
    )


def split_salts(total_g: float, mash_water_l: float, sparge_water_l: float) -> tuple[float, float]:
    """Split a total salt addition proportional to mash and sparge water."""
    if total_g < 0 or mash_water_l <= 0 or sparge_water_l < 0:
        raise ValueError("Invalid salt mass or water volumes")
    mash = total_g * mash_water_l / (mash_water_l + sparge_water_l)
    return mash, total_g - mash
