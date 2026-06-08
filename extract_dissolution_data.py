#!/usr/bin/env python3
"""
다운로드한 용출 논문 PDF 본문에서 pH / 시간 / %release 수치를 추출 → 엑셀.

전제: 먼저 download_from_catalog.py 로 PDF를 받아 ~/dissolution_pdfs/ 에
약물별 폴더로 저장돼 있어야 합니다. (PDF는 본인 PC에서 받습니다.)

이 스크립트는 각 PDF의 텍스트를 읽어:
  - pH 1.2 / 4.5 / 6.8 / 7.4 등 buffer 언급
  - "X% ... Y min/h" 형태의 용출/방출 수치
  - 용출 시험 조건 문장(USP apparatus, rpm, 매질)
을 정규식으로 뽑아 약물별로 정리한 detailed_dissolution_data.xlsx 를 만듭니다.

* 수치가 그래프(그림)에만 있는 논문은 본문 텍스트로 못 뽑을 수 있습니다.
  그런 논문은 'figure_only' 로 표시됩니다.

설치:  pip install pdfplumber openpyxl
실행:  python extract_dissolution_data.py
       python extract_dissolution_data.py --pdfdir "D:/논문/용출"
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    raise SystemExit("pip install pdfplumber openpyxl 가 필요합니다.")

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

# 용출 % 수치 + 시간:  "85.3% in 30 min", "89 % after 60 minutes", "released 23% at 10 h"
RE_PCT_TIME = re.compile(
    r"(\d{1,3}(?:\.\d+)?)\s*%[^.\n]{0,40}?(\d{1,3}(?:\.\d+)?)\s*(min|minute|minutes|h|hr|hour|hours)",
    re.I,
)
RE_TIME_PCT = re.compile(
    r"(\d{1,3}(?:\.\d+)?)\s*(min|minute|minutes|h|hr|hour|hours)[^.\n]{0,40}?(\d{1,3}(?:\.\d+)?)\s*%",
    re.I,
)
RE_PH = re.compile(r"pH\s*(\d(?:\.\d)?)", re.I)
RE_COND = re.compile(
    r"[^.\n]{0,80}(USP\s*(?:apparatus|type)\s*[IV12]+|paddle|basket|\d{2,3}\s*rpm|"
    r"0\.1\s*[MN]\s*HCl|phosphate buffer|simulated (?:gastric|intestinal) fluid)[^.\n]{0,80}",
    re.I,
)

PH_TARGETS = ["1.2", "4.5", "6.8", "7.4", "7.2", "5.8"]


def extract_text(pdf_path: Path) -> str:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    except Exception as e:
        return f"__ERROR__ {e}"


def analyze(text: str) -> dict:
    if text.startswith("__ERROR__"):
        return {"status": text, "ph_found": "", "conditions": "", "values": ""}
    phs = sorted({m.group(1) for m in RE_PH.finditer(text)}, key=lambda x: float(x))
    conds = []
    for m in RE_COND.finditer(text):
        s = re.sub(r"\s+", " ", m.group(0)).strip()
        if s not in conds:
            conds.append(s)
        if len(conds) >= 6:
            break
    vals = []
    for m in RE_PCT_TIME.finditer(text):
        vals.append(f"{m.group(1)}% @ {m.group(2)}{m.group(3)[:3]}")
    for m in RE_TIME_PCT.finditer(text):
        vals.append(f"{m.group(3)}% @ {m.group(1)}{m.group(2)[:3]}")
    # 중복 제거 후 상위 40개
    seen, uniq = set(), []
    for v in vals:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    status = "ok" if uniq else ("figure_only" if phs else "no_text")
    return {
        "status": status,
        "ph_found": ", ".join(phs),
        "has_1_2": "Y" if "1.2" in phs else "",
        "has_6_8": "Y" if "6.8" in phs else "",
        "conditions": " | ".join(conds),
        "values": "; ".join(uniq[:40]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdfdir", default=str(Path.home() / "dissolution_pdfs"))
    ap.add_argument("--out", default="detailed_dissolution_data.xlsx")
    args = ap.parse_args()

    root = Path(args.pdfdir).expanduser()
    pdfs = sorted(root.rglob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"PDF가 없습니다: {root}\n먼저 download_from_catalog.py 실행하세요.")

    print(f"{len(pdfs)}개 PDF 분석 중...")
    wb = Workbook()
    ws = wb.active
    ws.title = "세부용출데이터"
    head = ["약물폴더", "파일", "상태", "검출 pH", "pH1.2", "pH6.8",
            "시험조건", "용출수치(%@시간)"]
    ws.append(head)
    for c in range(1, len(head) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    widths = [22, 36, 12, 18, 7, 7, 50, 60]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = w

    ok = 0
    for p in pdfs:
        info = analyze(extract_text(p))
        if info["status"] == "ok":
            ok += 1
        ws.append([
            p.parent.name, p.name, info["status"], info["ph_found"],
            info.get("has_1_2", ""), info.get("has_6_8", ""),
            info["conditions"], info["values"],
        ])
        for c in range(1, len(head) + 1):
            ws.cell(row=ws.max_row, column=c).alignment = Alignment(
                vertical="top", wrap_text=(c in (7, 8)))
        print(f"  [{info['status']:11}] {p.name[:60]}")

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:H{ws.max_row}"
    wb.save(args.out)
    print(f"\n완료 ✅  {args.out}  (수치추출 성공 {ok}/{len(pdfs)}편)")
    print("status: ok=수치추출됨 / figure_only=pH는있으나 수치는 그래프 / no_text=텍스트없음(스캔본)")


if __name__ == "__main__":
    main()
