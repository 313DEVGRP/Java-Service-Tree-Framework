---
name: api-catalog
description: >-
  A-RMS 의 Java/Spring 저장소 6곳(Backend-Core · Engine-Fire · Middle-Proxy · AI · Global-Config · Broker-Hub)에서 REST API 표면을 전수 추출해
  엔드포인트 카탈로그(PDF + long CSV)를 만드는 도구와 규약.
  엔드포인트 목록, 각 엔드포인트가 부르는 서비스 메서드, 메서드→메서드 호출 체인, OpenFeign 외부 호출까지 기계로 뽑는다.
  Backend-Core 는 컨트롤러 92개 중 58개가 TreeAbstractController 를 상속해 엔드포인트가 선언 360개 → 실제 1,181개로 늘어나므로
  grep 으로 @*Mapping 을 세면 3배 틀린다. Middle-Proxy 는 Feign 인터페이스 이름이 한글이라 ASCII 전제 정규식이 통째로 놓친다.
  "API 목록", "엔드포인트가 뭐가 있나", "이 API 가 무슨 서비스 메서드를 부르나", "어떤 Feign 을 호출하나",
  "호출 체인", "컨트롤러-서비스 연결 관계" 같은 요청이 오거나 이 저장소들의 API 표면을 세거나 추적해야 하면,
  스킬 이름을 직접 부르지 않아도 이 스킬을 먼저 펼칠 것. 신규 분석뿐 아니라 기존 카탈로그 갱신·수치 검증에도 쓴다.
---

# API 카탈로그 (Java/Spring 저장소 공용)

## 이 스킬이 서는 자리

대상 저장소의 `docs/ai/01~13`이 **스택·도메인·계약의 단일 출처**다. 이 스킬은 그걸 베껴 적지 않는다.
담당하는 것은 **"API 표면이 실제로 몇 개이고 각각 무엇을 부르는가"를 기계로 뽑는 일**과, 그 과정에서 조용히 틀리는 지점들이다.

산출물은 **레퍼런스**다 — 구조 비평·결함 지적·개선 권고는 이 작업의 산출물이 아니다.
"분석"이라는 말에 끌려 평가문을 쓰지 말 것. **표를 채우는 작업이다.**

## 실행

저장소 루트에서 실행한다. **대상 저장소와 출력 경로는 환경변수로 지정한다.**

```bash
S=.claude/skills/api-catalog/scripts
export CATALOG_REPO=Java-Service-Tree-Framework-Backend-Core
#  다른 대상: -Engine-Fire · -Middle-Proxy · -AI · -Global-Config · -Broker-Hub
export CATALOG_TASK=tasks/<task>
mkdir -p $CATALOG_TASK/sources $CATALOG_TASK/artifacts

python $S/expand_inherit.py   # sources/endpoints_expanded.csv · feign_calls.csv · inventory.json
python $S/call_chain.py       # sources/call_chains.json   (메서드→메서드, 최대 4단계)
python $S/api_catalog.py      # artifacts/_catalog.json    (엔드포인트별 호출·Feign)
python $S/csv_long.py         # artifacts/*.csv            (long 형식)
python $S/api_doc.py          # artifacts/*.md

python $S/discover.py         # (선택) 대상 저장소 자동 탐지 결과만 보기
python $S/routes.py           # (선택) 게이트웨이 라우트 표 — 아래 참조
bash   $S/run_all.sh <task>   # 위 5단계를 탐지된 전 저장소에 한 번에
```

### 사람이 훑는 형태 — 플랫 CSV · 엑셀 · 프론트 대조 (2026-09-21 추가)

위 5단계가 PDF·long CSV 를 낸다면, 아래는 **엑셀에서 바로 필터해 보는 표**를 낸다.

