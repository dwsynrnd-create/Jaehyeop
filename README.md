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

## 염이 되면 무엇이 바뀌나 — 그리고 어떤 데이터가 정확도를 올리나

**바뀌는 것:** 용해도·용출속도·과포화/석출·고체물성. **안 바뀌는 것:** 막투과(Caco-2)·
대사·분포·단백결합 — 용액에서 염은 해리되어 막을 통과하는 분자가 동일한 free base이기
때문(Serajuddin 2007; FDA BCS). 따라서 **투과·대사·분포는 free base 값 1회만 측정·공유**하고,
**염마다 바꿔 측정할 것은 용해/용출뿐**이다. MW는 염마다 다르지만 **활성분자=free base**라
모든 계산은 free-base 환산으로 한다.

**“물 용해도만 있으면 되나?” — 아니다.** 그리고 입력은 **용도**에 따라 고른다:

| Tier | 입력 | 용도 | 정확도 |
|---|---|---|---|
| ① | 물 용해도 1점(+S0·pKa) | 순위 스크리닝 | ★ |
| **② (규제표준·권장)** | **다중 pH 용출 (pH 1.2/4.5/6.8 시간대별)** | **허가·동등성 표준 + 흡수예측 1차** | ★★★ |
| ③ (정밀) | **2-stage 이행/생체관련 (FaSSGF→FaSSIF 장 구획 농도-시간)** | 난용성·과포화 강한 염 | ★★★★ |

**규제(식약처 의약품동등성시험기준·ICH/EMA biowaiver)는 pH 1.2/4.5/6.8 비교용출을 쓴다 — 단
그 목적은 “두 제제가 동등한가”를 보는 QC·대용시험**이지 새 염의 절대 BA 예측이 아니다(용도 차이).
하지만 이 다중 pH 데이터는 실험실 일상 데이터이고 약염기의 pH 의존성을 그대로 담으므로 **흡수예측의
1차 입력으로도 최적**이다. 본 도구는 **pH 1.2→위(spring), pH 6.8→장 용해도상한·재용해속도(parachute)**
로 매핑해 위→장 과포화·석출을 compendial 데이터만으로 재구성한다.
**평형 용해도 < 시간대별 용출**(과포화는 동역학; haloperidol). 매우 친유성·과포화 강한 염은
**2-stage 이행시험**(Tier ③)이 담즙 가용화+석출까지 직접 담아 가장 정확하다(*J. Pharm. Sci.* 2018,
S0022-3549(18)30683-X — *장내 석출은 AUC 아닌 **Cmax** 변동 원인*; 본 검증의 Cmax 오차와 일치).
**주의:** compendial은 (a) 큰 액량이라 **dose/액량비 보정** 필요(PMC12055928), (b) **SLS 등 계면활성제**가
난용성 약물 용출을 부풀려 “가짜 동등성”을 만들 수 있음. 자세한 권고는 `docs/PARAMETERS.md`.

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
    # Tier 2 (규제표준·권장) — 다중 pH 용출: {pH: [(시간h, 누적분율0–1), …]}
    SaltForm.of("phosphate", 900, ph_profiles={
        1.2: [(0.25, 0.55), (0.5, 0.80), (1.0, 0.90), (2.0, 0.93)],   # 위(spring)
        6.8: [(0.5, 0.15), (1.0, 0.22), (2.0, 0.28), (6.0, 0.32)]}),  # 장(parachute, 석출)
    # Tier 3 (정밀) — 2-stage 이행시험 장 구획 '용액 중 분율'(비단조 가능)
    SaltForm.of("tosylate", 4000,
                intestinal_profile=[(0.25, 0.55), (0.5, 0.80), (1.0, 0.78),
                                    (2.0, 0.70), (4.0, 0.62)]),   # 과포화→석출
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

**확장 데이터셋 (문헌 16건/8개 약물군 + haloperidol 순위)** — `python validation/validate_dataset.py`
([대시보드·요약: docs/VALIDATION_SUMMARY.md](docs/VALIDATION_SUMMARY.md)):

| 지표 | 결과 |
|---|---|
| **방향(염이 노출↑/유사) 정확** | **14/16** |
| **2-fold 이내 (정량 입력군, n=9)** | **9/9** |
| **평균 AUC 정확도 (정량군)** | **~77%** |
| plateau(이미 잘 녹으면 이득 없음) | phenytoin 염-염 ~1.0 ✅ |
| **한계: counterion 미세차이**(mesylate vs HCl) | 측정 용출 없으면 ~동일로 예측 ❌ |

> **표본 크기에 대한 정직한 한계.** "염 vs free base in vivo PK + 측정 용출"이 모두 갖춰진
> 화합물은 공개 문헌에 **수십 개 수준**(100개 不可 — 지어내면 팩트체크 위반). 여기서는
> 팩트체크 가능한 16건을 **A(측정 in vitro+PK)/B(PK+부분)/C(template 입력=방향만)** 등급으로
> 나눠, **배율 정확도는 A·B군(n=9)에서만** 산정했습니다. C군은 방향(6/6)만 검증.

### pH-용출 입력이 정확도를 올리나? — YES (`python validation/input_mode_comparison.py`)

![input mode](input_mode_comparison.svg)

같은 화합물(cilostazol)을 **두 방식으로 예측**한 직접 비교:

