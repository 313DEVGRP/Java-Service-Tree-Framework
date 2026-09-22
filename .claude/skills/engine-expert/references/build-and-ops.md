# 빌드 · 배포 · 인덱스 운영

---

## 1. 빌드

| 항목 | 값 |
|------|----|
| 빌드 도구 | Gradle **8.13** (`gradlew` 래퍼), Groovy DSL |
| Java toolchain | **21** |
| 산출물 | Spring Boot `bootJar` → `javaServiceTreeFramework.jar` |
| group / artifact | `313devgrp` / `Java-Service-Tree-Framework-Engine-Fire` |
| 정적 분석 | SonarQube (`sonarqube` 태스크) |
| 라이선스 | `dependency-license-report` → `build/licenses` |

### ⚠️ Windows 에서는 빌드가 안 된다

`build.gradle` 의 `ext` 블록이 OS 를 판별해 Windows 면 `*** Windows is not support build` 만 출력하고,
`wget` 으로 Nexus `maven-metadata.xml` 을 받지 못해 버전 산정이 실패한다.

→ **이 워크스페이스(Windows)에서는 `./gradlew build` 로 검증할 수 없다.**
컴파일 검증이 필요하면 Mac/Linux 에서 수행하고, 불가능하면 **검증하지 못했다는 사실을 명시**한다.
추측으로 "빌드 통과"라고 보고하지 않는다.

### 버전은 자동 산정된다

Nexus 최신 버전 + `build.gradle` 의 `majorVersion`/`minorVersion` 상수로 patch 를 자동 증가시킨다.
`./gradlew printVersion` 으로 확인. **major/minor 를 임의로 올리지 않는다.**

### 주요 태스크

| 태스크 | 역할 |
|--------|------|
| `bootJar` | 실행 JAR |
| `printVersion` | 산정 버전 출력 |
| `generatePublishInfo` | `spinnaker.properties` 생성 |
| `publish` | Nexus(`ple-releases`) 배포 |
| `prepareDockerContext` → `buildDockerImage` → `pushDockerImage` | 도커 이미지 파이프라인 |
| `test` | JUnit5 (`useJUnitPlatform()`) |

자격 증명은 `~/.m2/settings.xml`(없으면 프로젝트 루트 `settings.xml`)의 `servers` 에서 읽는다.
**`settings.xml` 의 자격증명 값을 문서·로그에 복제하지 않는다.**

---

## 2. 런타임 · 배포

```
Dockerfile:  313.co.kr:5550/313devgrp/openjdk:21-jdk
entrypoint:  docker-entrypoint.sh
```

`docker-entrypoint.sh` 가 고정하는 것:

| 항목 | 값 |
|------|----|
| 타임존 | `-Duser.timezone=Asia/Seoul` |
| GC | `-XX:+UseNUMA -XX:+UseG1GC` |
| 힙 | `-Xms2048m -Xmx2048m` (`MEM_OPTS` 로 덮어쓰기 가능) |
| DirectMemory | `-XX:MaxDirectMemorySize=1024m` |
| 네트워크 | DNS TTL 0, IPv4 우선 |
| 프로파일 | `SPRING_PROFILES_ACTIVE` 기본 `live` |

Elastic APM javaagent 옵션이 스크립트에 정의돼 있으나 현재 JVM_OPTS 에는 포함되지 않는다
(`DEV_MONITOR_ELK_OPTS` / `LIVE_MONITOR_ELK_OPTS` 변수만 존재).

---

## 3. 설정은 전부 Spring Cloud Config 가 준다

저장소의 `src/main/resources/application*.yml` 은 **4줄짜리 뼈대**다.

```yaml
# application.yml
spring:
  application:
    name: javaServiceTreeFrameworkEngineFire

# application-live.yml / -stg.yml
spring:
  config:
    import: optional:configserver:http://global-config:33133
management:
  endpoints:
    web:
      exposure:
        include: refresh, env, health, beans, httptrace
```

(`application-dev.yml` 은 `http://www.313.co.kr:33133`)

→ 포트·OpenSearch URL·인덱스명·Jira 파라미터·시크릿은 **여기에 없다.**
`javaServiceTreeFrameworkEngineFire(-live).yml` 이 Global-Config 저장소에 있다.
**저장소에서 설정값을 못 찾는다고 코드에 하드코딩하지 말고, 설정 변경이 필요하다는 점을 명시한다.**

`@RefreshScope` 가 붙은 Bean(`ElasticsearchProperties`, `ElasticsearchIndexNameConfig`)은
`POST /actuator/refresh` 로 런타임 갱신된다.

