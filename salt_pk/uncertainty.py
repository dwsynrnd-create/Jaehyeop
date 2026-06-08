"""
Monte-Carlo uncertainty band for the predicted salt/free-base exposure ratio.

A single number ("salt gives 2.3x") hides input uncertainty. This perturbs the
uncertain inputs over plausible ranges and reports the MEDIAN and 90% interval of
the AUC/Cmax ratio — the decision-relevant quantity. Disposition is shared and
largely cancels in the ratio, so the band reflects mainly absorption uncertainty
(permeability, salt solubility/dissolution, precipitation rate, wettability).

Usage:
  from salt_pk import IonizableDrug, SaltForm, DrugPK, get_species
  from salt_pk.uncertainty import ratio_ci
  print(ratio_ci(pk, io, SaltForm.free_base(), SaltForm.of("hcl", 2000), get_species("rat")))
"""
import random
from dataclasses import replace

from .engine import AbsParams, predict


def _pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    i = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
    return xs[i]


def ratio_ci(drug, drug_io, free_form, salt_form, sp, n=60, seed=0,
             caco2_fold=2.0, sol_fold=1.5):
    """
    Returns dict with median and 5th/95th percentiles of the salt/free-base
    AUC and Cmax ratio under input uncertainty.
      caco2_fold: permeability uncertainty (e.g. 2 = within 2-fold)
      sol_fold  : salt solubility / dissolution-extent uncertainty (e.g. 1.5)
    """
    rng = random.Random(seed)
    auc_r, cmax_r = [], []
    import math
    for _ in range(n):
        # shared perturbations (cancel partially in the ratio)
        kf = math.exp(rng.gauss(0, math.log(caco2_fold) / 1.64))      # permeability
        s0f = math.exp(rng.gauss(0, math.log(2.0) / 1.64))            # intrinsic sol
        # absorption constants
        ap = AbsParams(kprecip=rng.uniform(0.5, 4.0),
                       salt_wettability=rng.uniform(2.0, 8.0))
        d = replace(drug, caco2=(drug.caco2 * kf) if drug.caco2 else drug.caco2)
        io = replace(drug_io, s0_ugml=drug_io.s0_ugml * s0f)
        # salt-specific solubility perturbation
        sf = math.exp(rng.gauss(0, math.log(sol_fold) / 1.64))
        sform = salt_form
        if salt_form.s_salt_ugml:
            sform = replace(salt_form, s_salt_ugml=salt_form.s_salt_ugml * sf)
        fb = predict(d, io, free_form, sp, ap)
        s = predict(d, io, sform, sp, ap)
        if fb["AUC"] > 0 and fb["Cmax"] > 0:
            auc_r.append(s["AUC"] / fb["AUC"])
            cmax_r.append(s["Cmax"] / fb["Cmax"])
    return dict(
        auc_median=_pct(auc_r, 0.5), auc_p05=_pct(auc_r, 0.05), auc_p95=_pct(auc_r, 0.95),
        cmax_median=_pct(cmax_r, 0.5), cmax_p05=_pct(cmax_r, 0.05), cmax_p95=_pct(cmax_r, 0.95),
        n=len(auc_r))


def fmt(ci):
    return (f"AUC비 {ci['auc_median']:.2f}  (90% CI {ci['auc_p05']:.2f}–{ci['auc_p95']:.2f}) · "
            f"Cmax비 {ci['cmax_median']:.2f}  (90% CI {ci['cmax_p05']:.2f}–{ci['cmax_p95']:.2f})")


if __name__ == "__main__":
    from .solubility import IonizableDrug, SaltForm
    from .physiology import get as get_species
    from .engine import DrugPK
    io = IonizableDrug(mw=462.3, pka=5.24, s0_ugml=8.6, is_base=True)
    pk = DrugPK(dose_mgkg=50, caco2=25, clint=8, ppb_percent=85)
    ci = ratio_ci(pk, io, SaltForm.free_base(), SaltForm.of("hcl", 387), get_species("mouse"))
    print("IIIM-290 HCl/free base:", fmt(ci), "(관측 AUC 1.44, Cmax 1.57)")