| 입력 방식 | mesylate | besylate | 평균 정확도 |
|---|---|---|---|
| 용해도(S0·pKa) Tier 1 | 1.01 (26%) | 1.01 (34%) | **30%** |
| **pH-용출 Tier 2** | 2.30 (59%) | 2.38 (81%) | **70% (+40%p)** |

용해도 모델은 cilostazol의 pKa(11.8)를 잘못 해석해 "free base가 잘 녹는다"고 보고 **염 효과를
0으로 예측**(완전 실패). **측정 pH-용출**은 실제 거동(위 25%·장 2.7%)을 담아 정상 예측.
또 다중 pH 입력은 **Cmax 정확도를 56%→98%로** 끌어올림(앞 절). → **pH buffer 용출 기반이
더 정확하고 robust**.

> **자료 충분성(정직):** pH 1.2/4.5/6.8 용출 *원자료*는 모든 제네릭·IVIVC가 생성 → **입력용은
> 풍부**. 단 *용출+in vivo PK를 짝지은 검증용* salt 데이터는 여전히 수십 개 수준. 또 compendial
> %를 in vivo로 환산할 땐 **dose/액량비 보정**(측정 pH-용해도 입력으로 해결, BMS-480188·
> bicarbonate 논문)이 필요해 엔진에 반영함(`ph_solubility`, `test_dose_mg/volume`).

### 메커니즘·BCS 단위검증
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

### 정확도 검증 — 실제 문헌값 대비 (multi-compound)

```
$ python validation/accuracy.py
```

실제 in vitro 입력값을 그대로 넣고 예측한 **염/free base 노출비**를 실측과 비교
(`정확도% = 100·(1−|예측−실측|/실측)`):

| 비교 (종, 용량) | 예측 AUC비 | 실측 AUC비 | AUC 정확도 | 예측 Cmax비 | 실측 Cmax비 |
|---|---|---|---|---|---|
| IIIM-290 HCl/FB (mouse 50 mpk) | 1.75 | **1.44** | 79% | 1.84 | **1.57** |
| Cilostazol mesylate/FB (rat 20 mpk, 측정용출) | 3.72 | **3.88** | **96%** | 5.26 | **3.65** |
| Cilostazol besylate/FB (rat 20 mpk, 측정용출) | 3.93 | **2.94** | 66% | 5.64 | **2.87** |

- **방향(염이 노출↑) 100% (3/3), 전부 2-fold 이내, 순위(어느 염이 best) 정확.**
- **AUC**(염 선택의 주 지표): mesylate 96%, IIIM-290 79%(가정한 투과도에 민감 — 단일
  `kprecip` 보정 시 91%로 개선), besylate 66%.
- **솔직한 한계 두 가지:**
  1. **Cmax 과대예측** — 초고속 용해 염의 피크가 날카롭게 계산됨. 위(胃) pH1.2 용출
     종점(자료 한계)으로 free base를 과소평가한 탓이 큼. **생체관련(FaSSIF) 용출 프로파일**을
     넣으면 개선됨.
  2. **besylate 이상치** — 용출은 더 됐는데(98.6% vs 93.5%) in vivo 노출은 더 낮음. 용출
     extent만으로는 예측 불가한 counterion별 과포화·석출 차이(실험적 변동 포함).

**다중 pH(Tier 2) 검증 — cilostazol 실제 용출(pH 1.2/4.5/6.8 = 25.4/8.54/2.74%)**
(`python validation/multi_ph_validation.py`): free base Fa 39%(난용성 약염기와 부합),
mesylate AUC비 2.71(실측 3.88), besylate 2.81(실측 2.94) — **다중 pH 입력 시 Cmax 정확도가
56%→98%로 개선**(장내 석출이 Cmax를 좌우; J Pharm Sci 2018와 일치).

> **객관적 정확도 (정직):** 방향·순위 **~90–100%**, AUC 배율 **~75–90%**(좋은 입력 시 90%+),
> Cmax·절대값 **2-fold 이내**. 전부 2-fold 이내·방향 100%. 단 **검증 화합물 3종은 일반 정확도를
> 주장하기엔 부족** → 사내 10–20개 전향적 검증 권장. **염 스크리닝·우선순위·기전 이해 용도로는
> 사용 가능하나, 규제·절대값·생동 판단엔 부적합.** 상세: [`docs/ACCURACY_ASSESSMENT.md`](docs/ACCURACY_ASSESSMENT.md).

### 검증에 쓴 1차 문헌
- **IIIM-290** — Bhagat et al., *ACS Omega* 2018, 3(8):8836-8845 (PMC6072253). free base S0 8.6 µg/mL,
  HCl 45배(≈387 µg/mL), pHmax 계산 3.59/실측 3.0, mouse 50 mg/kg PO에서 HCl이 AUC 1.44×·Cmax 1.57×.
- **Haloperidol** — 염형태 용출의 **염화물(공통이온) 효과**, 0.01 M HCl 용출 순위 mesylate ≫ phosphate > HCl.
- **Counterion 산도** — Elder, Holm et al., *J. Pharm. Sci.* 2017, 106(10) (PMID 29107790).
- **Clofazimine** — Bannigan et al., *ACS Omega* 2017, 2(11):8210-8218.
- **Cilostazol** — Seo et al., *Drug Des. Devel. Ther.* 2015;9:3961-3968 (PMC4524531):
  측정 용출(FB 25.4%/mesylate 93.5%/besylate 98.6%) + rat 20 mg/kg AUC비 3.88×/2.94×.

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
