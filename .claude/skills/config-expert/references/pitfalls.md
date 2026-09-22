# 함정 모음

착수 전 한 번, 이상 동작이 보일 때 한 번 훑는다. 전부 **코드에서 확인된 사실**이다.

---

## A. 스택을 착각해서 생기는 것

| # | 함정 | 실제 |
|---|------|------|
| A1 | Middle-Proxy 습관으로 `Mono`/`Flux` 컨트롤러를 작성 | 이 모듈은 **MVC(Tomcat)** 다. `starter-web` 이 있으면 webflux 가 있어도 서블릿으로 뜬다. 값을 직접 반환한다 |
| A2 | Middle-Proxy 규칙대로 Feign 에 `@RequestBody` 를 피함 | 여기는 MVC 라 기본 `SpringEncoder` 가 살아 있다. `EngineCommunicator.getScheduleHistory` 가 실제로 쓴다 |
| A3 | JPA·`@Transactional` 도입 | **DB 가 없다.** 영속은 Gitea 파일이다 |
| A4 | `GiteaRepositoryProvider` 를 직접 주입 | 진입점은 `GitFileService`. Provider 직접 사용은 owner/branch 를 손으로 넘겨야 해서 규약이 깨진다 |
| A5 | 스택 A 의 `serialize` 결과를 스택 B 의 `updateFile` 에 전달 | **이중 Base64.** A 는 인코딩된 문자열을 넘기고, B 는 평문을 받아 내부에서 인코딩한다 |

---

## B. 설정 전파

| # | 함정 | 실제 |
|---|------|------|
| B1 | 설정 파일을 push 했는데 반영 안 됨 | `default-label: main` — **`main` 브랜치**여야 한다. 이 저장소의 작업 브랜치 `dev` 와 다르다 |
| B2 | 파일명을 적당히 지음 | 클라이언트 `spring.application.name` 과 **정확히** 일치해야 Config Server 가 서빙한다 |
| B3 | 웹훅은 200 인데 아무 일도 없음 | 정규식 불일치 또는 `clients.urls` 에 key 없음. 둘 다 조용히 스킵되고 응답은 항상 200 `"Processed"` |
| B4 | refresh 실패를 응답으로 알 수 있다고 가정 | `.subscribe()` fire-and-forget. 성공/실패는 로그(`Refreshed:` / `Error refreshing`)에만 남는다 |
| B5 | Global-Config 자기 설정도 웹훅으로 갱신될 거라 기대 | key 가 `globalconfig` 로 나오는데 `clients.urls` 에 없다 → 재배포해야 한다 |
| B6 | 새 모듈을 `arms.*.url` 에만 추가 | `arms.*` 는 Feign 용, `clients.urls.*` 는 refresh 용. **별개다** |
| B7 | 새 모듈 이름이 정규식에 안 잡힘 | 접미사 그룹 `(Core\|Fire\|Proxy\|Hub\|AI)` 에 추가해야 한다 |
| B8 | 임시 프로파일을 `IGNORED_PROFILES` 에 추가 | `spring.profiles.group` 으로 상시 로드되는 프로파일(AI 의 `prompt` 등)을 넣으면 정식 설정이 반영 안 된다 |
| B9 | 설정 서버가 죽었는데 조용함 | 클라이언트가 `optional:configserver:` 를 쓴다 → 설정 없이 기본값으로 기동한다 |
| B10 | refresh 했는데 동작이 그대로 | `@RefreshScope`/`@ConfigurationProperties` 만 재바인딩된다. 커넥션 풀·리스너 컨테이너·게이트웨이 라우트 등은 재기동이 필요할 수 있다 |
| B11 | 설정 서버 로컬 클론을 손으로 고침 | `force-pull: true` 라 다음 pull 에서 날아간다 |

---

## C. 스케줄러

| # | 함정 | 실제 |
|---|------|------|
| C1 | yml 에 스케줄만 추가 | **Feign 무인자 메서드가 없으면** 크론은 돌지만 `(No business logic mapped)` 로그만 남는다 |
| C2 | 파라미터 있는 메서드를 크론으로 돌리려 함 | 디스패처는 `getParameters().length == 0` 만 등록한다 |
| C3 | 5필드 크론 사용 | Spring 은 **6필드**(초 분 시 일 월 요일) |
| C4 | 새 스케줄 파일을 화면에서 저장 | `saveScheduleList` 는 **기존 파일만 갱신**한다. 없으면 `"File does not exists."` 반환 |
| C5 | `notes`/`name` 에 `"` 나 개행 입력 | `convertScheduleListToYaml` 이 문자열 연결로 YAML 을 만든다 → 파일이 깨져 **다음 로드에서 스케줄 전체가 사라진다** |
| C6 | 크론 실행도 라이선스 검사를 탄다고 가정 | 디스패처는 **Feign 프록시를 직접** 호출한다. `ScheduleServiceImpl` 의 `isExistLicenseNumber` 게이트는 **수동 실행 경로에만** 적용된다 |
| C7 | 재등록하면 실행 중 작업이 즉시 멈출 거라 기대 | `ScheduledTask.cancel()` 은 진행 중 작업을 중단하지 않는다. 잠깐 겹칠 수 있다 |
| C8 | 스케줄 실패를 응답/예외로 감지하려 함 | 계측 래퍼가 예외를 삼키고 `Error during execution of [...]` 로그만 남긴다 |
| C9 | `getCurrentScheduleList` 의 `apiRegistered` 를 신뢰 | 빌더에서 채우지 않아 **항상 `false`** |
| C10 | 두 Feign 인터페이스에 같은 이름의 무인자 메서드 | 나중에 스캔된 쪽이 앞을 덮는다(경고 없음) |
| C11 | Gitea 없이 로컬 기동 | `ScheduleInitializer` 가 `ApplicationReadyEvent` 에서 `RuntimeException` 을 던진다 |

