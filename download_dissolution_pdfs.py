#!/usr/bin/env python3
"""
약물별 pH buffer 용출(dissolution) 문헌 PDF 자동 수집기  v2
=============================================================

BCS(Biopharmaceutics Classification System) 모델 약물에 대해
"pH / buffer 에 따른 용출(dissolution / release rate)" 관련 논문을
합법적인 오픈액세스(OA) 경로로만 검색·다운로드하여 PC 로컬 폴더에
자동 저장합니다.

v2 강화점
---------
* BCS 클래스(I~IV)별 22종 이상, 총 88종 모델 약물.
* **pH 1.2 와 pH 6.8 용출 데이터가 모두 확인된 논문만** 다운로드
  (Europe PMC 초록 + OA 전문(full-text) 텍스트에서 검증).
  - `--require-ph both`  : pH 1.2 AND pH 6.8 둘 다 있어야 함 (기본)
  - `--require-ph any`   : 둘 중 하나라도
  - `--require-ph off`   : 검증 끔
* manifest.csv 에 검출된 pH 값(ph_1_2 / ph_6_8 / others) 기록.

사용 경로 (저작권 안전):
  1) Europe PMC  : 논문 검색 + OA 전문(PDF / XML)
  2) Unpaywall   : DOI 기반 합법 OA PDF 탐색
  3) NCBI PMC    : PMCID 기반 OA PDF
* SCI-Hub 등 불법 배포 사이트는 사용하지 않습니다.

필요 패키지:
    pip install requests

사용 예:
    python download_dissolution_pdfs.py
    python download_dissolution_pdfs.py --outdir "D:/논문/용출" --per-drug 10
    python download_dissolution_pdfs.py --classes II --per-drug 15
    python download_dissolution_pdfs.py --drugs ibuprofen ketoprofen --require-ph any

주의: BCS 분류는 문헌(WHO/Lindenberg 2004, Takagi 2006 등)에 따라 다를 수
있으며, 염·용량·실험조건에 따라 경계 약물의 분류가 갈릴 수 있습니다.
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
# BCS 모델 약물 (클래스별 22종 이상, pH 의존 용출 연구가 풍부한 약물 중심)
# ---------------------------------------------------------------------------
BCS_MODEL_DRUGS: dict[str, list[str]] = {
    # Class I : 고용해도 / 고투과도
    "I": [
        "metoprolol", "propranolol", "diltiazem", "verapamil", "metformin",
        "captopril", "enalapril", "labetalol", "levodopa", "theophylline",
        "prednisolone", "metronidazole", "levofloxacin", "minocycline",
        "diphenhydramine", "chloroquine", "quinidine", "promethazine",
        "amitriptyline", "fluoxetine", "salbutamol", "acetaminophen",
        "tramadol", "venlafaxine",
    ],
    # Class II : 저용해도 / 고투과도  ← pH 의존 용출이 가장 두드러짐
    "II": [
        "ibuprofen", "ketoprofen", "indomethacin", "naproxen", "diclofenac",
        "aceclofenac", "flurbiprofen", "piroxicam", "meloxicam", "carbamazepine",
        "phenytoin", "nifedipine", "felodipine", "glibenclamide", "glipizide",
        "glimepiride", "ketoconazole", "itraconazole", "fluconazole", "danazol",
        "carvedilol", "atorvastatin", "simvastatin", "ezetimibe", "fenofibrate",
        "telmisartan", "valsartan", "candesartan", "celecoxib", "spironolactone",
        "griseofulvin", "albendazole",
    ],
    # Class III : 고용해도 / 저투과도
    "III": [
        "atenolol", "ranitidine", "cimetidine", "famotidine", "acyclovir",
        "valaciclovir", "amoxicillin", "ampicillin", "cefuroxime", "cefixime",
        "lisinopril", "nadolol", "pravastatin", "metformin", "trimethoprim",
        "gabapentin", "pregabalin", "hydralazine", "allopurinol", "folic acid",
        "ascorbic acid", "ciprofloxacin", "tetracycline", "zidovudine",
    ],
    # Class IV : 저용해도 / 저투과도
    "IV": [
        "furosemide", "hydrochlorothiazide", "chlorthalidone", "chlorothiazide",
        "indapamide", "bumetanide", "torsemide", "sulfasalazine",
        "sulfamethoxazole", "nitrofurantoin", "dapsone", "mebendazole",
        "methotrexate", "acetazolamide", "ritonavir", "saquinavir",
        "nelfinavir", "amphotericin B", "colistin", "cyclosporine",
        "tacrolimus", "rosuvastatin", "ofloxacin", "norfloxacin",
    ],
}

EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPE_PMC_FULLTEXT = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{pmcid}/fullTextXML"
)
EUROPE_PMC_PDF = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{pmcid}/fullTextPDF"
)
UNPAYWALL = "https://api.unpaywall.org/v2/{doi}"
NCBI_PMC_PDF = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OA-Dissolution-Collector/2.0; "
    "academic non-commercial use)"
}

# pH 검출 정규식 ----------------------------------------------------------------
RE_PH_12 = re.compile(
    r"(pH\s*1\.2|0\.1\s*[MN]\s*HCl|simulated\s+gastric\s+fluid|\bSGF\b)", re.I
)
RE_PH_68 = re.compile(
    r"(pH\s*6\.8|phosphate\s+buffer.{0,20}6\.8|simulated\s+intestinal\s+fluid|\bSIF\b)",
    re.I,
)
RE_PH_ANY = re.compile(r"pH\s*\d(?:\.\d)?", re.I)


def slugify(text: str, maxlen: int = 80) -> str:
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:maxlen] or "untitled"


def http_get(url, *, params=None, stream=False, timeout=60, retries=3):
    delay = 2
    last_exc = None
    for _ in range(retries):
        try:
            r = requests.get(
                url, params=params, headers=HEADERS, stream=stream, timeout=timeout
            )
            if r.status_code == 200:
                return r
            if r.status_code in (400, 403, 404):
                return r
        except requests.RequestException as exc:
            last_exc = exc
        time.sleep(delay)
        delay *= 2
    if last_exc:
        print(f"      ! 요청 실패: {last_exc}")
    return None


def search_europe_pmc(drug: str, page_size: int) -> list[dict]:
    query = (
        f'("{drug}") AND '
        f'(dissolution OR "release rate" OR "drug release" OR "release profile") AND '
        f'(pH OR buffer) AND '
        f'("1.2" OR "6.8" OR gastric OR intestinal)'
    )
    params = {
        "query": query,
        "format": "json",
        "pageSize": min(page_size, 100),
        "resultType": "core",
        "sort": "CITED desc",
    }
    r = http_get(EUROPE_PMC_SEARCH, params=params)
    if not r or r.status_code != 200:
        return []
    try:
        return r.json().get("resultList", {}).get("result", [])
    except ValueError:
        return []


def fetch_verification_text(record: dict) -> str:
    """검증용 텍스트: 초록 + (OA 인 경우) 전문 XML."""
    text = record.get("abstractText", "") or ""
    pmcid = record.get("pmcid")
    is_oa = str(record.get("isOpenAccess", "")).upper() == "Y"
    if is_oa and pmcid:
        r = http_get(EUROPE_PMC_FULLTEXT.format(source="PMC", pmcid=pmcid))
        if r and r.status_code == 200 and r.text:
            # 태그 제거 후 본문 추가
            text += " " + re.sub(r"<[^>]+>", " ", r.text)
    return text


def check_ph(text: str) -> tuple[bool, bool]:
    return bool(RE_PH_12.search(text)), bool(RE_PH_68.search(text))


def find_oa_pdf_url(record: dict, email: str) -> str | None:
    pmcid = record.get("pmcid")
    is_oa = str(record.get("isOpenAccess", "")).upper() == "Y"
    if is_oa and pmcid:
        return EUROPE_PMC_PDF.format(source="PMC", pmcid=pmcid)
    doi = record.get("doi")
    if doi:
        r = http_get(UNPAYWALL.format(doi=doi), params={"email": email})
        if r and r.status_code == 200:
            try:
                loc = (r.json().get("best_oa_location") or {})
                if loc.get("url_for_pdf"):
                    return loc["url_for_pdf"]
            except ValueError:
                pass
    if is_oa and pmcid:
        return NCBI_PMC_PDF.format(pmcid=pmcid)
    return None


def download_pdf(url: str, dest: Path) -> bool:
    r = http_get(url, stream=True, timeout=120)
    if not r or r.status_code != 200:
        return False
    ctype = r.headers.get("Content-Type", "").lower()
    first = next(r.iter_content(chunk_size=1024), b"")
    if b"%PDF" not in first[:1024] and "pdf" not in ctype:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        if first:
            f.write(first)
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    if dest.stat().st_size < 10_000:
        dest.unlink(missing_ok=True)
        return False
    return True


def passes_ph_filter(found12: bool, found68: bool, mode: str) -> bool:
    if mode == "off":
        return True
    if mode == "any":
        return found12 or found68
    return found12 and found68  # "both"


def collect_for_drug(drug, bcs, outdir, per_drug, email, mode, manifest) -> int:
    print(f"\n=== {drug}  (BCS Class {bcs}) ===")
    drug_dir = outdir / f"{slugify(drug)}_BCS-{bcs}"
    records = search_europe_pmc(drug, page_size=min(per_drug * 6, 100))
    print(f"    검색 {len(records)}건 → pH 검증 + OA PDF 탐색...")

    saved = 0
    for rec in records:
        if saved >= per_drug:
            break
        title = (rec.get("title") or "untitled").rstrip(".")
        year = rec.get("pubYear", "n.d.")
        pmid = rec.get("pmid") or rec.get("id", "")

        text = fetch_verification_text(rec)
        f12, f68 = check_ph(text)
        if not passes_ph_filter(f12, f68, mode):
            manifest.append({
                "drug": drug, "bcs": bcs, "title": title, "year": year,
                "pmid": pmid, "doi": rec.get("doi", ""),
                "pmcid": rec.get("pmcid", ""),
                "open_access": rec.get("isOpenAccess", "N"),
                "ph_1_2": f12, "ph_6_8": f68, "pdf_url": "",
                "status": "skipped_ph_filter",
            })
            continue

        pdf_url = find_oa_pdf_url(rec, email)
        row = {
            "drug": drug, "bcs": bcs, "title": title, "year": year,
            "pmid": pmid, "doi": rec.get("doi", ""),
            "pmcid": rec.get("pmcid", ""),
            "open_access": rec.get("isOpenAccess", "N"),
            "ph_1_2": f12, "ph_6_8": f68, "pdf_url": pdf_url or "",
            "status": "",
        }
        if not pdf_url:
            row["status"] = "ph_ok_but_no_OA_pdf (metadata only)"
            manifest.append(row)
            continue

        fname = f"{year}_{slugify(title, 60)}_{pmid}.pdf"
        dest = drug_dir / fname
        if dest.exists():
            row["status"] = "already_exists"
            manifest.append(row)
            saved += 1
            continue

        if download_pdf(pdf_url, dest):
            saved += 1
            row["status"] = "downloaded"
            tag = f"[pH1.2{'✓' if f12 else '·'} 6.8{'✓' if f68 else '·'}]"
            print(f"    ✓ {tag} {fname}")
        else:
            row["status"] = "download_failed"
            print(f"    × 실패: {title[:55]}")
        manifest.append(row)
        time.sleep(1)

    print(f"    → 저장 {saved}건")
    return saved


def main() -> None:
    ap = argparse.ArgumentParser(
        description="약물별 pH buffer 용출 문헌 OA PDF 자동 수집기 v2"
    )
    ap.add_argument("--outdir", default=str(Path.home() / "dissolution_pdfs"),
                    help="저장 폴더 (기본: 홈디렉터리/dissolution_pdfs)")
    ap.add_argument("--per-drug", type=int, default=8,
                    help="약물당 최대 PDF 수 (기본 8)")
    ap.add_argument("--classes", nargs="*", choices=["I", "II", "III", "IV"],
                    help="대상 BCS 클래스 (미지정 시 전체)")
    ap.add_argument("--drugs", nargs="*",
                    help="대상 약물 직접 지정 (BCS 목록 무시)")
    ap.add_argument("--require-ph", choices=["both", "any", "off"], default="both",
                    help="pH 1.2/6.8 필터 (기본 both = 둘 다 필수)")
    ap.add_argument("--email",
                    default=os.environ.get("UNPAYWALL_EMAIL", "dwsynrnd@gmail.com"),
                    help="Unpaywall API 용 이메일")
    args = ap.parse_args()

    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    # 대상 약물 → [(drug, class)] 구성
    targets: list[tuple[str, str]] = []
    if args.drugs:
        lookup = {d: c for c, ds in BCS_MODEL_DRUGS.items() for d in ds}
        targets = [(d, lookup.get(d.lower(), "?")) for d in args.drugs]
    else:
        classes = args.classes or ["I", "II", "III", "IV"]
        for c in classes:
            targets += [(d, c) for d in BCS_MODEL_DRUGS[c]]

    print(f"저장 위치 : {outdir}")
    print(f"대상      : {len(targets)}종 | 약물당 최대 {args.per_drug}편 "
          f"| pH 필터: {args.require_ph}")

    manifest: list[dict] = []
    total = 0
    for drug, bcs in targets:
        total += collect_for_drug(
            drug, bcs, outdir, args.per_drug, args.email, args.require_ph, manifest
        )

    csv_path = outdir / "manifest.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "drug", "bcs", "title", "year", "pmid", "doi", "pmcid",
            "open_access", "ph_1_2", "ph_6_8", "pdf_url", "status",
        ])
        writer.writeheader()
        writer.writerows(manifest)

    n_dl = sum(1 for m in manifest if m["status"] == "downloaded")
    n_both = sum(1 for m in manifest if m["ph_1_2"] and m["ph_6_8"])
    print(f"\n완료 ✅  PDF 저장 {total}편 (이번 실행 신규 {n_dl}편)")
    print(f"pH 1.2 & 6.8 동시 확인 논문 : {n_both}건")
    print(f"서지정보 매니페스트 : {csv_path}")


if __name__ == "__main__":
    main()