```bash
python $S/endpoints_flat.py   # artifacts/<repo>_endpoints_flat.csv + _by-controller.xlsx
                              #   자체 선언 1건=1행, 상속분은 부모 매핑 1행 + 상속 컨트롤러 열거
                              #   provider 컬럼: 자체 선언 / 상속(TreeAbstractController) …

export CATALOG_FRONT_REPO=Java-Service-Tree-Framework-Frontend-Web   # 기본값
python $S/front_calls.py      # artifacts/frontend-web_api-calls_flat.csv
                              #   arms/js·backoffice/js 의 $.ajax·$.get·fetch + 플러그인 config url
                              #   문자열 조합 URL 을 완성형으로 복원, menuname 을 네비게이션에서 매핑

export CATALOG_BE_CSV=<위 endpoints_flat.csv>
export CATALOG_FE_CSV=<위 api-calls_flat.csv>
python $S/fe_be_gaps.py       # artifacts/fe-be_mapping-gaps.csv — 매핑 안 되는 것만 양방향

python $S/sheets_xlsx.py <csv> <키컬럼|-> <out.xlsx> [요약컬럼]  # CSV → xlsx (`-` = 시트 분할 없음)
```

**메뉴명은 추정하지 않는다.** `front_calls.py` 는 ① `page-navigation.html`·`page-sidebar.html` 의
`page=` 링크 텍스트(한글 메뉴 라벨) → ② 없으면 `html/<page>/content-header.html` 의 breadcrumb·h3
(js/{page}.js ↔ html/{page}/ 1:1 규칙) → ③ 공통 모듈 → ④ 페이지 키 순으로 해석하고,
출처를 `menusource` 컬럼에 남긴다. 한 이름이 여러 페이지를 덮으면(여러 화면이 같은 헤더를 씀)
`이름 (page)` 로 구분한다. `fe_be_gaps.py` 의 `BE→호출없음` 행은 같은 basePath 를 실제로 호출하는
메뉴를 건수 순으로 전부 적고, 하나도 없으면 `(호출 메뉴 없음) <basePath>` 로 둔다.

`CATALOG_BE_CSV` 를 주면 `front_calls.py` 도 `provider` 컬럼을 채운다 — 프론트 호출이
Tree CRUD(`addNode.do`·`getNode.do` 등 23종)를 부르는지 백엔드 카탈로그의 `kind=inherited` 행에서
자동 판별한다(`tree_actions.py`). 액션 목록을 손으로 적지 말 것 — 카탈로그가 정본이다.

- `fe_be_gaps.py` 는 게이트웨이 규칙(`/{권한}/{서비스}/**` → 내부 경로)을 코드에 담고 있고,
  서비스 세그먼트가 `api` 가 아닌 호출(`ai`·`yml`·`search`·`hub`)은 Backend-Core 대조 대상이 아니라 제외한다.
  **`api` 여도 Backend-Core 가 아닌 구간이 있다** — Middle-Proxy 가 `/auth-user/api/aichat/**` 와
  `/auth-user/api/arms/reqAdd/(sync|async)/**` 를 자기 컨트롤러로 직접 처리한다. 이 판별은 Middle-Proxy 소스를
  읽어 자동으로 하고 해당 행 `note` 에 남긴다.
- **`provider` 는 세 산출물이 같은 어휘를 쓴다** — `상속(<부모클래스>)` / `자체 선언`(백엔드) ·
  `일반 호출`(프론트) / `프론트 호출`(미매핑). 상속분은 TreeFramework 공통 CRUD 라
  프론트가 안 부르거나(백엔드 쪽) 도메인 API 가 아니거나(프론트 쪽) 한 것이 정상이다.
