#!/usr/bin/env python3
"""
약물별 pH buffer 용출 문헌 PDF — 브라우저(Chrome) 자동 수집기 (하이브리드)
==========================================================================

전략: "데이터 최대화"
  1) API 발굴   : Europe PMC 로 약물별 후보 논문을 최대한 많이 수집
  2) pH 검증    : 초록 + OA 전문에서 pH 1.2 / 6.8 데이터 확인
  3) 다운로드   : 먼저 일반 HTTP 시도 → 막히면(JS/쿠키/Cloudflare)
                 **Playwright 가 실제 Chrome 을 띄워** 페이지에 들어가
                 쿠키를 얻은 뒤 PDF 를 직접 내려받음 (headed = 창이 보임)
  4) (선택) Google Scholar 를 브라우저로 검색해 추가 OA PDF 확보
            └ ToS·CAPTCHA 때문에 기본 비활성. --scholar 로만 켜짐.

* OA(합법 공개) PDF 만 받습니다. SCI-Hub·페이월 우회는 하지 않습니다.
* 이 스크립트는 **본인 PC에서** 실행해야 Chrome 이 동작합니다.

설치:
    pip install playwright requests
    playwright install chromium

실행 예:
    python browser_collect.py                          # 전체, 헤드리스 아님(창 보임)
    python browser_collect.py --classes II --per-drug 20
    python browser_collect.py --headless               # 창 숨김
    python browser_collect.py --scholar                # Scholar 보강(주의)
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import requests

# 약물 목록 · pH 검증 · 유틸은 API 스크립트에서 재사용
from download_dissolution_pdfs import (
    BCS_MODEL_DRUGS,
    EUROPE_PMC_SEARCH,
    EUROPE_PMC_FULLTEXT,
    EUROPE_PMC_PDF,
    UNPAYWALL,
    NCBI_PMC_PDF,
    HEADERS,
    slugify,
    check_ph,
    http_get,
    passes_ph_filter,
)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


# ---------------------------------------------------------------------------
# 1) API 발굴
# ---------------------------------------------------------------------------
def search_candidates(drug: str, page_size: int) -> list[dict]:
    query = (
        f'("{drug}") AND '
        f'(dissolution OR "release rate" OR "drug release" OR "release profile") AND '
        f'(pH OR buffer) AND ("1.2" OR "6.8" OR gastric OR intestinal)'
    )
    params = {
        "query": query, "format": "json",
        "pageSize": min(page_size, 100), "resultType": "core", "sort": "CITED desc",
    }
    r = http_get(EUROPE_PMC_SEARCH, params=params)
    if not r or r.status_code != 200:
        return []
    try:
        return r.json().get("resultList", {}).get("result", [])
    except ValueError:
        return []


def verification_text(rec: dict) -> str:
    text = rec.get("abstractText", "") or ""
    pmcid = rec.get("pmcid")
    if str(rec.get("isOpenAccess", "")).upper() == "Y" and pmcid:
        r = http_get(EUROPE_PMC_FULLTEXT.format(source="PMC", pmcid=pmcid))
        if r and r.status_code == 200 and r.text:
            import re
            text += " " + re.sub(r"<[^>]+>", " ", r.text)
    return text


def candidate_pdf_urls(rec: dict, email: str) -> list[str]:
    """가능한 OA PDF URL 후보들(여러 소스)을 순서대로 반환."""
    urls: list[str] = []
    pmcid = rec.get("pmcid")
    is_oa = str(rec.get("isOpenAccess", "")).upper() == "Y"
    if is_oa and pmcid:
        urls.append(EUROPE_PMC_PDF.format(source="PMC", pmcid=pmcid))
        urls.append(NCBI_PMC_PDF.format(pmcid=pmcid))
        urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/")
    doi = rec.get("doi")
    if doi:
        r = http_get(UNPAYWALL.format(doi=doi), params={"email": email})
        if r and r.status_code == 200:
            try:
                data = r.json()
                for loc in [data.get("best_oa_location")] + (data.get("oa_locations") or []):
                    if loc and loc.get("url_for_pdf"):
                        urls.append(loc["url_for_pdf"])
            except ValueError:
                pass
    # 중복 제거(순서 유지)
    seen, out = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


# ---------------------------------------------------------------------------
# 2) 다운로드: requests → playwright 폴백
# ---------------------------------------------------------------------------
def _is_pdf_bytes(b: bytes) -> bool:
    return b[:1024].find(b"%PDF") != -1


def save_via_requests(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=90)
    except requests.RequestException:
        return False
    if r.status_code != 200:
        return False
    first = next(r.iter_content(1024), b"")
    if not _is_pdf_bytes(first) and "pdf" not in r.headers.get("Content-Type", "").lower():
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


def save_via_browser(page, context, url: str, dest: Path) -> bool:
    """실제 Chrome 으로 페이지 방문(쿠키 확보) 후 PDF 바이트를 직접 받기."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)  # Cloudflare/JS 통과 대기
    except Exception:
        pass
    # 브라우저의 쿠키/세션으로 PDF 요청
    try:
        resp = context.request.get(url, timeout=60000)
        if resp.ok:
            body = resp.body()
            if _is_pdf_bytes(body) or "pdf" in (resp.headers.get("content-type", "")).lower():
                if len(body) >= 10_000:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(body)
                    return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# 3) (선택) Google Scholar 브라우저 검색
