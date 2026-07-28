# Result — claude-main / arms/html 언어팩 미적용 라벨 감사

```yaml
worker: claude-main
task: arms-i18n-label-audit (REQ-F-001)
status: complete
completed_at: 2026-07-28 17:03
tokens_used: 73868 (subagent), tool_uses 31
```

## Summary

`arms/html` 164개 전량의 노출 라벨 9,643건을 추출해 `data-locale` 태깅 여부와 언어별 값 존재 여부 두 축으로 분류하고, 폴더별 집계·대표 사례·우선순위를 담은 리포트를 `artifacts/`에 작성했다.

## Output

리포트 본문: `tasks/arms-i18n-label-audit/artifacts/i18n-label-audit-report.md` (315줄, 8섹션)

### 핵심 수치

| 지표 | 값 |
|---|---|
| 조사 HTML | 164개 전량 |
| 추출 라벨 | 9,643건 |
| `data-locale` 태깅 | 110건 / 6파일 (3.7%) |
| 속성 태깅 커버리지 | 1.14% |
| 사용 키 54개 해소 | ko 22 / en 20 / jp 0 |
| 런타임 실효 커버리지 | ko 0% · en 0% · jp 0% |
| JS 하드코딩 한국어 | 1,833건 / 118파일 |

### 치명 결함 3건 (사전 정찰 범위를 넘어선 발견)

정찰 단계 추정은 "`data-locale` 6개 파일뿐 → 미적용"까지였으나, 실제로는 **태깅된 110건조차 현재 어느 언어로도 치환되지 않는다**:

1. **`ko.json`이 유효하지 않은 JSON** — `arms/locales/ko.json:26` trailing comma. `$.ajax(dataType:"json")` 파싱 실패 → `.done()` 미실행 → 한국어 폴백 전량 무효. jp 공백만 이슈인 줄 알았으나 ko도 죽어 있음.
2. **`ja`/`jp` 식별자 불일치** — `arms/js/common.js:2417`은 `allowedLocale = ["ko","ja","en"]`인데 파일명은 `jp.json`. 일본어 선택 시 `/arms/locales/ja.json` 404 → **`jp.json`을 채워도 폴백으로 로드 안 됨**.
3. **키 48~59%가 어느 팩에도 없음** — `menu-nav.*` 16키, `landing.menu.*` 8키 전량 미정의. `nav.language.*` 3키 누락으로 언어 전환 메뉴 자체가 미번역.

부수 발견: `arms/html/reportWeekly/content-container.html:494`의 `<span data-locale="common.btn.btn_cancel"></span>`은 원문 텍스트가 없어 키 미해소 시 **버튼 라벨이 영구 공백**.

### 병행 i18n 스킴 3종 (표준 불일치)

`data-locale`(110) 외 호환 안 되는 독자 스킴 2개 — `data-lc-i18n`(12, landing_calendar, ko/en/ja/zh), `data-i18n`/`data-i18n-html`(187, landing_canyon 인라인, ko/en). 둘 다 전역 언어 전환 미연동. 집계표의 해당 폴더 0% 표기는 축① 기준이며 **재작업 대상이지 신규 번역 대상 아님**(리포트 §6.2).

`currentLanguagePack`은 `common.js:19` 선언·`:2439-2440` 대입 후 **어디서도 읽히지 않음** → JS 1,833건은 `data-locale` 태깅으로 해결 불가, `t(key)` 신설 필요.

### 우선순위 요지

- **P0** (번역 0건, 코드 1~3줄): ko.json 쉼표 제거 · ja/jp 통일 · 빈 span 폴백 · CI JSON 검증 → 기존 투자분(태깅 110 + 팩 값 43) 즉시 회생
- **P1** (54키 이하): 미정의 26키 + 누락 5키 + `nav.language.*` 3키 → 내비게이션 전 영역 ko/en 정상화
- **P3**: 랜딩(landing_* 약 4,000건, 문안 변경 잦음)보다 내부 업무 화면 우선

## Verification Checklist

- [x] output이 brief의 output_format과 일치 — 지정 경로에 Markdown 8섹션
- [x] 파일 경로 실존 확인 — 인용 경로·라인 `grep -n` 실측, 추정 기재 없음
- [x] task.md constraints 충족 — read-only 준수(`git status` 클린), 산출물 tasks-only, 164개 전량·두 축·ko/en/jp·JS 별도·집계+대표사례+우선순위
- [x] Do NOT 위반 없음 — target_repo 수정 0건, diff 미생성, 미확인 경로 추정 없음
- [x] 가정·불일치가 Issues/Caveats에 표면화됨

## Issues / Caveats

- §4 커버리지는 **폴백 파일 기준**. 1차 소스인 Global-Config API의 키 집합은 런타임 값이라 정적 조사 불가 — API 정상 시 실제 커버리지는 더 높을 수 있다. 다만 결함 1·2는 폴백 전용이라 **API 장애 시 무방비**라는 결론은 유효. 정확한 실측에는 API 응답 덤프 필요(후속 과제).
- 라벨 9,643건은 정규식 상한 추정치. 우선순위 판단에는 충분하나 **번역 발주 물량 산정 시 육안 검수 필요**.

## Artifacts

```
tasks/arms-i18n-label-audit/artifacts/i18n-label-audit-report.md   # 본 리포트 (315줄)
tasks/arms-i18n-label-audit/artifacts/_audit.py                    # 라벨 추출 재현 스크립트
tasks/arms-i18n-label-audit/artifacts/_keys.py                     # 키 해소 판정 스크립트
tasks/arms-i18n-label-audit/artifacts/_audit_detail.json           # 전건 상세 (720KB)
```
