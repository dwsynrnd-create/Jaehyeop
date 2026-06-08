# CLAUDE.md — 프로젝트 가이드

신약 **염 스크리닝 IVIVE PK 예측기**. free base 대비 염형태(HCl·mesylate·tosylate·
phosphate·esylate·oxalate…)의 in vivo 노출(AUC/Cmax)을 in vitro로 예측·순위화. BCS I–IV.

## 구조
```
salt_pk/            검증된 Python 엔진
  solubility.py     pH-용해도, pHmax=pKa+log10(S0/Ssalt), 공통이온; SaltForm(입력 4-tier)
  counterions.py    counterion 라이브러리(pKa, 공통이온 여부)
  physiology.py     종별 생리(mouse/rat/dog/human)
  engine.py         disposition(well-stirred CL) + 흡수 ODE(RK4): 위→소장, 과포화/석출
                    · 입력 tier: s_salt(기전) / ph_profiles(다중 pH) / intestinal_profile(2-stage)
                    · AbsParams(kd0, kprecip, salt_wettability) = 보정 상수
  report.py         표 출력 + CSV
  batch.py          CSV 일괄 임포트 + 예측 + 채점 (run_csv)
  calibrate.py      사내 데이터로 AbsParams 그리드 피팅
  uncertainty.py    Monte-Carlo 노출비 90% 신뢰구간 (ratio_ci)
salt_screening_predictor.html   대화형 웹툴(JS 포팅, Python과 수치 일치) + CSV 배치 패널
validation/         literature.py·dataset.py(18건)·run_validation·validate_dataset(대시보드)
                    ·multi_ph_validation·input_mode_comparison·accuracy
data/dataset_template.csv       배치 CSV 예시
  literature_dataset.csv          개발에 쓴 문헌 데이터셋(31건/23약물)
docs/DATASET.md                  문헌 출처·물성·용출 전체 공개
docs/               PARAMETERS·ACCURACY_ASSESSMENT·VALIDATION_SUMMARY·ROADMAP + SVG
tests/test_engine.py            단위테스트(8): 질량보존·BCS·공통이온·다중pH·배치·CI 등
```

## 자주 쓰는 명령
```bash
python tests/test_engine.py              # 단위테스트
python validation/validate_dataset.py    # 문헌 18건 검증 + 대시보드 SVG
python validation/input_mode_comparison.py   # 용해도 vs 용출 입력 정확도
python -m salt_pk.batch  data/dataset_template.csv   # CSV 일괄 검증
python -m salt_pk.calibrate data/your.csv            # 사내 보정
python -m salt_pk.report                 # 예제 리포트
```

## 핵심 원칙 (수정 시 유지)
- **disposition·투과는 free base 성질 → 모든 염 공유.** 염은 흡수만 바꿈 → `AUC비≈Fa비`.
- **측정 용출 > 평형 용해도** (과포화는 동역학). 다중 pH(위=pH1.2 spring, 장=pH6.8 parachute) 권장.
- **JS 엔진은 Python과 수치 일치 유지** (변경 시 node로 교차검증: `validation`의 비교 참고).
- **정직성:** 없는 데이터 안 지어냄. 검증은 등급(A 측정 / B 부분 / C template) 분리.

## 정확도 현황 (문헌 31건, BCS class별)
BCS I/III(salt 무효과) ≈1.0 정확 · BCS II 측정입력(S0≥1, n=10) 2-fold 10/10·평균 75% · 방향 29/31.
초난용성(S0<1) 과대예측(FaSSIF 보정 필요) · template 입력 magnitude·counterion·절대값 부적합. → `docs/VALIDATION_SUMMARY.md`.

## 확장 경로
사내 pH1.2/4.5/6.8 용출+PK를 `data/*.csv`로 적재 → `batch`로 검증 → `calibrate`로 보정 →
≥10–20개 확보 시 decision 등급. (공개 문헌 짝 데이터는 수십 개가 상한.)
