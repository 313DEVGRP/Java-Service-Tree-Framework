# result.md — claude-main / REQ-BACKEND-FUNC-01

대상: `/Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core` (읽기 전용 조회만 수행, 수정·빌드·테스트 없음)
근거: `tasks/req-backend-func-01/sources/endpoints_expanded.csv` · `inventory.json` · `.claude/skills/api-catalog/scripts/expand_inherit.py`

---

## 1. 누락 감사

추출기(`expand_inherit.py`)가 구조적으로 놓칠 수 있는 5개 지점을 소스 전수(`src/main/java` 하위 `*.java`)로 대조했다. **결론: 놓친 자체 선언 엔드포인트 0건.**

### 1-1. 점검 결과 요약

| # | 점검 항목 | 추출기 동작 | 소스 실측 | 누락 |
|---|---|---|---|---|
| A | 경로 배열 (`@GetMapping({"/a","/b"})`) | `q[0]` — **첫 경로만 채택** | 메서드 레벨 다중 경로 배열 **0건** | 없음 |
| B | 클래스 다중 경로 (`@RequestMapping({"/x","/y"})`) | `q[0]` — **첫 경로만 채택** | 클래스 레벨 경로 문자열 2개 이상 **0건** | 없음 |
| C | `@Controller`/`@RestController` 없는 매핑 클래스 | `isCtl` 거짓이면 행 미생성 | 해당 클래스 **2건** (아래 표) — 둘 다 상속 부모로서 `chain()` 경유 집계됨 | 없음 |
| D | 인터페이스 선언 매핑 | `CLS_RE` 가 `class` 만 매칭 → 인터페이스 미색인 | `@*Mapping` 보유 인터페이스 **8건** — 전부 OpenFeign **아웃바운드** 클라이언트 | 없음 (REST 표면 아님) |
| E | 파일당 클래스 2개 이상 | `CLS_RE.search` 가 첫 클래스만 | 해당 파일 **0건** | 없음 |

### 1-2. C 항목 — `@Controller` 없이 매핑을 가진 클래스 2건

| 파일:라인 | 클래스 | 매핑 수 | 처리 |
|---|---|---:|---|
| `com/arms/egovframework/javaservice/treeframework/controller/TreeAbstractController.java:176 외` | `TreeAbstractController` | 14 | 58개 자식이 상속 → 812행으로 전개 |
| `com/arms/api/globaltreemap/controller/TreeMapAbstractController.java:32,39,44,56,62,69,83,97,111` | `TreeMapAbstractController` | 9 | `GlobalTreeMapController` 1개가 상속 → 9행 |

`GlobalContentsTreeMapController`(`com/arms/api/globaltreemap/controller/GlobalContentsTreeMapController.java:12`)는 `ContentsTreeMapAbstractController` 를 상속하나, 부모 파일(`ContentsTreeMapAbstractController.java`) 본문에 `@*Mapping` 이 **0건**이고 자체 매핑도 0건이다 → 엔드포인트 0. 누락이 아니다.

### 1-3. D 항목 — 매핑 보유 인터페이스 8건 (전부 Feign, 인바운드 아님)

`com/arms/api/util/communicate/external/` : `EngineService` · `AggregationService` · `AiService` · `GlobalConfigService` · `MiddleProxyService` · `GotenbergClientService`
`com/arms/api/util/communicate/internal/` : `InternalService` · `TemplateInternalService`

Backend-Core 컨트롤러 중 **매핑을 선언한 인터페이스를 구현하는 것은 없다.**

### 1-4. 보강 대조 (수치 정합)

