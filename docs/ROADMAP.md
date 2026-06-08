# 개발 로드맵 (Salt-Screening IVIVE PK Predictor)

> 원칙: ① 정직(없는 데이터 안 지어냄) ② 측정 용출 우선 ③ 상대비교/순위 신뢰, 절대값 보수.

## ✅ 완료
- 기전 엔진(pHmax·공통이온·과포화/석출), BCS I–IV, 다중 pH(Tier 2)·2-stage(Tier 3) 입력
- dose/액량비 보정(`ph_solubility`/`test_dose`/`volume`)
- 문헌 18건 검증 + 대시보드, 입력방식 비교(용해도30%→용출70%)
- 웹툴(Python과 수치 일치), 단위테스트 6종

## ✅ 이번 라운드 완료
1. ~~CSV 배치 임포트 + 자동검증~~ → `salt_pk/batch.py` + `data/dataset_template.csv`
2. ~~보정(calibration)~~ → `salt_pk/calibrate.py` (template 77%→84%)
3. ~~신뢰구간/민감도~~ → `salt_pk/uncertainty.py` (Monte-Carlo 90% CI)
4. ~~웹툴 CSV 업로드 + 배치 결과표~~ → HTML 배치 패널(Python과 일치)
5. ~~Cmax 개선~~ → 불필요 확인(적정 입력 시 평균 1.26 fold, 9/9). 2-구획 추가 안 함.
7. ~~CLAUDE.md~~ → 작성 완료

## 다음 (남은 가치순)
- **counterion 불균등화 동역학** — 측정 용출 없을 때 mesylate vs HCl 차이(부분만 가능, 본질은 측정 필요)
- **사내 reference 10–20개 전향 검증** → decision 등급 승격 (데이터 필요, 사용자 측)
- 웹툴: 종 생리값 편집 UI, 결과 PDF 개선
- 입력 위저드/튜토리얼

## 데이터 전략 (표본 키우기)
- 입력 원자료(pH1.2/4.5/6.8 용출)는 풍부 → **CSV로 사내 일괄 적재**가 표본 확장의 핵심.
- 공개 문헌 salt+PK 짝은 수십 개가 상한 → 지어내지 않고 등급(A/B/C)으로 관리.
- 검증 표본 ≥10–20(사내) 확보 후 **보정 → 결정등급** 승격.
