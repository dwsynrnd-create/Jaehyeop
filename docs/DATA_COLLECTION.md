# 용출 데이터 수집 프로토콜 (dissolution-first)

## 왜 dissolution-first인가
- 염의 in vivo 이점은 **과포화→석출(spring-and-parachute)** 이라는 **동역학** 현상이다.
- **평형(물)용해도는 이 동역학을 못 담는다** → 예측력 약함.
- 본 도구로 직접 비교: 같은 약물에서 **용해도 입력 30% → pH-용출 입력 70%** (Cmax 56%→98%).
- 따라서 **1차 입력 = pH 1.2 / 4.5 / 6.8 시간대별 누적 용출율.** 물용해도(S0)는 fallback일 뿐.

## 한 약물당 모아야 할 최소 데이터
| 항목 | 비고 |
|---|---|
| free base + 각 염의 **pH 1.2/4.5/6.8 시간별 누적 용출(%)** | **필수.** 15·30·60·120·(240·360)분 |
| 장(pH6.8) **평형 용해도 µg/mL** | dose/액량비 보정용(권장) |
| MW · pKa · BCS class | 기본 |
| free base 공유값: Caco-2(Papp), CLint, PPB, (Vss) | 1회 측정 |
| 관측 PK (있으면): 염/free base **AUC·Cmax 비** | 검증·보정용 |

## 입력 방법
`data/dissolution_template.csv` 형식(폼당 1행, 용출 `"분:%;분:%"`)으로 채운 뒤:
```bash
python -m salt_pk.batch     data/your_dissolution.csv   # 예측·정확도 채점
python -m salt_pk.calibrate data/your_dissolution.csv   # 사내 보정(≥10개)
```

## 데이터 출처(공개) — 본 환경의 한계
- 시간별 용출 *원수치*는 논문 figure/table에 있고, 본 실행환경은 **외부 웹 fetch가 차단**(GitHub/API만 허용)
  되어 자동 수집이 불가하다. 그래서 공개 검증은 **cilostazol(전 pH 용출 공개)** 중심이다.
- **50+ 데이터셋의 현실적 경로 = 사내 용출/PK 자료**(대웅 보유). 위 템플릿으로 적재하면 즉시 검증·보정된다.
- 공개 보강 후보(추후 원문 접근 시): carvedilol, zolpidem, dipyridamole, albendazole 염, 각종 BCS biowaiver
  monograph(FIP/WHO)의 pH 1.2/4.5/6.8 용출 — 모두 *원문 표/그림*에서 시간별 % 발췌 필요.

## 권고
이 프로그램의 정확도는 **입력 용출 데이터 품질에 비례**한다. 사내 pH-buffer 용출을 넣고
reference 10–20개로 `calibrate`하면 screening→decision 등급으로 올라간다.
