"""
Accuracy validation against REAL literature numbers (multi-compound).

Reports, for each salt-vs-free-base comparison, the predicted AUC/Cmax ratio
against the observed ratio, plus an accuracy metric:
        accuracy% = 100 * (1 - |pred-obs| / obs)

Datasets (all values from the primary papers cited in README / validation.literature):
  1. IIIM-290·HCl       (mouse 50 mg/kg)  -- mechanistic mode (S0, S_salt, pKa)
  2. Cilostazol mesylate (rat 20 mg/kg)   -- MEASURED dissolution profile mode
  3. Cilostazol besylate (rat 20 mg/kg)   -- MEASURED dissolution profile mode
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from salt_pk import IonizableDrug, SaltForm, DrugPK, get_species, predict
from salt_pk.engine import AbsParams


def acc(pred, obs):
    return 100 * (1 - abs(pred - obs) / obs)


def ratio(drug_io, pk, sp, free_form, salt_form, ap):
    fb = predict(pk, drug_io, free_form, sp, ap)
    s = predict(pk, drug_io, salt_form, sp, ap)
    return s["AUC"] / fb["AUC"], s["Cmax"] / fb["Cmax"]


def build_cases(ap):
    cases = []

    # ---- 1. IIIM-290 (mouse 50 mg/kg) : mechanistic mode -------------------
    io = IonizableDrug(mw=462.3, pka=5.24, s0_ugml=8.6, is_base=True)
    pk = DrugPK(dose_mgkg=50, caco2=25, clint=8, ppb_percent=85)   # metabolically stable, permeable, no efflux
    rA, rC = ratio(io, pk, get_species("mouse"),
                   SaltForm.free_base(), SaltForm.of("hcl", 387), ap)
    cases.append(("IIIM-290 HCl/FB", rA, 1.44, rC, 1.57))

    # ---- 2&3. Cilostazol (rat 20 mg/kg) : MEASURED dissolution profiles -----
    # pKa 11.8 (effectively neutral in GI) -> use measured-profile mode (bypasses
    # the solubility model). Profiles approximate the reported pH 1.2 curves with
    # the exact 6 h endpoints: FB 25.4%, mesylate 93.5%, besylate 98.6%.
    cio = IonizableDrug(mw=369.46, pka=11.8, s0_ugml=4.0, is_base=True)
    cpk = DrugPK(dose_mgkg=20, caco2=22, clint=10, ppb_percent=96)
    fb_prof  = [(0.5, 0.09), (1, 0.14), (2, 0.19), (4, 0.23), (6, 0.254)]
    mes_prof = [(0.25, 0.68), (0.5, 0.84), (1, 0.91), (2, 0.93), (6, 0.935)]
    bes_prof = [(0.25, 0.80), (0.5, 0.93), (1, 0.97), (2, 0.98), (6, 0.986)]
    sp = get_species("rat")
    free = SaltForm.free_base(diss_profile=fb_prof)
    rA, rC = ratio(cio, cpk, sp, free, SaltForm.of("mesylate", 9999, diss_profile=mes_prof), ap)
    cases.append(("Cilostazol mesylate/FB", rA, 3.88, rC, 3.65))
    rA, rC = ratio(cio, cpk, sp, free, SaltForm.of("besylate", 9999, diss_profile=bes_prof), ap)
    cases.append(("Cilostazol besylate/FB", rA, 2.94, rC, 2.87))
    return cases


def report(ap, title):
    print(f"\n{title}  (kprecip={ap.kprecip}, salt_wettability={ap.salt_wettability})")
    print("-" * 92)
    print(f"{'comparison':26}{'predAUC':>9}{'obsAUC':>8}{'AUC acc%':>10}"
          f"{'predCmax':>10}{'obsCmax':>9}{'Cmax acc%':>11}")
    print("-" * 92)
    accs = []
    dir_ok = 0
    for name, pa, oa, pc, oc in build_cases(ap):
        aA, aC = acc(pa, oa), acc(pc, oc)
        accs += [aA, aC]
        dir_ok += (pa > 1) == (oa > 1)
        print(f"{name:26}{pa:9.2f}{oa:8.2f}{aA:10.0f}{pc:10.2f}{oc:9.2f}{aC:11.0f}")
    print("-" * 92)
    mean = sum(accs) / len(accs)
    n_ge90 = sum(1 for a in accs if a >= 90)
    within2 = all(max(p/o, o/p) <= 2 for n, p, o, _, __ in
                  [(c[0], c[1], c[2], c[3], c[4]) for c in build_cases(ap)])
    print(f"  mean accuracy {mean:.0f}% | endpoints ≥90% accurate: {n_ge90}/{len(accs)} | "
          f"direction correct: {dir_ok}/3 | all within 2-fold: {within2}")
    return mean


if __name__ == "__main__":
    print("=" * 92)
    print("ACCURACY VS REAL LITERATURE VALUES")
    print("=" * 92)
    # (a) blind defaults
    report(AbsParams(), "A) Default constants (blind)")
    # (b) single global calibration of kprecip across the 3 ratios
    best, best_ap = -1e9, None
    for kp in [x / 2 for x in range(1, 21)]:
        ap = AbsParams(kprecip=kp)
        m = sum(acc(p, o) + acc(pc, oc)
                for _, p, o, pc, oc in build_cases(ap)) / 6
        if m > best:
            best, best_ap = m, ap
    report(best_ap, "B) After single global kprecip calibration")