# ---------------------------------------------------------------------------
def scholar_pdf_links(page, drug: str, want: int) -> list[str]:
    """Scholar 결과에서 [PDF] 직링크 수집. CAPTCHA 시 사용자가 직접 풀도록 대기."""
    q = f"{drug} dissolution pH 1.2 6.8 buffer"
    try:
        page.goto("https://scholar.google.com/scholar?q=" + requests.utils.quote(q),
                  wait_until="domcontentloaded", timeout=45000)
    except Exception:
        return []
    if "sorry" in page.url or page.locator("#gs_captcha_f").count():
        print("      ⚠ Scholar CAPTCHA — 창에서 직접 풀어주세요(30초 대기)...")
        page.wait_for_timeout(30000)
    links = []
    for a in page.locator("div.gs_or_ggsm a").all()[:want]:
        href = a.get_attribute("href")
        if href and href.lower().endswith(".pdf"):
            links.append(href)
    return links


# ---------------------------------------------------------------------------
# 메인 수집 루프
# ---------------------------------------------------------------------------
def collect(drug, bcs, outdir, per_drug, email, mode, page, context,
            use_scholar, manifest) -> int:
    print(f"\n=== {drug}  (BCS Class {bcs}) ===")
    drug_dir = outdir / f"{slugify(drug)}_BCS-{bcs}"
    recs = search_candidates(drug, page_size=min(per_drug * 6, 100))
    print(f"    API 후보 {len(recs)}건 → pH 검증 + 다운로드...")

    saved = 0
    for rec in recs:
        if saved >= per_drug:
            break
        title = (rec.get("title") or "untitled").rstrip(".")
        year = rec.get("pubYear", "n.d.")
        pmid = rec.get("pmid") or rec.get("id", "")
        f12, f68 = check_ph(verification_text(rec))
        base = {
            "drug": drug, "bcs": bcs, "title": title, "year": year, "pmid": pmid,
            "doi": rec.get("doi", ""), "pmcid": rec.get("pmcid", ""),
            "open_access": rec.get("isOpenAccess", "N"),
            "ph_1_2": f12, "ph_6_8": f68, "source": "europepmc", "status": "",
        }
        if not passes_ph_filter(f12, f68, mode):
            base["status"] = "skipped_ph_filter"
            manifest.append(base)
            continue

        dest = drug_dir / f"{year}_{slugify(title, 60)}_{pmid}.pdf"
        if dest.exists():
            base["status"] = "already_exists"
            manifest.append(base)
            saved += 1
            continue

        ok = False
        for url in candidate_pdf_urls(rec, email):
            if save_via_requests(url, dest):
                ok = True
                break
            if page and save_via_browser(page, context, url, dest):
                ok = True
                break
        base["status"] = "downloaded" if ok else "no_OA_pdf"
        if ok:
            saved += 1
            print(f"    ✓ [pH1.2{'✓' if f12 else '·'} 6.8{'✓' if f68 else '·'}] {dest.name}")
        manifest.append(base)
        time.sleep(1)

    # Scholar 보강
    if use_scholar and page and saved < per_drug:
        for i, url in enumerate(scholar_pdf_links(page, drug, per_drug - saved)):
            dest = drug_dir / f"scholar_{slugify(drug)}_{i}.pdf"
            if save_via_requests(url, dest) or save_via_browser(page, context, url, dest):
                saved += 1
                manifest.append({
                    "drug": drug, "bcs": bcs, "title": dest.name, "year": "",
                    "pmid": "", "doi": "", "pmcid": "", "open_access": "?",
                    "ph_1_2": "", "ph_6_8": "", "source": "scholar",
                    "status": "downloaded",
                })
                print(f"    ✓ [scholar] {dest.name}")
            time.sleep(2)

    print(f"    → 저장 {saved}건")
    return saved


