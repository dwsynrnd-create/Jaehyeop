# Salt-Screening IVIVE PK Predictor — 염 스크리닝 in-vivo 노출 예측기

신약 후보의 **free base**에 대해 여러 **염형태(HCl · tosylate · phosphate · esylate ·
oxalate · mesylate …)** 를 만들었을 때, **각 염의 in vitro 데이터로 어떤 결정형/염형태가
in vivo 노출(AUC · Cmax)이 가장 높은지** 예측·순위화하는 도구. **BCS Class I–IV 모두 적용.**

```
┌─ in vitro ─────────────────┐        ┌─ 예측 ─────────────────┐
│ free base: pKa·S0·Caco-2   │        │ Fa · F · Cmax · Tmax   │
│ disposition: CLint·PPB·Vss │   →    │ AUC · 혈중농도 곡선     │
│ 염별: counterion·S_salt·   │        │ 염 순위 (상대 AUC/Cmax)│
│       (측정 용출 프로파일) │        └────────────────────────┘
└────────────────────────────┘
```

## 핵심 과학 (왜 이렇게 모델링했나)

대사·분포·단백결합·막투과는 **free base의 성질**이라 모든 염에서 동일하다. 염형태가
바꾸는 것은 **흡수**뿐이며, 그래서 `AUC(염)/AUC(free base) ≈ Fa(염)/Fa(free base)`.
이 한 줄 덕분에 **염 순위 예측은 disposition 가정에 둔감**하다(검증의 강건성).

흡수 모델은 염 스크리닝에 필요한 세 가지 메커니즘을 담는다:

1. **pH-용해도 / pHmax** — Henderson–Hasselbalch + `pHmax = pKa + log10(S0/S_salt)`.
   위(salt, 高용해)에서 장(free base, 低용해)으로 넘어가며 석출되는 지점.
2. **공통이온 효과(common-ion)** — HCl 염은 위장관의 염화물 때문에 위 용해도가 억제됨
   (`Ksp = [BH⁺][Cl⁻]`). mesylate·tosylate 등 비(非)공통이온 강산염은 이 패널티가 없음.
3. **과포화 → 석출(spring-and-parachute)** — 염은 빠르게 용해되어 일시적으로 과포화된 뒤
   free base 용해도를 향해 석출. 흡수가 석출보다 빠르면 노출 이득이 실현됨.

> 확산층(Mooney/Serajuddin) 관점의 Noyes–Whitney 용출 + 위→소장 구획 + 과포화/석출
> ODE(RK4)로 구현. 측정 용출 프로파일을 넣으면 그것이 용출을 직접 구동한다.

## 구성

| 경로 | 내용 |
|---|---|
| `salt_pk/` | 검증된 Python 엔진 (`solubility` · `counterions` · `physiology` · `engine` · `report`) |
| `salt_screening_predictor.html` | 동일 엔진을 포팅한 **대화형 웹 도구** (Python과 수치 일치 확인) |
| `validation/` | 문헌 데이터셋 + 검증 러너 |
| `docs/PARAMETERS.md` | **BCS class별 필요 파라미터** 가이드 |

## 사용법

### Python
```python
from salt_pk import IonizableDrug, SaltForm, DrugPK, get_species, screen

drug_io = IonizableDrug(mw=420, pka=6.0, s0_ugml=6, is_base=True)   # free base 물성
drug    = DrugPK(dose_mgkg=30, caco2=18, clint=22, ppb_percent=92)  # disposition(공유)

forms = [
    SaltForm.free_base(),
    SaltForm.of("hcl",       s_salt_ugml=1500),
    SaltForm.of("tosylate",  s_salt_ugml=3000),
    SaltForm.of("phosphate", s_salt_ugml=900),
    # 측정 용출 프로파일로 정밀 비교(권장): (시간[h], 누적분율 0–1)
    SaltForm.of("esylate", 4000,
                diss_profile=[(0.25, 0.60), (0.5, 0.85), (1.0, 0.95), (2.0, 0.98)],
                diss_medium="FaSSIF"),
]
for r in screen(drug, drug_io, forms, get_species("rat")):
    print(r["form"].label, round(r["AUC"]), round(r["rel_AUC"], 2))
```
보고서 표 + CSV 예제: `python -m salt_pk.report`