| 검사 | 결과 |
|---|---|
| 컨트롤러별 `@*Mapping` 원문 개수 vs CSV `자체` 행수 | **전 컨트롤러 불일치 0건** |
| 어노테이션 인자에 괄호 포함(정규식 조기 종료 위험) | 0건 |
| `HTTP=ANY` (RequestMethod 미지정 `@RequestMapping`) | 0건 |
| `path` 가 `base` prefix 로 시작하지 않는 행 | 0건 |
| 엔드포인트 보유 컨트롤러 중 base 미검출 | 0건 |
| `value=` + `name=` 동시 지정 (경로 오채택 위험) | 4건 — 전부 `q[0]` 이 올바른 경로 (`ResourceController.java:47,105` · `DashboardController.java:45,56`) |

### 1-5. 부수 관찰 (사실 기재)

- **경로 없는 메서드 매핑 11건** — `@GetMapping` 등에 경로 인자가 없어 전체경로 = 클래스 base. 예: `ReqStatusCalendarController.java:26` `getCalendarData`, `TemplateController` `listTemplates`, `SalaryController` `bulkUpdate` 등. 추출기가 base 로 채웠고 소스와 일치.
- **동일 (HTTP, 전체경로) 중복 2쌍** — 자식이 부모 매핑을 같은 경로로 재정의:
  - `ReqStateCategoryController.java:78` `DELETE /arms/reqStateCategory/removeNode.do` (`@Override`)
  - `ReqStateController.java:95` `PUT /arms/reqState/updateNode.do`
  → CSV 에 `자체` 1행 + `상속` 1행으로 2번 등장. 전개 합계 1181, distinct 1179.
- **동명·이경로 13건(재정의 아님)** — `WikiController`(11) · `ReqAddController`(2) · `ReqAddPureController`(1) 는 `getNode`/`addNode` 등 부모와 같은 메서드명을 쓰되 경로에 `/{changeReqTableName}` 세그먼트가 추가돼 부모 경로와 다르다. 메서드명 기준으로 재정의 판정하면 오탐이므로 **전체경로 기준으로 판정**해야 한다(아래 변환 코드 반영).
- **자체 엔드포인트 0개인 트리 상속 컨트롤러 31개** — `ReqReviewController` · `SenderController` · `*LogController` 계열 등. 이 컨트롤러들은 `자체` 행이 없으므로 basePath 가 자체 행에서 복원되지 않는다 → 상속 행의 `inheritedBy` 에 `클래스@basePath` 형태로 담아야 전체 경로가 복원된다(스펙 반영).

---

## 2. 컬럼 스펙

파일 1본: `tasks/req-backend-func-01/artifacts/backend-core_endpoints_flat.csv` (UTF-8 BOM, CRLF 없음, 콤마 구분)

| # | 컬럼 | 필수 | own 행 | inherited 행 |
|---:|---|---|---|---|
| 1 | `no` | | 1부터 연번 | 동일 |
| 2 | `kind` | | `own` | `inherited` |
| 3 | **`controllerClass`** | ✅ | 컨트롤러 클래스명 | **부모 추상 클래스명** (`TreeAbstractController` / `TreeMapAbstractController`) |
| 4 | **`package`** | ✅ | 선언 파일의 패키지 | 부모 클래스의 패키지 |
| 5 | **`endpoint`** | ✅ | `"<HTTP> <전체경로>"` | `"<HTTP> {basePath}<상대경로>"` |
| 6 | `httpMethod` | | GET/POST/PUT/DELETE | 동일 |
| 7 | `path` | | 전체경로 | `{basePath}` 플레이스홀더 + 상대경로 |
| 8 | `basePath` | | 클래스 레벨 `@RequestMapping` 값 | 공란 (상속 컨트롤러마다 다름 → 13번 컬럼) |
| 9 | `javaMethod` | | 핸들러 메서드명 | 부모 메서드명 |
| 10 | `sourceFile` | | `src/main/java` 기준 상대경로 | 부모 파일 경로 |
| 11 | `line` | | 어노테이션 줄번호 | 부모 파일 줄번호 |
| 12 | `inheritedByCount` | | 공란 | 상속 컨트롤러 수 (58 / 1) |
| 13 | `inheritedBy` | | 공란 | `클래스@basePath` 를 `;` 로 연결 |
| 14 | `note` | | 공란 | 자식이 같은 경로로 재정의한 경우 그 클래스명 |