def main() -> None:
    ap = argparse.ArgumentParser(description="브라우저 기반 용출 문헌 PDF 수집기")
    ap.add_argument("--outdir", default=str(Path.home() / "dissolution_pdfs"))
    ap.add_argument("--per-drug", type=int, default=15)
    ap.add_argument("--classes", nargs="*", choices=["I", "II", "III", "IV"])
    ap.add_argument("--drugs", nargs="*")
    ap.add_argument("--require-ph", choices=["both", "any", "off"], default="both")
    ap.add_argument("--email", default="dwsynrnd@gmail.com")
    ap.add_argument("--headless", action="store_true", help="창 숨김(기본은 보임)")
    ap.add_argument("--no-browser", action="store_true",
                    help="Playwright 없이 HTTP 다운로드만")
    ap.add_argument("--scholar", action="store_true",
                    help="Google Scholar 보강(ToS·CAPTCHA 주의)")
    args = ap.parse_args()

    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    if args.drugs:
        lookup = {d: c for c, ds in BCS_MODEL_DRUGS.items() for d in ds}
        targets = [(d, lookup.get(d.lower(), "?")) for d in args.drugs]
    else:
        classes = args.classes or ["I", "II", "III", "IV"]
        targets = [(d, c) for c in classes for d in BCS_MODEL_DRUGS[c]]

    print(f"저장 위치 : {outdir}")
    print(f"대상      : {len(targets)}종 | 약물당 {args.per_drug}편 | pH:{args.require_ph}"
          f" | scholar:{args.scholar}")

    manifest: list[dict] = []
    total = 0

    use_browser = not args.no_browser
    if use_browser and sync_playwright is None:
        print("⚠ playwright 미설치 → HTTP 전용으로 진행 "
              "(pip install playwright && playwright install chromium)")
        use_browser = False

    if use_browser:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.headless)
            context = browser.new_context(
                accept_downloads=True, user_agent=HEADERS["User-Agent"]
            )
            page = context.new_page()
            for drug, bcs in targets:
                total += collect(drug, bcs, outdir, args.per_drug, args.email,
                                 args.require_ph, page, context, args.scholar, manifest)
            browser.close()
    else:
        for drug, bcs in targets:
            total += collect(drug, bcs, outdir, args.per_drug, args.email,
                             args.require_ph, None, None, args.scholar, manifest)

    csv_path = outdir / "manifest.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "drug", "bcs", "title", "year", "pmid", "doi", "pmcid",
            "open_access", "ph_1_2", "ph_6_8", "source", "status"])
        w.writeheader()
        w.writerows(manifest)

    n_dl = sum(1 for m in manifest if m["status"] == "downloaded")
    print(f"\n완료 ✅  PDF 저장 {total}편 (신규 {n_dl}편)")
    print(f"매니페스트 : {csv_path}")


if __name__ == "__main__":
    main()
