# Brief — claude-main / arms/html 언어팩 미적용 라벨 감사

## Worker 행동 규약 (고정 — 모든 brief에 그대로 유지, 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: C:/DEV/sourcecode/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web
write_scope: tasks-only   # target_repo는 read-only
```

## Objective

`arms/html/**`(164개)의 노출 라벨을 언어팩(ko/en/jp) 적용 여부로 분류해 미적용 리포트 작성.

## Input

```
task:    tasks/arms-i18n-label-audit/task.md
context: tasks/arms-i18n-label-audit/context.md   # 메커니즘·정찰 필독
대상:    <target_repo>/arms/{html,js}/**, arms/locales/*.json
```

## Constraints

- 1차 판정 = `data-locale` 유무 (근거: context.md `bindLocaleText`)
- 두 축 분리: ①속성 태깅 ②언어별 값 존재(ko/en/jp)
- 라벨 범위: 텍스트 노드·placeholder·title·alt·버튼 value·option. script/style/주석 제외
- `arms/js/**` 하드코딩 주입 문자열은 별도 섹션
- **전건 나열 금지** — 집계표 + 대표 사례 + 우선순위

## Output Format

- 파일: `tasks/arms-i18n-label-audit/artifacts/i18n-label-audit-report.md` 직접 작성
- Markdown 8섹션: ①요약 ②판정기준 ③폴더별 집계 ④언어별 커버리지 ⑤대표사례(경로:라인) ⑥JS 문자열 ⑦우선순위 ⑧Issues/Caveats
- 응답: 리포트 경로 + 핵심 수치 + Verification Checklist

## Do NOT

- target_repo 파일 수정·생성 (read-only)
- 코드 변경 diff 생성 (리포트만)
- 미확인 경로·라인 추정 기재
