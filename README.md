# 약물별 pH buffer 용출 문헌 PDF 자동 수집기

BCS(생물약제학적 분류체계) 모델 약물에 대해 **"pH / buffer 에 따른 용출
(dissolution / drug release)"** 관련 논문을, **합법적인 오픈액세스(OA) 경로**로만
검색·다운로드하여 **PC 로컬 폴더에 자동 저장**합니다.

## ⚖️ 사용 경로 (저작권 안전)

| 순서 | 서비스 | 역할 |
|------|--------|------|
| 1 | **Europe PMC** | 논문 검색 + OA 전문 PDF |
| 2 | **Unpaywall** | DOI 기반 합법 OA PDF 탐색 |
| 3 | **NCBI PMC** | PMCID 기반 OA PDF |

- **SCI-Hub 등 불법 배포 사이트는 사용하지 않습니다.**
- OA(무료 공개)로 확인된 PDF만 내려받습니다.
- 페이월(유료) 논문은 PDF 없이 **서지정보만 `manifest.csv`** 에 기록됩니다.
  → 이 목록으로 소속 기관 도서관/구독을 통해 합법적으로 원문을 받으세요.

## 🧪 pH buffer 검증

각 논문이 **pH 1.2 와 pH 6.8 용출 데이터를 실제로 담고 있는지** 초록 + OA 전문
텍스트에서 검증한 뒤에만 다운로드합니다 (`--require-ph` 로 조절).

- `both` (기본): pH 1.2 **AND** pH 6.8 둘 다 확인된 논문만
- `any`: 둘 중 하나라도
- `off`: 검증 끔

검출 키워드: `pH 1.2`, `0.1 N HCl`, `simulated gastric fluid(SGF)` ↔
`pH 6.8`, `phosphate buffer 6.8`, `simulated intestinal fluid(SIF)`.

## 🚀 설치 & 실행 (본인 PC에서)

```bash
# 1) 의존성 설치
pip install requests

# 2) 기본 실행 (BCS 전체 104종, 약물당 8편, pH 1.2&6.8 필수)
python download_dissolution_pdfs.py

# 3) 옵션 예시
python download_dissolution_pdfs.py --outdir "D:/논문/용출" --per-drug 10
python download_dissolution_pdfs.py --classes II --per-drug 15     # Class II만
python download_dissolution_pdfs.py --drugs ibuprofen ketoprofen --require-ph any
```

> ⚠️ 이 저장소가 돌아가는 클라우드 환경은 네트워크가 차단(403)되어 있어
> **다운로드는 반드시 본인 PC에서** 실행해야 합니다.

## ⚙️ 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--outdir` | `~/dissolution_pdfs` | 저장 폴더 |
| `--per-drug` | `8` | 약물당 최대 PDF 수 |
| `--classes` | (전체) | 대상 BCS 클래스 (`I II III IV`) |
| `--drugs` | (전체) | 대상 약물 직접 지정 |
| `--require-ph` | `both` | pH 1.2/6.8 필터 (`both`/`any`/`off`) |
| `--email` | `dwsynrnd@gmail.com` | Unpaywall API 정책상 필요한 이메일 |

## ⭐ 바로 받는 큐레이션 카탈로그 (`oa_catalog.csv` + `download_from_catalog.py`)

이미 **검증된 OA 논문 45편**(17개 약물, pH 1.2 / 6.8 용출 데이터 확인)을
`oa_catalog.csv` 에 정리해 두었습니다. 검색 단계 없이 바로 PDF만 받으려면:

```bash
pip install requests
python download_from_catalog.py                 # ~/dissolution_pdfs 에 저장
python download_from_catalog.py --outdir "D:/논문/용출"
```

각 줄에 약물·BCS 클래스·논문 제목·PMCID·PMC 링크·pH 1.2/6.8 여부·비고가 들어
있습니다. 표만 보고 싶으면 `oa_catalog.csv` 를 엑셀로 열어보세요.

## 🌐 브라우저 자동화 버전 (`browser_collect.py`)

데이터 최대화를 위한 하이브리드 수집기. **API 발굴 → pH 검증 → 일반 다운로드,
막히면 실제 Chrome(Playwright)이 페이지에 들어가 PDF를 직접 받음**(headed=창 보임).

```bash
pip install playwright requests
playwright install chromium          # 브라우저 1회 설치

python browser_collect.py                          # 전체, 창 보임
python browser_collect.py --classes II --per-drug 20
python browser_collect.py --headless               # 창 숨김
python browser_collect.py --no-browser             # HTTP 다운로드만
python browser_collect.py --scholar                # Google Scholar 보강(주의)
```

- `--scholar`: Google Scholar를 브라우저로 검색해 `[PDF]` 직링크를 추가 확보합니다.
  Scholar는 자동 검색에 CAPTCHA를 띄울 수 있어 기본 비활성이며, 뜨면 보이는 창에서
  직접 풀면 진행됩니다. (Scholar ToS 유의, 요청 간 지연 적용)
- API 버전(`download_dissolution_pdfs.py`)이 더 가볍고 안정적이며, 브라우저 버전은
  JS/Cloudflare 뒤에 있는 OA PDF까지 추가로 잡는 용도입니다.

## 📁 저장 구조

```
dissolution_pdfs/
├── ibuprofen_BCS-II/
│   ├── 2019_Effect_of_pH_on_dissolution_..._31234567.pdf
│   └── ...
├── ketoprofen_BCS-II/
├── ...
└── manifest.csv        # 전체 서지정보 (다운로드/페이월/실패 상태 포함)
```

## 💊 기본 대상 약물 (BCS 분류별, 총 104종)

각 클래스 20종 이상. 전체 목록은 `download_dissolution_pdfs.py` 의
`BCS_MODEL_DRUGS` 참고.

- **Class I** (고용해도·고투과) — 24종: metoprolol, propranolol, diltiazem,
  verapamil, metformin, captopril, enalapril, labetalol, levodopa, theophylline …
- **Class II** (저용해도·고투과, *pH 의존 용출 핵심*) — 32종: ibuprofen,
  ketoprofen, indomethacin, naproxen, diclofenac, piroxicam, carbamazepine,
  nifedipine, glibenclamide, ketoconazole, itraconazole, atorvastatin …
- **Class III** (고용해도·저투과) — 24종: atenolol, ranitidine, cimetidine,
  famotidine, acyclovir, amoxicillin, lisinopril, gabapentin …
- **Class IV** (저용해도·저투과) — 24종: furosemide, hydrochlorothiazide,
  chlorthalidone, sulfasalazine, nitrofurantoin, methotrexate, ritonavir …

> ⚠️ BCS 분류는 문헌(WHO/Lindenberg 2004, Takagi 2006 등)에 따라 다를 수 있고,
> 염·용량·실험조건에 따라 경계 약물의 분류가 갈릴 수 있습니다.

## 📝 비고

- 검색은 피인용 수 내림차순(`CITED desc`)으로 정렬해 신뢰도 높은 문헌을 우선합니다.
- 동일 파일이 이미 있으면 건너뜁니다(재실행 안전).
- 서버 과부하 방지를 위해 요청 사이에 지연을 둡니다.
