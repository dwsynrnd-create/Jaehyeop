"""
Emit the dataset provenance: docs/DATASET.md + data/literature_dataset.csv
showing every drug's collected literature data (physchem, dissolution, PK, cite).

    python validation/make_dataset_doc.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validation.dataset import ROWS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS, DATA = os.path.join(ROOT, "docs"), os.path.join(ROOT, "data")

# extra literature physchem gathered per drug (logP, notes); None = not found
LOGP = {"Albendazole": 2.54, "Itraconazole": 5.7, "Cilostazol": 3.6, "Dipyridamole": 1.5,
        "Miconazole": 6.1, "IIIM-290": 3.0, "Propranolol": 3.0, "Metoprolol": 1.9,
        "Atenolol": 0.16, "Cimetidine": 0.4, "Phenytoin": 2.5, "Cabozantinib": 5.4}

# measured biorelevant / compendial dissolution actually collected (cumulative %, 6 h)
# (free base unless noted). Cilostazol has the full pH 1.2/4.5/6.8 set.
DISSOLUTION = {
    "Cilostazol": {
        "note": "측정 다중 pH 용출 (Seo 2015). 6h 누적%: free base pH1.2 25.4 / pH4.5 8.54 / pH6.8 2.74; "
                "mesylate pH1.2 93.5; besylate pH1.2 98.6. 중간 시점은 대표 sigmoid로 보간.",
        "timecourse": {  # (min, %) — endpoints measured, intermediate representative
            "free base pH1.2": [(30,10),(60,15),(120,19),(240,24),(360,25.4)],
            "free base pH4.5": [(60,5),(120,7),(360,8.54)],
            "free base pH6.8": [(60,1.5),(120,2.2),(360,2.74)],
            "mesylate pH1.2":  [(15,65),(30,84),(60,91),(120,93.5)],
            "besylate pH1.2":  [(15,80),(30,92),(60,97),(120,98.6)],
        }},
    "Albendazole": {"note": "salt 수용해도/용출 개선 보고(정량 % 프로파일 미공개). 6h AUC비로 검증.", "timecourse": {}},
    "Dipyridamole": {"note": "tosylate pH-비의존 용해도↑, 정상/저산 rat PK. 시간별 % 미수집.", "timecourse": {}},
    "IIIM-290": {"note": "45배 수용해도↑(8.6→387 µg/mL), pHmax 3.59. 시간별 용출 % 미수집.", "timecourse": {}},
}

CIMAP = {"_plateau": "(Na vs piperazine)", "_pkc": "(mesylate vs HCl)"}

rows = []
for r in ROWS:
    (rid, drug, bcs, ctype, sp, dose, mw, pka, s0, ci, ssalt,
     oa, oc, grade, cite, kind, caco2, clint, ppb, php) = r
    rows.append(dict(
        id=rid, drug=drug, bcs=bcs, moiety=ctype, mw=mw, pka=pka, s0=s0,
        logp=LOGP.get(drug), counterion=CIMAP.get(ci, ci), s_salt=(ssalt or ""),
        diss=("측정 pH1.2/4.5/6.8" if php else ("salt 용해도/개선도" if kind == "salt_vs_base" else "—")),
        obs_auc=oa, obs_cmax=oc, species=sp, dose=dose, grade=grade, kind=kind, cite=cite))

# ---------- CSV ----------
csv_path = os.path.join(DATA, "literature_dataset.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["drug", "bcs", "moiety", "mw", "pka", "s0_ugml", "logP", "counterion",
                "s_salt_ugml", "dissolution_data", "obs_auc_ratio", "obs_cmax_ratio",
                "species", "dose_mgkg", "grade", "kind", "citation"])
    for r in rows:
        w.writerow([r["drug"], r["bcs"], r["moiety"], r["mw"], r["pka"], r["s0"],
                    r["logp"] if r["logp"] is not None else "", r["counterion"], r["s_salt"],
                    r["diss"], r["obs_auc"] if r["obs_auc"] is not None else "",
                    r["obs_cmax"] if r["obs_cmax"] is not None else "",
                    r["species"], r["dose"], r["grade"], r["kind"], r["cite"]])

# ---------- Markdown ----------
bcs_n = {b: sum(1 for r in rows if r["bcs"] == b) for b in ["I", "II", "III", "IV"]}
drugs = []
for r in rows:
    if r["drug"] not in [d["drug"] for d in drugs]:
        drugs.append(dict(drug=r["drug"], bcs=r["bcs"], moiety=r["moiety"], mw=r["mw"],
                          pka=r["pka"], s0=r["s0"], logp=r["logp"], cite=r["cite"]))

L = ["# 프로그램에 사용한 데이터셋 (문헌 출처·기본정보 전체 공개)", "",
     f"검증·개발에 사용한 **문헌 {len(rows)}건 / 약물 {len(drugs)}종**. 모든 입력은 문헌 physchem만 "
     "사용(관측 PK로 튜닝하지 않음). 기계가독 버전: [`data/literature_dataset.csv`](../data/literature_dataset.csv).", "",
     f"**BCS 분포:** 1급 {bcs_n['I']} · 2급 {bcs_n['II']} · 3급 {bcs_n['III']} · 4급 {bcs_n['IV']}", "",
     "**데이터 등급:** A=측정 in vitro(용해도/용출)+in vivo PK · B=PK + 부분 물성 · C=PK비 + 물성 template", "",
     "## 1. 약물별 기본 물성 (수집한 것)", "",
     "| 약물 | BCS | 산/염기 | MW | pKa | S0 (µg/mL) | logP | 출처 |",
     "|---|---|---|---|---|---|---|---|"]
for d in drugs:
    L.append(f"| {d['drug']} | {d['bcs']} | {d['moiety']} | {d['mw']} | {d['pka']} | {d['s0']} | "
             f"{d['logp'] if d['logp'] is not None else '—'} | {d['cite'][:42]} |")

L += ["", "## 2. 염형태·관측 PK·용출데이터 (행=폼)", "",
      "| 약물 | 염 | 염용해도 µg/mL | 용출데이터 | 실측 AUC비 | 실측 Cmax비 | 종 | 용량 mg/kg | 등급 | 출처 |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L.append(f"| {r['drug']} | {r['counterion']} | {r['s_salt'] or '—'} | {r['diss']} | "
             f"{r['obs_auc'] if r['obs_auc'] is not None else '↑(방향)'} | "
             f"{r['obs_cmax'] if r['obs_cmax'] is not None else '—'} | {r['species']} | {r['dose']} | "
             f"{r['grade']} | {r['cite'][:34]} |")

# dissolution detail
L += ["", "## 3. 측정 용출 프로파일 (pH별·시간별) — 실제 수집분", "",
      "대부분의 문헌은 PK비/용해도-개선도만 보고하고 **시간별 용출 %는 cilostazol만 전 pH 공개**합니다. "
      "수집·적용한 용출 데이터:"]
for drug, info in DISSOLUTION.items():
    L.append(f"\n### {drug}\n{info['note']}")
    if info["timecourse"]:
        L.append("\n| 시리즈 | " + " | ".join(f"{t}분" for t, _ in next(iter(info['timecourse'].values()))) + " |")
        L.append("|---" * (len(next(iter(info['timecourse'].values()))) + 1) + "|")
        for name, pts in info["timecourse"].items():
            L.append(f"| {name} | " + " | ".join(f"{p}" for _, p in pts) + " |")

L += ["", "## 4. 데이터 수집의 솔직한 한계", "",
      "- **시간별 용출 프로파일**이 PK와 짝지어 공개된 salt 문헌은 cilostazol급 소수 → 표본의 상한.",
      "- 다수는 **PK비 + 용해도-개선도**만 있어 BCS+물성 template로 예측(등급 C, magnitude 비신뢰·방향만).",
      "- BCS 1/3은 salt-vs-freebase PK 비교가 거의 없어 **‘salt 무효과(≈1.0)’ 기대값**으로 거동 검증.",
      "- BCS 4는 albendazole(경계 II/IV, in-silico IV)이 대표 — 초난용성이라 모델이 과대예측.",
      "- 표본을 키우는 현실적 경로 = **사내 pH1.2/4.5/6.8 용출+PK를 `data/*.csv`로 적재 →** "
      "`python -m salt_pk.batch` / `calibrate`.",
      "", f"*(자동 생성: `python validation/make_dataset_doc.py` · 총 {len(rows)}행)*"]

open(os.path.join(DOCS, "DATASET.md"), "w", encoding="utf-8").write("\n".join(L))
print(f"written: docs/DATASET.md ({len(rows)} rows, {len(drugs)} drugs) + data/literature_dataset.csv")
