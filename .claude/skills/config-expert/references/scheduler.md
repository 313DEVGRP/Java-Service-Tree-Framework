# 동적 크론 스케줄러

`SKILL.md` §4 의 상세판. 정본은 `com/arms/config/DynamicSchedulerConfig.java` 와
`com/arms/api/schedule/**`.

---

## 1. 구성 요소

| 클래스 | 역할 |
|--------|------|
| `DynamicSchedulerConfig` | `SchedulingConfigurer`. 크론 작업 등록/취소의 유일한 주체 |
| `ScheduleMapProvider` | `ScheduleMapVO` 홀더. **`ScheduleServiceImpl` ↔ `DynamicSchedulerConfig` 순환참조 차단용** |
| `ScheduleTaskDispatcher` | `CommandLineRunner`. Feign 무인자 메서드를 `이름 → Runnable` 로 등록 |
| `ScheduleInitializer` | `ApplicationReadyEvent` 리스너. 기동 완료 후 최초 등록 |
| `ScheduleSavedEvent` | 화면 저장 후 재등록 트리거 |
| `ScheduleServiceImpl` | Gitea `schedule-config` 읽기/쓰기 + 수동 실행 위임 |
| `ScheduleFileReader` | yml ↔ VO 변환 |

`taskScheduler` 빈 이름은 `dynamicTaskScheduler`, 풀 크기 10, 스레드 접두 `Dynamic-scheduler-`.

---

## 2. yml 포맷 (Gitea `schedule-config` 저장소)

```yaml
schedule:
  - name: "updateReqStatusFromElasticsearch"
    cron: "0 0/10 * * * *"
    notes: "ES 기준 요구사항 상태 갱신"
    enabled: true
  - name: "serverInfoBackup"
    cron: "0 0 3 * * *"
    notes: "서버 정보 백업"
    enabled: false
```

- 최상위 키는 `schedule` 고정(`ScheduleFileReader.ScheduleListWrapper`).
- `cron` 은 **Spring 6필드 크론**(초 분 시 일 월 요일). Unix 5필드를 넣으면 등록 시점에 예외가 난다.
- 파일 하나가 `ScheduleMapVO.scheduleInfoMap` 의 한 항목(key = 확장자 없는 파일명)이 된다.
- `ScheduleInfoVO` 에 `methodName` 필드는 **주석 처리되어 있다.** `name` 하나가 식별자 겸 디스패치 키다
  (`DynamicSchedulerConfig` 에 `String methodName = scheduleInfo.getName(); // 임시처리` 로 남아 있음).

---

## 3. 디스패치 계약 (`ScheduleTaskDispatcher`)

```java
Map<String, Object> feignClientBeans = applicationContext.getBeansWithAnnotation(FeignClient.class);
// 각 빈의 @FeignClient 인터페이스를 찾아
//   public 이고 getParameters().length == 0 인 메서드만
//   feignClientTaskMap.put(method.getName(), Runnable)
```

기동 로그에 등록/스킵이 그대로 찍힌다:

```
  Added task:  updateReqStatusFromElasticsearch
  Skipping method (has parameters or not public):  almIssueMergeWithReindex
```

### 현재 등록 가능한 무인자 메서드

`BackendCoreCommunicator` (`@FeignClient(name="backend-core", url="${arms.backend-core.url}")`)

| 메서드 | 대상 경로 |
|--------|----------|
| `updateReqStatusFromElasticsearch` | `GET /arms/scheduler/pdservice/reqstatus/updateFromES` |
| `retryFailedReqStatusCreationToElasticsearch` | `GET .../recreateFailedReqIssue` |
| `executeSequentialSchedules` | `GET .../executeSequentialSchedules/storeToES` |
| `executeIncrementalIssueSequentialSchedules` | `GET .../increment/executeSequentialSchedules/storeToES` |
| `cacheStatusMappingData` | `PUT /arms/scheduler/cacheStatusMappingData` |
| `syncAtlassianDirectoryUsers` | `GET /arms/scheduler/atlassian/directory-user/sync` |
| `getTestA` · `postTestA` | 테스트용 |

`EngineCommunicator` (`@FeignClient(name="engine-fire", url="${arms.engine-fire.url}")`)

| 메서드 | 대상 경로 |
|--------|----------|
| `serverInfoBackup` | `POST /engine/serverInfo/backup/scheduler` |
| `keepAlive` | `GET /engine/connection/keep-alive` |
| `almIssueMergeWithReindex` | `POST /engine/index/alm-issue/merge-with-reindex` |
| `fluentdMergeWithReindex` | `POST /engine/index/fluentd/merge-with-reindex` |
| `updateArmsStateCategory` | `PUT /engine/jira/arms-state-category` |
| `indexBackup` | `POST /engine/admin/schedule/index/backup` |

> 파라미터가 있는 오버로드(`almIssueMergeWithReindex(int day)`, `getScheduleHistory(SearchDTO)`,
> `executeIncrementalIssueWithDateRangeSequentialSchedules(String,String)`)는 **디스패처에 등록되지 않는다.**
> 크론으로 돌릴 수 없고 `ScheduleController` 수동 엔드포인트로만 실행된다.

### 주의: 디스패처는 Feign 프록시를 **직접** 호출한다

