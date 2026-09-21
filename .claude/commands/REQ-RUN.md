---
description: 요구사항정의서 엑셀의 요구사항을 TASK로 변환해 생성·갱신하고 끝까지 실행한다 (ID 생략 시 수용 전체)
argument-hint: [REQ-ID] (생략 시 수용 여부=수용인 전체 행)
---

# REQ-RUN

`요구사항정의서_엑셀양식_v3_1_3.xlsx` 의 요구사항을 `요구사항_TASK_전환_Format.md` · `요구사항_TASK_전환_Sample.md` 규칙으로 요청문으로 바꾸고, `CLAUDE.md` Task Lifecycle 에 따라 작업을 만들어(이미 있으면 갱신) 끝까지 진행한다.

대상 요구사항 ID: **$ARGUMENTS**

## 0. 입력 해석

- `$ARGUMENTS` 에 ID(들)가 있으면 그 행만 처리한다. 공백·쉼표로 여러 개를 받을 수 있다.
- **비어 있으면 `수용 여부 = 수용` 인 전체 행**을 대상으로 한다. ID 오름차순으로 **한 건씩 순차 처리**하고, 한 건이 실패해도 멈추지 말고 다음 건으로 넘어간다(실패는 `[ERROR]` 로 기록).
- 시트에 없는 ID를 받으면 그 ID만 건너뛰고 사용자에게 마지막 요약에서 알린다.

## 1. 진행 원칙 (이 커맨드 전용)

- **사용자에게 승인·결정을 묻지 않는다.** 모호한 값은 아래 기본값 규칙으로 스스로 정하고 진행한다.
- 임의로 정한 모든 사항은 `tasks/<task>/log.md` 에 `[DECISION]` 태그로 **무엇을/왜/대안** 한 줄씩 남긴다. 작업 종료 시 `## 임의 결정 요약` 섹션을 `log.md` 끝에 append 한다.
- 승인 게이트는 없애지 않는다. **`/REQ-RUN` 호출 자체가 시트의 `[Worker Settings]` 에 적힌 워커에 대한 사용자 승인**으로 간주하고, `task.md` 의 `workers_approved` 에 `approved_by: user (via /REQ-RUN)` 로 기록한 뒤 `log.md` 에 `[APPROVAL]` 을 남긴다. 시트에 없는 워커는 호출하지 않는다.
- 외부 repo 쓰기는 `CLAUDE.md` 의 4조건을 그대로 지킨다. 시트 `[작업 대상]` 이 `target_repo` 를, 아래 3-c 가 `write_scope` 를 정하며, `[APPROVAL]` 로그를 남긴 경우에만 직접 쓴다. 하나라도 불명확하면 `tasks-only` 로 낮추고 diff 로 산출한다.

## 2. 요구사항 추출

`openpyxl` 이 없으면 `python -m pip install openpyxl -q` 로 설치한다. 콘솔이 cp949 라 반드시 UTF-8 파일로 떨어뜨려 읽는다.

```bash
python - <<'PY'
import openpyxl, pathlib, tempfile
DUMP = pathlib.Path(tempfile.gettempdir()) / 'req-dump.md'
wb = openpyxl.load_workbook('요구사항정의서_엑셀양식_v3_1_3.xlsx', data_only=True)
ws = wb['요구사항정의서']
rows = list(ws.iter_rows(values_only=True))
hdr = rows[0]
out = []
for r in rows[1:]:
    if not r[0]:
        continue
    out.append('\n'.join(f'## {h}\n{v}' for h, v in zip(hdr, r)))
DUMP.write_text('\n\n---\n\n'.join(out), encoding='utf-8')
print(DUMP)
PY
# 출력된 경로를 읽는다. 저장소 안에는 임시 파일을 만들지 않는다.
```

시트 컬럼: `요구사항 ID · 대분류 · 중분류 · 소분류 · 요구사항명 · 상세 내용 · 요청자 · 수용 여부 · 우선순위 · 담당자 · 진행 현황 · 비고`.
`상세 내용` 은 `[개요] / [상세 기능 요구사항] / [입력 / 출력] / [제약 조건 / 비기능 요구사항] / [검증 기준] / [작업 대상] / [Worker Settings]` 블록으로 구성된다(빈 블록 있을 수 있음).

## 3. 요청문 변환

`요구사항_TASK_전환_Format.md` 의 매핑표가 정본이고, `요구사항_TASK_전환_Sample.md` 가 출력 형태의 정본이다. 시트가 Format 문서보다 블록이 많으므로 아래를 덧붙여 적용한다.

