# 코딩 컨벤션 — DTO/VO · 패턴 · 응답 · AOP · 네이밍

정본: 저장소 루트 `CLAUDE.md`, `rules/auto-code.md`, `rules/business-pattern.md`.

---

## 1. DTO / VO 규칙

| 규칙 | 내용 |
|------|------|
| DTO | **요청(Request) 전용**. `model/dto/` |
| VO | **응답(Response) 전용**. `model/vo/` |
| `record` | **사용 금지** (Java 21 이지만 이 저장소의 명시적 규약) |
| 상속 | 검색 요청 DTO 는 필요 시 `SearchRequestDTO` 를 상속 |
| Lombok | `@Getter @Setter @NoArgsConstructor @AllArgsConstructor @ToString` (DTO) / `@Getter @Builder @NoArgsConstructor @AllArgsConstructor` (VO) |

DTO 에 응답 필드를 얹거나 VO 를 `@RequestBody` 로 받지 않는다. 경계가 흐려지면 되돌리기 어렵다.

---

## 2. 의존성 주입

```java
@Service
@AllArgsConstructor        // 또는 @RequiredArgsConstructor (final 필드)
public class XxxServiceImpl implements XxxService {
    private final EsCommonRepositoryWrapper<AlmIssueEntity> esCommonRepositoryWrapper;
}
```

- **생성자 주입만.** `@Autowired` 필드 주입·세터 주입 금지.
- 저장소에는 `@AllArgsConstructor` 와 `@RequiredArgsConstructor` 가 섞여 있다. **파일 안에서 일관되게**,
  새 파일은 주변 도메인 스타일을 따른다.
- `@Service("이름")` 으로 빈 이름을 명시하는 도메인이 있다(`@Service("analysisScope")`). 기존 관례를 유지한다.

---

## 3. 새 도메인 템플릿 (`rules/auto-code.md`) — 1단계에서 지킬 것

입력은 `${domain}` 하나. 파생 규칙:

```
${requestDto}     = ${domain}RequestDTO
${vo}             = ${domain}VO
${entity}         = ${domain}Entity
${domainPackage}  = ${domain} 소문자
```

생성물 5개: `controller/${domain}Controller`, `service/${domain}Service`, `service/${domain}ServiceImpl`,
`model/dto/${requestDto}`, `model/vo/${vo}`.

**1단계 금지 사항**
- 메서드 본문 로직 · 조건문 · 반복문 작성 금지 (`return List.of()` 등 기본값만)
- 추가 필드 · 추가 메서드 · 주석 생성 금지
- 설명 문장 출력 금지

ServiceImpl 은 `EsCommonRepositoryWrapper<${entity}>` 를 생성자 주입으로 받는 형태로 시작한다.

---

## 4. 비즈니스 패턴 (`rules/business-pattern.md`) — 2단계

### 4.1 정적 팩토리 (Entity → VO)

```java
public class ServerInfoVO {
    public static ServerInfoVO fromEntity(ServerInfoEntity entity) {
        return ServerInfoVO.builder()
                .connectId(entity.getConnectId())
                .type(entity.getType())
                .build();
    }
}
```

네이밍은 `from` / `of` / `create`. **변환 로직을 Service 에 노출하지 않는다.**

### 4.2 조건부 빌더

```java
AlmIssueVO.AlmIssueVOBuilder builder = AlmIssueVO.builder()
        .fields(issueFieldData)
        .armsStateCategory(getMappingCategory(serverInfoVO, issueFieldData));

if (serverInfoVO.isCloud()) {
    builder.priority(normalizePriority(issueFieldData.getPriority()));
} else {
    builder.priority(issueFieldData.getPriority());
}
return builder.build();
```

### 4.3 가드 절

```java
BbsEntity entity = Optional.ofNullable(esCommonRepositoryWrapper.findDocById(dto.getId()))
        .orElseThrow(() -> new IllegalArgumentException("삭제된 게시글입니다."));
```

`IllegalArgumentException` 은 `ErrorControllerAdvice` 가 **400 + 메시지** 로 변환한다. 사용자에게 보일 문구를 넣는다.

### 4.4 설명 변수

```java
WikiEntity savedEntity = esCommonRepositoryWrapper.save(wikiDTO.createEntity());
return savedEntity.generateIdWithVersion();
```

### 안티패턴

```java
// ✗ 조건 분기가 있는데 한 줄 체이닝
return SomeVO.builder()
        .field(condition ? computeA() : computeB())
        .other(list.stream().filter(...).findFirst().orElse(null))
        .build();

// ✗ Entity 변환 로직이 Service 에 노출
SomeVO vo = SomeVO.builder().id(entity.getId()).name(entity.getName()).build();
```

---

## 5. 컨트롤러 규약

```java
@Slf4j
@RestController
@RequestMapping("/engine/analysis-scope")
@AllArgsConstructor
public class AnalysisScopeController {

    private final AnalysisScope analysisScope;

    @PostMapping("/tree-bar-data")
    public ResponseEntity<List<TreeBarIssueVO>> treeBarData(@RequestBody ScopeDTO scopeDTO) {
        log.info("[AnalysisScopeController :: treeBarData] :: topN = {}", ...);
        return ResponseEntity.ok(analysisScope.treeBarData(scopeDTO));
    }
}
```

- 집계·검색은 본문이 크므로 **`@PostMapping` + `@RequestBody DTO`** 가 기본이다.
- 반환은 `ResponseEntity<VO>` 또는 VO 직접 반환. 둘 다 쓰이며 도메인별로 일관되게.
- 로그 접두는 `[클래스명 :: 메서드명]` 또는 `클래스명 :: 메서드명` 관례.
- 컨트롤러에 비즈니스 로직을 넣지 않는다(입력 검증·위임·로깅까지).

