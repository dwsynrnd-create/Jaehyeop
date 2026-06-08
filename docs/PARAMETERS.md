# 염 스크리닝 PK 예측 — 필요한 파라미터 (Required Parameters)

신약 freebase에 대해 여러 염형태(HCl·tosylate·phosphate·esylate·oxalate …)를
만들었을 때, **어떤 염형태가 in vivo 노출(AUC·Cmax)이 가장 높은지**를 in vitro
데이터로 예측하기 위한 입력값을 정리한다.

핵심 원리: **disposition(대사·분포·결합)과 막투과는 free base의 성질이라 모든 염에서
동일**하다. 염형태가 바꾸는 것은 **오직 흡수(용해·용출·과포화)**뿐이다. 따라서
`AUC(염)/AUC(free base) ≈ Fa(염)/Fa(free base)` 이고, 염 순위는 흡수 파라미터만으로
결정된다.

---

## 1. 모든 염이 공유하는 파라미터 (Free base 1회만 측정)

| 파라미터 | 단위 | 무엇에 영향 | 비고 |
|---|---|---|---|
| 용량 Dose | mg/kg | 전부 | **free base 환산** 값으로 입력 |
| 분자량 MW (free base) | g/mol | common-ion 몰농도 환산 | 구조에서 계산 |
| **pKa** | – | pH-용해도, pHmax | 약염기/약산의 주 이온화 |
| **고유용해도 S0** (free base) | µg/mL | 용해/석출 한계 | 중성종 용해도 (intrinsic) |
| **Caco-2 Papp** | 10⁻⁶ cm/s | Fa·Cmax (투과) | BCS III·IV에서 결정적 |
| CLint (대사안정성) | µL/min/mg or /10⁶cells | **AUC** | microsome/hepatocyte |
| PPB (혈장단백결합) | % | AUC·분포 | |
| Vss | L/kg | Cmax·t½ | 없으면 logD로 추정(불확실) |
| 간외 CL | mL/min/kg | AUC | 신/담즙 배설형 필수 |
| Fg (장벽통과) | 0–1 | AUC | CYP3A 장대사 기질만 <1 |

> 위 값들은 **염 순위에는 영향이 없다**(상쇄됨). 절대 AUC·Cmax 값을 위해 필요.

---

## 2. 염형태마다 측정하는 파라미터 (Salt-specific)

| 파라미터 | 단위 | 어떻게 얻나 | 모델에서의 역할 |
|---|---|---|---|
| **Counterion 종류** | – | 합성 시 결정 | pKa(HX)·common-ion 여부 자동 결정 |
| **염 용해도 S_salt** (물/완충액) | µg/mL (free base 환산) | 평형 용해도 측정 | 용출 속도·pHmax·과포화 |
| (자동) **pHmax** | – | `pHmax = pKa + log10(S0/S_salt)` | 위(salt) → 장(free base) 전환 pH |
| **측정 용출 프로파일** (생체관련 매질) | %, 시간 | FaSSGF/FaSSIF 2-stage 용출 | **염 간 차이의 가장 신뢰성 있는 입력** |
| 입자크기 D50 | µm | 측정 | 용출 속도 보정 |

### 왜 "측정 용출 프로파일"이 핵심인가
용해도 값 하나로는 **과포화(supersaturation)·불균등화(disproportionation)·
입자/결정형 차이**를 구분할 수 없다. counterion 이름만으로는 in vivo 차이를
정확히 예측하기 어렵다(아래 한계 참조). 생체관련 매질의 측정 용출 프로파일을
form별로 넣으면 이런 실제 차이가 그대로 반영된다.

---

## 3. BCS class별로 "꼭 챙겨야 하는" 파라미터

| BCS | 용해도 | 투과 | 염이 도움? | 우선 측정 |
|---|---|---|---|---|
| **I** | 高 | 高 | ✗ (이미 완전흡수) | 염은 제제안정성 위주, PK 이득 적음 |
| **II** | 低 | 高 | ✔ (용해/용출 律速) | **S0, S_salt, 용출 프로파일, pKa** |
| **III** | 高 | 低 | ✗ (투과 律速) | Caco-2 — 염 바꿔도 Fa 안 변함 |
| **IV** | 低 | 低 | △ (용해는 개선되나 투과가 상한) | S_salt·용출 **그리고** Caco-2 |

요약: **염 스크리닝으로 노출을 올릴 수 있는 것은 사실상 BCS II(그리고 일부 IV).**
BCS I·III에서는 염 선택이 PK가 아니라 고체물성(흡습성·안정성·제조성)으로 정당화된다.

---

## 4. counterion 라이브러리(내장값)

`pka_hx` = counterion 짝산의 pKa (낮을수록 강산 → 낮은 pHmax, 불균등화 위험↓).
`gi_common_ion` = 위장관에 흔한 이온인가(염화물만 해당 → HCl 염 위(胃) 용해도 억제).

| counterion | pKa(HX) | common ion | 특징 |
|---|---|---|---|
| HCl | −6 | **예(Cl⁻)** | 강산이지만 위에서 common-ion으로 용해도 억제 |
| mesylate | −1.9 | 아니오 | 강산, common-ion 없음 |
| esylate | −1.5 | 아니오 | |
| besylate | −2.5 | 아니오 | |
| tosylate | −2.8 | 아니오 | 매우 강산·친유성 |
| sulfate | 1.99 | 아니오 | 2가 |
| phosphate | 2.12 | 아니오 | 약산 → 높은 pHmax, 불균등화 위험 |
| oxalate | 1.25 | 아니오 | 2가 |
| maleate / tartrate / citrate / fumarate / succinate / benzoate | 1.9–4.2 | 아니오 | 약산일수록 pHmax↑·불균등화↑ |

---

## 5. 모델 보정 상수(AbsParams, 자사 데이터로 조정 가능)

| 상수 | 기본값 | 의미 |
|---|---|---|
| `kd0` | 0.5 /h | free base 용출속도상수(미세입자 기준) |
| `salt_wettability` | 4.0 | 염의 빠른 용출·젖음성 이득 (≥1) |
| `kprecip` | 2.0 /h | 과포화 → 석출 속도상수 (작을수록 parachute 유지 ↑) |
| `d50_um` | – | 입자크기(주면 용출속도 보정) |

이 상수들은 **자사 Caco-2/용출 프로토콜과 reference 약물로 한 번 보정**한 뒤
상대비교·순위에 쓰는 것이 정확하다(IVIVE의 표준 사용법).
