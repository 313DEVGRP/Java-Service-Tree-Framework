# 분석 범위 — wiki 동시 편집 동기화 불일치

target_repo: `C:\Users\www\IdeaProjects\Java-Service-Tree-Framework\Java-Service-Tree-Framework-Frontend-Web`

## 읽을 파일 (target_repo 기준 상대 경로)

| 경로 | 내용 |
|---|---|
| `arms/js/adms.js` | 진입점. diff 송신(`sendDiffIfChanged`, 150ms debounce, IME `compositionstart/end`), 수신 라우팅(`sessionManager.onContentsChange`), 저장 API(`updateWiki.do`), `setData` 경로 |
| `arms/js/adms/collab-diff.js` | 핵심. `getEditorBlocks` / `computeBlockDiff`(LCS dp) / `applyBlockDiff` / `sanitizeRemoteHtml` / `getCursorPath` / `showRemoteCursor` |
| `arms/js/adms/session-manager.js` | STOMP + SockJS 세션·룸 관리, `remoteUserUpdate` 송수신 경로, 참여자 상태 |
| `arms/js/adms/wiki-list.js` | jstree 문서 트리·전환. 문서 전환 시 `setData` 호출 경로 |

`arms/js/adms/editor-operation.js`는 CKEditor 인스턴스 설정 파일이고 diff 로직은 없다 — 확인만 하고 넘어가도 된다.

## 서버측

브로드캐스트 정책(발신자에게도 되보내는지 = echo 여부)이 이 repo에 없을 수 있다.
없으면 **echo 있음 / 없음 두 경우로 나눠** 결론을 쓰고 Issues/Caveats에 명시할 것.

## 검증할 선행 가설

Orchestrator가 코드 열람 중 관측한 것. **참이라 가정하지 말고 검증할 것.** 반증되면 반증이라고 쓸 것. 아래 4개 외의 원인도 찾을 것.

1. **자기 diff 재적용** — `adms.js`의 수신 핸들러에서 `cursor` 타입은 발신자 ID를 거르는데(`String(contents.id) !== String(userInfo.userId)`) `diff` 타입은 그 검사 없이 바로 `applyBlockDiff`로 간다. 서버가 발신자에게도 브로드캐스트하면 자기 삽입을 자기 문서에 한 번 더 적용

2. **`lastBlocks` stale** — `sendDiffIfChanged`는 로컬 송신 시에만 `lastBlocks`를 갱신한다. 원격 diff를 `applyBlockDiff`로 DOM에 반영해도 `lastBlocks`는 그대로다. 다음 로컬 입력 때 옛 기준으로 diff를 떠서, 원격이 넣은 블록을 "내가 지워야 할 것"으로 오판하거나 이미 있는 블록을 다시 insert하는 ops를 만들어 전파

3. **블록 동일성을 `outerHTML` 문자열로만 판정** — `getEditorBlocks`가 블록을 `outerHTML`로 뽑고 `computeBlockDiff`가 `===`로 비교한다. 동일한 문단이 둘 이상이면(빈 `<p>`, 반복 문구) LCS가 어느 쪽을 매칭할지 모호해져 엉뚱한 블록이 지워지거나 겹침

4. **버전·시퀀스 번호 부재** — ops에 base version이 없고 `applyBlockDiff`가 수신 즉시 인덱스 순서로 적용한다. 서로 다른 기준에서 뜬 동시 diff가 변환(transform) 없이 적용되어 위치가 어긋남. OT/CRDT의 수렴 보장이 없는 구조

## 참고 — 이미 코드에 있는 방어 흔적

이전에도 같은 계열 문제를 겪은 정황. 왜 이 방어들이 부족한지도 함께 설명할 것.

- `dataReady`마다 `lastBlocks` 재동기화 (주석: "전체 삭제 + 전체 삽입 폭주 diff")
- IME 조합 중 diff 전송 차단, `compositionend`에서 debounce 우회 즉시 전송
- 150ms debounce
- 커서 요소(`data-remote-cursor`)를 콘텐츠 블록에서 제외
