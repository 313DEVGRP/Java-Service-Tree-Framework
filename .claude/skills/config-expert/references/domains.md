# 도메인별 API 계약

`SKILL.md` §1 · §6 의 상세판. 경로는 **컨트롤러 기준**이다(프론트는 게이트웨이 접두를 붙여 부른다).

---

## 1. languageconfig — 언어팩(i18n)

파일: `com/arms/api/languageconfig/**`
저장소: Gitea `language-config` (`gitea.lang-pack.repo-name`), 루트의 `<lang>.json`
접근 스택: **A(`gcframework`)**

### 1.1 엔드포인트

| 메서드 | 경로 | 반환 |
|--------|------|------|
| GET | `/admin/language-config/packs/files?repoType=GITEA` | `List<LanguagePackFileVO>` |
| GET | `/anonymous/language-config/packs/language/{language}` | `SingleLanguagePackVO` |
| PUT | `/admin/language-config/packs/language/{language}` | `String` (파일명 또는 `FAILED`) |
| DELETE | `/admin/language-config/packs/language/{language}` | `String` (파일명 또는 `Error: ...`) |
| GET | `/admin/language-config/packs/language/{language}/refresh` | `SingleLanguagePackVO` |
| GET | `/admin/language-config/packs/all-contents` | `List<SingleLanguagePackVO>` |
| GET | `/admin/language-config/packs/all-contents/refresh` | `List<SingleLanguagePackVO>` |
| GET | `/admin/language-config/packs/language/{language}/keys/exists?keys=a&keys=b` | `List<String>` (**존재하는** 키만) |

- 조회는 `/anonymous/**`(게이트웨이 `/auth-anon/yml/**`)라 **로그인 전 로케일 로딩**에 쓰인다.
  프론트 `arms/js/common.js` 의 `setLocale` 이 여기를 호출한다.
- 수정은 `/admin/**`(게이트웨이 `/auth-admin/yml/**`), 백오피스 `backoffice/js/languageConfig.js` 전용.
- PUT 바디는 `List<Map<String,String>>` 이고 컨트롤러가 하나의 `Map` 으로 합친다. 단일 Map 이 아니다.

### 1.2 평면화 규약 (`LanguagePackFileReader`)

```
저장소 파일(중첩 JSON)        API 표현(평면)
{ "menu": { "req": "요구사항" } }  ↔  { "menu.req": "요구사항" }
```

- 조회는 `flattenLanguagePack`, 저장은 `unflattenLanguagePack`.
- `unflatten` 은 `key.split("\\.")` 로 자른다 → **키에 `.` 을 의미상 넣으면 계층이 갈라져 되돌릴 수 없다.**
- `flatten` 은 값이 `Map` 이 아니면 `toString()` 한다 → 배열·숫자가 문자열로 굳는다.

### 1.3 캐시 (가장 자주 묻는 문제)

```java
private final Map<String, Map<String, Object>> languagePacks = new HashMap<>();  // 인스턴스 필드
private List<String> availableLanguages = new ArrayList<>();
private LocalDateTime lastRefreshTime;
```

- **프로세스 로컬**이다. 레플리카가 여러 개면 refresh 가 한 인스턴스에만 먹는다.
- `HashMap`/`ArrayList` 라 **동시 수정 시 안전하지 않다.**
- `getSingleLanguagePack` 은 캐시에 있으면 Gitea 를 보지 않는다.
  → **Gitea 에서 직접 고친 값은 `/refresh` 를 타야 보인다.**
- `updateSingleLanguagePack`/`deleteSingleLanguagePack` 은 캐시를 무효화한다.
- `getAllLanguagePackContents` 는 `availableLanguages` 가 비어 있을 때만 `fetchLanguagePacks()` 로 전수 로드한다.
  개별 언어팩 로드 실패는 로그만 남기고 건너뛴다(응답에서 조용히 빠진다).
- `checkLanguageKeyExists` 는 키가 비면 `RuntimeException` 을 던진다.

### 1.4 `LanguagePackFileVO` 의 미채움 필드

`getLanguagePackFiles` 는 `fileName`·`languageCode`·`filePath`·`sha`·`size` 만 채운다.
`lastModified`·`totalKeys` 는 **항상 기본값**이다(소스 주석도 "확인필요"/"검토"로 남아 있다).
프론트에서 이 값을 쓰려면 먼저 채우는 작업이 필요하다.

---

## 2. systeminfo — 조직/라이선스 정보

파일: `com/arms/api/systeminfo/**`
저장소: Gitea `SystemInfo` (`gitea.system-info` 전체 URL)
접근 스택: **B(레거시)**

```
GET /system-info/org-link?orgLink={Long}   →  SystemInfoVO
```

호출자는 **Backend-Core 의 `GlobalConfigService` Feign** 이다
(`@FeignClient(name="global-config", url="${arms.global-config.url}")`).
프론트는 Backend-Core 경유로 `/auth-admin/api/arms/backoffice/system-info/getSystemInfo/org-link/` 를 부른다.
→ **시그니처를 바꾸면 Backend-Core 도 함께 고쳐야 한다.**

### 파일 선택 규칙

