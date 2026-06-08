# 프로그램에 사용한 데이터셋 (문헌 출처·기본정보 전체 공개)

검증·개발에 사용한 **문헌 31건 / 약물 23종**. 모든 입력은 문헌 physchem만 사용(관측 PK로 튜닝하지 않음). 기계가독 버전: [`data/literature_dataset.csv`](../data/literature_dataset.csv).

**BCS 분포:** 1급 2 · 2급 22 · 3급 2 · 4급 5

**데이터 등급:** A=측정 in vitro(용해도/용출)+in vivo PK · B=PK + 부분 물성 · C=PK비 + 물성 template

## 1. 약물별 기본 물성 (수집한 것)

| 약물 | BCS | 산/염기 | MW | pKa | S0 (µg/mL) | logP | 출처 |
|---|---|---|---|---|---|---|---|
| IIIM-290 | II | base | 462.3 | 5.24 | 8.6 | 3.0 | Bhagat 2018 ACS Omega PMC6072253 |
| Cilostazol | II | base | 369.5 | 11.8 | 4.0 | 3.6 | Seo 2015 DDDT PMC4524531 |
| Dipyridamole | II | base | 504.6 | 6.4 | 6.0 | 1.5 | Wakasawa 2015 (DP tosylate, rat) |
| Canertinib-type | II | base | 485.0 | 6.0 | 4.0 | — | US 8,022,216 (quinolinyl maleate) |
| NK-1 antagonist | II | base | 500.0 | 6.5 | 6.0 | — | US 10,233,154/10,676,440 |
| Mesembrine | II | base | 289.4 | 8.0 | 20.0 | — | US 11,970,446 |
| AXL inhibitor | II | base | 480.0 | 5.5 | 8.0 | — | US 11,400,091 |
| Miconazole | II | base | 416.1 | 6.7 | 1.0 | 6.1 | Tsutsumi 2022 Pharmaceutics PMC9143750 |
| Itraconazole | II | base | 705.6 | 3.7 | 0.5 | 5.7 | cocrystal/salt, rat 2.8x AUC (BCS II) |
| Cabozantinib | II | base | 501.5 | 5.0 | 3.0 | 5.4 | Mol Pharm 2018 lipophilic salt ~2x rat |
| RPR2000765 | II | base | 450.0 | 5.3 | 10.0 | — | Pudipeddi 2002 (S0 10->39000 ug/mL) |
| Compound A | II | base | 450.0 | 6.0 | 3.0 | — | salt 3-8x vs free base unmilled (rat) |
| Compound B1 | II | base | 450.0 | 6.0 | 3.0 | — | US 6,015,807 (PTSA ~3x rat) |
| Serajuddin A | II | base | 450.0 | 6.0 | 4.0 | — | Serajuddin 2007 ADDR 59:603 |
| Serajuddin B | II | base | 450.0 | 6.0 | 2.0 | — | Serajuddin 2007 ADDR 59:603 |
| Albendazole | IV | base | 265.3 | 3.3 | 0.2 | 2.54 | Molecules 2024 29:3571 PMC11314343 |
| Phenytoin | II | acid | 252.3 | 8.3 | 22.0 | 2.5 | Serajuddin 2007; phenytoin PBPK PMC3787220 |
| Barbiturate | II | acid | 240.0 | 7.8 | 30.0 | — | US 7,683,071 (Na >=1.5-2x) |
| PKC inhibitor | II | base | 520.0 | 6.5 | 5.0 | — | US 6,015,807 mesylate ~2.5x HCl |
| Propranolol | I | base | 259.3 | 9.5 | 500.0 | 3.0 | BCS I; biowaiver: salt no PK change |
| Metoprolol | I | base | 267.4 | 9.7 | 500.0 | 1.9 | BCS I; biowaiver: salt no PK change |
| Atenolol | III | base | 266.3 | 9.6 | 500.0 | 0.16 | BCS III; perm-limited, salt no benefit |
| Cimetidine | III | base | 252.3 | 6.8 | 500.0 | 0.4 | BCS III; perm-limited, salt no benefit |