### 규칙

- **자체 선언 1건 = 1행** (360행). 정렬: `controllerClass` → `path` → `httpMethod`.
- **상속분은 컨트롤러마다 반복하지 않는다.** 부모의 `(HTTP, 상대경로, javaMethod)` 조합당 **1행**만 두고, 상속 컨트롤러는 `inheritedBy` 에 열거 (23행).
- 상속 행의 구체 경로 복원: `inheritedBy` 의 `@` 뒤 basePath + `path` 의 `{basePath}` 치환.
- 도달 가능 총 인스턴스 = `own 행수 + Σ inheritedByCount` = 360 + 821 = **1181** (sources 와 일치).

---

## 3. 변환 코드

표준 라이브러리만 사용. `python3 flatten.py tasks/req-backend-func-01` 로 실행(인자 생략 시 동일 경로 기본값). 입력은 읽기만 한다.

```python
# -*- coding: utf-8 -*-
"""endpoints_expanded.csv + inventory.json -> 컨트롤러별 플랫 CSV 1본.

자체 선언 = 1건 1행. 상속분 = 부모 매핑 1행 + 상속 컨트롤러 열거(컨트롤러별 반복 없음).
표준 라이브러리만 사용. 입력 미수정(읽기 전용).

사용법: python3 flatten.py [tasks/req-backend-func-01]
"""
import csv, io, json, os, sys

TASK = sys.argv[1] if len(sys.argv) > 1 else 'tasks/req-backend-func-01'
SRC  = os.path.join(TASK, 'sources')
OUT  = os.path.join(TASK, 'artifacts', 'backend-core_endpoints_flat.csv')

HEADER = ['no', 'kind', 'controllerClass', 'package', 'endpoint', 'httpMethod',
          'path', 'basePath', 'javaMethod', 'sourceFile', 'line',
          'inheritedByCount', 'inheritedBy', 'note']

pkg_of = lambda f: f.rsplit('/', 1)[0].replace('/', '.') if '/' in f else ''

rows = list(csv.DictReader(
    io.open(os.path.join(SRC, 'endpoints_expanded.csv'), encoding='utf-8-sig')))
inv = json.load(io.open(os.path.join(SRC, 'inventory.json'),
                        encoding='utf-8'))['perController']
base_of = lambda c: inv.get(c, {}).get('base', '')

own_rows  = [r for r in rows if r['출처'] == '자체']
# 재정의 판정은 메서드명이 아니라 (컨트롤러, HTTP, 전체경로) 로 한다.
# WikiController 등이 부모와 같은 메서드명을 다른 경로로 쓰기 때문(감사 1-5 참조).
own_paths = set((r['controller'], r['HTTP'], r['path']) for r in own_rows)

out = []

# ── 1) 자체 선언: 1건 1행 ──────────────────────────────────────────────
for r in sorted(own_rows, key=lambda x: (x['controller'], x['path'], x['HTTP'])):
    out.append(['', 'own', r['controller'], pkg_of(r['선언파일']),
                '%s %s' % (r['HTTP'], r['path']), r['HTTP'], r['path'],
                base_of(r['controller']), r['javaMethod'],
                r['선언파일'], r['line'], '', '', ''])

# ── 2) 상속분: 부모 매핑 1행 + 상속 컨트롤러 열거 ──────────────────────
inh = {}
for r in rows:
    if r['출처'] == '자체':
        continue
    parent = r['출처'][r['출처'].index('(') + 1:-1]         # "상속(Xxx)" -> "Xxx"
    b   = base_of(r['controller'])
    rel = r['path'][len(b):] if b and r['path'].startswith(b) else r['path']
    e = inh.setdefault((parent, r['HTTP'], rel, r['javaMethod']),
                       {'ctls': set(), 'file': r['선언파일'], 'line': r['line']})
    e['ctls'].add(r['controller'])

for (parent, http, rel, jm), e in sorted(
        inh.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][1])):
    ctls = sorted(e['ctls'])
    ov   = [c for c in ctls if (c, http, base_of(c) + rel) in own_paths]
    out.append(['', 'inherited', parent, pkg_of(e['file']),
                '%s {basePath}%s' % (http, rel), http, '{basePath}%s' % rel, '',
                jm, e['file'], e['line'], len(ctls),
                ';'.join('%s@%s' % (c, base_of(c)) for c in ctls),
                ('자체 선언으로 재정의: ' + ';'.join(ov)) if ov else ''])

for i, r in enumerate(out, 1):
    r[0] = i

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    w.writerows(out)

n_own = sum(1 for r in out if r[1] == 'own')
print('%s\n총 %d행 = 자체 %d + 상속 부모매핑 %d | 자체 선언 컨트롤러 %d | '
      '상속 전개 실인스턴스 %d | 도달 가능 합계 %d'
      % (OUT, len(out), n_own, len(out) - n_own,
         len(set(r[2] for r in out if r[1] == 'own')),
         sum(int(r[11]) for r in out if r[1] == 'inherited'),
         n_own + sum(int(r[11]) for r in out if r[1] == 'inherited')))
```

