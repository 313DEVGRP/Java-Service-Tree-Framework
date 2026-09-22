---
name: config-expert
description: >-
  A-RMS 중앙 설정·스케줄 허브 저장소(Java-Service-Tree-Framework-Global-Config)의 작업 규약.
  Spring Boot 2.6 · Java 11 · Spring Cloud Config Server(Gitea 백엔드) 기반이며
  Middle-Proxy(WebFlux)와 달리 Spring MVC(Tomcat)이고 인증이 없다.
  Config Server 설정 배포 · Gitea 웹훅 → /actuator/refresh 전파 · 동적 크론 스케줄러 ·
  언어팩(i18n) · system-info(라이선스) · Gitea 파일 CRUD 프레임워크(gcframework)를 건드릴 때 반드시 먼저 읽을 것.
  javaServiceTreeFrameworkBackendCore.yml · clients.urls · ConfigServerWebhookController ·
  IGNORED_PROFILES · ContextRefresher · RefreshScopeRefreshedEvent · ScheduleTaskDispatcher ·
  ScheduleMapProvider · DynamicSchedulerConfig · ScheduleSavedEvent · GitFileService · GiteaRepositoryProvider ·
  AbstractContentParser · GiteaFileUtil · GiteaHttpURLConnection · LanguageConfigServiceImpl ·
  flattenLanguagePack · SystemInfoVO · isExistLicenseNumber · SlackSendAlarm · 설정이 반영 안 됨 ·
  스케줄이 안 돈다 · 언어팩이 안 바뀐다 같은 주제도 대상이다.
  "글로벌컨피그", "global config", "설정 서버", "config server", "컨피그 서버", "스케줄러 설정",
  "언어팩", "33133" 요청도 여기서 시작한다.
  WebFlux(Mono/Flux 반환 · ServerHttpRequest)나 JPA로 작성하지 않는다 — 이 저장소는 MVC이고 DB가 없다.
---

# A-RMS Global-Config 작업 규약

대상 저장소: `Java-Service-Tree-Framework-Global-Config/`
(워크스페이스 루트 `C:\DEV\Project\Java-Service-Tree-Framework` 하위, 중첩 git 저장소 · 브랜치 `dev`)

이 저장소는 **A-RMS 전 모듈의 설정 원천이자 배치 스케줄러**다. 여기서 설정을 잘못 내보내면
화면 하나가 아니라 **모든 모듈이 잘못된 값으로 재기동 없이 갈아탄다.** 그리고 이 모듈에는
**인증이 없고 테스트가 한 건도 없다.** 아래 계약을 먼저 파악하는 것이 가장 비용이 싼 길이다.

---

## 0. 30초 요약 — 반드시 먼저 각인할 것

| 항목 | 값 |
|------|----|
| 스택 | Spring Boot **2.6.15** · Spring Cloud **2021.0.9** · **Java 11** · Gradle(wrapper 동봉) |
| 웹 모델 | **Spring MVC (Tomcat)**. `spring-boot-starter-webflux`도 있지만 `WebClient`용이다 |
| 역할 | ① Spring Cloud **Config Server** ② 자체 REST 앱(스케줄·언어팩·system-info) |
| 영속 | **DB 없음.** Gitea 저장소가 저장소 역할을 한다 |
| 인증 | **없음.** `spring-boot-starter-security` 의존성 자체가 없다 |
| 포트 | 33133 · Swagger `/global-config-api/swagger-ui/` |
| 설정 백엔드 | Gitea `root/ARMS`(label `main`), 그 외 `SystemInfo` · `schedule-config` · `language-config` 저장소 |
| 테스트 | **`src/test` 자체가 없다** |

> 저장소 `README.md`는 프레임워크 홍보 문서이고 이 모듈 설명이 아니다. **코드가 정본**이다.
> 버전 사실이 의심되면 언제나 `build.gradle`이 정본이다.

### 이 저장소에서 쓰면 안 되는 것

