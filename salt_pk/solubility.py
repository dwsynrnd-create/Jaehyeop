"""
pH-dependent solubility for a monoprotic weak base and its salts.

This is the heart of salt screening: the *same* free base, presented as
different salts, sees a different effective solubility profile along the GI
tract. We model three effects that distinguish salt forms:

  (1) Henderson-Hasselbalch pH-solubility of the free base
          S_base(pH)  = S0 * (1 + 10^(pKa - pH))        [weak base]
          S_acid(pH)  = S0 * (1 + 10^(pH - pKa))        [weak acid]

  (2) pHmax — the pH where the salt solid and free-base solid solubility
      curves cross. Below pHmax the salt is the stable solid (high solubility);
      above pHmax the drug disproportionates to the free base (low solubility).
          pHmax = pKa + log10(S0 / S_salt)               [weak base]
      (Serajuddin 2007; Elder 2017)

  (3) Common-ion effect — for an HCl salt, chloride is abundant in gastric
      fluid, so the salt solubility is suppressed by the solubility product:
          Ksp = [BH+][X-]   ->   [BH+] solved with added common ion.
      Strong-acid counterions that are NOT common ions (mesylate, esylate,
      tosylate ...) escape this penalty and give higher gastric solubility.

All solubilities are handled in µg/mL (free-base equivalent). The common-ion
calculation is done in molar units internally using the free-base MW.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from .counterions import Counterion, get as get_counterion


@dataclass
class IonizableDrug:
    """Free-base (or free-acid) intrinsic properties — shared by ALL salt forms."""
    mw: float                 # g/mol of the FREE form
    pka: float                # most relevant ionizable pKa
    s0_ugml: float            # intrinsic (neutral-species) aqueous solubility, µg/mL
    is_base: bool = True      # True=weak base, False=weak acid


@dataclass
class SaltForm:
    """One physical form to screen (free base or a specific salt)."""
    counterion: Counterion
    # Measured salt solubility (µg/mL, free-base equivalent) in COMMON-ION-FREE
    # water/buffer. None for the free base (uses the drug's S0 instead).
    s_salt_ugml: Optional[float] = None
    label: str = ""
    # OPTIONAL measured biorelevant dissolution profile: list of
    # (time_h, cumulative_fraction_0to1). When given it OVERRIDES the mechanistic
    # dissolution and captures real form differences (supersaturation, particle
    # size, disproportionation) that solubility alone cannot predict.
    diss_profile: Optional[list] = None
    diss_medium: str = ""     # label only, e.g. 'FaSSGF', 'FaSSIF'

    @classmethod
    def free_base(cls, label="free base", diss_profile=None):
        return cls(counterion=get_counterion("free_base"), s_salt_ugml=None,
                   label=label, diss_profile=diss_profile)

    @classmethod
    def of(cls, counterion_name: str, s_salt_ugml: float, label: str = "",
           diss_profile=None, diss_medium=""):
        ci = get_counterion(counterion_name)
        return cls(counterion=ci, s_salt_ugml=s_salt_ugml,
                   label=label or f"{counterion_name} salt",
                   diss_profile=diss_profile, diss_medium=diss_medium)


# Typical GI chloride concentration (mM) used for the common-ion calculation.
# Gastric fluid ~0.1 N HCl; small intestine much lower.
GI_CHLORIDE_mM = {"stomach": 100.0, "si": 30.0}


def _hh_factor(drug: IonizableDrug, pH: float) -> float:
    """Ionised-to-neutral solubility multiplier (>=1)."""
    if drug.is_base:
        return 1.0 + 10 ** (drug.pka - pH)
    return 1.0 + 10 ** (pH - drug.pka)


def pHmax(drug: IonizableDrug, form: SaltForm) -> Optional[float]:
    """pH at which the salt and free-base solid curves intersect."""
    if form.s_salt_ugml is None or form.counterion.valence == 0:
        return None
    # [BH+] plateau (free-base equiv) = salt intrinsic solubility
    if drug.is_base:
        return drug.pka + math.log10(drug.s0_ugml / form.s_salt_ugml)
    return drug.pka - math.log10(drug.s0_ugml / form.s_salt_ugml)


def _bh_plus_with_common_ion(drug: IonizableDrug, form: SaltForm, region: str,
                             ignore_common_ion: bool = False) -> float:
    """
    Saturated ionised-species concentration (µg/mL free-base equiv) of the salt,
    accounting for the common-ion effect.  Solves Ksp = [BH+]([BH+]+C_ci).
    """
    s_salt_M = (form.s_salt_ugml / 1000.0) / drug.mw          # mM (free-base equiv)
    ksp = s_salt_M ** 2                                       # intrinsic Ksp (mM^2)
    if ignore_common_ion or not form.counterion.gi_common_ion:
        bh_M = s_salt_M                                       # no common-ion penalty
    else:
        c_ci = GI_CHLORIDE_mM.get(region, 0.0)               # mM chloride
        # [BH+] = (-C + sqrt(C^2 + 4 Ksp)) / 2
        bh_M = (-c_ci + math.sqrt(c_ci ** 2 + 4 * ksp)) / 2.0
    return bh_M * drug.mw * 1000.0                            # back to µg/mL


def solubility(drug: IonizableDrug, form: SaltForm, pH: float, region: str = "si",
               ignore_common_ion: bool = False) -> float:
    """
    Effective equilibrium solubility (µg/mL, free-base equiv) of `form` at `pH`.
    `region` ('stomach'|'si') selects the common-ion (chloride) level.
    Set `ignore_common_ion=True` to get the salt's intrinsic (water) solubility,
    used to drive the wetting/dissolution-RATE advantage (which common-ion does
    not abolish — it only lowers the equilibrium ceiling).
    """
    s_base = drug.s0_ugml * _hh_factor(drug, pH)              # free-base solid curve
    if form.s_salt_ugml is None:                             # pure free base
        return s_base

    pm = pHmax(drug, form)
    salt_is_solid = (pH < pm) if drug.is_base else (pH > pm)
    if not salt_is_solid:
        return s_base                                        # disproportionated -> free base

    bh = _bh_plus_with_common_ion(drug, form, region, ignore_common_ion)  # ionised plateau (µg/mL)
    # total dissolved on the salt curve = ionised plateau + neutral fraction
    if drug.is_base:
        s_salt_curve = bh * (1.0 + 10 ** (pH - drug.pka))
    else:
        s_salt_curve = bh * (1.0 + 10 ** (drug.pka - pH))
    # below pHmax the salt is the stable solid -> its (higher) curve governs
    return s_salt_curve
