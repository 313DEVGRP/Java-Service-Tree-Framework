# Backend-Core API 카탈로그 생성기

`REQ-BACKEND-FUNC-01` 산출물(엔드포인트 카탈로그 PDF + long CSV)을 만드는 정적 추출 스크립트.
**저장소 루트에서 실행한다.** 대상은 `Java-Service-Tree-Framework-Backend-Core`.

## 실행 순서

```bash
T=tasks/req-backend-func-01
mkdir -p $T/sources $T/artifacts
D=_shared/tools/backend-api-catalog

python $D/expand_inherit.py   # sources/endpoints_expanded.csv · feign_calls.csv · inventory.json
python $D/call_chain.py       # sources/call_chains.json   (메서드→메서드 체인, 최대 4단계)
python $D/api_catalog.py      # artifacts/_catalog.json    (엔드포인트별 호출·Feign)
python $D/csv_long.py         # artifacts/*.csv            (long 형식, 호출 1건 = 1행)
python $D/api_doc.py          # artifacts/*.md
python $D/render.py "$T/artifacts/<name>.md" /tmp/x.html "제목" "부제" "v0.7"
"<Edge 경로>" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$(cygpath -w "$PWD/$T/artifacts/<name>.pdf")" "$(cygpath -w /tmp/x.html)"
rm -f /tmp/x.html $T/artifacts/<name>.md $T/artifacts/_catalog.json
```

`OUT` / `ROOT` 상수는 각 스크립트 상단에 있다. 작업 폴더명이 바뀌면 거기만 고친다.

## 산출 기준값 (2026-09-21 실측)

| 항목 | 값 |
|---|---|
| 컨트롤러 | 92 (엔드포인트 보유 89) |
| 자체 선언 엔드포인트 | 359 |
| 상속 전개 | 821 = `TreeAbstractController` 58×14 + `TreeMapAbstractController` 1×9 |
| 도달 가능 합계 / distinct 라우트 | 1,180 / 1,178 (오버라이드 2건 중복) |
| Feign 클라이언트 | 8 · 메서드 171 |
| 호출 체인 | 2,155 노드 · 최대 4단계 · 체인 있는 엔드포인트 346 |
| long CSV | 2,168행 (bean 1,917 · feign 238 · none 13) |

**재실행 결과가 위와 크게 다르면 소스가 바뀐 게 아니라 추출기가 깨진 것부터 의심한다.**

## 이 추출기가 조용히 틀리는 지점 (전부 한 번씩 밟았음 — 고쳐진 상태)

값이 **0이나 빈칸으로** 나올 뿐 예외를 던지지 않는다. 그래서 눈치채기 어렵다.

1. **메서드 본문 시작** — 시그니처 뒤 첫 `{` 를 잡으면 파라미터 안의 `@Validated({AddNode.class})` 에 걸린다. 파라미터 괄호를 짝 맞춰 닫은 뒤에 본문 `{` 를 찾아야 한다. (`body()` 참조)
2. **인터페이스 메서드엔 `public` 이 없다** — 시그니처 정규식이 `public\s+` 를 요구하면 Feign 메서드 목록이 비어 "호출자 0"이 무더기로 나온다.
3. **로컬 private 메서드 투과** — 서비스가 같은 클래스의 private 메서드를 거쳐 Feign 을 부르면 1홉 탐색은 끊긴다. `collect()` 가 로컬 호출을 노드로 만들지 않고 따라 들어가며 `via` 에 경로를 남긴다.
4. **부모 클래스 상속 주입 필드** — `GlobalTreeMapController` 는 자체 필드가 0개이고 `globalTreeMapService` 가 부모 `TreeMapAbstractController` 에 `protected` 로 있다. 상속 체인을 올라가 필드를 병합한다.
5. **단일 대문자 제네릭** — `private T treeService;` 는 `[A-Z]\w+` 에 안 걸린다. `[A-Z]\w*` 로 쓴다.

## 설계 규칙 (깨뜨리지 말 것)

- **문서의 모든 수치는 생성 시점에 집계한다.** 문장에 숫자를 박으면 수정 뒤 반드시 어긋난다.
- **표를 손으로 적지 않는다.** §2 상속 14개를 이름으로 유추해 적었더니 `getNodesWithoutRoot`·`getMonitor` 가 실제로는 둘 다 `treeService.getChildNode` 를 불러 틀렸다. 지금은 `TreeAbstractController` 원문에서 생성한다.
- **§3 표 · §4 체인 · CSV 는 전부 `call_chains.json` 한 원천에서 유도한다.** 따로 계산하면 같은 엔드포인트가 세 곳에서 다른 값을 갖는다.
- **CSV 는 long(tidy)** — 호출 1건 = 1행, 한 칸에 값 하나. wide 로 내면 한 칸에 값이 여러 개 붙어 필터·피벗이 안 된다.
- **정규식이 든 코드는 Write/Edit 로 직접 쓴다.** bash heredoc 을 거치면 `\b` 가 백스페이스(0x08)로 박혀 매칭이 전부 실패한다.

## 산출물 성격

요구사항 `[제약 조건]` 이 못박고 있다 — **레퍼런스 문서다. 구조 비평·결함 지적·개선 권고는 산출물이 아니다.**
"분석"이라는 말에 끌려 평가문을 쓰지 말 것. 표를 채우는 작업이다.

상세 경위는 `_shared/learnings.md` 의 `[2026-09-21] [REQ-BACKEND-FUNC-01]` 항목.