```
✗ Mono / Flux 반환 컨트롤러             → ✓ 값 직접 반환 (MVC)
✗ ServerHttpRequest / ServerWebExchange → ✓ HttpServletRequest (필요할 때만)
✗ @Entity / @Transactional / JPA        → ✓ Gitea 파일 CRUD (§3)
✗ RestTemplate 새로 도입                 → ✓ Feign(모듈 간) 또는 기존 WebClient.Builder
✗ 최상위 @PathVariable 경로              → ✓ 리터럴 경로 (Config Server 패턴과 충돌, §5.3)
✗ 새 시크릿을 yml·코드에 평문 추가         → ✓ 기존 키 경로 참조 / 환경변수
```

---

## 1. 요청이 어디로 가는지 먼저 판별한다

이 프로세스는 **같은 포트에서 두 가지 앱**을 동시에 서빙한다. 어느 쪽인지 모르면 엉뚱한 파일을 고친다.

```
                      Global-Config :33133
                             │
 ┌──(A) Spring Cloud Config Server ── @EnableConfigServer 가 매핑하는 경로
 │      GET /{app}/{profile}[/{label}] · /{app}-{profile}.yml · /{label}/{app}-{profile}.yml ...
 │      → Gitea root/ARMS 저장소의 yml 을 읽어 Environment 로 반환
 │      → 코드에 없다. 의존성이 만들어 주는 것이다
 │
 └──(B) 이 저장소의 자체 컨트롤러
        src/main/java/com/arms/api/<domain>/controller/
```

**(B)에 해당하는 자체 도메인 지도** (실제 `@RequestMapping` 기준)

| 도메인 | 컨트롤러 경로 | 게이트웨이 접두(프론트가 부르는 경로) | 하는 일 |
|--------|-------------|--------------------------------|---------|
| `schedule` | `/admin/schedule/**` | `/auth-admin/yml/schedule/**` | 스케줄 목록·저장·이력, 배치 수동 실행 |
| `schedule`(웹훅) | `/auth-sche/api/schedule/refresh` | (Gitea 웹훅이 직접 호출) | `ContextRefresher`로 스케줄 재적재 |
| `languageconfig` | `/admin/language-config/**` · `/anonymous/language-config/**` | `/auth-admin/yml/**` · `/auth-anon/yml/**` | 언어팩 조회·수정·삭제·refresh |
| `systeminfo` | `/system-info/org-link` | (Backend-Core `GlobalConfigService` Feign) | 조직별 시스템/라이선스 정보 |
| `configserver`(웹훅) | `/api/config-server/config-changed` | (Gitea 웹훅이 직접 호출) | 변경 파일 → 대상 모듈 `/actuator/refresh` |
| `scmframework` | `/gitInitTest` · `/gitHubCloneTest` · `/gitAddTest` · `/gitCommitTest` · `/gitPushTest` · `/gitBranchMergeTest` | - | **JGit 실험용 잔재. 건드리지 말 것**(§9) |

> 게이트웨이 접두는 Middle-Proxy가 `RewritePath`로 벗겨서 보낸다. 라우트 정의는
> **이 저장소에도 Middle-Proxy에도 없고** Gitea `root/ARMS`의 yml에 있다.
> 프론트 경로와 컨트롤러 경로가 안 맞아 보이면 그건 라우트 문제다(§5.4).

---

## 2. Config Server 계약 — 이 저장소의 1번 책임

### 2.1 무엇이 어디서 오는가

```
Gitea root/ARMS (label: main)
   javaServiceTreeFrameworkBackendCore.yml        ← 공통
   javaServiceTreeFrameworkBackendCore-dev.yml    ← 프로파일별
   javaServiceTreeFrameworkMiddleProxy-live.yml
   javaServiceTreeFrameworkEngineFire-stg.yml
   ...
        │  clone-on-start: true / force-pull: true
        ▼
Global-Config :33133  (@EnableConfigServer)
        │
        ▼  각 모듈이 부팅 시 가져가서 자기 설정과 병합
Backend-Core · Middle-Proxy · Engine-Fire · AI · Broker-Hub
```

파일명은 클라이언트의 `spring.application.name`과 **정확히** 일치해야 한다.

| 모듈 | `spring.application.name` | 설정 파일명 |
|------|--------------------------|------------|
| Backend-Core | `javaServiceTreeFrameworkBackendCore` | `javaServiceTreeFrameworkBackendCore[-<profile>].yml` |
| Middle-Proxy | `javaServiceTreeFrameworkMiddleProxy` | `javaServiceTreeFrameworkMiddleProxy[-<profile>].yml` |
| Engine-Fire | `javaServiceTreeFrameworkEngineFire` | 〃 |
| Global-Config(자기 자신) | `javaServiceTreeFrameworkGlobalConfig` | 〃 (단, §2.4 참조) |