### 웹 도구
`salt_screening_predictor.html` 을 브라우저로 열기 → free base 물성·종·염형태 입력 →
**“PK 예측 · 염 순위 계산”**. counterion을 고르면 pKa·공통이온 여부가 자동 적용되고
pHmax·위 평형용해도가 실시간 표시된다. 용출표는 **분 / 누적 %** 로 입력(내부에서 변환).

## 문헌 기반 검증 (실제 결과와 비교)

```
$ python validation/run_validation.py
```

| Tier | 검증 항목 | 결과 |
|---|---|---|
| **A** | IIIM-290·HCl **pHmax** (분석식) | 예측 **3.59** vs 논문 계산 3.59 (실측 3.0) — Δ0.00 ✓ |
| **A** | **공통이온** 위 용해도 (동일 수용해도 염) | mesylate=phosphate ≫ HCl(억제) ✓, 문헌 순위 일치 |
| **B** | **IIIM-290 AUC비** (HCl/free base, mouse 50 mg/kg) | 예측 **1.89** vs 실측 **1.44** — fold-error 1.31 (2-fold 이내) ✓ |
| **B** | **IIIM-290 Cmax비** | 예측 **1.85** vs 실측 **1.57** — fold-error 1.18 ✓ |
| **C** | **BCS class 거동** | I·III: 염 효과 없음 / II·IV: 염 효과 있음 ✓ |
| **C** | 과포화→석출(clofazimine형) | spring-and-parachute 재현 ✓ |

**8 PASS / 0 FAIL.** 수용기준: pHmax Δ<0.1; 노출비 2-fold 이내(IVIVE 표준); BCS 거동·공통이온 방향 일치.

### 검증에 쓴 1차 문헌
- **IIIM-290** — Bhagat et al., *ACS Omega* 2018, 3(8):8836-8845 (PMC6072253). free base S0 8.6 µg/mL,
  HCl 45배(≈387 µg/mL), pHmax 계산 3.59/실측 3.0, mouse 50 mg/kg PO에서 HCl이 AUC 1.44×·Cmax 1.57×.
- **Haloperidol** — 염형태 용출의 **염화물(공통이온) 효과**, 0.01 M HCl 용출 순위 mesylate ≫ phosphate > HCl.
- **Counterion 산도** — Elder, Holm et al., *J. Pharm. Sci.* 2017, 106(10) (PMID 29107790).
- **Clofazimine** — Bannigan et al., *ACS Omega* 2017, 2(11):8210-8218.

## 솔직한 한계 (반드시 읽을 것)

- **절대값보다 후보 간 상대비교/순위가 신뢰구간.** raw in vitro CLint는 청소율을 3–9배
  과소예측(IVIVE 고유) → 자사 reference 약물로 보정 후 사용 권장.
- **counterion 이름만으로의 미세 순위는 과신 금물.** 소장에서는 모든 염이 같은 free base로
  석출되므로, 위(胃)에서 용출이 律速이 아닌 한 HCl·mesylate·tosylate의 **통합 PK 차이는 작을 수
  있다.** 실제 염 간 차이(과포화·불균등화·결정형·입자)는 **생체관련 매질의 측정 용출 프로파일**을
  넣어야 정확히 반영된다.
- BCS IV·난용성의 절대 흡수는 불확실. 능동수송/유출, 담즙 가용화 등은 단순화됨.
- 보정상수(`kd0·kprecip·salt_wettability`)는 BCS I–IV 거동·IIIM-290으로 합리적 기본값을
  잡았으나, **자사 프로토콜로 재보정**하는 것이 정확하다(`docs/PARAMETERS.md` §5).

## 출처(생리 스케일링)
Davies & Morris 1993; Barter 2007; Sohlenius-Sternbeck 2006.
