---
description: 요구사항정의서 엑셀의 요구사항을 분석해 요구사항 분석 보고서를 작성하고 PDF로 산출
argument-hint: [REQ-ID ...] (생략 시 전체 요구사항)
---

# REQ-ANAL — 요구사항 분석 → 분석 보고서

`요구사항정의서_엑셀양식_v3_1_3.xlsx`의 요구사항을 분석해 **요구사항 분석 보고서**를 작성하고 **PDF**로 산출한다.

이 커맨드는 **분석**이 목적이다 — 요구사항이 무엇을 요구하는지 해석하고, 품질(명확성·검증가능성·완전성·일관성)을 판정하고, 영향 범위·의존·리스크를 드러낸다. **설계안(클래스·API 시그니처·DDL)을 짓지 않는다.** 설계가 필요하면 분석 보고서를 입력으로 별도 진행한다.

대상 요구사항 ID: **$ARGUMENTS**

## 0. 입력 해석

- `$ARGUMENTS`에 ID(들)가 있으면 그 행만 분석한다. 공백·쉼표 구분, `{REQ-...}`처럼 중괄호가 붙어 있으면 벗겨낸다.
- **비어 있으면 전체 요구사항을 분석한다.** 단 `수용 여부`가 `수용`·`부분 수용`이 아닌 행은 본문 분석에서 빼고 부록에 `ID / 요구사항명 / 수용 여부` 한 줄만 남긴다.
- 시트에 없는 ID는 진행을 멈추지 말고 건너뛴 뒤, 유사 ID 후보를 최종 보고와 부록에 남긴다.
- 대상이 0건이면 PDF를 만들지 말고 이유를 보고하고 끝낸다.

## 1. 요구사항 로드

첫 번째 시트(요구사항정의서), 1행 헤더, 12개 컬럼:
`요구사항 ID | 대분류 | 중분류 | 소분류 | 요구사항명 | 상세 내용 | 요청자 | 수용 여부 | 우선순위 | 담당자 | 진행 현황 | 비고`

```bash
python - <<'PY'
import json, openpyxl
TASK = 'tasks/<task>'          # 실제 작업 폴더로 치환
targets = []                   # $ARGUMENTS 의 ID 목록. 비었으면 전체
ws = openpyxl.load_workbook('요구사항정의서_엑셀양식_v3_1_3.xlsx', data_only=True).worksheets[0]
cols = ['id','major','mid','minor','name','detail','requester','accepted','priority','owner','progress','note']
rows = [dict(zip(cols, [(c.value or '') for c in r[:12]])) for r in ws.iter_rows(min_row=2) if r[0].value]
if targets:
    rows = [r for r in rows if r['id'] in targets]
with open(f'{TASK}/sources/requirements.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
print(len(rows), [r['id'] for r in rows])
PY
```

> **stdout으로 파이프하지 말 것** — 콘솔이 cp949라 한글이 깨진다. 위처럼 `encoding='utf-8'`로 파일에 직접 쓴다.
> `Data Validation extension is not supported` 경고는 무시한다. `~$`로 시작하는 엑셀 잠금 파일도 무시한다.
> `openpyxl`이 없으면 `python -m pip install openpyxl -q`.

## 2. 작업 폴더 생성

`_templates/task-folder.md` 규약대로 `tasks/REQ-ANAL-<YYYYMMDD-HHMM>/`에 `task.md` · `context.md` · `log.md` · `sources/` · `artifacts/`를 만든다.
분석·문서 작업이므로 **`target_repo`는 묻지 않는다.** 모든 산출물은 `artifacts/`에 남는다.

## 3. 요구사항 해석

`상세 내용` 셀의 `[개요] / [상세 기능 요구사항] / [입력·출력] / [제약 조건] / [검증 기준]` 블록을 파싱한다. 블록이 없는 행은 서술에서 유도하되 **유도한 값에 `[유도]` 표시**를 붙인다. 해석 규칙의 정본은 `요구사항_TASK_전환_Format.md`.

| 컬럼 | 분석 입력으로의 변환 |
|---|---|
| 요구사항명 + `[개요]` | 요구 의도 — "무엇이 되어 있으면 끝인지" |
| `[검증 기준]` | 완료 조건. 없으면 검증 가능한 문장으로 초안 작성 후 `[보완]` 표시 |
| `[제약 조건]` | 금지(Do NOT)와 품질 요구(성능·보안·호환)를 분리 |
| 대/중/소분류 | 영향 모듈·리포지토리 특정 |
| 진행 현황 | 성숙도 — 기획중=의도 확인 필요 / 설계중=범위 확정 필요 / 개발중·검증중=기존 구현과의 정합성 확인 |
| 우선순위·수용 여부·담당자 | 집계·권고의 근거 |

리포지토리 매핑: `-Backend-Core`(API·도메인·배치) / `-Frontend-Web`(화면·언어팩) / `-Engine-Fire` / `-Broker-Hub` / `-Middle-Proxy` / `-Global-Config` / `-AI`

**품질 판정은 근거와 함께 쓴다.** "모호함"만 쓰지 말고 어느 문장이 왜 모호한지 원문을 인용한다. 판정 축 5개: 명확성 · 검증가능성 · 완전성 · 일관성(요구사항 간 충돌) · 중복.

## 4. 분석 보고서 작성

