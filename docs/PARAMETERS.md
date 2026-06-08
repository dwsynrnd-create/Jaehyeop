# 염 스크리닝 PK 예측 — 필요한 파라미터 & 정확도 계층

신약 freebase에 대해 여러 염형태(HCl·tosylate·phosphate·esylate·oxalate …)를 만들었을 때
**어떤 형태가 in vivo 노출(AUC·Cmax)이 가장 높은지** in vitro 데이터로 예측하기 위한
입력값과, **어떤 데이터가 얼마나 정확도를 올리는지**를 정리한다.

---

## 0. 먼저 — 염이 되면 무엇이 바뀌고 무엇이 안 바뀌나? (자주 하는 오해)

| 물성 | 염형태에 따라 바뀌나? | 이유 |
|---|---|---|
| **용해도 / 용출속도 / 과포화·석출** | **✔ 바뀜 (핵심)** | 염의 결정격자·짝이온·확산층 pH가 달라짐 |
| 고체물성(흡습성·안정성·결정형) | ✔ 바뀜 | 제제·보관에 중요 |
| **막투과도 (Caco-2 Papp)** | **✗ 안 바뀜** | 용액에서 염은 **해리** → 막을 통과하는 분자는 동일한 free base/이온 평형 |
| **대사(CLint)·분포(Vss)·단백결합(PPB)·청소율** | **✗ 안 바뀜** | 모두 **용해된 활성분자(free base)**의 성질 |
| 분자량(MW) | 염은 ↑ (free base + 짝이온) | 단, **활성분자는 free base** → 모든 계산은 **free-base 환산**으로 수행 |

> 즉 염스크리닝에서 **투과·대사·분포·결합은 free base 값 1회만 측정해 공유**하고,
> **염마다 바꿔 측정해야 하는 것은 사실상 용해/용출 데이터뿐**이다. 그래서
> `AUC(염)/AUC(free base) ≈ Fa(염)/Fa(free base)` 가 성립한다.
> 근거: Serajuddin, *Adv. Drug Deliv. Rev.* 2007; FDA BCS 가이던스(투과도는 약물의 성질).

**MW 처리:** 용량은 **free base 환산 mg/kg**로 입력. 염 분말을 칭량할 때의 환산계수
(salt factor = 염MW/freeMW)는 `counterion_mw`를 주면 리포트에 표시된다. 약리·PK 계산
자체에는 free base MW만 쓰인다(활성분자 기준).

---

## 1. 모든 염이 공유하는 파라미터 (Free base 1회 측정)

| 파라미터 | 단위 | 영향 | 비고 |
|---|---|---|---|
| 용량 Dose | mg/kg (free base 환산) | 전부 | |
| MW(free base) | g/mol | 환산·common-ion 몰농도 | |
| **pKa** | – | pH-용해도·pHmax | |
| **Caco-2 Papp** | 10⁻⁶ cm/s | Fa·Cmax | **염 무관(공유)** |
| CLint·PPB·Vss·간외CL·Fg | – | AUC·Cmax·t½ | **염 무관(공유)** |

---

## 2. 염마다 측정하는 입력 — **정확도 계층 (낮음 → 높음)**

핵심 결론부터: **약염기 염은 “평형 용해도”보다 “시간대별 용출(특히 2-stage 이행시험)”이
더 정확하다.** 염의 이점은 *과포화(supersaturation)* 라는 **동역학 현상**인데, 이는 평형
용해도 값에는 보이지 않기 때문이다. (Haloperidol: “dissolution rate rather than solubility
may be the best predictor of bioavailability.”)

| Tier | 입력 | 무엇을 잡나 / 한계 | 정확도 |
|---|---|---|---|
| **1** | **물 용해도 1점** + (S0·pKa) | 메커니즘 추정. pH·과포화·석출 **못 잡음** → 순위 스크리닝만 | ★ |
| **2** | **pH별 평형 용해도** (pH 1.2·4.5·6.8, FaSSGF·FaSSIF) | GI pH별 용해 한계. 단, 여전히 **동역학(과포화) 못 잡음** | ★★ |
| **3** | **시간대별 용출율** (단일 매질, 보통 FaSSIF 또는 pH 6.8) | 용출속도·도달%·일부 과포화 | ★★★ |
| **4 (권장)** | **2-stage 이행 용출** (FaSSGF→FaSSIF, pH-shift; 장 구획의 *용액 중 농도-시간*) | **과포화 + 석출(spring-and-parachute) 직접 측정** — 약염기 염 PK를 좌우 | ★★★★ |

