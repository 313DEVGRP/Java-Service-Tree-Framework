# Brief — claude-main / REQ-FRONTEND-FUNC-01

## Worker 행동 규약 (고정)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web
write_scope: tasks-only
```

## Objective

`arms/js/`·`backoffice/js/` API 호출 추출 스펙·URL 복원·변환 코드. 파일 생성은 Orchestrator.

## Input

```
task: tasks/req-frontend-func-01/task.md
ctx:  tasks/req-frontend-func-01/context.md
구조: <repo>/docs/ai/03_directory_structure/frontend-web-directory.md
메뉴: <repo>/arms/html/template/page-navigation.html
```

## 할 일

1. 호출 지점 전수 식별 — `$.ajax`·`$.get`·`$.post`·`fetch` (실측 448건).
2. **URL 복원** — 연결·템플릿·상수·헬퍼로 조합된 url 을 완성형으로. 변수는 `{param}` 로.
   **`/` 로 끝나면 실패.** 복원 불가 건은 파일:라인+사유.
3. 메뉴 매핑 — `page=` ↔ `js/{page}.js` 1:1 로 menuname. backoffice 메뉴 정의 위치는 찾아 명시.
   미연결 js 는 사유 라벨(`common` 등).
4. 컬럼 스펙 — `menuname,area,jsfile,line,httpMethod,apiurl,callPattern,note` 기준 확정.
5. 변환 코드 — 재현용 python(표준 라이브러리만). 복원 불가분은 수작업 dict + 근거 주석.

## Constraints

- 읽기 전용. 저장소 수정·빌드·서버 기동 금지
- 레퍼런스다. 비평·권고 금지. 소스에 없는 URL 창작 금지

## Output Format

응답 본문 = result.md 원문. 섹션: 추출 범위 / 컬럼 스펙 / URL 복원 규칙 /
메뉴 매핑 / 변환 코드 / 예상 행수 / Verification Checklist / Issues

## Do NOT

- 파일 쓰기 (저장소·엑셀·tasks/)
- `/` 로 끝나는 미복원 URL 싣기