- `sheets_xlsx.py` 는 키컬럼에 `-` 를 주면 한 장(`data`)에 전부 담는다(기본 산출 형태).
  `provider` 컬럼이 있으면 상속 행을 회색으로 깔고, 요약컬럼을 주면 `_요약` 에 교차 집계를 만든다.
  엑셀 시트명 제약(31자·`[]:*?/\` 금지)은 자동 치환하고 원래 값은 `_목차` 에 남긴다.

PDF 는 `python-markdown → HTML → 크로미엄 헤드리스` 로 낸다 (pandoc·wkhtmltopdf 없음).
**브라우저 경로와 폰트는 OS 마다 다르다 — 쓰기 전에 실제 존재를 확인할 것.**

macOS (2026-09-21 실측: Edge 없음, Chrome 있음):

```bash
python3 $S/render.py "$CATALOG_TASK/artifacts/<name>.md" /tmp/x.html "제목" "부제" "v0.1"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-pdf-header-footer --print-to-pdf="$PWD/$CATALOG_TASK/artifacts/<name>.pdf" /tmp/x.html
rm -f /tmp/x.html "$CATALOG_TASK/artifacts/<name>.md" "$CATALOG_TASK/artifacts/_catalog.json"
```

Windows(git-bash) — Edge 가 있는 환경:

```bash
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu \
  --no-pdf-header-footer --print-to-pdf="$(cygpath -w "$PWD/$CATALOG_TASK/artifacts/<name>.pdf")" \
  "$(cygpath -w /tmp/x.html)"
```

생성 후 `%PDF` 헤더 · 쪽수 · 한글 폰트 임베딩(Windows `MalgunGothic` / macOS `AppleSDGothicNeo`)을 확인하고 중간 HTML 을 지운다.
환경변수를 안 주면 Backend-Core / `tasks/api-catalog` 가 기본값이다.

## 저장소별 기준값 — 크게 어긋나면 소스가 아니라 추출기를 의심한다

2026-09-21 실측(같은 날 재측정 — 함정 7 수정·소스 드리프트 반영). 소스가 조금 바뀌어 숫자가 몇 개 움직이는 건 정상이지만,
**0 이 무더기로 나오거나 자릿수가 바뀌면 추출기가 깨진 것이다.**

| 저장소 | 컨트롤러 | 자체 선언 | 상속 전개 | 합계 | Feign | 체인 노드 | CSV 행 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Backend-Core** | 92 | 360 | **821** | **1,181** (distinct 1,179) | 8 | 2,155 | 2,168 |
| **Engine-Fire** | 45 | 162 | 0 | 162 | 5 | 532 | 534 |
| **Middle-Proxy** | 16 | 112 | 0 | 112 | 3 | 494 | 498 |
| **AI** | 18 | 43 | 0 | 43 | 4 | 128 | 138 |
| **Global-Config** | 4 | 11 | 0 | 11 | 2 | 21 | 27 |
| **Broker-Hub** | 7 | 5 | 0 | 5 | 2 | 8 | 9 |

**상속 전개는 6곳 중 Backend-Core 에만 있다** — `TreeAbstractController` 14개 × 58 + `TreeMapAbstractController` 9개 × 1.
나머지 다섯 저장소는 추상 컨트롤러가 없어 "선언 = 실제"이고, 문서에서 §2 절이 자동으로 빠진다.

## 저장소별로 다른 점

| 저장소 | 특징 | 주의 |
|---|---|---|
| **Backend-Core** | Spring MVC + egovframework TreeFramework 상속. **6곳 중 유일하게 상속 전개가 있다** | 상속을 빼먹으면 엔드포인트가 3배 틀린다. `@PostConstruct` 에서 `setTreeService(...)` 로 도메인 빈을 꽂는다. Feign 8개 중 2개(`loopback`·`template-loopback`)가 **자기 자신**을 부른다 |
| **Middle-Proxy** | WebFlux + Spring Cloud Gateway. **Feign 인터페이스 이름이 한글** (`백엔드코어통신기`·`엔진통신기`·`내부통신기`) | 정규식이 `[A-Z]` 로만 타입을 잡으면 **Feign 이 통째로 0건**이 된다(함정 6). 이 추출기는 **로컬 핸들러만** 세고 게이트웨이 라우트는 못 본다 |
| **Engine-Fire** | Spring MVC, 추상 컨트롤러 없음 | Feign 이름이 `backendCoreReportPerformance` 처럼 camelCase 다 |
| **AI** | Spring MVC | Feign 4개(`backend-core`·`engine-fire`·`tts-engine`·`dwrClient`) |
| **Global-Config** | 규모가 작다 (엔드포인트 11에 체인 노드 21) | Feign 2개 모두 실제 호출됨 |
| **Broker-Hub** | **가장 작다** — 컨트롤러 7개에 엔드포인트 5개뿐 | 컨트롤러 수보다 엔드포인트가 적다. Feign 2개 선언돼 있으나 **호출 노드 0** — 실제 미사용인지 확인이 필요하다 |

## 조용히 틀리는 6곳 — 전부 한 번씩 밟았고 지금은 고쳐져 있다

**공통점: 예외를 던지지 않고 0이나 빈칸으로 나온다.** 스크립트를 고칠 때 되살리지 말 것.

| # | 함정 | 증상 | 처치 |
|---|---|---|---|
| 1 | 메서드 본문 시작을 "시그니처 뒤 첫 `{`" 로 잡음 | 파라미터의 `@Validated({AddNode.class})` 에 걸려 본문을 `{AddNode.class}` 로 읽음 | 파라미터 괄호를 짝 맞춰 닫은 뒤 본문 `{` 를 찾는다 (`body()`) |
| 2 | 시그니처 정규식이 `public\s+` 를 요구 | **인터페이스 메서드엔 수식어가 없다** → Feign 메서드 목록이 비고 "호출자 0" 이 무더기 | `(?:public\|protected\|private\|default\s+)?` |
| 3 | 1홉만 탐색 | 서비스가 같은 클래스 private 메서드를 거쳐 Feign 을 부르면 끊김 | 로컬 메서드를 **노드로 만들지 않고 투과**해 따라가고 `via` 에 경로를 남긴다 |
| 4 | 주입 필드를 자기 클래스에서만 수집 | 부모에 `protected` 로 선언된 필드를 놓침 (`GlobalTreeMapController` 는 자체 필드 0개) | 상속 체인을 올라가 필드를 병합한다 |
| 5 | 필드 타입 패턴 `[A-Z]\w+` | `private T treeService;` 의 **단일 대문자 제네릭**을 놓침 | `\w*` 로 완화 |
| 6 | 타입이 ASCII 로 시작한다고 가정 | **Middle-Proxy 의 한글 Feign 인터페이스**를 통째로 놓쳐 Feign 0건 | `((?:[A-Z]\|[가-힣])\w*)` |
| 7 | 경로는 `/` 로 시작하거나 `/` 를 안 갖는다고 가정 | `@GetMapping("getNodes.do/{id}")` 같은 **선행 슬래시 없는 상대 경로**를 버려 path 가 빈 값 → basePath 단독 행으로 조용히 둔갑. 행 수는 그대로라 개수 검증으로 안 잡힌다(Backend-Core 4건) | `expand_inherit.py` 필터에서 `'/' not in x` 제거 — `call_chain.py`·`api_catalog.py` 와 동일 조건으로 통일 (2026-09-21) |

## 설계 규칙 — 깨뜨리면 문서가 스스로와 어긋난다

- **수치를 문장에 박지 않는다.** 생성 시점에 집계하게 한다. 한 번 고치면 반드시 어딘가 옛 숫자가 남는다.
- **표를 손으로 적지 않는다.** 상속 14개 표를 메서드 이름에서 유추해 적었더니
  `getNodesWithoutRoot`·`getMonitor` 가 실제로는 **둘 다 `treeService.getChildNode`** 를 불러 틀렸다.
  지금은 원문에서 생성한다.
- **엔드포인트 표·호출 체인·CSV 를 `call_chains.json` 한 원천에서 유도한다.** 따로 계산하면 같은 엔드포인트가 세 곳에서 다른 값을 갖는다.
- **CSV 는 long(tidy)** — 호출 1건 = 1행, 한 칸에 값 하나.
  wide 로 내면 한 칸에 값이 여러 개 붙어 필터·피벗이 안 된다(실제로 146개 셀이 그랬다).
  사람이 훑는 건 PDF, 기계·엑셀 처리는 CSV 로 역할을 나눈다.
- **정규식이 든 코드는 파일에 직접 쓴다.** bash heredoc 을 거치면 `\b` 가 백스페이스(0x08)로 박혀 매칭이 전부 실패한다.
  사고가 의심되면 스크립트를 제어문자로 스캔한다.

## 산출 문서 구성

| 절 | 내용 |
|---|---|
| §2 | 상속 공통 매핑 — 1회만 싣고 상속 컨트롤러를 나열. **상속이 없는 저장소에선 자동으로 빠진다** |
| §3 | 자체 선언 엔드포인트 — `HTTP / 경로 / 컨트롤러 메서드 / line / 호출 / Feign` |
| §4 | 호출 체인 — 고정폭 트리(`├─ └─ │`), `→ Feign[name]`, `via x→y` |
| §5 | Feign 클라이언트 전수 |
| §6 | 동반 CSV 읽는 법 |
| §7 | 추출 한계 |

## 게이트웨이 라우트 (선택)

프론트가 부르는 **외부 경로**(`/auth-user/api/...`)와 저장소의 **내부 경로**(`/arms/...`)는 다르다.
변환 규칙은 게이트웨이 config 에 있고 **소스에는 없다.** 보려면 그 내용을 파일로 떨궈 둔다.

```
_local/gateway-routes.yml      ← 여기에 두면 읽는다 (.yaml / .json 도 가능)
CATALOG_ROUTES=<경로>          ← 다른 위치를 쓸 때
```

config 의 `spring.cloud.gateway.routes` 부분을 **그대로 붙여넣으면 된다.**
상위 `spring:` 키가 있어도 없어도 되고 들여쓰기도 그대로 둬도 된다. 형식만 보이면 이렇다.

```yaml
      routes:
        - id: <아무 이름>
          uri: http://127.0.0.1:<포트>      # 또는 lb://<서비스명>
          predicates:
            - Path=/auth-user/api/**
          filters:
            - RewritePath=/auth-user/api/(?<path>.*), /$\{path}
```

```bash
python $S/routes.py          # 외부 경로 → 내부 경로 → 수신 저장소 + 포트 매핑
python $S/routes.py --json   # 기계용
```

**파일이 없으면 안내만 출력하고 끝난다** — 나머지 파이프라인은 영향받지 않는다.

이 도구는 라우트를 카탈로그 문서에 싣지 않는다. 표가 필요하면 위 명령을 직접 돌린다.
라우트와 실제 엔드포인트를 맞대보면 **어디에도 도달하지 않는 라우트**가 드러난다
(예: `/auth-manager/**` → `/manager/**` 는 매칭 엔드포인트 0건). 한쪽만 봐선 안 보이는 종류다.

## 알려진 한계

- **정적 분석 전용.** 리플렉션·동적 프록시·SpEL 경유 호출은 안 잡힌다. "호출자 0"은 **정적 참조 0**을 뜻한다.
- **깊이 상한 4단계**, 같은 `(클래스.메서드)`를 두 번 밟지 않는다. 더 깊거나 순환하는 경로는 잘린다.
- **조건 분기를 반영하지 않는다.** 정적으로 도달 가능한 것을 모두 싣는다 — 한 번의 호출에서 전부 실행되지는 않는다.
- **게이트웨이 라우팅은 소스에 없다** — Config Server 가 외부 저장소에서 받아 주입한다. 추출기는 각 저장소의 **로컬 핸들러만** 센다. 보완 방법은 아래 참조.

## 하지 말 것

- 대상 저장소·엑셀 수정 (읽기 전용)
- CSV·JSON 에 없는 엔드포인트를 지어내기 — 수치는 `sources/` 가 정본이고 목록을 새로 열거하지 않는다
- 구조 비평·결함 지적·개선 권고를 카탈로그에 섞기
- 확인 못 한 것을 단정 — "미검증" 으로 남긴다