### 2.2 클라이언트 접속 방식이 모듈마다 다르다

| 모듈 | 방식 | 파일 |
|------|------|------|
| Backend-Core | **레거시 bootstrap**(`spring.cloud.config.uri`) | `bootstrap-{dev,stg,live,mklee}.yml` |
| Middle-Proxy · Engine-Fire | **ConfigData**(`spring.config.import: optional:configserver:...`) | `application-{dev,stg,live}.yml` |
| Global-Config | 없음(자기 자신을 클라이언트로 쓰지 않는다) | - |

`optional:` 접두가 붙어 있으므로 **설정 서버가 죽어도 클라이언트는 기동한다.**
그래서 "설정이 옛날 값이다"는 장애가 조용히 지나간다. 배포 후에는 클라이언트의 `/actuator/env`를 확인한다.

### 2.3 설정 변경 전파 체인 (가장 자주 깨지는 곳)

```
① 개발자가 Gitea root/ARMS 에 yml push
      ▼
② Gitea 웹훅 → POST /api/config-server/config-changed  (GitHub 형식 payload)
      ▼
③ commits[].added/modified/removed 를 모아 파일명 목록 생성
      ▼
④ 정규식 javaServiceTreeFramework(\w+?)(Core|Fire|Proxy|Hub|AI)?(?:-(\w+))?\.yml
      · group(3) = 프로파일. IGNORED_PROFILES(local, mklee) 면 스킵
      · key = group(1).toLowerCase() + ("-" + group(2).toLowerCase())
        예) ...BackendCore-dev.yml → "backend-core"
            ...MiddleProxy.yml     → "middle-proxy"
            ...EngineFire-live.yml → "engine-fire"
            ...AI.yml              → "ai"
            ...BrokerHub.yml       → "broker-hub"
      ▼
⑤ clients.urls[key].url + "/actuator/refresh" 로 WebClient POST (fire-and-forget)
      ▼
⑥ 클라이언트가 @RefreshScope 빈을 재바인딩
```

**끊어지는 지점 체크리스트**

- 파일명이 정규식에 안 맞으면 조용히 스킵된다 → 로그 `대상 아님(패턴 불일치)`를 찾는다.
- `clients.urls`에 key가 없으면 아무 일도 안 일어난다 → `application-<profile>.yml`의 `clients.urls`를 본다.
- `sendRefreshRequest`는 `.subscribe()`로 던지고 끝난다. **실패해도 HTTP 응답은 200 "Processed"**다.
- 새 모듈을 추가하면 **정규식 접미사 그룹**(`Core|Fire|Proxy|Hub|AI`)과 **`clients.urls`**를 둘 다 고쳐야 한다.
- 서비스에 반영하면 안 되는 개인용 프로파일이면 `IGNORED_PROFILES`에 추가한다.
  단, `spring.profiles.group`으로 상시 로드되는 프로파일(예: AI의 `prompt`)은 넣으면 안 된다.

### 2.4 Global-Config 자신은 이 체인으로 갱신되지 않는다

`javaServiceTreeFrameworkGlobalConfig.yml`은 정규식상 key가 `globalconfig`가 되고,
`clients.urls`에는 그 키가 없다 → 자기 자신에게는 refresh를 쏘지 않는다.
이 모듈의 설정을 바꾸려면 **저장소의 `application-*.yml`을 고치고 재배포**한다.

상세: `references/config-server.md`

---

## 3. Gitea 파일 접근 — 두 스택, 절대 섞지 않는다

이 저장소에는 Gitea REST를 때리는 코드가 **두 벌** 있다. 도메인마다 하나만 쓴다.

### 스택 A — `gcframework` (신규 · language-config 전용)

```
GitFileService(Impl)
   ├─ providers : Map<RepoType, GitRepositoryProvider>   (GITEA 구현체만 존재)
   └─ parsers   : Map<확장자, AbstractContentParser>      (json → Json…, yaml/yml → Yaml…)
```

