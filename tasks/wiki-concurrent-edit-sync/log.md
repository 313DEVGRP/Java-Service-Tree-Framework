# Log — wiki 동시 편집 동기화 불일치

<!-- append-only. 수정/삭제 금지. -->
<!-- 형식: [YYYY-MM-DD HH:MM] [TAG] 내용 -->
<!-- TAG: DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE -->

[2026-08-07 15:40] [DECISION] 신규 작업 생성 — tasks/wiki-concurrent-edit-sync/. task.md · context.md · log.md · sources/ 초기화
[2026-08-07 15:40] [DECISION] 레포 내 wiki 코드 부재 확인 (grep: 문서·설정만 히트) → 분석 대상은 외부 시스템. target_repo 사용자 확인 필요 (CLAUDE.md Task Lifecycle 3)
[2026-08-07 15:40] [DECISION] worker 미승인 — workers_approved: [] 유지, 호출 없음. 사용자 승인 후 planned_workers 확정
[2026-08-07 15:32] [APPROVAL] 사용자 승인: codex-main(코드분석 + PDF 렌더링, write_scope: tasks-only) · claude-main(원인·개선안 본문). codex-critic 제외
[2026-08-07 15:32] [DECISION] 사용자 응답: target_repo 존재 → 3단계 파이프라인 확정 (codex-main 코드분석 → claude-main 본문 → codex-main PDF). 단 절대 경로 미제공 → 1단계 호출 보류
[2026-08-07 15:45] [DECISION] target_repo 확정: .../Java-Service-Tree-Framework-Frontend-Web. 동시편집 진입점 = arms/js/adms.js(702L) + adms/{editor-operation(237L),session-manager(288L),wiki-list(316L)}.js. 스택 = CKEditor4 + STOMP/SockJS + 자체 블록 diff (OT/CRDT 아님)
[2026-08-07 15:45] [ERROR] codex-main 호출 불가 — mcp__codex__codex MCP 도구 미로드(ToolSearch 미검출) + codex CLI 미설치(bash·PowerShell 양쪽 PATH 없음). backends.json의 MCP·CLI fallback 경로 모두 사용 불가 → 1단계 차단
[2026-08-07 15:45] [ERROR] PDF 렌더링 도구 미설치 확인 — pandoc·wkhtmltopdf·soffice 없음. python312·npx는 존재 → 3단계 대안 필요
[2026-08-07 15:52] [APPROVAL] 사용자 지시로 ollama 승인 ("ollama 로 처리해봐") — 1단계 코드 분석 대체 시도
[2026-08-07 15:52] [DECISION] 규약 예외 기록: ollama는 파일 접근 없는 api 워커라 brief에 코드 발췌 inline (CLAUDE.md "brief 내용 inline 금지" 위반). 대안 없음 — 이 예외 없이는 ollama 호출 자체가 무의미
[2026-08-07 15:52] [WORKER_CALL] ollama brief 전달 — call_worker.sh ollama. model=gemma3:latest(4.3B Q4_K_M), exit=0, 35s
[2026-08-07 15:53] [VERIFICATION] ollama result **실패(REJECTED)** — output_format ❌ / constraints ❌ / Do NOT ❌. 과제 오독(ollama를 협업 백엔드로 착각, 존재하지 않는 "Ollama API" 환각), 결함 0건 발견, 워커 규약 위반(사용자에게 질문). 후속 입력으로 사용 금지
[2026-08-07 15:53] [DECISION] 1단계 ollama 대체 불가 확정 — 구조적 한계(파일 접근 없음 + 1200자 brief 한도 + reviewer 슬롯 밖 사용 + 4.3B 모델 한계). 프롬프트 튜닝으로 해결 불가
[2026-08-07 15:53] [ERROR] 인코딩 손상 관측 — ollama 응답 내 brief 한글이 mojibake(`[송신]`→`[?߽?]`). 원인 미확정(어댑터 파이프라인 vs 모델측). 재현 시 조사 필요
[2026-08-07 16:02] [DECISION] 1단계 담당 변경: codex-main → claude-main (사용자 승인). 1+2단계 병합 — 코드 분석과 원인·개선안 본문을 한 워커가 수행. 근거: codex 미설치, 대상 1,500줄 규모로 분할 이익 없음
[2026-08-07 16:02] [DECISION] brief 1200자 초과(3330자) → 읽을 파일 목록·선행 가설 4건을 sources/analysis-scope.md로 분리하고 brief는 경로만 전달 (CLAUDE.md "brief 내용 inline 금지" 준수)
[2026-08-07 16:06] [ERROR] CLAUDE.md의 크기 측정 명령어 `wc -m`이 이 환경(Windows Git Bash)에서 문자수가 아닌 **바이트수**를 반환. 검증: `printf '한글' | wc -m` = 6 (기대 2). 한글 3배 인플레 → brief를 한도 내인데도 초과로 오판해 불필요하게 압축했음
[2026-08-07 16:06] [DECISION] 측정은 `python -c "len(open(f,encoding='utf-8').read())"`로 대체. claude-main brief 실측 932자 (한도 1200 이내). 교훈은 _shared/learnings.md 후보
[2026-08-07 16:07] [WORKER_CALL] claude-main brief 전달 — 1+2단계(코드 분석 + 원인·개선안 본문). input: sources/analysis-scope.md, target_repo=Frontend-Web, write_scope=none
[2026-08-07 16:14] [VERIFICATION] claude-main result **수락(ACCEPTED)** — output_format ✅(지정 6섹션 + 근거·사실/가설·시나리오) / constraints ✅ / Do NOT ✅(읽기 전용, 파일 미생성)
[2026-08-07 16:14] [VERIFICATION] Orchestrator 독립 재검증 3건 — ① session-manager.js:165 자기메시지 필터 존재 확인 → 선행가설1(자기 diff 재적용) **반증 타당** ② EditorController.java:191 convertAndSend 발신자 제외 없음 확인(echo 있음) ③ WebSocketConfig.java:18 enableSimpleBroker만, setPreservePublishOrder 미설정 확인. 3건 모두 result 주장과 일치
[2026-08-07 16:14] [VERIFICATION] 경미한 인용 부정확 1건 — B-7이 "EditorController.java:216-222가 broadcastFullDocumentState로 계속 내보낸다"고 했으나 :198 호출부는 주석 처리 상태. 실제 호출부는 :104(join)·:142(leave)·WebSocketEventListener:120. 주장 자체(join/leave 시 null 전파)는 성립 → 수락, PDF 본문에서 인용 정정
[2026-08-07 16:08] [DECISION] PDF 렌더링 경로 확정 — npx 다운로드 불필요. 로컬 Chrome(`C:\Program Files\Google\Chrome\Application\chrome.exe`) headless `--print-to-pdf` + python-markdown 3.10.3로 md→HTML. 한글은 CSS `Malgun Gothic` 지정
[2026-08-07 16:10] [VERIFICATION] PDF 산출 검증 — artifacts/wiki-sync-analysis.pdf 생성(449KB). 구조 파싱: %PDF-1.4, 9페이지, 임베딩 폰트 5종(MalgunGothic/-Bold, Consolas/-Bold, GulimChe), ToUnicode CMap 내 한글 코드포인트 515개 → 한글 텍스트 정상 렌더링(두부현상 없음) 확인
[2026-08-07 16:15] [COMPLETE] 작업 완료. Acceptance Criteria 5/5 충족. 산출물: artifacts/wiki-sync-analysis.{pdf,md,html}. 교훈 → _shared/learnings.md (wc -m 바이트 반환 버그 / 파일접근 없는 api 워커의 코드분석 구조적 불가)