- **목표** = `요구사항명` + `[개요]`. `[검증 기준]` 은 별도 섹션을 만들지 말고 `완료 조건 = ① ② ③` 으로 목표에 흡수. `[검증 기준]` 이 비어 있으면 `[개요]`·`[상세 기능 요구사항]` 에서 완료 조건을 직접 만들고 `[DECISION]` 으로 남긴다.
- **제약** = `[제약 조건 / 비기능 요구사항]` 중 **금지 항목만**. 달성해야 할 품질은 목표로, 이미 정해진 환경은 "~를 전제로" 한 줄로.
- **성격** = `진행 현황` 치환 (기획중·설계중 → 분석·요약 / 개발중·검증중 → 코드 구현).
- **target_repo** = `[작업 대상]` 에 적힌 모듈 경로를 이 저장소 기준 **절대경로**로 해석 (예: `Java-Service-Tree-Framework-Frontend-Web 모듈의 arms\html\landing_index` → `C:\313dev\Java-Service-Tree-Framework\Java-Service-Tree-Framework-Frontend-Web`). `[작업 대상]` 이 비었으면 `대분류·중분류` 로 모듈을 추정하고 `[DECISION]` 기록.
- **워커** = `[Worker Settings]` 의 `MainWorker` / `SubWorker` / `MainWorker-SubAgent` 를 그대로 사용. `N/A` 는 사용 안 함. 이 블록이 비어 있을 때만 `담당자` 컬럼과 `_shared/routing.md` 로 결정한다(DEV 단독 → 생산=claude-main / DEV+SE → 리뷰=codex-critic 추가).
- (c) **write_scope** 기본값: 성격이 `분석·요약` 이면 `tasks-only`, `코드 구현` 이면 `[작업 대상]` 하위 경로 패턴(예: `arms/html/landing_index/**`). 경로가 애매하면 `none(diff-first)` 로 낮춘다.
- **산출물** = 분석·요약 → 설계 문서로 `artifacts/`, 코드 구현 → 외부 쓰기 승인 시 대상 경로에 직접, 아니면 diff 로 `artifacts/`.
- `요청자 · 우선순위 · 수용 여부 · 비고` 는 버린다. 단 `수용 여부 ≠ 수용` 인 행은 작업으로 만들지 않는다.

변환 결과(Sample 형식 7줄 블록)를 `tasks/<task>/sources/request.md` 에, 엑셀 원문 행을 `tasks/<task>/sources/requirement.md` 에 저장한다. `requirement.md` 가 시트 변경 감지의 기준선이다.

## 4. 작업 생성 또는 갱신 (엑셀 갱신 반영)

작업 폴더명은 요구사항 ID 소문자 — `tasks/req-landing-func-02/`.

**이미 폴더가 있으면 `_shared/orchestrator-rules.md` §3 재진입 프로토콜을 먼저 따른다.** 1단계 재정박(`task.md` → `context.md` → `log.md` 최근 항목 → `workers/<role>/brief.md`·`result.md`) 전에는 아무 것도 고치지 않는다. 그 다음:

1. 기존 `sources/requirement.md` 와 방금 추출한 원문을 비교한다.
2. **차이 없음** → status 기준으로 분기. `done` 이면 재실행하지 않고 "변경 없음"으로 보고하고 종료.
3. **차이 있음** → `[UPDATE]` 로그에 바뀐 블록명을 기록하고 `sources/requirement.md`·`request.md`·`task.md`(Goal·Constraints·Acceptance Criteria)·`context.md` 를 새 내용으로 갱신, status 를 `in_progress` 로 되돌린 뒤 영향받은 단계만 다시 실행한다. **기존 `result.md` 는 덮어쓰지 말고** `result-<YYYYMMDD>.md` 로 버전 보존하고, 현재 채택본 경로를 `context.md` 에 명시한다.
4. `target_repo` 또는 `write_scope` 가 바뀌었으면 기존 외부 쓰기 승인은 무효다. 새 `[APPROVAL]` 을 남기기 전까지는 `artifacts/` diff 로만 산출한다.
5. 새 작업이면 `_templates/` 의 `task.md`·`context.md`·`log.md` 를 복사해 폴더를 만든다 (`workers/`, `sources/`, `artifacts/` 포함).

`context.md` 는 1500자(한글)를 넘기지 말 것 — `wc -m` 으로 확인하고 초과분은 `log.md` 로 옮긴다.