- 진입점은 **항상 `GitFileService`**. `GiteaRepositoryProvider`를 직접 주입하지 않는다.
- owner·branch는 `GiteaUserConfig`에서 자동으로 채워진다. 호출자가 넘기지 않는다.
- **파서가 다루는 `content`는 항상 Base64다.** `parse`/`parseToMap`은 디코드하고,
  `serialize`/`serializeFromMap`은 인코드해서 돌려준다. Provider는 **이미 인코딩된 문자열**을 받는다.
- 확장자로 파서를 고른다 → 새 형식을 지원하려면 `AbstractContentParser`를 상속한 `@Component`를 추가하면 자동 등록된다.
- `upsertFile`은 기존 파일 SHA를 스스로 조회해 붙인다. `deleteFile`은 SHA가 없으면 `false`를 반환한다(예외 아님).

### 스택 B — 레거시(`GiteaFileUtil` + `GiteaHttpURLConnection` · schedule · system-info)

- 디렉터리 목록을 받아 `download_url`을 뽑고 **raw 파일을 직접 GET**한다.
- `GiteaHttpURLConnection.updateFile/createFile/deleteFile`은 **평문을 받아 내부에서 Base64 인코딩**한다
  (스택 A와 규약이 정반대다 — 헷갈리면 파일이 이중 인코딩된다).
- 요청 바디를 `String.format` 문자열로 만든다 → 내용에 `"`나 개행이 있으면 깨진다.

`YamlFileUtils`는 스택 B의 더 오래된 버전으로, `ScheduleServiceImpl`이 주입만 하고 **쓰지 않는다.**

상세: `references/gitea-file-access.md`

---

## 4. 동적 스케줄러 — 이 저장소에서 가장 복잡한 흐름

```
Gitea schedule-config 저장소의 *.yml
   schedule:
     - name: "updateReqStatusFromElasticsearch"   ← Feign 무인자 메서드명과 동일해야 한다
       cron: "0 0/10 * * * *"
       notes: "..."
       enabled: true
        │
        ▼ ScheduleServiceImpl.getScheduleList()  (레거시 스택 B로 읽음)
   ScheduleMapVO { fileName → List<ScheduleInfoVO> }
        │
        ▼ ScheduleMapProvider (순환참조 차단용 홀더)
   DynamicSchedulerConfig.scheduleTasks()
        │  기존 ScheduledTask 전부 cancel → enabled=true 만 CronTask 로 재등록
        ▼
   ScheduleTaskDispatcher.getTask(name)
        │  @FeignClient 빈들의 public 무인자 메서드를 메서드명으로 맵에 등록해 둠
        ▼
   BackendCoreCommunicator / EngineCommunicator 의 해당 메서드 호출
```

### 4.1 핵심 계약 — 스케줄 `name` = Feign 무인자 메서드명

`ScheduleTaskDispatcher`는 `CommandLineRunner`로 기동 시 `@FeignClient` 빈을 스캔해서
**public이고 파라미터가 0개인 메서드만** `메서드명 → Runnable`로 등록한다.

- 이름이 맵에 없으면 **크론은 등록되지만 로그만 찍고 아무 일도 안 한다**(`No business logic mapped`).
- 파라미터가 있는 메서드(`almIssueMergeWithReindex(int day)` 등)는 **등록되지 않는다.**
  같은 이름의 무인자 오버로드가 있으면 그것이 선택된다.
- 두 Feign 인터페이스에 같은 이름의 무인자 메서드가 있으면 **나중에 스캔된 쪽이 앞을 덮는다.**

**스케줄을 새로 추가하는 순서**

1. `BackendCoreCommunicator` 또는 `EngineCommunicator`에 **무인자** 메서드를 추가한다.
2. (선택) `ScheduleService`/`Impl`과 `ScheduleController`에 수동 실행용 엔드포인트를 만든다.
3. Gitea `schedule-config` 저장소 yml에 `name`을 **1의 메서드명과 똑같이** 적는다.
4. 반영: 화면에서 저장(`/admin/schedule/saveScheduleList`)하거나 Gitea 웹훅으로 `/auth-sche/api/schedule/refresh`를 친다.

### 4.2 재등록이 일어나는 경로는 셋뿐이다

