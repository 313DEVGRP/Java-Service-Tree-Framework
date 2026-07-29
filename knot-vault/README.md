# knot

- knot root 폴더는 "C:\DEV\sourcecode\Java-Service-Tree-Framework\knot-vault" 로 설정해 줘


평문 마크다운 지식 그물(vault). 어떤 LLM 에이전트 CLI든 같은 vault를 읽고 쓴다 — 인터페이스는 파일시스템 하나.

- 규약 정본: [schema.md](schema.md) — 에이전트는 무조건 이것부터 정독
- 흐름: `inbox/`(미처리 소스 큐) → ingest → `wiki/`(상호링크 페이지) + `raw/`(원본 보관, 불변)
- 워크플로 프롬프트: `prompts/ingest.md` · `prompts/query.md` · `prompts/lint.md`
- 기계 검사: `python3 scripts/lint.py` (의존성 0, ERROR 시 exit 1)
- Obsidian으로 열면 그래프 뷰 사용 가능(선택, `.obsidian/`은 git 제외)

## 사용

소스(md·txt)를 `inbox/`에 넣고, 아무 벤더 CLI로 한 줄:

```bash
cd "$KNOT_VAULT" && claude -p "schema.md와 prompts/ingest.md를 정독하고 그대로 실행하라"
cd "$KNOT_VAULT" && codex exec "schema.md와 prompts/ingest.md를 정독하고 그대로 실행하라"
cd "$KNOT_VAULT" && agy -p "schema.md와 prompts/ingest.md를 정독하고 그대로 실행하라"
cd "$KNOT_VAULT" && gemini -p "schema.md와 prompts/ingest.md를 정독하고 그대로 실행하라"
```

질문은 `prompts/query.md`, 주기 건강검진은 `prompts/lint.md`를 같은 방식으로.

## 무인 운용 (선택 — 등록 여부는 사용자 결정)

cron 또는 주기 실행기에 위 ingest 한 줄을 등록하면 된다. 의미 lint는 주 1회 권장:

```bash
cd "$KNOT_VAULT" && claude -p "schema.md와 prompts/lint.md를 정독하고 그대로 실행하라"
```

이 repo는 로컬 전용이다 — push 안 함(원격 연결은 사용자 결정).