```
system-info_org{orgLink}.yml  존재?  → 그 파일
                              없음?  → system-info_base.yml
```

- 접두는 enum `SystemInfoFileName.PREFIX` = `"system-info_org"`.
  `application.yml` 의 `filename.system-info.prefix` = `"system-info_"` 와 **값이 다르고 쓰이지 않는다.**
  베이스 파일명만 `filename.system-info.base` 프로퍼티(`system-info_base`)를 쓴다.
- 두 파일이 다 없으면 `parseYamlFileToVO(null)` 로 들어가 NPE 성격의 실패가 난다. 방어 코드가 없다.

### `SystemInfoVO` 구조 (YAML 키는 kebab-case, `@JsonProperty` 로 매핑)

```yaml
system-info:
  general-settings:   { product-name, product-version, base-url, service-status }
  internalization:    { default-language, time-zone }
  server-config:      { connection-timeout, socket-timeout }
  license-info:       { org_link, org-name, purchase-date, expiration-date,
                        license-type, license-update, license-number, server-id, host-limit, note }
```

`isExistLicenseNumber()` = `license-info.license-number` 가 비어 있지 않은가.
**`ScheduleServiceImpl` 의 엔진 리인덱싱 4종이 이 값을 게이트로 쓴다**
(`almIssueMergeWithReindex` · `fluentdMergeWithReindex` 및 각 `(int day)` 오버로드).
실패 시 던지는 예외는 전부 `IllegalStateException("라이센스 정보 가져오기 실패.")` 로 뭉뚱그려져
**원인(Gitea 접근 실패 / 라이선스 없음)이 구분되지 않는다.** 디버깅 시 상위 로그를 봐야 한다.

---

## 3. schedule — 관리 API

파일: `com/arms/api/schedule/**` (스케줄러 동작 자체는 `references/scheduler.md`)

### 3.1 조회·저장

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/admin/schedule/getScheduleList` | Gitea 재조회 |
| GET | `/admin/schedule/getCurrentScheduleList` | 메모리(`ScheduleMapProvider`) |
| POST | `/admin/schedule/saveScheduleList?fileName=<이름>` | 바디 `List<ScheduleInfoDTO>`. **기존 파일만 갱신** |
| POST | `/admin/schedule/getScheduleHistory` | 바디 `SearchDTO` → Engine-Fire 위임 |

`@RequestMapping("/admin/schedule/")` 가 슬래시로 끝나지만 Spring 이 정규화하므로
실제 경로는 `/admin/schedule/<method-path>` 다.

### 3.2 수동 실행 (배치 강제 트리거)

| 메서드 | 경로 | 위임 대상 |
|--------|------|----------|
| GET | `/admin/schedule/server_info_backup` | Engine `serverInfoBackup` |
| GET | `/admin/schedule/sequentially_issue_es_store` | BackendCore `executeSequentialSchedules` |
| GET | `/admin/schedule/increment/sequentially_issue_es_store/withDateRange?startDate&endDate` | BackendCore |
| GET | `/admin/schedule/issue_es_load` | BackendCore `updateReqStatusFromElasticsearch` |
| GET | `/admin/schedule/retry-failed-req-status-creation-to-elasticsearch` | BackendCore |
| GET | `/admin/schedule/cache-status-mapping-data` | BackendCore |
| GET | `/admin/schedule/update-arms-state-category` | Engine |
| GET | `/admin/schedule/sync-atlassian-directory-users` | BackendCore |
| POST | `/admin/schedule/es-index/alm-issue/merge` (`/day/{day}`) | Engine (**라이선스 게이트 적용**) |
| POST | `/admin/schedule/es-index/fluentd/merge` (`/day/{day}`) | Engine (**라이선스 게이트 적용**) |

대부분 **`void` 반환**이다 → 호출 성공(200)이 실행 성공을 뜻하지 않는다.
결과는 로그·Slack·다운스트림에서 확인한다.

프론트 사용처: `backoffice/js/scheduleConfig.js`, `backoffice/js/esIndexConfig.js`,
`arms/js/reqStatus/batchManualControlApi.js`(base_url `/auth-admin/yml/schedule`).

---

## 4. configserver — 웹훅

`POST /api/config-server/config-changed` — `references/config-server.md` §3 참조.

---

## 5. scmframework — 건드리지 않는다

`ScmController` 의 `/gitInitTest` · `/gitHubCloneTest` · `/gitAddTest` · `/gitCommitTest` ·
`/gitPushTest` · `/gitBranchMergeTest` 는 JGit 실험 코드다.

- GitHub PAT 가 **평문 하드코딩**되어 있다(값을 옮겨 적지 말 것).
- 컨테이너 작업 디렉터리에 파일을 만들고 지운다.
- 인증이 없으므로 이 경로가 외부에 노출되면 곧바로 악용 가능하다.
- JGit·commons-io 는 `build.gradle` 에 선언이 없고 `spring-cloud-config-server` 를 통해 **전이 의존**으로 들어온다.
  설정 서버 버전을 올리면 이 파일이 먼저 깨질 수 있다.

**조치 제안(실행은 사용자 판단):** GitHub 토큰 폐기 → 이 컨트롤러 제거.