| 트리거 | 경로 |
|--------|------|
| 부팅 완료 | `ScheduleInitializer`(`ApplicationReadyEvent`) → `refreshSchedules()` |
| 화면에서 스케줄 저장 | `saveScheduleList` → 성공(200) 시 `ScheduleSavedEvent` → `onScheduleSaved()` |
| Gitea 웹훅 | `/auth-sche/api/schedule/refresh` → `ContextRefresher.refresh()` → `RefreshScopeRefreshedEvent` → `onRefresh()` |

`saveScheduleList`는 **존재하는 파일만 갱신**한다. 파일이 없으면 `"File does not exists."`를 반환하고
새로 만들지 않는다 → 새 스케줄 파일은 Gitea에서 먼저 만들어야 한다.

상세: `references/scheduler.md`

---

## 5. 경로·노출 — 인증이 없다는 전제로 판단한다

### 5.1 이 모듈에는 Spring Security가 없다

의존성 자체가 없다. `/admin/**`이라는 접두는 **관례일 뿐 강제되지 않는다.**
보호는 오직 ① 게이트웨이(Middle-Proxy)의 `pathMatchers` ② 내부망 배치로만 이루어진다.

### 5.2 액추에이터가 전부 열려 있다

```yaml
management.endpoints.web.exposure.include: "*"
management.endpoint.shutdown.enabled: true
```

`POST /actuator/shutdown` 하나로 설정 서버가 내려간다 → **A-RMS 전체 부팅이 막힌다.**
이 포트를 외부에 노출하는 변경은 절대 하지 않는다. 이 설정을 건드릴 일이 생기면 먼저 보고한다.

### 5.3 Config Server가 루트 경로 패턴을 점유한다

Config Server의 `EnvironmentController`는 `/{name}/{profiles}`, `/{name}/{profiles}/{label}` 같은
**와일드카드 패턴**을 최상위에 매핑한다. 리터럴 경로(`/admin/schedule/...`)는 더 구체적이라 우선하지만,
**최상위에 `@PathVariable`로 시작하는 새 경로를 만들면 충돌한다.** 새 경로는 반드시 리터럴 접두로 시작한다.

`spring.mvc.pathmatch.matching-strategy: ant_path_matcher`는 Config Server·Springfox 호환을 위해 필요하다. 지우지 말 것.

### 5.4 프론트 경로와 컨트롤러 경로가 다르면 라우트를 의심한다

| 프론트(Frontend-Web) | 컨트롤러 |
|---------------------|---------|
| `/auth-admin/yml/language-config/packs/files` | `/admin/language-config/packs/files` |
| `/auth-anon/yml/language-config/packs/language/{lang}` | `/anonymous/language-config/packs/language/{lang}` |
| `/auth-admin/yml/schedule/getCurrentScheduleList` | `/admin/schedule/getCurrentScheduleList` |
| `/auth-admin/yml/saveScheduleList` ⚠️ | `/admin/schedule/saveScheduleList` |

마지막 줄은 접두 규칙이 다른 것들과 어긋난다. Gitea 라우트에 별도 규칙이 있다는 뜻이므로,
**코드를 고치기 전에 라우트부터 확인**한다(라우트 정의는 이 저장소에 없다).

---

## 6. 언어팩 · system-info

### 6.1 언어팩 (`language-config` 저장소의 `<lang>.json`)

- 캐시는 `LanguageConfigServiceImpl`의 **인스턴스 필드**(`HashMap`/`ArrayList`)다.
  → 스레드 안전하지 않고, **레플리카마다 따로 논다.** 수평 확장 시 `/refresh`는 한 인스턴스에만 먹는다.
- 저장(`updateSingleLanguagePack`)은 캐시를 무효화하지만, **조회(`getSingleLanguagePack`)는 캐시가 있으면 Gitea를 보지 않는다.**
  Gitea에서 직접 고친 값은 `/refresh` 엔드포인트를 타야 보인다.
- API는 평면 키(`a.b.c`)를 주고받고, 저장 시 `unflatten`해서 중첩 JSON으로 쓴다.
  → **키 자체에 `.`이 들어가면 구조가 갈라진다.** 새 키를 만들 때 `.`은 계층 구분자 전용이다.
- `getAllLanguagePackContents`는 `availableLanguages`가 비었을 때만 저장소를 훑는다.

