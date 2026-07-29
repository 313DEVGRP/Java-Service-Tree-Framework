# query — 질문에 답하기

0. **`schema.md`를 먼저 정독한다.** 이 프롬프트만 보고 시작하지 말 것.
1. 질문을 받는다(호출 인자 또는 지시문).
2. `index.md`에서 관련 페이지를 찾고(필요하면 grep 보조) 해당 페이지들을 정독한다.
3. `[[링크]]` 인용을 달아 답을 합성한다. vault에 근거가 없으면 없다고 답한다 — 지어내지 말 것.
4. 답이 재사용 가치가 있으면 `note` 페이지로 저장한다:
   - frontmatter의 `sources:`에는 합성에 쓴 근거의 원 출처(raw/ 경로 또는 URL)를 적는다
   - `index.md`·`log.md`(`## [YYYY-MM-DD] query — <제목>`)를 갱신한다
   - `python3 scripts/lint.py` 확인 후 `git add -A && git commit` — 메시지 `query: <제목>`, 모델명 트레일러
   저장하지 않는 읽기 전용 답변이면 커밋 없이 끝낸다.