`artifacts/요구사항분석보고서_<범위>_<YYYYMMDD>.md`를 정본으로 쓴다. 목차 고정:

```
1. 문서 개요          목적 · 범위 · 근거 자료 · 작성일 · 버전
2. 분석 대상 요약      전체/대상 건수 · 분류별·우선순위별·수용여부별·진행현황별 집계표
3. 요구사항 품질 분석   5개 축별 판정 + 원문 인용 근거 · 요약 점수표
4. 요구사항별 분석      ← 요구사항 ID 하나당 한 절
   4.x.1 요구 내용 요약 (원문 근거)
   4.x.2 해석 — 무엇이 되어 있으면 끝인가 (완료 조건)
   4.x.3 영향 범위 (모듈 · 리포지토리 · 연동 지점)
   4.x.4 선행 의존 · 전제
   4.x.5 규모 · 난이도 판단과 그 근거
   4.x.6 제약 (Do NOT) · 품질 요구
   4.x.7 미확인 사항 / 확인 질의
5. 영향 범위 종합      리포지토리·모듈별 요구사항 매핑표 · 집중도
6. 의존 · 충돌 · 중복   요구사항 간 선후 의존 · 충돌 쌍 · 중복 쌍 (각각 근거 포함)
7. 리스크             리스크 항목 · 영향 요구사항 ID · 근거 · 완화 방향
8. 미결 사항 · 가정     [유도]/[보완] 항목 전수 · 작성자 질의 목록
9. 권고               우선순위·범위 조정 제안 · 추가 확인 필요 항목 · 다음 단계
10. 부록              대상 요구사항 목록 · 제외 행 · 미발견 ID
```

- 단건 실행이면 2·5·6장은 그 요구사항이 닿는 범위만 쓴다. 전체 실행이면 전수 기준으로 쓴다.
- 판단에 코드 실측이 필요하면 해당 리포지토리를 읽고 근거(파일:라인)를 남긴다. **읽기만 한다.**
- 엑셀에도 코드에도 없는 값은 단정하지 말고 8장에 가정으로 명시한다.
- 규모·난이도는 등급(S/M/L 등)만 쓰지 말고 "무엇이 그렇게 만드는지"를 한 줄로 붙인다. **사람-일(man-day)·일정·담당자는 지어내지 않는다.**

## 5. PDF 산출

Markdown → HTML → PDF. 이 환경엔 pandoc·wkhtmltopdf·weasyprint가 없으므로 **헤드리스 Edge로 인쇄한다** (한글 폰트 임베딩 검증 완료: MalgunGothic + ToUnicode).

HTML 요건: `<meta charset="utf-8">` · `font-family:"Malgun Gothic","맑은 고딕",sans-serif` · `@page{size:A4;margin:18mm 15mm}` · 본문 10.5pt/행간 1.6 · `table{border-collapse:collapse;width:100%}`에 셀 테두리와 헤더 음영 · `thead{display:table-header-group}` · `h1,h2{page-break-after:avoid}` · 1페이지는 표지(문서명 · 대상 ID 목록 · 작성일 · `v0.1(draft)`).

```bash
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$(cygpath -w "$PDF")" "$(cygpath -w "$HTML")"
```

렌더 후 `ls -l "$PDF"`로 크기를 확인하고 `grep -a -o -i MalgunGothic "$PDF" | head -1`로 폰트 임베딩을 확인한다. 실패하면 HTML 경로라도 안내한다.

## 6. 마무리

`log.md`에 `[ANALYSIS]` · `[VERIFICATION]` 태그로 기록하고 `task.md`의 `status: done`.
사용자에게 **PDF 절대경로 · 대상 요구사항 ID와 건수 · 품질 판정 요약 · 미결 질의 상위 3~5개**를 한 화면으로 보고한다.

## Verification Checklist

- [ ] 대상 요구사항 수 = 보고서 4장의 절 개수 (전체 실행 시 제외 행은 10장에만 존재)
- [ ] 각 요구사항에 완료 조건이 있다 (원본에 없던 행은 `[보완]` 표시)
- [ ] 3장 품질 판정이 모든 대상 ID를 5개 축 전부로 다룬다
- [ ] 부정 판정(모호·검증불가·충돌·중복)마다 원문 인용 근거가 붙어 있다
- [ ] 6·7장의 각 항목에 관련 요구사항 ID가 명시돼 있다
- [ ] PDF가 실제 존재하고 0바이트가 아니며 한글이 깨지지 않는다
- [ ] 엑셀·외부 리포지토리에 쓰기 없음 (읽기 전용)

## Do NOT

- 엑셀 원본과 외부 리포지토리 코드를 수정하지 않는다. 이 커맨드는 분석 보고서만 만든다.
- 설계안을 짓지 않는다 — 클래스·메서드 시그니처·API 스펙·DDL·화면 설계는 이 보고서의 산출물이 아니다. 영향 범위와 제약까지만 쓴다.
- 워커(claude-main · codex-critic 등)를 호출하지 않는다. 제3자 검토가 필요하면 사용자 승인을 먼저 받고 `task.md`의 `workers_approved`에 기록한 뒤 호출한다.
- 시트에도 코드에도 없는 수치·일정·담당자·공수를 지어내지 않는다. 8장 미결 사항으로 남긴다.