드라이런 검증 완료 (스크래치패드 `.../scratchpad/dry/` 에서 실행, `tasks/`·저장소 미접촉). 출력 요약:

```
총 383행 = 자체 360 + 상속 부모매핑 23 | 자체 선언 컨트롤러 58 |
상속 전개 실인스턴스 821 | 도달 가능 합계 1181
```

---

## 4. 예상 행수

| 구분 | 행수 | 비고 |
|---|---:|---|
| 헤더 | 1 | |
| `kind=own` | **360** | 자체 선언 엔드포인트 1건 1행 (컨트롤러 58개) |
| `kind=inherited` (`TreeAbstractController`) | **14** | 각 행 `inheritedByCount=58` → 812 인스턴스 |
| `kind=inherited` (`TreeMapAbstractController`) | **9** | 각 행 `inheritedByCount=1` (`GlobalTreeMapController`) → 9 인스턴스 |
| **데이터 행 합계** | **383** | |
| (참고) 도달 가능 엔드포인트 인스턴스 | 1181 | distinct 1179 — 재정의 2건 중복 |

엔드포인트 0개 컨트롤러 3개(`ErrorControllerAdvice` · `ReportExceptionHandler` · `GlobalContentsTreeMapController`)는 행 없음 → CSV 에 등장하는 컨트롤러는 89개 (inventory 92 - 3).

---

## 5. Verification Checklist

Orchestrator 가 CSV 생성 후 실행할 것.

| # | 항목 | 검증 명령/기준 | 기대값 |
|---|---|---|---|
| 1 | 파일 존재 | `ls tasks/req-backend-func-01/artifacts/backend-core_endpoints_flat.csv` | 존재 |
| 2 | 헤더 3필수 | `head -1` 에 `controllerClass`·`endpoint`·`package` 포함 | 포함 |
| 3 | 총 행수 | `python3 -c "import csv,io;print(len(list(csv.DictReader(io.open(P,encoding='utf-8-sig')))))"` | **383** |
| 4 | own 행수 | `kind=='own'` 카운트 | **360** |
| 5 | inherited 행수 | `kind=='inherited'` 카운트 | **23** |
| 6 | 필수 3필드 공란 | 세 컬럼 중 하나라도 빈 행 카운트 | **0** |
| 7 | 상속 반복 없음 | `(controllerClass, endpoint)` 중복 카운트, kind=inherited | **0** |
| 8 | 상속 전개 합 | `Σ inheritedByCount` | **821** |
| 9 | 도달 가능 합계 | own(360) + 821 | **1181** = `inventory.totalEndpointInstances` |
| 10 | 자체 행 ↔ sources 정합 | own 행의 `(HTTP, path, controller)` 집합 == `endpoints_expanded.csv` 의 `출처='자체'` 집합 | 완전 일치 |
| 11 | 재정의 note | `note` 비어있지 않은 행 | **2** (`ReqStateCategoryController` · `ReqStateController`) |
| 12 | 창작 없음 | CSV 의 모든 `(HTTP, path)` 가 sources 에서 유도 가능 | 100% |
| 13 | 평가문 부재 | 비평·권고 문구 없음 (`note` 는 사실 기재만) | 없음 |
| 14 | 저장소 무변경 | `git -C Java-Service-Tree-Framework-Backend-Core status --porcelain` | 빈 출력 |

