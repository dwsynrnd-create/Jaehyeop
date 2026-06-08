"""
Counterion library for salt screening.

A salt's biopharmaceutical behaviour is governed mostly by three things:
  1. the *acidity* of the counterion (pKa of the conjugate acid HX),
  2. whether the counterion is a *common ion* already abundant in GI fluid
     (chloride is the classic one — gastric fluid is ~0.1 N HCl), and
  3. the resulting *salt solubility* (measured, or estimated from the above).

Reference for the counterion-acidity concept:
  Elder, Holm, Diego. "The Selection of a Pharmaceutical Salt — The Effect of
  the Acidity of the Counterion on Its Solubility and Potential
  Biopharmaceutical Performance." J. Pharm. Sci. 2017; 106(10):...  (PMID 29107790)

`pka_hx` is the pKa of the conjugate ACID of the counterion (lower = stronger
acid = better at keeping a weak base protonated/ionised over a wider pH range,
i.e. a lower pHmax and less disproportionation risk).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Counterion:
    name: str
    pka_hx: float          # pKa of conjugate acid HX
    valence: int           # counterion charge magnitude (mono=1, di=2)
    gi_common_ion: bool    # is this ion abundant in GI fluid? (chloride only)
    note: str = ""


# pKa values are standard textbook conjugate-acid pKa's.
COUNTERIONS = {
    "free_base":  Counterion("free base",     pka_hx=float("nan"), valence=0, gi_common_ion=False,
                             note="reference; no counterion"),
    "hcl":        Counterion("HCl",           pka_hx=-6.0, valence=1, gi_common_ion=True,
                             note="strong acid, but chloride is a GI common ion -> gastric solubility suppressed"),
    "mesylate":   Counterion("mesylate",      pka_hx=-1.9, valence=1, gi_common_ion=False,
                             note="methanesulfonate; strong acid, no common-ion penalty"),
    "esylate":    Counterion("esylate",       pka_hx=-1.5, valence=1, gi_common_ion=False,
                             note="ethanesulfonate"),
    "besylate":   Counterion("besylate",      pka_hx=-2.5, valence=1, gi_common_ion=False,
                             note="benzenesulfonate"),
    "tosylate":   Counterion("tosylate",      pka_hx=-2.8, valence=1, gi_common_ion=False,
                             note="p-toluenesulfonate; very strong acid, lipophilic"),
    "sulfate":    Counterion("sulfate",       pka_hx=1.99, valence=2, gi_common_ion=False,
                             note="divalent; pKa2 used"),
    "phosphate":  Counterion("phosphate",     pka_hx=2.12, valence=1, gi_common_ion=False,
                             note="weaker acid -> higher pHmax, disproportionation risk"),
    "oxalate":    Counterion("oxalate",       pka_hx=1.25, valence=2, gi_common_ion=False,
                             note="pKa1; divalent"),
    "maleate":    Counterion("maleate",       pka_hx=1.92, valence=1, gi_common_ion=False),
    "tartrate":   Counterion("tartrate",      pka_hx=3.04, valence=1, gi_common_ion=False),
    "citrate":    Counterion("citrate",       pka_hx=3.13, valence=1, gi_common_ion=False),
    "fumarate":   Counterion("fumarate",      pka_hx=3.03, valence=1, gi_common_ion=False),
    "succinate":  Counterion("succinate",     pka_hx=4.21, valence=1, gi_common_ion=False),
    "benzoate":   Counterion("benzoate",      pka_hx=4.20, valence=1, gi_common_ion=False,
                             note="weak acid -> high pHmax, prone to disproportionation"),
}


def get(name: str) -> Counterion:
    key = name.strip().lower().replace(" ", "_")
    if key not in COUNTERIONS:
        raise KeyError(f"Unknown counterion '{name}'. Known: {list(COUNTERIONS)}")
    return COUNTERIONS[key]
