# 사용량 뷰 Fable 5 주간 사용량 표시 — 설계

날짜: 2026-07-20 · 상태: 승인됨

## 목표

mat 사용량 뷰(`u` 키)의 claude 프로바이더 박스에 Fable 5 주간 사용량 줄을 추가한다.
coach는 Max 구독에서만 `fable_7d` 윈도우를 보고하므로, **정보가 있을 때만** 표시된다
(기본 구독자 화면은 지금과 동일).

## 데이터

`coach --json`의 claude 프로바이더 `windows`에 이미 `fable_7d`(`left_pct`/`reset_min`)가
들어온다. `internal/coach`의 `Windows map[string]Window`가 그대로 담으므로 어댑터 변경 없음.

## 변경 (internal/ui/view.go 단일 파일)

1. `usageWindowOrder` → `{"5h", "7d", "fable_7d"}` — coach 화면과 같은 순서(Fable 마지막).
2. 윈도우 키 → 표시 라벨 매핑 추가: `fable_7d` → `Fable` (coach 미러). 매핑에 없는 키는
   키 문자열 그대로 fallback — coach가 윈도우를 추가해도 안전.
3. 라벨 포맷 `%-3s` → `%-5s` ("Fable" 5자 정렬 유지).
4. 색·바 스타일은 claude 프로바이더 색(노랑) 그대로.

## 조건부 표시

기존 윈도우 루프가 `Windows`에 키가 없으면 줄을 건너뛴다. 별도 분기 없이 요구사항
(정보 있을 때만 표시)이 충족된다.

## 검증

`go build ./...` · `go vet ./...` · `go test ./...` + 실행 화면 확인(`u` 키).
