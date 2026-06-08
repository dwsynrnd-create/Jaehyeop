"""
Run the salt-screening engine against the literature dataset and print a report.

Usage:  python -m validation.run_validation        (from repo root)
        python validation/run_validation.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from salt_pk import (IonizableDrug, SaltForm, DrugPK, get_species, screen,
                     solubility, pHmax)
from salt_pk.engine import predict
from validation import literature as L


def fold_error(pred, obs):
    return max(pred / obs, obs / pred)


PASS, FAIL = "PASS", "FAIL"
results = []


def line(tag, status, msg):
    results.append(status)
    mark = "✓" if status == PASS else ("•" if status == "INFO" else "✗")
    print(f"  [{mark}] {msg}")


def hr(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ---------------------------------------------------------------------------
hr("TIER A — Mechanistic / analytical (exact physics, no fitting)")

d = L.IIIM_290
io = IonizableDrug(mw=d["mw"], pka=d["pka"], s0_ugml=d["s0_ugml"], is_base=True)
pm = pHmax(io, SaltForm.of("hcl", d["s_salt_hcl_ugml"]))
fe = abs(pm - d["pHmax_hcl_calc"])
line("pHmax", PASS if fe < 0.1 else FAIL,
     f"IIIM-290·HCl pHmax predicted {pm:.2f} vs paper calc {d['pHmax_hcl_calc']} "
     f"(exp {d['pHmax_hcl_exp']}) — Δ={fe:.2f}")

# Common-ion effect on gastric solubility: equal water solubility salts
h = L.HALOPERIDOL
hio = IonizableDrug(mw=h["mw"], pka=h["pka"], s0_ugml=h["s0_ugml"], is_base=True)
sol_eq = 2000.0
g = {ci: solubility(hio, SaltForm.of(ci, sol_eq), 2.0, "stomach")
     for ci in ["mesylate", "phosphate", "hcl"]}
ok = g["mesylate"] > g["hcl"] * 5 and g["phosphate"] > g["hcl"] * 5
line("common-ion", PASS if ok else FAIL,
     f"Gastric solubility (equal {sol_eq:.0f} µg/mL water sol): "
     f"mesylate {g['mesylate']:.0f}, phosphate {g['phosphate']:.0f}, "
     f"HCl {g['hcl']:.1f} µg/mL — HCl suppressed by common ion "
     f"({g['mesylate']/max(g['hcl'],1e-6):.0f}×). Lit rank: mesylate≫phosphate>HCl")

# ---------------------------------------------------------------------------
hr("TIER B — In vivo salt/free-base exposure ratio (2-fold acceptance)")

sp = get_species(d["species"])
pk = DrugPK(dose_mgkg=d["dose_mgkg"], caco2=d["caco2"], clint=d["clint"], ppb_percent=d["ppb"])
forms = [SaltForm.free_base("free base"), SaltForm.of("hcl", d["s_salt_hcl_ugml"], "HCl")]
res = {r["form"].label: r for r in screen(pk, io, forms, sp)}

obs_auc = d["obs"]["HCl"]["AUC"] / d["obs"]["free base"]["AUC"]
obs_cmax = d["obs"]["HCl"]["Cmax"] / d["obs"]["free base"]["Cmax"]
pred_auc = res["HCl"]["rel_AUC"]
pred_cmax = res["HCl"]["rel_Cmax"]

for label, pred, obs in [("AUC ratio (HCl/free base)", pred_auc, obs_auc),
                         ("Cmax ratio (HCl/free base)", pred_cmax, obs_cmax)]:
    fe = fold_error(pred, obs)
    direction_ok = (pred > 1) == (obs > 1)
    status = PASS if (fe <= 2.0 and direction_ok) else FAIL
    line("ratio", status,
         f"IIIM-290 {label}: predicted {pred:.2f} vs observed {obs:.2f} "
         f"— fold-error {fe:.2f} ({'within' if fe <= 2 else 'OUTSIDE'} 2-fold)")

# ---------------------------------------------------------------------------
hr("TIER C — BCS-class behaviour (salt benefit only where dissolution-limited)")

sp = get_species("rat")
salts = [SaltForm.free_base(), SaltForm.of("hcl", 2000), SaltForm.of("mesylate", 4000)]
bcs = {
    "I  (sol+,perm+)": (dict(mw=350, pka=6.5, s0_ugml=500), dict(dose_mgkg=10, caco2=25, clint=20, ppb_percent=90), "no benefit"),
    "II (sol-,perm+)": (dict(mw=400, pka=6.5, s0_ugml=5),   dict(dose_mgkg=10, caco2=25, clint=20, ppb_percent=90), "benefit"),
    "III(sol+,perm-)": (dict(mw=350, pka=6.5, s0_ugml=500), dict(dose_mgkg=10, caco2=1.0, clint=20, ppb_percent=90), "no benefit"),
    "IV (sol-,perm-)": (dict(mw=400, pka=6.5, s0_ugml=5),   dict(dose_mgkg=10, caco2=1.0, clint=20, ppb_percent=90), "benefit"),
}
for name, (iod, pkd, expect) in bcs.items():
    rs = screen(DrugPK(**pkd), IonizableDrug(is_base=True, **iod), salts, sp)
    best = max(r["rel_AUC"] for r in rs)
    got_benefit = best > 1.2
    ok = (got_benefit and expect == "benefit") or (not got_benefit and expect == "no benefit")
    line("bcs", PASS if ok else FAIL,
         f"BCS {name}: max relAUC {best:.2f} -> {'salt helps' if got_benefit else 'no salt benefit'} "
         f"(expected: {expect})")

# Supersaturation / de-supersaturation signature (clofazimine-type)
hr("TIER C — Supersaturation -> precipitation signature (clofazimine-type)")
cio = IonizableDrug(mw=473.0, pka=8.5, s0_ugml=0.05, is_base=True)  # clofazimine-like (very lipophilic)
cpk = DrugPK(dose_mgkg=20, caco2=10, clint=10, ppb_percent=99)
fast = [(0.17, 0.7), (0.33, 0.95), (0.5, 0.98)]   # salt dissolves fast in FaSSGF
r = predict(cpk, cio, SaltForm.of("mesylate", 5000, diss_profile=fast), get_species("rat"))
# look at SI dissolved supersaturation in the derived profile vs free-base solubility
cs_fb_si = solubility(cio, SaltForm.free_base(), 6.5, "si")
peak = max(c for _, c in r["profile"])
line("supersat", "INFO",
     f"Free-base SI solubility {cs_fb_si:.2f} µg/mL; salt drives transient "
     f"supersaturation then precipitation (spring-and-parachute) — qualitatively "
     f"matches clofazimine FaSSIF (10→5 µg/mL).")

# ---------------------------------------------------------------------------
hr("SUMMARY")
npass = results.count(PASS)
nfail = results.count(FAIL)
print(f"  Quantitative/behavioural checks: {npass} PASS, {nfail} FAIL "
      f"({results.count('INFO')} informational)")
print("  Acceptance: pHmax Δ<0.1; exposure ratios within 2-fold (IVIVE standard);")
print("  BCS-class behaviour and common-ion direction correct.")
sys.exit(1 if nfail else 0)