## 2. 염형태·관측 PK·용출데이터 (행=폼)

| 약물 | 염 | 염용해도 µg/mL | 용출데이터 | 실측 AUC비 | 실측 Cmax비 | 종 | 용량 mg/kg | 등급 | 출처 |
|---|---|---|---|---|---|---|---|---|---|
| IIIM-290 | hcl | 387 | salt 용해도/개선도 | 1.44 | 1.57 | mouse | 50 | A | Bhagat 2018 ACS Omega PMC6072253 |
| Cilostazol | mesylate | 50000 | 측정 pH1.2/4.5/6.8 | 3.88 | 3.65 | rat | 20 | A | Seo 2015 DDDT PMC4524531 |
| Cilostazol | besylate | 50000 | 측정 pH1.2/4.5/6.8 | 2.94 | 2.87 | rat | 20 | A | Seo 2015 DDDT PMC4524531 |
| Dipyridamole | tosylate | 4000 | salt 용해도/개선도 | 1.7 | 2.8 | rat | 10 | B | Wakasawa 2015 (DP tosylate, rat) |
| Canertinib-type | maleate | 1500 | salt 용해도/개선도 | 2.0 | 2.0 | rat | 20 | B | US 8,022,216 (quinolinyl maleate) |
| NK-1 antagonist | tartrate | 1200 | salt 용해도/개선도 | 1.9 | 2.0 | dog | 12 | B | US 10,233,154/10,676,440 |
| NK-1 antagonist | maleate | 2500 | salt 용해도/개선도 | 2.9 | 2.4 | dog | 12 | B | US 10,233,154/10,676,440 |
| Mesembrine | besylate | 3000 | salt 용해도/개선도 | 1.5 | 1.5 | rat | 10 | B | US 11,970,446 |
| AXL inhibitor | tartrate | 1500 | salt 용해도/개선도 | 1.5 | 1.3 | rat | 10 | B | US 11,400,091 |
| Miconazole | mesylate | 8000 | salt 용해도/개선도 | 2.9 | 2.4 | rat | 20 | B | Tsutsumi 2022 Pharmaceutics PMC914 |
| Itraconazole | tosylate | 5000 | salt 용해도/개선도 | 2.8 | 2.3 | rat | 20 | C | cocrystal/salt, rat 2.8x AUC (BCS  |
| Cabozantinib | tosylate | 4000 | salt 용해도/개선도 | 2.0 | 2.0 | rat | 10 | C | Mol Pharm 2018 lipophilic salt ~2x |
| RPR2000765 | mesylate | 39000 | salt 용해도/개선도 | ↑(방향) | — | rat | 20 | C | Pudipeddi 2002 (S0 10->39000 ug/mL |
| Compound A | mesylate | 9000 | salt 용해도/개선도 | 5.0 | 5.0 | rat | 20 | C | salt 3-8x vs free base unmilled (r |
| Compound A | tosylate | 9000 | salt 용해도/개선도 | 5.0 | 5.0 | rat | 20 | C | salt 3-8x vs free base unmilled (r |
| Compound B1 | tosylate | 6000 | salt 용해도/개선도 | 3.0 | 3.0 | rat | 20 | C | US 6,015,807 (PTSA ~3x rat) |
| Compound B1 | tosylate | 6000 | salt 용해도/개선도 | 4.0 | 4.0 | dog | 20 | C | US 6,015,807 (PTSA ~4x dog) |
| Serajuddin A | mesylate | 8000 | salt 용해도/개선도 | 2.6 | 2.6 | rat | 20 | C | Serajuddin 2007 ADDR 59:603 |
| Serajuddin B | mesylate | 12000 | salt 용해도/개선도 | 5.0 | 5.0 | rat | 20 | C | Serajuddin 2007 ADDR 59:603 |
| Albendazole | fumarate | 2000 | salt 용해도/개선도 | 3.4 | 3.0 | rat | 20 | B | Molecules 2024 29:3571 PMC11314343 |
| Albendazole | tartrate | 4000 | salt 용해도/개선도 | 5.2 | 4.5 | rat | 20 | B | Molecules 2024 29:3571 PMC11314343 |
| Albendazole | hcl | 6000 | salt 용해도/개선도 | 8.8 | 7.0 | rat | 20 | B | Molecules 2024 29:3571 PMC11314343 |
| Albendazole | besylate | 10000 | salt 용해도/개선도 | 7.6 | 6.0 | rat | 20 | B | ABZ-BSA-H (rat) 7.6x |
| Albendazole | mesylate | 20000 | salt 용해도/개선도 | 20.3 | 15.0 | rat | 20 | B | ABZ-MSA-H (rat) 20.3x |
| Phenytoin | (Na vs piperazine) | — | — | 1.0 | 1.0 | dog | 10 | A | Serajuddin 2007; phenytoin PBPK PM |
| Barbiturate | hcl | 9000 | salt 용해도/개선도 | 1.75 | 1.75 | rat | 20 | C | US 7,683,071 (Na >=1.5-2x) |
| PKC inhibitor | (mesylate vs HCl) | — | — | 2.5 | 2.5 | dog | 20 | C | US 6,015,807 mesylate ~2.5x HCl |
| Propranolol | hcl | 100000 | — | 1.0 | 1.0 | human | 1 | B | BCS I; biowaiver: salt no PK chang |
| Metoprolol | tartrate | 100000 | — | 1.0 | 1.0 | human | 1 | B | BCS I; biowaiver: salt no PK chang |
| Atenolol | hcl | 100000 | — | 1.0 | 1.0 | human | 1 | B | BCS III; perm-limited, salt no ben |
| Cimetidine | hcl | 100000 | — | 1.0 | 1.0 | human | 4 | B | BCS III; perm-limited, salt no ben |

## 3. 측정 용출 프로파일 (pH별·시간별) — 실제 수집분

대부분의 문헌은 PK비/용해도-개선도만 보고하고 **시간별 용출 %는 cilostazol만 전 pH 공개**합니다. 수집·적용한 용출 데이터:

### Cilostazol
측정 다중 pH 용출 (Seo 2015). 6h 누적%: free base pH1.2 25.4 / pH4.5 8.54 / pH6.8 2.74; mesylate pH1.2 93.5; besylate pH1.2 98.6. 중간 시점은 대표 sigmoid로 보간.

| 시리즈 | 30분 | 60분 | 120분 | 240분 | 360분 |
|---|---|---|---|---|---|
| free base pH1.2 | 10 | 15 | 19 | 24 | 25.4 |
| free base pH4.5 | 5 | 7 | 8.54 |
| free base pH6.8 | 1.5 | 2.2 | 2.74 |
| mesylate pH1.2 | 65 | 84 | 91 | 93.5 |
| besylate pH1.2 | 80 | 92 | 97 | 98.6 |

### Albendazole
salt 수용해도/용출 개선 보고(정량 % 프로파일 미공개). 6h AUC비로 검증.

### Dipyridamole
tosylate pH-비의존 용해도↑, 정상/저산 rat PK. 시간별 % 미수집.

### IIIM-290
45배 수용해도↑(8.6→387 µg/mL), pHmax 3.59. 시간별 용출 % 미수집.

## 4. 데이터 수집의 솔직한 한계

- **시간별 용출 프로파일**이 PK와 짝지어 공개된 salt 문헌은 cilostazol급 소수 → 표본의 상한.
- 다수는 **PK비 + 용해도-개선도**만 있어 BCS+물성 template로 예측(등급 C, magnitude 비신뢰·방향만).
- BCS 1/3은 salt-vs-freebase PK 비교가 거의 없어 **‘salt 무효과(≈1.0)’ 기대값**으로 거동 검증.
- BCS 4는 albendazole(경계 II/IV, in-silico IV)이 대표 — 초난용성이라 모델이 과대예측.
- 표본을 키우는 현실적 경로 = **사내 pH1.2/4.5/6.8 용출+PK를 `data/*.csv`로 적재 →** `python -m salt_pk.batch` / `calibrate`.

*(자동 생성: `python validation/make_dataset_doc.py` · 총 31행)*