> **개행 주의**: Windows 파이썬의 `write_text()` 는 기본으로 LF→CRLF 변환을 하므로 `wc -m` 글자수가 줄 수만큼 부풀려진다. 파일을 파이썬으로 쓸 때는 `newline="\n"` 을 지정하고, 글자수를 재기 전 `python - <<'PY'` 로 `b'\r\n'`→`b'\n'` 정규화를 돌린다.

## 5. 실행

0. **대상 저장소의 규약 문서를 먼저 읽는다.** `docs/ai/12_known_issues` · `02_tech_stack` · `07_review_checklist` 가 있으면 훑고, 해당 저장소용 스킬(`.claude/skills/<repo>`)이 있으면 그것도 본다. 요구사항과 겹치는 known-issue 가 있으면 brief 의 Input 에 **경로로** 넣는다(내용 inline 금지). 이 단계를 건너뛰면 저장소가 이미 문서화한 결함을 리뷰 라운드로 재발견하게 된다.
1. worker 별 brief 를 **`tasks/<task>/workers/<role>/brief.md`** 에 작성한다 (≤1200자, 파일 내용 inline 금지 — 경로만). `_templates/worker-brief.md` 의 "Worker 행동 규약" 고정 블록을 그대로 포함하고, brief 에 "사용자에게 질문" 지시를 넣지 않는다.
2. 생산 워커 → (있으면) 리뷰 워커 순으로 호출한다. 리뷰는 생산 산출물이 나온 뒤에만.
3. 응답 원문을 **`tasks/<task>/workers/<role>/result.md`** 에 저장한다. 호출마다 `log.md` 에 `[WORKER_CALL]`.
4. 워커 실패·타임아웃은 1회 재시도, 재실패 시 `[ERROR]` 기록 후 가능한 부분만 진행한다.
5. `MainWorker-SubAgent` 가 지정돼 있으면 해당 서브에이전트를 메인 워커 작업의 실행 주체로 사용한다.

## 6. 검증 · 마감

1. 각 `result.md` 의 Verification Checklist 를 실행한다. 기본 항목: output 이 brief 의 `output_format` 과 일치 / 파일 경로 실존 / `task.md` constraints 충족 / Do NOT 위반 없음.
2. 결과를 `log.md` 에 `[VERIFICATION]` 으로 append 한다. 실패 항목이 있으면 해당 워커만 재호출(부분 재실행)한다.
   - **리뷰 루프에 들어가기 전에 종료 규칙을 `[DECISION]` 으로 먼저 기록한다.** 보정은 매 라운드 새 표면을 만들므로(1차 Critical 해소 → 2차 신규 Major) 수락 기준과 별개로 "몇 라운드까지, 어떤 등급까지"를 못 박아야 루프가 끝난다.
   - 리뷰어 지적은 그대로 받지 말고 **오케스트레이터가 소스로 전수 대조**한 뒤 성립하는 것만 보정 brief 에 넣는다.
3. 통과하면 `task.md` 의 `status: done`, `updated:` 를 오늘 날짜로 갱신한다.
4. `log.md` 끝에 `## 임의 결정 요약` 을 append — 이번 실행에서 사용자 대신 정한 값(완료 조건 보충, target_repo 해석, write_scope 하향, 워커 선택 등)을 표로 정리한다.
5. 교훈이 생기면 시스템 운영 일반 → `_shared/learnings.md`, 특정 외부 프로젝트 한정 → `_local/learnings.md`.
6. 산출물을 `artifacts/` 에 통합본 1본으로 합친다(라운드가 여러 번이면 "뒤 장이 앞 장을 대체" 구조 + 머리말에 채택 우선순위 표). PDF 가 필요하면 `python-markdown → HTML → Edge 헤드리스 --print-to-pdf` 경로를 쓴다(이 PC 에 pandoc·wkhtmltopdf 없음). 생성 후 `%PDF` 헤더·쪽수·`MalgunGothic` 임베딩을 확인하고 중간 HTML 은 지운다.
7. temp 의 `req-dump.md` 등 임시 파일을 삭제한다.

## 7. 최종 보고

처리한 요구사항별로 한 줄씩: `REQ-ID — 신규/갱신/변경없음 · status · 산출물 경로 · 임의 결정 n건`. 마지막에 사용자가 확인해야 할 임의 결정 중 되돌릴 만한 것 2~3개만 짚는다.