---

## 6. Issues / Caveats

| # | 내용 |
|---|---|
| 1 | **기준값 불일치 (+1).** `task.md` Acceptance Criteria 와 `SKILL.md` 기준표는 자체 선언 **359** / 합계 **1180** (distinct 1178) 이나, `sources/` 추출물 실측은 자체 **360** / 합계 **1181** (distinct 1179) 이다. 컨트롤러 92 · 상속 전개 821 은 일치. 이전 추출물이 남아있지 않아 어느 엔드포인트가 증분인지 특정 불가. `task.md` constraints 가 "수치 정본은 `sources/`" 로 규정하므로 **360/1181 을 채택**했다. Acceptance Criteria 의 "359" 문구는 Orchestrator 판단 필요. |
| 2 | **`inheritedBy` 는 한 셀에 다중 값** (최장 2,640자, `;` 구분). api-catalog 스킬의 long/tidy 원칙(한 칸에 값 하나)과 어긋나지만, 요구사항 ②("상속분을 컨트롤러마다 반복 금지")가 우선한다. 두 요구는 동시 충족 불가 — 요구사항 쪽을 따랐다. Excel 셀 한도(32,767자) 내. |
| 3 | **상속 행의 `basePath` 는 공란**이고 구체 경로는 `{basePath}` 플레이스홀더다. 자체 엔드포인트 0개인 트리 컨트롤러 31개가 있어 basePath 를 자체 행에서 복원할 수 없으므로 `inheritedBy` 를 `클래스@basePath` 형식으로 정했다. 플레이스홀더를 싫어하면 상속분을 컨트롤러별로 펼쳐야 하는데 그건 요구사항 ② 위반. |
| 4 | **중복 2건은 의도적으로 양쪽에 남는다.** `ReqStateCategoryController` / `ReqStateController` 는 own 행 1개 + 부모 상속 행의 `inheritedBy` 목록에도 포함된다. `note` 로 표시했다. 상속 목록에서 빼면 `inheritedByCount` 가 58/57 로 갈려 sources 의 821 과 어긋난다. |
| 5 | **추출기 한계 승계.** 정적 분석 전용 — 리플렉션·동적 등록 핸들러는 범위 밖. 또한 게이트웨이(Middle-Proxy) 가 부여하는 외부 노출 경로는 소스에 없으므로 이 CSV 의 경로는 **Backend-Core 내부 경로**다. |
| 6 | **미검증.** `inventory.json` 의 `base` 값 자체는 추출기 산출물을 그대로 신뢰했다. 다만 "own 행의 path 가 전부 자기 base 로 시작"(0건 불일치) 과 "컨트롤러별 매핑 개수 원문 대조"(0건 불일치) 로 간접 확인했다. |
| 7 | 감사·드라이런 모두 읽기 전용으로 수행. 스크립트 시험 실행은 세션 스크래치패드(`/private/tmp/claude-501/.../scratchpad/`)에서만 했고 저장소·`tasks/`·엑셀에 파일을 쓰지 않았다. |
