#!/usr/bin/env python3
"""
oa_catalog.csv 의 OA 논문(PMCID)을 PC 로컬 폴더로 일괄 다운로드.

oa_catalog.csv 는 약물별 pH 1.2 / 6.8 용출 데이터가 확인된 PubMed Central
오픈액세스 논문 목록입니다(WebSearch 로 큐레이션). 이 스크립트는 각 PMCID 의
OA PDF 를 여러 미러에서 시도해 내려받아 약물별 폴더에 저장합니다.

* OA(합법 공개) PDF 만 받습니다.
* 본인 PC에서 실행하세요. (네트워크가 열려 있어야 합니다)

설치:  pip install requests
실행:  python download_from_catalog.py
       python download_from_catalog.py --outdir "D:/논문/용출" --catalog oa_catalog.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OA-Catalog-Downloader/1.0; "
    "academic non-commercial use)"
}


def pdf_urls(pmcid: str) -> list[str]:
    pid = pmcid.replace("PMC", "")
    return [
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/PMC/PMC{pid}/fullTextPDF",
        f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pid}/pdf/",
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pid}/pdf/",
    ]


def slug(t: str, n: int = 70) -> str:
    t = re.sub(r"[^\w\s\-]", "", t)
    return re.sub(r"\s+", "_", t.strip())[:n] or "untitled"


def save_pdf(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=90)
    except requests.RequestException:
        return False
    if r.status_code != 200:
        return False
    first = next(r.iter_content(1024), b"")
    if b"%PDF" not in first[:1024] and "pdf" not in r.headers.get("Content-Type", "").lower():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(first)
        for c in r.iter_content(8192):
            if c:
                f.write(c)
    if dest.stat().st_size < 10_000:
        dest.unlink(missing_ok=True)
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="oa_catalog.csv 일괄 다운로더")
    ap.add_argument("--catalog", default="oa_catalog.csv")
    ap.add_argument("--outdir", default=str(Path.home() / "dissolution_pdfs"))
    args = ap.parse_args()

    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    with open(args.catalog, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    print(f"카탈로그 {len(rows)}건 → {outdir} 로 다운로드")
    ok = 0
    for row in rows:
        pmcid = row.get("pmcid", "").strip()
        if not pmcid:
            continue
        drug = row.get("drug", "misc")
        bcs = row.get("bcs_class", "?")
        ddir = outdir / f"{slug(drug)}_BCS-{bcs}"
        dest = ddir / f"{pmcid}_{slug(row.get('title', ''), 55)}.pdf"
        if dest.exists():
            print(f"  = 이미있음 {pmcid}")
            ok += 1
            continue
        done = False
        for u in pdf_urls(pmcid):
            if save_pdf(u, dest):
                done = True
                break
        if done:
            ok += 1
            print(f"  ✓ {pmcid}  {drug}")
        else:
            print(f"  × 실패 {pmcid}  {drug}  (수동: {row.get('pmc_url','')})")
        time.sleep(1)

    print(f"\n완료 ✅  {ok}/{len(rows)} 편 저장 → {outdir}")


if __name__ == "__main__":
    main()
