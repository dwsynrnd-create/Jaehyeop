"""
Does pH-buffer DISSOLUTION input beat mechanistic SOLUBILITY input?

Direct head-to-head on the case where both are available (cilostazol, which has
measured pH 1.2/4.5/6.8 dissolution AND in-vivo PK). Emits a bar-chart SVG.

    python validation/input_mode_comparison.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from salt_pk import IonizableDrug, SaltForm, DrugPK, get_species, predict

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def acc(p, o):
    return max(0.0, 100 * (1 - abs(p - o) / o))


def _mp(p12, p68):
    f = lambda e: [(0.25, 0.7*e), (0.5, 0.9*e), (1, 0.97*e), (2, e)]
    return {1.2: f(p12), 6.8: f(p68)}


io = IonizableDrug(mw=369.46, pka=11.8, s0_ugml=4.0, is_base=True)
pk = DrugPK(dose_mgkg=20, caco2=22, clint=10, ppb_percent=96)
sp = get_species("rat")
cases = [("Cilostazol mesylate", 0.935, 3.88), ("Cilostazol besylate", 0.986, 2.94)]

results = []
print("Input-mode comparison (cilostazol; obs = measured in-vivo AUC ratio):")
print(f"{'salt':22}{'SOLUBILITY':>12}{'acc%':>6}{'DISSOLUTION':>13}{'acc%':>6}")
for nm, p12, obs in cases:
    fb_s = predict(pk, io, SaltForm.free_base(), sp)["AUC"]
    s_s = predict(pk, io, SaltForm.of("mesylate", 50000), sp)["AUC"]
    r_sol = s_s / fb_s
    fb_d = predict(pk, io, SaltForm.free_base(ph_profiles=_mp(0.254, 0.0274)), sp)["AUC"]
    s_d = predict(pk, io, SaltForm.of("mesylate", 50000, ph_profiles=_mp(p12, 0.20)), sp)["AUC"]
    r_d = s_d / fb_d
    results.append((nm, r_sol, acc(r_sol, obs), r_d, acc(r_d, obs), obs))
    print(f"{nm:22}{r_sol:12.2f}{acc(r_sol,obs):6.0f}{r_d:13.2f}{acc(r_d,obs):6.0f}")

mean_sol = sum(r[2] for r in results) / len(results)
mean_dis = sum(r[4] for r in results) / len(results)
print(f"\nMean accuracy:  SOLUBILITY {mean_sol:.0f}%   ->   DISSOLUTION {mean_dis:.0f}%   "
      f"(+{mean_dis-mean_sol:.0f} %p)")


# ---- SVG grouped bars ------------------------------------------------------
def svg():
    W, H = 560, 360
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica,Arial,sans-serif">',
          f'<rect width="{W}" height="{H}" fill="#f5f2ec"/>',
          f'<text x="{W/2}" y="30" font-size="16" font-weight="bold" text-anchor="middle" fill="#073d39">'
          f'입력 방식별 예측 정확도 (cilostazol)</text>',
          f'<text x="{W/2}" y="50" font-size="11.5" text-anchor="middle" fill="#828a92">'
          f'용해도 입력 vs pH-용출 입력 — 실측 AUC비 대비</text>']
    bx, by, bw, bh = 70, 90, 200, 170
    for i, (nm, rs, asol, rd, adis, obs) in enumerate(results):
        gx = bx + i * 230
        # solubility bar
        el.append(f'<rect x="{gx}" y="{by+bh-bh*asol/100:.0f}" width="70" height="{bh*asol/100:.0f}" fill="#b5651d" rx="3"/>')
        el.append(f'<text x="{gx+35}" y="{by+bh-bh*asol/100-6:.0f}" font-size="12" text-anchor="middle" fill="#6e3d12">{asol:.0f}%</text>')
        # dissolution bar
        el.append(f'<rect x="{gx+90}" y="{by+bh-bh*adis/100:.0f}" width="70" height="{bh*adis/100:.0f}" fill="#0d6b63" rx="3"/>')
        el.append(f'<text x="{gx+125}" y="{by+bh-bh*adis/100-6:.0f}" font-size="12" text-anchor="middle" fill="#073d39">{adis:.0f}%</text>')
        el.append(f'<text x="{gx+80}" y="{by+bh+18:.0f}" font-size="11" text-anchor="middle" fill="#1b2127">{nm.split()[-1]}</text>')
    # axis baseline
    el.append(f'<line x1="{bx-8}" y1="{by+bh}" x2="{W-30}" y2="{by+bh}" stroke="#444"/>')
    # legend
    el.append(f'<rect x="{bx}" y="{H-44}" width="13" height="13" fill="#b5651d"/>')
    el.append(f'<text x="{bx+19}" y="{H-33}" font-size="11.5" fill="#1b2127">용해도 입력 (Tier 1)</text>')
    el.append(f'<rect x="{bx+170}" y="{H-44}" width="13" height="13" fill="#0d6b63"/>')
    el.append(f'<text x="{bx+189}" y="{H-33}" font-size="11.5" fill="#1b2127">pH-용출 입력 (Tier 2)</text>')
    el.append('</svg>')
    open(os.path.join(DOCS, "input_mode_comparison.svg"), "w").write("\n".join(el))


svg()
print("SVG written: docs/input_mode_comparison.svg")
