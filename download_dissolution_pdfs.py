#!/usr/bin/env python3
"""
약물별 pH buffer 용출(dissolution) 문헌 PDF 자동 수집기
=========================================================

BCS(Biopharmaceutics Classification System) 모델 약물에 대해
"pH / buffer 에 따른 용출(dissolution / release rate)" 관련 논문을
합법적인 오픈액세스(OA) 경로로만 검색·다운로드하여 PC 로컬 폴더에
자동 저장합니다.

사용 경로 (저작권 안전):
  1) Europe PMC  : 논문 검색 + OA 전문 PDF
  2) Unpaywall   : DOI 기반 합법 OA PDF 탐색
  3) NCBI PMC    : PMCID 기반 OA PDF

* SCI-Hub 등 불법 배포 사이트는 사용하지 않습니다.
* OA(무료 공개)로 확인된 PDF만 내려받습니다. 페이월 논문은
  서지정보(metadata)만 CSV로 기록하고 건너뜁니다.

필요 패키지:
    pip install requests

사용 예:
    python download_dissolution_pdfs.py
    python download_dissolution_pdfs.py --outdir "D:/논문/용출" --per-drug 8
    python download_dissolution_pdfs.py --drugs ibuprofen ketoprofen
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests 패키지가 필요합니다.  실행:  pip install requests")


# ---------------------------------------------------------------------------
# BCS 모델 약물 (pH 의존 용출 거동 연구가 풍부한 대표 약물)
# ---------------------------------------------------------------------------
BCS_MODEL_DRUGS = {
    # Class I : 고용해도 / 고투과도
    "metoprolol": "I",
    "propranolol": "I",
    "diltiazem": "I",
    "verapamil": "I",
    "metformin": "I",
    # Class II : 저용해도 / 고투과도  ← pH 의존 용출이 가장 두드러짐
    "ibuprofen": "II",
    "ketoprofen": "II",
    "indomethacin": "II",
    "naproxen": "II",
    "diclofenac": "II",
    "carbamazepine": "II",
    "nifedipine": "II",
    "glibenclamide": "II",
    "ketoconazole": "II",
    "itraconazole": "II",
    "danazol": "II",
    # Class III : 고용해도 / 저투과도
    "atenolol": "III",
    "ranitidine": "III",
    "cimetidine": "III",
    "acyclovir": "III",
    # Class IV : 저용해도 / 저투과도
    "furosemide": "IV",
    "hydrochlorothiazide": "IV",
    "chlorthalidone": "IV",
}

EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPE_PMC_PDF = "https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{pmcid}/fullTextPDF"
UNPAYWALL = "https://api.unpaywall.org/v2/{doi}"
NCBI_PMC_PDF = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OA-Dissolution-Collector/1.0; "
    "academic non-commercial use)"
}


def slugify(text: str, maxlen: int = 80) -> str:
    """파일/폴더명으로 안전한 문자열로 변환."""
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:maxlen] or "untitled"


def http_get(url: str, *, params=None, stream=False, timeout=60, retries=3):
    """지수 백오프 재시도가 적용된 GET."""
    delay = 2
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(
                url, params=params, headers=HEADERS, stream=stream, timeout=timeout
            )
            if r.status_code == 200:
                return r
            # 404/403 은 재시도 의미 없음
            if r.status_code in (403, 404):
                return r
        except requests.RequestException as exc:
            last_exc = exc
        time.sleep(delay)
        delay *= 2
    if last_exc:
        print(f"      ! 요청 실패: {last_exc}")
    return None


def search_europe_pmc(drug: str, limit: int) -> list[dict]:
    """Europe PMC 에서 약물 + pH/buffer + 용출 논문 검색."""
    query = (
        f'("{drug}") AND '
        f'(dissolution OR "release rate" OR "drug release") AND '
        f'(pH OR buffer)'
    )
    params = {
        "query": query,
        "format": "json",
        "pageSize": min(limit * 4, 100),  # OA 필터 후 충분히 남도록 넉넉히
        "resultType": "core",
        "sort": "CITED desc",  # 피인용 많은 순 → 신뢰도 높은 문헌 우선
    }
    r = http_get(EUROPE_PMC_SEARCH, params=params)
    if not r:
        return []
    try:
        return r.json().get("resultList", {}).get("result", [])
    except ValueError:
        return []


def find_oa_pdf_url(record: dict, email: str) -> str | None:
    """레코드에서 합법 OA PDF URL을 탐색 (Europe PMC → NCBI → Unpaywall)."""
    pmcid = record.get("pmcid")
    is_oa = str(record.get("isOpenAccess", "")).upper() == "Y"

    # 1) Europe PMC OA 전문 PDF
    if is_oa and pmcid:
        return EUROPE_PMC_PDF.format(source="PMC", pmcid=pmcid)

    # 2) Unpaywall (DOI 기반 합법 OA 버전)
    doi = record.get("doi")
    if doi:
        r = http_get(UNPAYWALL.format(doi=doi), params={"email": email})
        if r and r.status_code == 200:
            try:
                data = r.json()
            except ValueError:
                data = {}
            loc = data.get("best_oa_location") or {}
            pdf = loc.get("url_for_pdf")
            if pdf:
                return pdf

    # 3) NCBI PMC (OA 인 경우)
    if is_oa and pmcid:
        return NCBI_PMC_PDF.format(pmcid=pmcid)

    return None


def download_pdf(url: str, dest: Path) -> bool:
    """PDF 다운로드. 실제 PDF 인지 확인 후 저장."""
    r = http_get(url, stream=True, timeout=120)
    if not r or r.status_code != 200:
        return False

    ctype = r.headers.get("Content-Type", "").lower()
    first = next(r.iter_content(chunk_size=1024), b"")
    if b"%PDF" not in first[:1024] and "pdf" not in ctype:
        return False  # HTML 랜딩페이지 등 → 스킵

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        if first:
            f.write(first)
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    # 너무 작으면(에러 페이지) 실패 처리
    if dest.stat().st_size < 10_000:
        dest.unlink(missing_ok=True)
        return False
    return True


def collect_for_drug(drug: str, bcs: str, outdir: Path, per_drug: int,
                     email: str, manifest: list[dict]) -> int:
    """한 약물에 대해 검색·다운로드. 저장 성공 건수 반환."""
    print(f"\n=== {drug}  (BCS Class {bcs}) ===")
    drug_dir = outdir / f"{slugify(drug)}_BCS-{bcs}"
    records = search_europe_pmc(drug, per_drug)
    print(f"    검색 결과 {len(records)}건 → OA PDF 탐색 중...")

    saved = 0
    for rec in records:
        if saved >= per_drug:
            break
        title = rec.get("title", "untitled").rstrip(".")
        year = rec.get("pubYear", "n.d.")
        pmid = rec.get("pmid") or rec.get("id", "")

        pdf_url = find_oa_pdf_url(rec, email)
        row = {
            "drug": drug,
            "bcs": bcs,
            "title": title,
            "year": year,
            "pmid": pmid,
            "doi": rec.get("doi", ""),
            "pmcid": rec.get("pmcid", ""),
            "open_access": rec.get("isOpenAccess", "N"),
            "pdf_url": pdf_url or "",
            "status": "",
        }

        if not pdf_url:
            row["status"] = "no_OA_pdf (metadata only)"
            manifest.append(row)
            continue

        fname = f"{year}_{slugify(title, 60)}_{pmid}.pdf"
        dest = drug_dir / fname
        if dest.exists():
            row["status"] = "already_exists"
            manifest.append(row)
            saved += 1
            continue

        ok = download_pdf(pdf_url, dest)
        if ok:
            saved += 1
            row["status"] = "downloaded"
            print(f"    ✓ {fname}")
        else:
            row["status"] = "download_failed"
            print(f"    × 실패: {title[:60]}")
        manifest.append(row)
        time.sleep(1)  # 서버 예의(rate-limit) 차원의 지연

    print(f"    → 저장 {saved}건")
    return saved


def main() -> None:
    ap = argparse.ArgumentParser(
        description="약물별 pH buffer 용출 문헌 OA PDF 자동 수집기"
    )
    ap.add_argument(
        "--outdir",
        default=str(Path.home() / "dissolution_pdfs"),
        help="저장 폴더 (기본: 홈디렉터리/dissolution_pdfs)",
    )
    ap.add_argument(
        "--per-drug", type=int, default=5, help="약물당 최대 PDF 수 (기본 5)"
    )
    ap.add_argument(
        "--drugs", nargs="*", help="대상 약물 직접 지정 (미지정 시 BCS 전체 목록)"
    )
    ap.add_argument(
        "--email",
        default=os.environ.get("UNPAYWALL_EMAIL", "dwsynrnd@gmail.com"),
        help="Unpaywall API 용 이메일 (필수 정책)",
    )
    args = ap.parse_args()

    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    if args.drugs:
        targets = {d.lower(): BCS_MODEL_DRUGS.get(d.lower(), "?") for d in args.drugs}
    else:
        targets = BCS_MODEL_DRUGS

    print(f"저장 위치 : {outdir}")
    print(f"대상 약물 : {len(targets)}종, 약물당 최대 {args.per_drug}편")

    manifest: list[dict] = []
    total = 0
    for drug, bcs in targets.items():
        total += collect_for_drug(
            drug, bcs, outdir, args.per_drug, args.email, manifest
        )

    # 서지정보 매니페스트 CSV 저장 (다운로드 실패/페이월 건도 기록)
    csv_path = outdir / "manifest.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "drug", "bcs", "title", "year", "pmid",
                "doi", "pmcid", "open_access", "pdf_url", "status",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest)

    print(f"\n완료 ✅  총 {total}편 PDF 저장")
    print(f"서지정보 매니페스트 : {csv_path}")
    print("(페이월 논문은 PDF 없이 manifest.csv 에 서지정보만 기록됩니다)")


if __name__ == "__main__":
    main()