### 6.2 system-info (`SystemInfo` 저장소)

- `getSystemInfo(orgLink)` → `system-info_org{orgLink}.yml`이 있으면 그것, 없으면 `system-info_base.yml`.
  (enum `SystemInfoFileName.PREFIX` = `"system-info_org"`이고 `application.yml`의 `filename.system-info.prefix`와 값이 다르다 — **enum이 실제로 쓰인다.**)
- `isExistLicenseNumber()`가 **엔진 리인덱싱 스케줄의 실행 게이트**다.
  라이선스 번호가 없으면 `almIssueMergeWithReindex` · `fluentdMergeWithReindex`가 `IllegalStateException`으로 끝난다.
- Backend-Core가 `GlobalConfigService` Feign으로 `/system-info/org-link`를 호출한다 → 시그니처를 바꾸면 Backend-Core도 함께 고쳐야 한다.

상세: `references/domains.md`

---

## 7. 관측 · 알림 · 응답 규약

- **모든 컨트롤러·서비스가 AOP로 감싸진다.** `LoggingAdvice`가 `com.arms..controller.*.*`와
  `com.arms..service.*.*`에 `@Before`/`@AfterReturning`/`@Around`를 건다. 진입·종료 로그를 중복으로 넣지 않는다.
- 예외는 `LoggingAdvice`가 Slack으로 보내고 **다시 던진다** → `ErrorControllerAdvice`가 또 Slack으로 보낸다.
  같은 예외가 두 번 알림 간다. 여기에 세 번째 알림을 추가하지 않는다.
- 응답 봉투: 정상은 `ResponseEntity`로 값 직접 반환, 에러는 `CommonResponse.error(...)` → `ApiResult<T>`(`{success, response, error}`).
  컨트롤러에서 임의 에러 포맷을 만들지 않는다.
- **Slack은 `stg`/`live` 프로파일에서만 나간다**(`SlackNotificationService.isStageOrLiveProfile`).
  dev에서 알림이 안 온다고 버그가 아니다. 채널 enum은 `SlackProperty.Channel.globalconfig` 하나뿐이다.
- 시작/종료 알림이 필요한 엔드포인트에는 `@SlackSendAlarm(messageOnStart=..., messageOnEnd=...)`를 쓴다
  (`@LogAndSlackNotify`는 구형이고 현재 사용처가 없다).

---

## 8. 빌드 · 실행 · 배포

```bash
# 컴파일만 (가장 빠른 검증)
./gradlew compileJava            # Windows: gradlew.bat compileJava

# 로컬 구동: Active Profile = dev, 포트 33133
#   Gitea(www.313.co.kr) 접근이 필요하다
```

- Swagger: `http://127.0.0.1:33133/global-config-api/swagger-ui/`
- **테스트가 없다.** `./gradlew test`는 항상 통과한다 — 검증 근거로 쓰지 말 것.
- `./gradlew build`·`publish`는 Nexus `metadata.xml` 조회와 `settings.xml` 자격증명에 의존해 오프라인에서 실패한다.
- **버전은 자동 계산된다.** `build.gradle`의 `majorVersion`/`minorVersion` + Nexus 최신 버전 → patch 자동 증분.
  Windows·Mac에서는 `wget`을 건너뛰고 **저장소에 커밋된 `metadata.xml`**(오래된 스텁)을 읽는다 → 로컬 버전이 CI와 다르게 나온다. 정상이다.
- Docker 이미지 `313devgrp/java-service-tree-framework-global-config`, 레지스트리 `313.co.kr:5550`,
  배포는 Spinnaker(`spinnaker.properties` 자동 생성).
- `docker-entrypoint.sh`는 **4개 모듈이 동일한 org 공통 파일**이다. 이 저장소에서만 단독으로 고치지 않는다.

상세: `references/ops-and-build.md`

---

## 9. 손대면 안 되는 것 · 먼저 보고할 것

- **`scmframework/controller/ScmController`** — JGit 실험 코드다. GitHub PAT가 **평문으로 하드코딩**되어 있고
  `/gitInitTest` 같은 경로가 인증 없이 열려 있다. 기능 작업으로 이 파일을 건드리지 말고,
  **토큰 폐기 + 파일 제거가 필요하다는 점을 사용자에게 보고**한다(삭제 여부는 사용자 판단).
