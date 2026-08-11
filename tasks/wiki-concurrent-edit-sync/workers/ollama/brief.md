# Brief — ollama / wiki 동시 편집 동기화 불일치

## Worker 행동 규약 (고정 — 모든 brief에 그대로 유지, 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: C:\Users\www\IdeaProjects\Java-Service-Tree-Framework\Java-Service-Tree-Framework-Frontend-Web
write_scope: none
```

## Objective

아래 CKEditor4 + STOMP 협업 편집 코드에서 ① 같은 내용이 중복 삽입되는 원인 ② 편집 내용이 유실되는 원인을 짚어라.

## Input

```
sources: tasks/wiki-concurrent-edit-sync/sources/collab-core.js
```

<!-- 규약 예외: ollama는 파일 접근이 없는 api 워커라 발췌를 inline 한다. log.md [DECISION] 기록 -->

```javascript
// [송신] adms.js
var lastBlocks = [];
function sendDiffIfChanged() {
  var currentBlocks = getEditorBlocks(editor);
  var ops = computeBlockDiff(lastBlocks, currentBlocks);
  if (ops.some(function (op) { return op.op !== "retain"; })) {
    lastBlocks = currentBlocks.slice();
    sessionManager.remoteUserUpdate(JSON.stringify({ type: "diff", ops: ops }));
  }
}
editable.attachListener(editor.document, "keyup", function () {
  if (isComposing) return;
  sendDiffIfChangedDebounced();   // 150ms debounce
});

// [수신] adms.js
sessionManager.onContentsChange = function (contents) {
  var parsed = JSON.parse(contents.selection.message);
  if (parsed.type === "diff") {
    applyBlockDiff(CKEDITOR.instances["editor"], parsed.ops);
    return;
  }
  if (parsed.type === "cursor") {
    if (String(contents.id) !== String(userInfo.userId)) {   // 커서만 발신자 검사
      showRemoteCursor(CKEDITOR.instances["editor"], contents, parsed);
    }
    return;
  }
};

// [블록 추출] collab-diff.js — 블록의 동일성 판정은 outerHTML 문자열 비교
function getEditorBlocks(editor) {
  var body = editor.document.getBody().$, result = [];
  for (var i = 0; i < body.children.length; i++) {
    var el = body.children[i];
    if (!el.getAttribute("data-remote-cursor")) result.push(el.outerHTML);
  }
  return result;
}
// computeBlockDiff(old,new): LCS(dp) 로 retain/insert/delete 생성, 인접 delete+insert 는 replace 로 병합
// applyBlockDiff(editor, ops): ops 를 body.children 인덱스 순서대로 적용 (버전·시퀀스 번호 없음)
```

## Constraints

- 코드에 실제로 있는 근거만. 없는 함수·변수 지어내지 말 것
- 원인마다 "어떤 순서로 이벤트가 일어나면 깨지는지" 1~3줄 시나리오를 붙일 것

## Output Format

- 형식: Markdown
- 구조: `## 중복 삽입` / `## 내용 유실` 두 섹션. 각 섹션은 원인 항목의 목록이고, 항목마다 `근거:`(코드 지점) + `시나리오:` 두 줄
- 마지막에 `## Issues/Caveats` — 불확실한 점

## Do NOT

- 코드 수정·파일 쓰기 금지 (분석만)
- 일반론적 CRDT/OT 교과서 설명만 늘어놓지 말 것 — 위 코드에 붙은 지적만
