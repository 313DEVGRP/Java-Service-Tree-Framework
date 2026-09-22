# Gitea 파일 접근 — 두 스택

`SKILL.md` §3 의 상세판. 이 저장소에는 DB 가 없고 **Gitea 저장소가 영속 계층**이다.
접근 코드가 두 벌 있으며 **Base64 규약이 서로 반대**다. 섞으면 파일이 조용히 깨진다.

---

## 0. 어느 스택을 쓰는가

| 도메인 | 스택 | 대상 Gitea 저장소 |
|--------|------|------------------|
| `languageconfig` | **A — `gcframework`** | `language-config` (`gitea.lang-pack.repo-name`) |
| `schedule` | **B — 레거시** | `schedule-config` (`gitea.schedule-config` 전체 URL) |
| `systeminfo` | **B — 레거시** | `SystemInfo` (`gitea.system-info` 전체 URL) |
| Config Server 자체 | (JGit, 의존성 내부) | `root/ARMS` (`spring.cloud.config.server.git.uri`) |

새 도메인을 만든다면 **스택 A** 를 쓴다. 기존 도메인을 건드릴 때는 그 도메인의 스택을 유지한다.

---

## 1. 스택 A — `gcframework`

패키지: `com/arms/egovframework/javaservice/gcframework/`

```
service/   GitFileService (인터페이스) · GitFileServiceImpl   ← 진입점. 이것만 주입한다
provider/  GitRepositoryProvider (인터페이스) · GiteaRepositoryProvider
parser/    AbstractContentParser · JsonContentParser · YamlContentParser
model/     FileContent · GitFileInfo · GiteaFileInfo · GitHubFileInfo · Links · RepoType · AbstractContentVO
```

### 1.1 `GitFileService` API

```java
FileContent getFileContent(RepoType, String repoName, String filePath);
<T extends AbstractContentVO> boolean upsertFileContent(RepoType, String repoName, String filePath, T configVo, String commitMessage);
boolean upsertFileContentFromMap(RepoType, String repoName, String filePath, Map<String,Object> data, String commitMessage);
List<GitFileInfo> listFilesAndDirectories(RepoType, String repoName, String directoryPath);
boolean deleteFile(RepoType, String repoName, String filePath, String commitMessage);
<T extends AbstractContentVO> T parseFileContent(FileContent, String filePath, Class<T> targetVoType);
Map<String,Object> parseFileContentToMap(FileContent, String filePath);
```

- **owner·branch 를 넘기지 않는다.** `GitFileServiceImpl` 이 `GiteaUserConfig` 에서 채운다
  (`owner` = `gitea.owner`, branch = `spring.cloud.config.server.git.default-label` = `main`).
- `repoName` 은 저장소 이름만(`"language-config"`). 전체 URL 이 아니다.
- `directoryPath` 는 루트가 `"/"`.

### 1.2 파서 선택 = 파일 확장자

`GitFileServiceImpl` 생성자가 `List<AbstractContentParser>` 를 받아 `확장자 → 파서` 맵을 만든다.

| 파서 | `getHandledTypes()` |
|------|--------------------|
| `JsonContentParser` | `json` |
| `YamlContentParser` | `yaml`, `yml` |

확장자에 맞는 파서가 없으면 `UnsupportedOperationException("No parser found for file type: ...")`.
새 형식은 `AbstractContentParser` 를 상속한 `@Component` 를 추가하면 자동 등록된다.

### 1.3 Base64 규약 (스택 A)

```
Gitea 응답 content (Base64)
      │ parse / parseToMap  → 내부에서 decode
      ▼
  VO 또는 Map<String,Object>
      │ serialize / serializeFromMap → 내부에서 encode
      ▼
Provider.upsertFile(content)   ← 이미 Base64. 여기서 다시 인코딩하지 않는다
```

`AbstractContentParser` 의 `parse`/`parseToMap`/`serialize`/`serializeFromMap` 은 전부 `final` 이고
Base64 처리를 담당한다. 하위 클래스는 `doParse`/`doParseToMap`/`doSerialize`/`doSerializeFromMap` 만 구현한다.

### 1.4 `GiteaRepositoryProvider` 동작

기본 URL: `{gitea.base-url}/api/v1/repos/{owner}/{repoName}/contents`
인증: HTTP Basic (`git.username:git.password` Base64) — `HttpURLConnection` 직접 사용.

| 메서드 | Gitea API | 성공 코드 | 특이사항 |
|--------|-----------|----------|---------|
| `getListFilesAndDirectories` | `GET .../contents/{dir}?ref={branch}` | 200 | 응답의 `url` 을 `rewriteUrlToInternal` 로 치환 |
| `getFileContent` | `GET .../contents/{path}?ref={branch}` | 200 | `content` 키가 없으면 **`null` 반환** |
| `upsertFile` | `PUT .../contents/{path}` | 200 / 201 | 기존 SHA 를 스스로 조회해 붙임(없으면 신규 생성) |
| `deleteFile` | `DELETE .../contents/{path}` | 204 | SHA 조회 실패 시 **예외 없이 `false`** |