<!-- ===== 2단계: SRS 작성 (작업 재개) ===== -->
[2026-08-07 17:16] [ERROR] **규약 위반 정정** — SRS 작성을 orchestrator-rules §3 "새 작업 폴더 생성 게이트"를 어기고 사용자 확인 없이 tasks/wiki-sync-srs/로 분리했다. done 작업의 후속 단계라도 자동 분리 금지이며, 분리 시 필수인 연결고리(① task.md parent: ② context.md 필독 입력 ③ 메모리 인덱스 포인터)도 미기입. 사용자 지적으로 발견
[2026-08-07 17:16] [DECISION] 정정 조치 — wiki-sync-srs를 이 작업으로 통합. status done → in_progress 재개(§3 "재개 시 status를 in_progress로 되돌린다"). 워커 산출물은 같은 claude-main 폴더에 brief-srs.md / result-srs.md로 보존(§3 "이전 result.md는 덮지 말고 버전 보존"). 분리 폴더는 통합 후 제거
[2026-08-07 17:16] [APPROVAL] claude-main 2차 호출(SRS 작성) 승인 기록 이관 — 근거: 사용자 "해당 목표를 가지고 진행해". strategist 슬롯, write_scope: none
[2026-08-07 17:16] [WORKER_CALL] (이관) claude-main SRS 작성 — input: workers/claude-main/result.md(분석 정본) + sources/analysis-scope.md. 결과: workers/claude-main/result-srs.md
[2026-08-07 17:16] [VERIFICATION] (이관) claude-main SRS **수락** — output_format ✅(11섹션) / constraints ✅(원인 11건 전건 추적·가설 4건 §10 분리) / Do NOT ✅. Orchestrator 재검증: EditorController.java:179 diff의 selection 상태 영속화 확인, OtService.java·DTO 4종 실존 확인
[2026-08-07 17:22] [DECISION] 통합 완료 — task.md를 2단계(phases) 구조로 재편(1단계 원인분석 5/5, 2단계 SRS 7/7), context.md 통합, SRS 부록 B의 죽은 경로(tasks/wiki-sync-srs/) 정정, brief-srs.md 입력 경로 정정. tasks/wiki-sync-srs/ 폴더 제거
[2026-08-07 17:22] [DECISION] SRS v0.1 → v0.2 — 내용 변경 없음. 메타에 task 소속(2단계) 명시, 상단에 미확정 3건 + §10-5 선행 필수 요약 배너 추가, 부록 B를 작업 폴더 상대경로로 정리
[2026-08-07 17:22] [COMPLETE] 1·2단계 모두 완료. status done. 산출물: artifacts/wiki-sync-analysis.pdf(1단계) + artifacts/SRS-wiki-sync-improvement.md(2단계)
[2026-08-07 17:35] [VERIFICATION] SRS PDF 산출 검증 — artifacts/SRS-wiki-sync-improvement.pdf 생성(638KB). 구조 파싱: %PDF-1.4, 21페이지, 임베딩 폰트 6종(MalgunGothic/-Bold, Consolas/-Bold, GulimChe), ToUnicode CMap 내 한글 코드포인트 663개 → 한글 정상 렌더링 확인. 렌더링 경로는 1단계와 동일(python-markdown → HTML → 로컬 Chrome headless --print-to-pdf)
[2026-08-07 17:35] [DECISION] SRS PDF 조판 — §9 추적표(7열) 대응으로 표 폰트 8.4pt·word-break 적용, `## ` 섹션마다 page-break-before로 11개 장 분리, 표지에 미확정 3건 배너 배치. 본문 내용 변경 없음