주요 설정 키:

| 키 | 용도 |
|----|------|
| `server.port` | `33333` |
| `elasticsearch.url` | OpenSearch (live: `es-coordinating:9200`) |
| `arms-index-name.{jiraissue,serverinfo,fluentd}` | 인덱스 베이스명 |
| `opensearch.buffer-limit-mb` | 응답 버퍼 (기본 300) |
| `spring.elasticsearch-repository.path` | `RepositoryConfiguration` 스캔 경로 |
| `arms.backend-core.url` / `arms.middle-proxy.url` | Feign 대상 (:31313 / :13131) |
| `alm.discovery.start-date` / `.dateRange` | 수집 범위 |
| `jira.api.*` / `redmine.api.*` | 엔드포인트·JQL 템플릿 |
| `backup.directory` / `backup.batch-size` | 인덱스 백업 |
| `aes.token` / `slack.token` | 시크릿 — **값 복제 금지** |
| springdoc 경로 | Swagger UI `/engine-fire-api/`, api-docs `/engine-fire-api/v3/api-docs` |

---

## 4. OpenSearch 클라이언트 설정 (`OpensearchClientConfig`)

| 항목 | 값 | 함의 |
|------|----|------|
| connect / socket timeout | 60,000ms | 무거운 집계도 60초 안에 끝나야 한다 |
| keepAlive | 180초 | |
| `RefreshPolicy` | **IMMEDIATE** | 저장 직후 검색에 보인다. 대량 색인 시 비용이 크다는 점 인지 |
| `largeBufferRequestOptions` | `opensearch.buffer-limit-mb`(300MB) | 대용량 응답용 `RequestOptions` Bean |
| 템플릿 | `CustomOpenSearchRestTemplate` | 빈 이름 `elasticsearchOperations`/`elasticsearchTemplate`/`opensearchTemplate` |

- 헬스는 `CustomElasticsearchHealthIndicator`. 기본 ES 헬스는 설정으로 꺼져 있다.
- Reactive Elasticsearch 자동설정은 설정에서 제외돼 있다. **임의로 풀지 않는다.**

---

## 5. 인덱스 운영 (`api/admin`)

| 작업 | 진입점 | Wrapper 메서드 |
|------|--------|----------------|
| 백업 | `POST /engine/index/backup`, `/engine/admin/schedule/index/backup` | (`IndexBackupAsyncServiceImpl`) |
| 복구 | `/engine/index/restore` | |
| 인덱스 삭제 | `/engine/index/es-index` | `deleteIndex(int days)` / `deleteIndex(Map<월, List<인덱스>>)` |
| force merge | | `merge(int day)` — 일자 인덱스를 월 단위로 그룹핑해 머지 |
| reindex | | `reindex(Map<월, List<인덱스>>)` |
| 목록·건수 | `/engine/admin/monitoring` | `catIndexVOList()`, `indexAllCount()` |
| 상태 스냅샷 | `/engine/index/index-status` | `@IndexStatusSnapShot` AOP → `IndexStatusEntity` |

- `@MonthBackup` / `@MonthMerge` 애너테이션이 붙은 엔티티만 월 단위 백업·머지 대상이다.
- 이 작업들은 **되돌릴 수 없다**(인덱스 삭제·reindex). 실행 전 대상 인덱스 목록을 사용자에게 확인시킨다.
- `@Scheduled` 는 없다. 스케줄은 외부에서 REST 로 트리거한다.

---

## 6. 관측

| 항목 | 상태 |
|------|------|
| actuator | `refresh, env, health, beans, httptrace` 노출 |
| Micrometer Tracing + Zipkin(Brave) | 의존성 있음. live 기본 `management.tracing.enabled: false` |
| Slack | `util/slack` + AOP. 미처리 예외는 `engine` 채널로 자동 통보 |
| logback | `src/main/resources/logback-spring.xml` + `logback/logback-{dev,stg,live}.xml` |
| fluentd | 로그를 `fluentd-yyyyMMdd` 인덱스로 수집 (`api/fluentd`) |

---

## 7. CI

`.github/workflows/release-drafter.yml` 하나뿐이다. **테스트·빌드를 도는 CI 가 없다.**
→ 변경의 안전망이 얇다. 수집·변환 계층을 고치면 기존 WireMock 테스트를 돌려보고,
집계 계층을 고치면 최소한 쿼리 필드·alias 를 코드로 재확인한다.
