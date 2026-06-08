"""
Pretty-print a salt-screening comparison and (optionally) export CSV.

    python -m salt_pk.report            # runs the built-in worked example
"""

from typing import List, Dict
from .solubility import IonizableDrug, SaltForm, pHmax
from .physiology import Species, get as get_species
from .engine import DrugPK, AbsParams, screen


def print_report(drug: DrugPK, drug_io: IonizableDrug, forms: List[SaltForm],
                 sp: Species, ap: AbsParams = AbsParams(), title: str = "Salt screening"):
    res = screen(drug, drug_io, forms, sp, ap)
    print(f"\n{title}  —  {sp.label}, {drug.dose_mgkg} mg/kg {drug.route}")
    print("-" * 92)
    print(f"{'form':22}{'pHmax':>7}{'Fa %':>8}{'Cmax':>10}{'Tmax':>7}{'AUC':>11}"
          f"{'F %':>7}{'relAUC':>8}{'relCmax':>9}")
    print(f"{'':22}{'':>7}{'':>8}{'ng/mL':>10}{'h':>7}{'ng·h/mL':>11}{'':>7}{'':>8}{'':>9}")
    print("-" * 92)
    for r in res:
        pm = pHmax(drug_io, r["form"])
        print(f"{r['form'].label[:22]:22}"
              f"{('%.2f' % pm) if pm is not None else '  –':>7}"
              f"{r['Fa']*100:8.1f}{r['Cmax']:10.0f}{r['Tmax']:7.1f}{r['AUC']:11.0f}"
              f"{r['F']*100:7.1f}{r['rel_AUC']:8.2f}{r['rel_Cmax']:9.2f}")
    print("-" * 92)
    best = max(res, key=lambda r: r["AUC"])
    print(f"  ▶ Highest predicted exposure: {best['form'].label} "
          f"(AUC {best['AUC']:.0f} ng·h/mL, {best['rel_AUC']:.2f}× free base)")
    return res


def to_csv(res: List[Dict], path: str):
    import csv
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["form", "Fa_%", "Cmax_ng/mL", "Tmax_h", "AUC_ng.h/mL",
                    "F_%", "rel_AUC", "rel_Cmax"])
        for r in res:
            w.writerow([r["form"].label, round(r["Fa"]*100, 1), round(r["Cmax"]),
                        round(r["Tmax"], 2), round(r["AUC"]), round(r["F"]*100, 1),
                        round(r["rel_AUC"], 3), round(r["rel_Cmax"], 3)])
    print(f"  CSV written: {path}")


if __name__ == "__main__":
    # Worked example: a BCS II weak base, screen free base + 5 salts.
    drug_io = IonizableDrug(mw=420, pka=6.0, s0_ugml=6, is_base=True)
    drug = DrugPK(dose_mgkg=30, caco2=18, clint=22, ppb_percent=92, vss=2.5)
    forms = [
        SaltForm.free_base(),
        SaltForm.of("hcl",       s_salt_ugml=1500),
        SaltForm.of("tosylate",  s_salt_ugml=3000),
        SaltForm.of("phosphate", s_salt_ugml=900),
        SaltForm.of("esylate",   s_salt_ugml=4000),
        SaltForm.of("oxalate",   s_salt_ugml=1200),
    ]
    print_report(drug, drug_io, forms, get_species("rat"),
                 title="Example: BCS II weak base salt screen")
