# mat — MultiAgent Tracker

[multi-agent-starter](https://github.com/netwaif/multi-agent-starter) 시스템의
작업 진행 상황을 터미널에서 모니터링하는 TUI 도구.

시스템을 **읽기만** 한다 — 작업 생성·승인·워커 호출은 하지 않는다.
starter 시스템 없이 단독으로는 의미가 없다.

## 누가 이 도구를 쓰나

AI 치트키 채널의 MultiAgent 매뉴얼을 보고 starter를 설치한 학습자.

## 무엇을 보여주나

한 작업의 워커 현황을 한 화면에서 본다.

- 현재 작업의 status / goal
- 워커 목록과 각 워커의 상태 (대기 / 실행 중 / 완료 / 에러)
- 각 워커가 무엇을 하고 있는지 한 줄 요약
- result 파일 경로·크기, log.md 최근 줄(메인) / 전체(모달)

한 작업만 본다. 동시 모니터링은 안 하고 작업 전환만 된다.
자동 새로고침은 2초 폴링이다. 실시간 파일 watch는 안정성을 위해 쓰지 않는다.

## 설치

Homebrew:

```bash
brew install netwaif/tap/mat
```

또는 소스 빌드 (Go 1.22 이상):

```bash
git clone https://github.com/netwaif/mat.git
cd mat
go build -o mat .
```

소스로 빌드한 경우엔 `mat` 대신 `./mat`로 실행한다.

## 사용

starter root를 가리켜야 동작한다. root는 `MAT_ROOT` 환경변수, 없으면 현재 디렉토리.

```bash
MAT_ROOT=~/VSCodeWorkspace/MultiAgent mat            # 활성 작업 자동 선택
MAT_ROOT=~/VSCodeWorkspace/MultiAgent mat <task>     # 특정 작업에 고정
```

활성 작업 결정 순서: ① 인자로 준 작업 → ② status가 `in_progress`·`reviewing`·`waiting_*`인 것 중 가장 최근 수정된 것 → ③ 없으면 작업 목록 모달.

### 키 조작

| 키 | 동작 |
|----|------|
| `r` | 즉시 새로고침 (2초 폴링을 안 기다림) |
| `t` | 작업 전환 (`j/k` 선택, `enter` 열기, `esc` 취소) |
| `L` / `l` | 로그 모달 (`j/k` 스크롤, `g/G` 처음·끝, `esc` 닫기) |
| `q` | 종료 |

## 상태

동작하는 read-only 관찰 도구. starter 표준 레이아웃을 따르는 작업을 모니터링한다.


$env:MAT_ROOT = "C:\DEV\sourcecode\Java-Service-Tree-Framework\"