"""
Sanity tests for the salt-screening engine. Run:  python tests/test_engine.py
(plain asserts so it works without pytest)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from salt_pk import (IonizableDrug, SaltForm, DrugPK, get_species, screen,
                     predict, pHmax, solubility)


def approx(a, b, tol=0.02):
    return abs(a - b) <= tol * max(abs(a), abs(b), 1e-9)


def test_pHmax_formula():
    io = IonizableDrug(mw=450, pka=5.24, s0_ugml=8.6, is_base=True)
    assert approx(pHmax(io, SaltForm.of("hcl", 387)), 3.59, tol=0.01)
    print("ok  pHmax analytical")


def test_mass_balance_and_Fa_le_1():
    """AUC ratio must equal Fa ratio (identical disposition) and Fa<=1."""
    io = IonizableDrug(mw=350, pka=6.5, s0_ugml=500, is_base=True)
    pk = DrugPK(dose_mgkg=10, caco2=25, clint=20, ppb_percent=90)
    rs = screen(pk, io, [SaltForm.free_base(), SaltForm.of("hcl", 2000)], get_species("rat"))
    for r in rs:
        assert r["Fa"] <= 1.0 + 1e-6, "Fa exceeded 1 (mass not conserved)"
    fa_ratio = rs[1]["Fa"] / rs[0]["Fa"]
    auc_ratio = rs[1]["rel_AUC"]
    assert approx(fa_ratio, auc_ratio, tol=0.03), (fa_ratio, auc_ratio)
    print("ok  mass balance (AUC ratio == Fa ratio, Fa<=1)")


def test_bcs_behaviour():
    sp = get_species("rat")
    salts = [SaltForm.free_base(), SaltForm.of("mesylate", 4000)]
    # BCS I: no benefit
    r1 = screen(DrugPK(dose_mgkg=10, caco2=25, clint=20, ppb_percent=90),
                IonizableDrug(mw=350, pka=6.5, s0_ugml=500, is_base=True), salts, sp)
    assert r1[1]["rel_AUC"] < 1.2, "BCS I should show no salt benefit"
    # BCS II: benefit
    r2 = screen(DrugPK(dose_mgkg=10, caco2=25, clint=20, ppb_percent=90),
                IonizableDrug(mw=400, pka=6.5, s0_ugml=5, is_base=True), salts, sp)
    assert r2[1]["rel_AUC"] > 1.2, "BCS II should show salt benefit"
    print("ok  BCS-class behaviour")


def test_common_ion_suppresses_hcl():
    io = IonizableDrug(mw=375, pka=8.3, s0_ugml=2.5, is_base=True)
    s_hcl = solubility(io, SaltForm.of("hcl", 2000), 2.0, "stomach")
    s_mes = solubility(io, SaltForm.of("mesylate", 2000), 2.0, "stomach")
    assert s_mes > 5 * s_hcl, "common-ion should suppress HCl gastric solubility"
    print("ok  common-ion suppression")


def test_compendial_multi_pH_high_pH_discriminates():
    """A poor high-pH (6.8) dissolution must give lower exposure than a robust one,
    even with identical gastric (pH 1.2) dissolution — the parachute matters."""
    io = IonizableDrug(mw=400, pka=6.0, s0_ugml=5, is_base=True)
    pk = DrugPK(dose_mgkg=20, caco2=20, clint=15, ppb_percent=92)
    sp = get_species("rat")
    g = [(0.25, 0.8), (0.5, 0.95), (1, 0.98)]                      # same gastric spring
    poor = SaltForm.of("mesylate", 2000, ph_profiles={1.2: g, 6.8: [(1, 0.15), (2, 0.25), (6, 0.40)]})
    good = SaltForm.of("mesylate", 2000, ph_profiles={1.2: g, 6.8: [(0.25, 0.7), (0.5, 0.9), (1, 0.95)]})
    fa_poor = predict(pk, io, poor, sp)["Fa"]
    fa_good = predict(pk, io, good, sp)["Fa"]
    assert fa_good > fa_poor + 0.05, (fa_poor, fa_good)
    print("ok  compendial multi-pH: high-pH (6.8) profile discriminates")


def test_measured_profile_is_absorption_ceiling():
    io = IonizableDrug(mw=400, pka=6.5, s0_ugml=5, is_base=True)
    pk = DrugPK(dose_mgkg=10, caco2=20, clint=20, ppb_percent=90)
    slow = [(0.25, 0.10), (0.5, 0.20), (1, 0.35), (2, 0.50), (4, 0.60)]  # plateau 60%
    r = predict(pk, io, SaltForm.of("phosphate", 1500, diss_profile=slow), get_species("rat"))
    assert r["Fa"] <= 0.62, "Fa must not exceed final dissolved fraction"
    print("ok  measured-profile absorption ceiling")


def test_batch_csv_import():
    """CSV batch loader runs end-to-end and scores the template."""
    from salt_pk.batch import run_csv, summary
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "dataset_template.csv")
    res = run_csv(path)
    assert len(res) >= 3, "expected >=3 salt forms"
    s = summary(res)
    assert s["n_scored"] >= 3 and s["within2"] == s["n_scored"], s
    assert 50 <= s["mean_acc"] <= 100, s["mean_acc"]
    print("ok  CSV batch import + scoring")


if __name__ == "__main__":
    for fn in [test_pHmax_formula, test_mass_balance_and_Fa_le_1, test_bcs_behaviour,
               test_common_ion_suppresses_hcl, test_compendial_multi_pH_high_pH_discriminates,
               test_measured_profile_is_absorption_ceiling, test_batch_csv_import]:
        fn()
    print("\nALL TESTS PASSED")