### 왜 Tier 4(2-stage 이행시험)가 가장 정확한가
약염기·염은 **위(산성, 高용해)에서 녹아 과포화 상태로 장(중성, 低용해)으로 넘어가며
석출**한다. 흡수가 석출보다 빠른 만큼만 노출 이득이 실현된다. **이 과포화→석출 곡선을
직접 측정**하는 것이 2-stage(또는 multicompartment transfer)이고, 이것을 흡수모델에 넣으면
PK 예측이 가장 정확하다.
근거: Fiolka 2018 (*J Pharm Pharmacol*); **Multicompartment transfer + mechanistic
absorption, *J. Pharm. Sci.* 2018, S0022-3549(18)30683-X** — *“intestinal precipitation may
be one of the factors contributing to variability in **Cmax** but not AUC.”* (본 모델 검증에서
Cmax가 AUC보다 덜 맞은 이유와 정확히 일치.)

### 어떤 buffer/매질이 필요한가 (실무 권고)
- **필수:** **FaSSGF**(위, pH≈1.6) + **FaSSIF**(장, pH≈6.5) — 약염기 염엔 이 두 가지가 핵심.
- **권장:** 위 두 매질을 잇는 **pH-shift / 2-stage 이행시험**(USP-II 또는 transfer model)에서
  장 구획의 **용액 중 약물 농도 vs 시간** 곡선. 이 한 곡선이 과포화·석출을 모두 담는다.
- 보조: pH 1.2·4.5·6.8 평형 용해도(Tier 2)와 D50(입자크기).
- HCl 염은 **염화물 매질(예: FaSSGF, 0.01–0.1 M NaCl)**에서 common-ion 억제를 확인.

### 이 도구에서의 입력 방법
- **Tier 1:** `s_salt_ugml`(+ free base S0·pKa) → 메커니즘 모드(공통이온·pHmax 자동).
- **Tier 3:** `diss_profile = [(시간h, 누적분율0–1), …]` (위/단일 매질 용출).
- **Tier 4:** `intestinal_profile = [(시간h, 용액중분율0–1), …]` — 2-stage 이행시험의 장 구획
  곡선. **비단조(오르락내리락) 가능**: 상승=과포화/용해, 하강=석출. 이 모드가 besylate처럼
  “용출은 더 됐는데 노출은 낮은” 현상을 데이터로 직접 반영한다.

---

## 3. BCS class별 우선순위

| BCS | 용해/투과 | 염이 도움? | Tier 권고 |
|---|---|---|---|
| **I** | 高/高 | ✗ | 염은 PK가 아니라 고체물성으로 판단 |
| **II** | 低/高 | ✔ (용출 律速) | **Tier 4 강력 권장** (과포화·석출이 좌우) |
| **III** | 高/低 | ✗ (투과 律速) | Caco-2가 상한 — 염 바꿔도 Fa 거의 불변 |
| **IV** | 低/低 | △ | Tier 4 + Caco-2 (용해 개선해도 투과가 상한) |

---

## 4. 보정 상수 (자사 reference로 1회 보정)

| 상수 | 기본값 | 의미 |
|---|---|---|
| `kd0` | 0.5 /h | free base 용출속도상수(Tier 1–3 메커니즘 모드) |
| `salt_wettability` | 4.0 | 염의 용출·젖음 이득(Tier 1–3) |
| `kprecip` | 2.0 /h | 과포화→석출 속도(Tier 1–3). **Tier 4에선 측정 곡선이 대체** |
| `kScale`(Caco-2→ka) | 0.30 | 자사 Caco-2 프로토콜 보정 |

**Tier 4 입력을 쓰면 `kprecip` 추정이 측정값으로 대체되어 보정 의존도가 크게 줄고
정확도가 올라간다.**
