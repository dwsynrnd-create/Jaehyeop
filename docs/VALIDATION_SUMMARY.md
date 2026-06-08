# 문헌 검증 종합 (한눈 요약)

![dashboard](validation_dashboard.svg)

실제 문헌 **16건**(8개 약물군). 모델 상수 기본값 고정, 입력은 문헌 physchem만 사용(관측 PK비로 튜닝 안 함). 등급 A=측정 in vitro+PK, B=PK+부분 in vitro, C=template 입력(방향만).

## ① 정량 검증 (측정/문헌 입력 — 배율 신뢰)
| 화합물 | 등급 | 종 | 예측 | 실측 | 정확도 | 판정 |
|---|---|---|---|---|---|---|
| AXL inhib. L-tartrate | B | rat | 1.53 | 1.50 | 98% | ✅ |
| Canertinib-type maleate | B | rat | 1.81 | 2.00 | 91% | ✅ |
| Phenytoin Na/piperazine (plateau) | A | dog | 1.10 | 1.00 | 90% | ✅ |
| Cilostazol besylate | A | rat | 2.38 | 2.94 | 81% | ✅ |
| NK-1 antag. tartrate | B | dog | 1.50 | 1.90 | 79% | ✅ |
| IIIM-290 HCl | A | mouse | 1.75 | 1.44 | 79% | ✅ |
| Mesembrine besylate | B | rat | 1.02 | 1.50 | 68% | ✅ |
| Cilostazol mesylate | A | rat | 2.30 | 3.88 | 59% | ✅ |
| NK-1 antag. malate | B | dog | 1.50 | 2.90 | 52% | ✅ |

→ **2-fold 이내 9/9, 평균 정확도 77%**

## ② 방향 검증 (template 입력 — 배율 비신뢰, 방향만)
| 화합물 | 등급 | 종 | 예측 | 실측 | 방향 |
|---|---|---|---|---|---|
| RPR2000765 mesylate | C | rat | 1.62 | ↑ | ✅ |
| Serajuddin base A mesylate | C | rat | 1.73 | 2.6 | ✅ |
| Serajuddin base B mesylate | C | rat | 1.81 | 5.0 | ✅ |
| Compound B1 tosylate (rat) | C | rat | 1.73 | 3.0 | ✅ |
| Compound B1 tosylate (dog) | C | dog | 1.71 | 4.0 | ✅ |
| Diphenylbarbiturate Na | C | rat | 4.04 | 1.75 | ✅ |

→ 방향 6/6 일치. **단 magnitude는 template 입력이라 신뢰 불가** — 큰 개선(>3x)은 과소예측 경향(보수적). 측정 용출 넣어야 정확.

## ③ 한계 (정직)
- **counterion끼리 미세차이**: PKC mesylate/HCl 예측 1.00 vs 실측 2.50 → 측정 다중pH/2-stage 용출 없으면 ~동일로 예측.
- **Haloperidol 순위** mesylate > phosphate > hcl: 정성 방향만, 차이 미미.
- **Cmax·절대값**: AUC보다 불확실(2-fold).

## 총평
| 항목 | 수준 |
|---|---|
| 염이 노출 올리나?(방향) | **매우 우수 ~90-100%** |
| BCS II/IV 염 vs free base 배율 | **양호 (2-fold, 평균 ~77%)** |
| plateau(이미 잘 녹으면 무이득) | **우수** |
| counterion 미세순위·Cmax·절대값·규제 | **부적합** |

**연구소 사용:** 염 스크리닝·우선순위·기전 이해 ✅ / 규제·절대값·counterion 최종결정 ❌. 결정등급은 사내 10–20개 전향검증 + 측정 용출 입력 후. 상세: `docs/ACCURACY_ASSESSMENT.md`.