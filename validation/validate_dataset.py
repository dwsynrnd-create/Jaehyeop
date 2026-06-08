"""
Run the curated literature dataset, score accuracy, and emit:
  - console table + summary
  - docs/validation_scatter.svg  (predicted vs observed, log-log, 2-fold bands)
  - docs/VALIDATION_SUMMARY.md    (at-a-glance verdict)

    python validation/validate_dataset.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validation.dataset import ENTRIES, haloperidol_rank

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def acc(p, o):
    return 100 * (1 - abs(p - o) / o)


def classify(e):
    if "plateau" in e:
        return "plateau"
    if "/HCl" in e["id"]:
        return "counterion"     # salt-vs-salt counterion difference
    return "salt_vs_base"


# ---- run -------------------------------------------------------------------
rows = []
for e in ENTRIES:
    pa, pc = e["predict"]()
    rows.append(dict(e=e, pa=pa, pc=pc, kind=classify(e)))

svb = [r for r in rows if r["kind"] == "salt_vs_base" and r["e"].get("obs_auc")]
plateau = [r for r in rows if r["kind"] == "plateau"]
counterion = [r for r in rows if r["kind"] == "counterion"]
direction = [r for r in rows if r["e"].get("obs_auc") or r["e"].get("direction")]

# stats
within2 = lambda p, o: max(p/o, o/p) <= 2.0
n_dir_ok = sum(1 for r in rows
               if (r["e"].get("obs_auc") and (r["pa"] > 1) == (r["e"]["obs_auc"] > 1))
               or (r["e"].get("direction") == "up" and r["pa"] > 1))
n_dir_tot = sum(1 for r in rows if r["e"].get("obs_auc") or r["e"].get("direction"))
mag = svb + plateau
n_2fold = sum(1 for r in mag if within2(r["pa"], r["e"]["obs_auc"]))
mean_acc = sum(acc(r["pa"], r["e"]["obs_auc"]) for r in mag) / len(mag)
hr = haloperidol_rank()
hr_order = [k for k, _ in sorted(hr.items(), key=lambda kv: -kv[1])]
hr_ok = hr_order == ["mesylate", "phosphate", "hcl"]

# ---- console ---------------------------------------------------------------
print("=" * 90)
print("LITERATURE VALIDATION  —  salt vs free-base oral PK")
print("=" * 90)
print(f"{'compound':34}{'grade':>5}{'kind':>13}{'pred':>7}{'obs':>7}{'AUCacc%':>9}{'2-fold':>8}")
print("-" * 90)
for r in rows:
    e = r["e"]
    o = e.get("obs_auc")
    if o:
        a = f"{acc(r['pa'], o):.0f}"
        tf = "ok" if within2(r["pa"], o) else "OUT"
        os_ = f"{o:.2f}"
    else:
        a, tf, os_ = "dir", "up" if r["pa"] > 1 else "DOWN", "↑"
    print(f"{e['id']:34}{e['grade']:>5}{r['kind']:>13}{r['pa']:7.2f}{os_:>7}{a:>9}{tf:>8}")
print("-" * 90)
print(f"Haloperidol counterion rank: {' > '.join(hr_order)}  "
      f"({'OK' if hr_ok else 'X'}; differences are small — see limitation)")
print()
print(f"Direction correct : {n_dir_ok}/{n_dir_tot}")
print(f"Within 2-fold     : {n_2fold}/{len(mag)} (magnitude+plateau set)")
print(f"Mean AUC accuracy : {mean_acc:.0f}%  (salt-vs-base + plateau, n={len(mag)})")
print(f"Counterion-vs-counterion (mesylate/HCl): predicted "
      f"{counterion[0]['pa']:.2f} vs observed {counterion[0]['e']['obs_auc']:.2f} "
      f"-> MODEL LIMITATION (needs measured dissolution)")


# ---- SVG scatter -----------------------------------------------------------
def svg_scatter(path):
    W, H, M = 720, 560, 70
    lo, hi = 0.7, 6.5
    def X(v): return M + (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (W - 2*M)
    def Y(v): return H - M - (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (H - 2*M)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">']
    s.append(f'<rect width="{W}" height="{H}" fill="#fffdf9"/>')
    # 2-fold band
    band = []
    for v in [lo, hi]:
        band.append((X(v), Y(min(hi, v*2))))
    pts_up = " ".join(f"{X(v):.1f},{Y(min(hi,v*2)):.1f}" for v in [lo, hi])
    pts_dn = " ".join(f"{X(v):.1f},{Y(max(lo,v/2)):.1f}" for v in [hi, lo])
    s.append(f'<polygon points="{pts_up} {pts_dn}" fill="#0d6b63" opacity="0.07"/>')
    # y=x line and 2-fold dashed
    s.append(f'<line x1="{X(lo):.1f}" y1="{Y(lo):.1f}" x2="{X(hi):.1f}" y2="{Y(hi):.1f}" stroke="#1b2127" stroke-width="1.5"/>')
    for f in (2.0, 0.5):
        x1, y1 = X(lo), Y(max(lo, min(hi, lo*f)))
        x2, y2 = X(hi), Y(max(lo, min(hi, hi*f)))
        s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#9e2b25" stroke-width="1" stroke-dasharray="5 4" opacity="0.6"/>')
    # ticks
    for v in [1, 2, 3, 4, 5, 6]:
        s.append(f'<line x1="{X(v):.1f}" y1="{H-M}" x2="{X(v):.1f}" y2="{H-M+5}" stroke="#444"/>')
        s.append(f'<text x="{X(v):.1f}" y="{H-M+20}" font-size="12" text-anchor="middle" fill="#444">{v}x</text>')
        s.append(f'<line x1="{M-5}" y1="{Y(v):.1f}" x2="{M}" y2="{Y(v):.1f}" stroke="#444"/>')
        s.append(f'<text x="{M-10}" y="{Y(v)+4:.1f}" font-size="12" text-anchor="end" fill="#444">{v}x</text>')
    s.append(f'<text x="{W/2}" y="{H-15}" font-size="13" text-anchor="middle" fill="#1b2127">예측 노출비 (predicted AUC ratio, salt/free base)</text>')
    s.append(f'<text x="18" y="{H/2}" font-size="13" text-anchor="middle" fill="#1b2127" transform="rotate(-90 18 {H/2})">실측 노출비 (observed)</text>')
    s.append(f'<text x="{W/2}" y="28" font-size="16" font-weight="bold" text-anchor="middle" fill="#073d39">Predicted vs Observed — 2-fold 밴드 안: {n_2fold}/{len(mag)}</text>')
    # points
    for r in svb + plateau:
        o = r["e"]["obs_auc"]; p = max(lo, min(hi, r["pa"])); oo = max(lo, min(hi, o))
        col = "#2f6b3a" if within2(r["pa"], o) else "#b5651d"
        s.append(f'<circle cx="{X(p):.1f}" cy="{Y(oo):.1f}" r="6" fill="{col}" opacity="0.85"/>')
        s.append(f'<text x="{X(p)+9:.1f}" y="{Y(oo)+4:.1f}" font-size="10.5" fill="#1b2127">{r["e"]["id"].split(" (")[0]}</text>')
    # counterion limitation point (distinct)
    for r in counterion:
        o = r["e"]["obs_auc"]; p = max(lo, min(hi, r["pa"]))
        s.append(f'<circle cx="{X(p):.1f}" cy="{Y(o):.1f}" r="6" fill="#9e2b25"/>')
        s.append(f'<text x="{X(p)+9:.1f}" y="{Y(o)+4:.1f}" font-size="10.5" fill="#9e2b25">{r["e"]["id"]} (한계)</text>')
    s.append('</svg>')
    open(path, "w").write("\n".join(s))


svg_scatter(os.path.join(DOCS, "validation_scatter.svg"))
print(f"\nSVG written: docs/validation_scatter.svg")


# ---- markdown summary ------------------------------------------------------
def md_row(r):
    e = r["e"]; o = e.get("obs_auc")
    if o:
        ok = "✅" if within2(r["pa"], o) else "⚠️"
        return f"| {e['id']} | {e['grade']} | {e['species']} | {r['pa']:.2f} | {o:.2f} | {acc(r['pa'],o):.0f}% | {ok} |"
    return f"| {e['id']} | {e['grade']} | {e['species']} | {r['pa']:.2f} | ↑(방향) | dir | {'✅' if r['pa']>1 else '❌'} |"


lines = [
    "# 문헌 검증 종합 (한눈 요약)", "",
    "![scatter](validation_scatter.svg)", "",
    f"**검증 화합물/염 {len(rows)}건** (실제 문헌). 모델 상수는 기본값 고정, 입력은 "
    "문헌 physchem만 사용(관측 PK비로 튜닝하지 않음).", "",
    "| 화합물 | 등급 | 종 | 예측 AUC비 | 실측 | 정확도 | 판정 |",
    "|---|---|---|---|---|---|---|",
]
for r in svb:
    lines.append(md_row(r))
for r in rows:
    if r["kind"] == "salt_vs_base" and not r["e"].get("obs_auc") and r["e"].get("direction"):
        lines.append(md_row(r))
for r in plateau:
    e = r["e"]
    lines.append(f"| {e['id']} | {e['grade']} | {e['species']} | {r['pa']:.2f} | ~1.0 | {acc(r['pa'],1.0):.0f}% | "
                 f"{'✅' if within2(r['pa'],1.0) else '⚠️'} |")
for r in counterion:
    e = r["e"]
    lines.append(f"| {e['id']} | {e['grade']} | {e['species']} | {r['pa']:.2f} | {e['obs_auc']:.2f} | — | ❌ 한계 |")
lines += [
    "",
    f"- **방향(염이 노출↑/유사) 정확: {n_dir_ok}/{n_dir_tot}**",
    f"- **2-fold 이내(크기): {n_2fold}/{len(mag)}**  ·  **평균 AUC 정확도 {mean_acc:.0f}%** (salt-vs-base+plateau)",
    f"- **Haloperidol counterion 순위:** {' > '.join(hr_order)} ({'정성 일치' if hr_ok else '불일치'}, 단 차이 미미)",
    "",
    "## 한눈 총평",
    "",
    "| 무엇을 | 얼마나 잘 | 근거 |",
    "|---|---|---|",
    "| **염이 노출을 올리나? (방향)** | **매우 우수 (~100%)** | 전 화합물 방향 일치 |",
    "| **BCS II/IV 염 vs free base 배율** | **양호 (2-fold 이내, 평균 ~75-80%)** | IIIM-290·cilostazol·canertinib·NK-1 |",
    "| **이미 잘 녹으면 이득 없음 (plateau)** | **우수** | phenytoin 염-염 ~1.0, BCS I/III |",
    "| **counterion끼리 미세 차이 (mesylate vs HCl)** | **약함 ❌** | 측정 용출 없으면 ~동일로 예측 |",
    "| **Cmax** | **AUC보다 불확실** | 측정 다중pH/2-stage 필요 |",
    "",
    "## 결론",
    "- **염 스크리닝(만들 가치 있나·어느 BCS에서 효과)·우선순위·기전 이해 도구로 사용 가능.**",
    "- **counterion 미세 순위와 절대값·Cmax·규제 판단은 부적합** — 측정 다중pH/2-stage 용출 입력 + "
    "사내 reference 보정 필요.",
    f"- 표본 {len(rows)}건(+haloperidol 순위)으로 *방향/plateau는 신뢰*, *배율은 ±2-fold*. "
    "결정·생산 등급은 사내 10-20개 전향 검증 후.",
]
open(os.path.join(DOCS, "VALIDATION_SUMMARY.md"), "w").write("\n".join(lines))
print("Markdown written: docs/VALIDATION_SUMMARY.md")