실패 시에는 `RuntimeException` 을 던진다(체크 예외 없음). 호출부는 `RuntimeException` 을 잡는다 —
`LanguageConfigServiceImpl` 이 그렇게 하고 있다.

`rewriteUrlToInternal(url)` 은 `(https?://)([^/]+)(/gitea)` 를 `gitea.replace-url` 로 치환한다.
dev 에서는 사실상 항등, stg/live 에서는 URL 에 `/gitea` 가 없어 no-op 이다. **동작을 바꾸려 하지 말 것.**
`rewriteGiteaUrl`(`/src/branch/` → `/raw/branch/`)은 같은 클래스에 있지만 현재 호출되지 않는다
(소스에 "이거 기술 잘못되었음" 주석이 그대로 남아 있다).

---

## 2. 스택 B — 레거시 (`GiteaFileUtil` + `GiteaHttpURLConnection`)

패키지: `com/arms/api/util/`

### 2.1 `GiteaFileUtil`

```java
List<String> getYamlFilesFromDirectory(String directoryUrl, String branch);  // schedule · system-info 가 사용
List<String> getJsonFileDownloadUrlsInDirectory(String directoryUrl, String branch);
List<String> getJsonFileUrlsInDirectory(String directoryUrl, String branch);
String extractFileNameWithoutExtension(String fileUrl);
String rewriteGiteaUrl(String url);
```

- `directoryUrl` 은 **전체 URL** 이다(`gitea.schedule-config` = `http://.../api/v1/repos/root/schedule-config/contents/`).
  스택 A 의 `repoName` 과 인자 성격이 다르다.
- 디렉터리 목록 JSON 을 **SnakeYAML `Yaml.load`** 로 파싱한다(JSON 은 YAML 의 부분집합이라 통한다).
  `getJsonFile*` 쪽은 Jackson 을 쓴다 — 같은 클래스 안에서 파서가 갈린다.
- 반환값은 `download_url`(raw 파일 URL) 목록이다. 이후 그 URL 을 다시 GET 해서 본문을 읽는다.
- 디렉터리 조회가 200 이 아니면 `RuntimeException`.

### 2.2 `GiteaHttpURLConnection`

```java
HttpURLConnection createConnection(String url, String method);   // Basic 인증 자동
HttpURLConnection createGetConnection(String url);
String readResponseBody(HttpURLConnection);
void   writeRequestBody(HttpURLConnection, String body);
int    updateFile(String apiUrl, String fileName, String sha, String branch, String contents);  // PUT, 200 기대
int    createFile(String apiUrl, String fileName, String branch, String contents);              // POST, 201 기대
int    deleteFile(String apiUrl, String fileName, String sha, String branch);                   // DELETE, 200 기대
```

**Base64 규약이 스택 A 와 정반대다.**

```
updateFile/createFile 은 평문 contents 를 받아 내부에서 Base64.encode 한다.
→ 스택 A 의 serialize 결과(이미 Base64)를 여기에 넘기면 이중 인코딩된다.
```

요청 바디는 `String.format` 문자열 조립이다:

```java
String.format("{\"content\":\"%s\",\"message\":\"Update %s\",\"sha\":\"%s\",\"branch\":\"%s\"}", ...)
```

`content` 는 Base64 라 안전하지만 `fileName` 에 `"`·`\`·개행이 들어가면 JSON 이 깨진다.

### 2.3 `YamlFileUtils`

스택 B 의 더 오래된 버전. `ScheduleServiceImpl` 이 필드로 주입만 하고 **호출하지 않는다.**
`http://` → `https://` URL 을 중복으로 리스트에 넣는 등 동작이 특이하다. **새로 쓰지 말 것.**
정리(제거)는 사용자 판단이므로 발견 사실만 보고한다.

---

## 3. 자주 나는 실수

| 증상 | 원인 |
|------|------|
| 저장한 파일이 Base64 문자열 그대로 보인다 | 스택 A 의 `serialize` 결과를 스택 B 의 `updateFile` 에 넘김(이중 인코딩) |
| `getFileContent` 가 `null` | Gitea 응답에 `content` 키가 없음(디렉터리를 가리켰거나 대용량 파일) — NPE 나기 전에 null 체크 |
| `deleteFile` 이 `false` 인데 예외는 없음 | 파일이 없거나 SHA 조회 실패. 정상 분기다 |
| `No parser found for file type` | 확장자가 없거나 json/yaml/yml 이 아님 |
| stg/live 에서만 URL 이 안 맞음 | `gitea.base-url` / `gitea.replace-url` 프로파일 값 확인 |
| 401/403 | `spring.cloud.config.server.git.username/password` 가 Gitea 계정과 다름 (Provider·레거시 둘 다 이 값을 Basic 인증으로 쓴다) |