---

## 6. 공통 응답 봉투 `CommonResponse`

모든 API 가 쓰는 것은 아니다. **쓰는 도메인은 일관되게 쓴다**(admin 계열이 주로 사용).

```java
import static com.arms.api.util.response.CommonResponse.success;

@PostMapping("/index/backup")
public ResponseEntity<CommonResponse.ApiResult<String>> indexBackup() {
    backupScheduleService.indexBackup();
    return ResponseEntity.ok(success("Issue 인덱스 백업 작업이 시작되었습니다."));
}
```

```json
{ "success": true,  "response": {...}, "error": null }
{ "success": false, "response": null,  "error": { "message": "...", "errorCode": "...", "status": 400 } }
```

`CommonResponse.error(...)` 오버로드: `(Throwable, HttpStatus)`, `(String, HttpStatus)`,
`(ErrorCode, HttpStatus)`, `(String, ErrorCode, HttpStatus)`.

---

## 7. 에러 처리

`util/errors/ErrorControllerAdvice` (`@RestControllerAdvice(annotations = RestController.class)`, `@Hidden`):

| 예외 | 처리 |
|------|------|
| `Exception` | 500 + 메시지, **Slack `engine` 채널 통보** |
| `MissingPathVariableException` | 400 — `connectId` 누락 검사 |
| `MethodArgumentNotValidException` | 400 — `@Valid` 실패 |
| `HttpMessageNotReadableException` | 400 — 본문 없음/JSON 아님 |
| `IllegalArgumentException` | 400 + 예외 메시지 그대로 |

에러 문구는 새로 만들지 말고 **`ErrorCode` enum 에 추가**한다(한글 메시지, `String.format` 인자 지원).
핸들러 메서드명이 한글(`커넥트아이디_오류체크`)인 것은 이 저장소 관례다.

---

## 8. AOP (`util/aspect`)

| 애너테이션/어드바이스 | 역할 |
|---------------------|------|
| `LoggingAdvice` | 요청/응답 공통 로깅 |
| `@SlackSendAlarm(messageOnStart, messageOnEnd)` + `SlackSendAdvice` | 장시간 작업 Slack 알림 |
| `@DwrSendAlarm` + `DwrSendAdvice` | Backend-Core 실시간 알림 |
| `@IndexStatusSnapShot` + `IndexStatusSaveAspect` (`admin/indexstatus`) | 인덱스 작업 상태 스냅샷 저장 |

횡단 관심사를 서비스 메서드 안에 직접 넣지 말고 애너테이션으로 붙인다.

---

## 9. Swagger

- springdoc-openapi 자동 노출. 별도 애너테이션 없이도 `@RestController` 는 문서에 뜬다.
- 그룹: `OpenApiConfig` 의 `GroupedOpenApi("arms", packagesToScan="com.arms")`.
- UI: `/engine-fire-api/swagger-ui/` (`SwaggerUIConfiguration` 이 `index.html` 로 포워딩).
- 문서에서 숨길 것은 `@Hidden`(`ErrorControllerAdvice` 참고).
- 새 API 추가 후 위 경로에서 노출되는지 확인한다.

---

## 10. 네이밍 · 기타 관례

- **한글 식별자가 실재한다.** 중첩 클래스 `AlmIssueEntity.상태`, 예외 핸들러 `커넥트아이디_오류체크`,
  집계 VO `요구사항_지라이슈상태_주별_집계` 등. **기존 것을 영문으로 바꾸지 않는다.**
  신규 코드는 영문 네이밍을 우선한다.
- 서비스 인터페이스 이름이 `XxxService` 가 아닌 경우가 있다(`AnalysisScope` / `AnalysisScopeImpl`,
  `AnalysisCost` / `AnalysisCostImpl`). 도메인 관례를 따른다.
- 파일 상단 저작권 주석 블록(`@author ... 313 DEV GRP ...`)이 있는 파일이 많다. 새 파일에 붙일지는
  주변 파일을 보고 맞춘다. 기존 주석을 지우지 않는다.
- 로그는 `@Slf4j` + `log.info("... {}", value)`. 인증정보·토큰을 로그에 남기지 않는다.
- 타임존은 `Asia/Seoul`(UTC+9) 기준 코드가 곳곳에 있다. 날짜 계산 시 어느 존인지 확인한다.

---

## 11. 테스트 (`src/test/java`)

| 도구 | 용도 |
|------|------|
| JUnit5 (`useJUnitPlatform()`) | 실행. JUnit4 는 제외됨 |
| Mockito (`mockito-inline`) | 목 (static/final 목 가능) |
| AssertJ | `assertThat(...)` |
| `spring-cloud-contract-wiremock` | 외부 ALM HTTP 스텁 |

- 서비스 단위 테스트는 `EsCommonRepositoryWrapper` 를 목으로 두고 **DTO → VO 변환·집계 로직만** 검증한다.
- 외부 ALM 은 WireMock 으로 스텁한다. 실제 Jira/Redmine·OpenSearch 에 붙는 테스트는 단위 테스트에 두지 않는다.
  기존 스텁: `src/test/resources/wiremock/{cloud_jira,...}/mappings/*.json`, 설정 클래스 `WireMock*Config`.
- 현재 테스트는 수집·변환 계층에 집중돼 있다(`*ToAlmIssueVOConverterTest`, `*DiscoveryTest`, `EsDataValidationTest`).
  집계 도메인에는 테스트가 거의 없다 — 새 집계를 넣을 때 변환 단위 테스트를 함께 두면 가치가 크다.
