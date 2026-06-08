# 개발 로드맵 (Salt-Screening IVIVE PK Predictor)

> 원칙: ① 정직(없는 데이터 안 지어냄) ② 측정 용출 우선 ③ 상대비교/순위 신뢰, 절대값 보수.

## ✅ 완료
- 기전 엔진(pHmax·공통이온·과포화/석출), BCS I–IV, 다중 pH(Tier 2)·2-stage(Tier 3) 입력
- dose/액량비 보정(`ph_solubility`/`test_dose`/`volume`)
- 문헌 18건 검증 + 대시보드, 입력방식 비교(용해도30%→용출70%)
- 웹툴(Python과 수치 일치), 단위테스트 6종

## �doing / 다음 (가치순)
1. **CSV 배치 임포트 + 자동검증** ← 사내 데이터로 표본 100+ 확장하는 현실적 경로 ★
2. **보정(calibration)** — 사내 reference로 `kd0·kprecip·salt_wettability·kScale` 자동 피팅
3. **신뢰구간/민감도** — 입력 불확실성 → 예측 노출비의 90% 구간(Monte-Carlo)
4. **웹툴 CSV 업로드 + 배치 결과표**
5. **Cmax 개선** — 2-구획 분포로 피크 과대예측 완화
6. **counterion 불균등화(disproportionation) 동역학** — mesylate vs HCl 미세차이
7. CLAUDE.md(개발 가이드), 사용 튜토리얼

## 데이터 전략 (표본 키우기)
- 입력 원자료(pH1.2/4.5/6.8 용출)는 풍부 → **CSV로 사내 일괄 적재**가 표본 확장의 핵심.
- 공개 문헌 salt+PK 짝은 수십 개가 상한 → 지어내지 않고 등급(A/B/C)으로 관리.
- 검증 표본 ≥10–20(사내) 확보 후 **보정 → 결정등급** 승격.