---

## D. 언어팩

| # | 함정 | 실제 |
|---|------|------|
| D1 | Gitea 에서 직접 고쳤는데 화면이 그대로 | 캐시가 살아 있으면 저장소를 안 본다. `/refresh` 엔드포인트를 쳐야 한다 |
| D2 | 레플리카가 여러 개인데 refresh 한 번 | 캐시가 **프로세스 로컬**이다. 인스턴스마다 따로 논다 |
| D3 | 키 이름에 의미상 `.` 사용 | `unflatten` 이 `.` 으로 쪼개 중첩 구조를 만든다. 되돌릴 수 없다 |
| D4 | `LanguagePackFileVO.totalKeys`/`lastModified` 사용 | `getLanguagePackFiles` 가 채우지 않는다(항상 기본값) |
| D5 | 언어팩 값에 숫자/배열 기대 | `flatten` 이 `toString()` 으로 문자열화한다 |
| D6 | `getAllLanguagePackContents` 가 전부 준다고 가정 | 개별 로드 실패는 로그만 남기고 **응답에서 조용히 빠진다** |
| D7 | 동시 수정 안전성 가정 | 캐시가 `HashMap`/`ArrayList` 다 |

---

## E. 경로 · 노출 · 보안

| # | 함정 | 실제 |
|---|------|------|
| E1 | `/admin/**` 이니 관리자만 접근 가능하다고 가정 | **이 모듈에 Spring Security 가 없다.** 접두는 관례일 뿐, 보호는 게이트웨이와 내부망뿐이다 |
| E2 | 최상위에 `@PathVariable` 로 시작하는 경로 추가 | Config Server 의 `/{app}/{profile}[/{label}]` 패턴과 충돌한다. 리터럴 접두로 시작할 것 |
| E3 | `spring.mvc.pathmatch.matching-strategy` 제거 | Config Server·Springfox 호환 우회다. 제거하면 기동/문서가 깨진다 |
| E4 | `Swagger2Config` 의 static BeanPostProcessor 정리 | Boot 2.6 + Springfox 3.0 NPE 우회다. 제거하면 기동이 깨진다 |
| E5 | 액추에이터가 안전하다고 가정 | `exposure.include: "*"` + `endpoint.shutdown.enabled: true`. `POST /actuator/shutdown` 하나로 A-RMS 전체 부팅이 막힌다 |
| E6 | `ScmController` 를 손봄 | JGit 실험 코드 + **평문 GitHub PAT**. 토큰 폐기 + 파일 제거를 보고하고 기능 작업으로는 건드리지 않는다 |
| E7 | 시크릿을 문서·로그·새 파일로 옮김 | Gitea 계정/토큰(`application-*.yml`), Sonar(`build.gradle`), Nexus(`settings.xml`) 전부 평문이다. **복제 금지** |

---

## F. 빌드 · 배포

| # | 함정 | 실제 |
|---|------|------|
| F1 | `./gradlew test` 통과를 검증 근거로 씀 | **`src/test` 가 없다.** 아무것도 검증하지 않는다 |
| F2 | 로컬 빌드 버전이 CI 와 달라 당황 | Windows/Mac 은 `wget` 을 건너뛰고 커밋된 스텁 `metadata.xml`(latest 0.0.1)을 읽는다 → `26.0.0` |
| F3 | 오프라인에서 `./gradlew build` 시도 | Nexus 메타데이터 + `settings.xml` 자격증명이 필요하다. `compileJava` 로 확인한다 |
| F4 | `generateLicenseReport` 실행 | `allowed-licenses.json` 이 저장소에 없다 |
| F5 | `docker-entrypoint.sh` 를 이 저장소에서만 수정 | 4개 모듈 공통 파일이다. 동시 변경으로 제안한다 |
| F6 | APM 이 붙어 있다고 가정 | `*_MONITOR_ELK_OPTS` 가 정의만 되고 exec 줄에서 쓰이지 않는다. 붙이려면 `JAVA_OPTS` 로 주입 |
| F7 | `starter-web` 을 빼고 리액티브로 전환 | 앱이 통째로 WebFlux 가 되어 AOP(`RequestFacade`)·Swagger·Config Server 매핑이 함께 깨진다 |
| F8 | JGit/commons-io 를 `build.gradle` 에서 찾음 | 선언이 없다. `spring-cloud-config-server` 전이 의존이다 |

---

## G. 관측

| # | 함정 | 실제 |
|---|------|------|
| G1 | dev 에서 Slack 이 안 와서 버그로 판단 | `stg`/`live` 프로파일에서만 전송한다 |
| G2 | 예외 알림을 추가로 붙임 | `LoggingAdvice` + `ErrorControllerAdvice` 로 **이미 두 번** 간다 |
| G3 | 컨트롤러에 진입/종료 로그 추가 | `LoggingAdvice` 가 `com.arms..controller.*.*` · `..service.*.*` 전체에 자동으로 남긴다 |
| G4 | stg/live 로그가 다 남을 거라 가정 | `ASYNC_CONSOLE` 이 `neverBlock=true` 라 부하 시 유실될 수 있다 |
| G5 | `HighlightingCompositeConverterCustom` 을 이동/개명 | logback xml 이 FQCN 으로 참조한다. 로깅이 통째로 깨진다 |
| G6 | 수동 실행 API 가 200 이면 성공이라 판단 | 대부분 `void` 반환이고 다운스트림 결과를 기다리지 않는다 |