- `application-*.yml`의 Gitea 계정·토큰, `build.gradle`의 Sonar 자격증명, `settings.xml`의 Nexus 자격증명도
  평문이다. **새 파일·문서·로그로 복제하지 않는다.**
- `private.key` · `public.key` · `license.lic` · `com.arms.license.*`는 라이선스 서명 실험 잔재다
  (Spring 빈이 아니라 `main` 메서드). 서명 로직을 손대야 하면 먼저 확인한다.
- `ThreadPoolConfig`는 `@Configuration`이 주석 처리되어 **비활성**이다. 살리려면 영향 범위를 먼저 보고한다.

---

## 10. 제출 전 자가 점검

- [ ] 컨트롤러가 값을 직접 반환하는가? (`Mono`/`Flux`를 쓰지 않았는가)
- [ ] 새 경로가 리터럴 접두로 시작하는가? Config Server 패턴과 충돌하지 않는가?
- [ ] 새 경로가 게이트웨이 접두 규약(`/admin/**` · `/anonymous/**`)에 맞는가? 무인증 노출 위험을 판단했는가?
- [ ] Gitea 접근이 도메인의 기존 스택(A `gcframework` / B 레거시) 하나로 통일되었는가? Base64 규약을 지켰는가?
- [ ] 스케줄을 추가했다면 **Feign 무인자 메서드**를 먼저 만들고 yml `name`과 일치시켰는가?
- [ ] 모듈을 추가했다면 웹훅 정규식 접미사와 `clients.urls`를 **둘 다** 고쳤는가?
- [ ] 언어팩 키에 계층 구분자 외의 `.`을 넣지 않았는가?
- [ ] 설정 값 변경이 필요하면 **Gitea 저장소 변경 필요**를 보고했는가? (코드에 하드코딩하지 않았는가)
- [ ] 시크릿(Gitea·Sonar·Nexus·Slack) 값을 코드·로그·문서에 복제하지 않았는가?
- [ ] Boot 2.6 / Java 11에서 쓸 수 있는 API만 썼는가? (`jakarta.*` · Java 17 문법 금지)
- [ ] 테스트가 없는 저장소임을 감안해, 새 로직에 순수 단위 테스트를 붙였거나 수동 검증 절차를 제시했는가?

---

## 11. 산출 및 인계

- 사용자 대상 설명은 **한국어**로 한다.
- **commit·push 하지 않는다.** 작업 요약과 커밋 메시지 초안만 제시하고 커밋은 사용자가 한다.
  이 저장소의 실제 컨벤션(YouTrack 연동):
  ```
  feat: [ARMS-1167] #comment GlobalConfig :: Atlassian 사용자 동기화 스케쥴러 기능 추가
  feat : [ARMS-1023] #comment✅9월 버전업 + 비밀번호 변경 26.08.28 #close #time 1h +review SR @sevoon0909
  chore: cloudJiraTestApiRequest 잔여 코드 삭제
  ```
  현재 작업 브랜치는 `dev`다(`main` 아님).
- 확신이 없는 지점(Gitea `root/ARMS`·`schedule-config`·`language-config` 저장소의 실제 내용,
  게이트웨이 라우트 정의, 운영 크론 값)은 추측으로 메우지 말고 **가정을 명시**하거나 질문한다.

---

## 12. 참조 파일 지도

| 파일 | 언제 읽나 |
|------|----------|
| `references/config-server.md` | 설정 배포·프로파일·웹훅 전파·새 모듈 등록을 다룰 때 |
| `references/gitea-file-access.md` | Gitea 파일을 읽고 쓸 때. 두 스택의 API·Base64 규약·에러 처리 |
| `references/scheduler.md` | 스케줄 추가·크론 변경·"스케줄이 안 돈다" 디버깅 |
| `references/domains.md` | language-config · system-info · schedule API의 세부 계약 |
| `references/ops-and-build.md` | 빌드·버전·Docker·배포·Swagger·Slack·로깅 |
| `references/pitfalls.md` | 이상 동작이 보일 때 / 착수 전 함정 확인 |

이 저장소에는 모듈 자체 `docs/ai/` 하네스 문서가 **없다.** 코드가 유일한 정본이다.