`ScheduleServiceImpl` 을 거치지 않는다. 그래서 크론 실행 시에는
`ScheduleServiceImpl.almIssueMergeWithReindex()` 의 **라이선스 검사(`isExistLicenseNumber`)가 적용되지 않는다.**
수동 실행(`ScheduleController` → `ScheduleServiceImpl`)과 크론 실행의 동작이 다르다는 점을 기억한다.

---

## 4. 등록 흐름 (`DynamicSchedulerConfig.scheduleTasks`)

```java
for (ScheduledTask task : scheduledTasks) task.cancel();   // 기존 전부 취소
scheduledTasks.clear();

scheduleInfoMap.forEach((fileName, list) -> {
    for (ScheduleInfoVO info : list) {
        if (!Boolean.TRUE.equals(info.getEnabled())) continue;   // enabled=false 는 건너뜀
        Runnable logic = dispatcher.contains(name) ? dispatcher.getTask(name) : null;
        Runnable task  = (logic != null)
            ? 계측 래퍼(시작/종료/소요ms 로그, 예외는 잡아서 로그만)
            : () -> log.info("... (No business logic mapped)");
        scheduledTasks.add(taskRegistrar.scheduleCronTask(new CronTask(task, cron)));
    }
});
```

- `task.cancel()` 은 **이미 실행 중인 작업을 중단하지 않는다**(소스 주석도 "동작하는 schedule 에 대한 방법 고민"으로 남아 있다).
  재등록 직후 잠깐 구·신 작업이 겹칠 수 있다.
- 계측 래퍼가 예외를 삼킨다 → 스케줄 실패는 `Error during execution of [...]` **로그로만** 드러난다.
- 성공 시 `Finished [name] from [file] in {ms} ms` 가 남는다. 이 로그가 없으면 등록 자체가 안 된 것이다.

---

## 5. 재등록 트리거 3종

### ① 기동 (`ScheduleInitializer`)

`ApplicationReadyEvent` → `dynamicSchedulerConfig.refreshSchedules()`.
실패하면 `RuntimeException` 으로 감싸 다시 던진다 → **Gitea 접근이 안 되면 기동이 시끄럽게 깨진다.**

### ② 화면 저장 (`POST /admin/schedule/saveScheduleList?fileName=<이름>`)

```
① gitea.schedule-config 디렉터리 조회
② fileName + ".yml" 이 이미 있는지 확인 + SHA 획득
③ ScheduleFileReader.convertScheduleListToYaml 로 본문 생성
④ 있으면 GiteaHttpURLConnection.updateFile (PUT)
   없으면 "File does not exists." 반환하고 끝 ← 신규 생성 안 함
⑤ 200 이면 getScheduleList() 재조회 → ScheduleMapProvider 갱신 → ScheduleSavedEvent 발행
```

`ScheduleSavedEvent` → `@EventListener` `onScheduleSaved()` → `scheduleTasks()`.

> `convertScheduleListToYaml` 은 문자열 연결로 YAML 을 만든다.
> `notes` 나 `name` 에 `"` · 개행이 들어가면 **YAML 이 깨져 다음 로드에서 스케줄 전체가 사라진다.**
> 프론트 입력 제한이 방어선이므로, 이 경로에 새 필드를 추가할 때는 이스케이프를 반드시 고려한다.

### ③ Gitea 웹훅 (`POST /auth-sche/api/schedule/refresh`)

```java
Set<String> refreshedKeys = contextRefresher.refresh();   // configDataContextRefresher
// → RefreshScopeRefreshedEvent → DynamicSchedulerConfig.onRefresh()
//   onRefresh() 는 scheduleService.getScheduleList() 로 Gitea 를 다시 읽고 재등록
```

`@SlackSendAlarm(messageOnEnd = "배치 스케쥴 리플레시 및 적용 완료")` 가 붙어 stg/live 에서 알림이 간다.

---

## 6. 조회·이력 API

| 엔드포인트 | 출처 | 비고 |
|-----------|------|------|
| `GET /admin/schedule/getScheduleList` | **Gitea 를 다시 읽는다** | 파일 기준 최신값 |
| `GET /admin/schedule/getCurrentScheduleList` | `ScheduleMapProvider` **메모리** | 현재 등록 기준. `ScheduleDetailVO.apiRegistered` 는 빌더에서 채우지 않아 항상 `false` |
| `POST /admin/schedule/getScheduleHistory` | `EngineCommunicator.getScheduleHistory` | Engine-Fire 의 `schedule-history-log` 인덱스 |

둘이 다르면 "파일은 바뀌었는데 재등록이 안 됐다" 는 뜻이다 — §5 의 트리거를 확인한다.

---

## 7. "스케줄이 안 돈다" 진단 순서

1. 기동 로그에 `Added task: <name>` 이 있는가?
   - 없으면 → Feign 무인자 메서드가 없거나 파라미터가 있다.
2. `Registered [<name>] from [<file>] with cron [<cron>]` 이 있는가?
   - 없으면 → yml 에 없거나 `enabled: false` 거나, Gitea 읽기가 실패했다.
3. 실행 시각에 `Executing [<name>]` 이 있는가?
   - 있는데 `(No business logic mapped)` 가 붙어 있으면 → 1번 문제(이름 불일치).
4. `Error during execution of [<name>]` 이 있는가?
   - 있으면 다운스트림(Backend-Core / Engine-Fire) 문제. Feign 대상 URL(`arms.*.url`)부터 확인.
5. `getCurrentScheduleList` 와 `getScheduleList` 를 비교한다(§6).
6. 크론 식이 **6필드**인지 확인한다.
