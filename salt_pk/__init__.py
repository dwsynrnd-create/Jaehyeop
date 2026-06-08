"""
salt_pk — In-vitro -> in-vivo (IVIVE) oral PK predictor for SALT SCREENING.

Given a free base/acid and a set of candidate salt forms (HCl, tosylate,
phosphate, esylate, oxalate, ...), predict which form gives the highest in vivo
exposure (AUC / Cmax) from in vitro data. Works across BCS Class I-IV.

Quick start
-----------
    from salt_pk import IonizableDrug, SaltForm, DrugPK, get_species, screen

    drug_io = IonizableDrug(mw=400, pka=6.5, s0_ugml=5, is_base=True)
    drug_pk = DrugPK(dose_mgkg=50, caco2=20, clint=30, ppb_percent=90)
    forms = [SaltForm.free_base(),
             SaltForm.of("hcl", s_salt_ugml=2000),
             SaltForm.of("tosylate", s_salt_ugml=5000)]
    for r in screen(drug_pk, drug_io, forms, get_species("mouse")):
        print(r["form"].label, r["AUC"], r["rel_AUC"])
"""

from .solubility import IonizableDrug, SaltForm, solubility, pHmax
from .counterions import Counterion, COUNTERIONS, get as get_counterion
from .physiology import Species, SPECIES, get as get_species
from .engine import DrugPK, AbsParams, predict, screen

__all__ = [
    "IonizableDrug", "SaltForm", "solubility", "pHmax",
    "Counterion", "COUNTERIONS", "get_counterion",
    "Species", "SPECIES", "get_species",
    "DrugPK", "AbsParams", "predict", "screen",
]
