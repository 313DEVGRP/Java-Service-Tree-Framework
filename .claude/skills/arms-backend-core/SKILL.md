---
name: arms-backend-core
description: >-
  A-RMS 백엔드 저장소(Java-Service-Tree-Framework-Backend-Core)의 서버 작업 규약.
  Java 11 · Spring Boot 2.6.15 · Hibernate 5 Criteria 기반 TreeFramework(nested-set)
  멀티테넌트 API 서버에서 도메인을 만들거나 고칠 때, TreeAbstractController 상속 ·
  TreeSearchEntity/TreeServiceImpl 계약 · jsonView 응답 봉투 · 제품별 동적 테이블
  라우팅(T_ARMS_REQADD_<pdServiceId> · RouteTableInterceptor · SessionUtil) ·
  loopback Feign(InternalService) · Engine-Fire/AggregationService Feign 위임 ·
  Kafka REQADD 순차 소비 · Flyway + DynamicDBMakerDao.xml 이중 스키마 ·
  Apache POI 리포트를 이 규약대로 따르게 한다.
  com/arms/api/** 또는 com/arms/egovframework/** 를 건드리거나, "요구사항 API",
  "reqAdd", "reqStatus", "pdService", "대시보드 집계 API", "Engine 호출", "Feign",
  "Kafka 컨슈머", "엑셀 다운로드", "PPT 리포트", "트리 노드", "c_left/c_right", "백엔드 코어"
  같은 요청이 나오면 반드시 이 스킬을 먼저 읽을 것.
  DB 작업도 대상이다 — src/main/resources/com/arms 의 Flyway V*.sql · 초기 스키마 · 컬럼 추가 ·
  _LOG 짝 테이블 · 트리거 · 루트 seed · 프리셋 시드값(상태·우선순위·난이도·중요도·긴급도) ·
  DynamicDBMakerDao.xml 동적 테이블 DDL · MyBatis 매퍼 설정이 여기 정리돼 있다.
  Spring Boot 3 · jakarta.* · Java 17+ 문법으로 새로 만들지 않는다 — 이 저장소는 Boot 2.6/Java 11이다.
---

# A-RMS Backend-Core 작업 규약

대상 저장소: `Java-Service-Tree-Framework-Backend-Core/`
(워크스페이스 루트 `C:\DEV\Project\Java-Service-Tree-Framework` 하위, **중첩된 별개 git 저장소**, 작업 브랜치 `dev`)

규모: Java 911개 파일 / `@Entity` 69개 / `TreeSearchEntity` 상속 78개 /
`TreeAbstractController` 상속 58개 / `TreeServiceImpl` 상속 61개 / **`src/test` 없음**.

이 저장소는 **Hibernate 5 Criteria 기반의 자체 트리 프레임워크 위에 도메인을 얹는 구조**다.
Spring Data JPA 프로젝트처럼 접근하면 거의 모든 판단이 틀린다. 그리고 요구사항 테이블은
**제품마다 물리적으로 다른 테이블**이고, 어떤 테이블을 칠지는 **HTTP 요청 경로가 결정**한다.
이 두 가지를 먼저 이해하는 것이 이 저장소에서 가장 비용이 싼 길이다.

---

## 1. 먼저 무엇을 건드리는지 판별한다

| 영역 | 경로 | 성격 |
|------|------|------|
| 공통 트리 프레임워크 | `com/arms/egovframework/javaservice/treeframework/**` | **58개 컨트롤러·61개 서비스가 공유.** 고치면 전역 영향 |
| 도메인 API | `com/arms/api/**` | 실제 작업 대부분. 도메인별로 독립 |
| 스프링 설정 | `com/arms/config/**` + `resources/com/arms/egovframework/spring/*.xml` | Java Config와 **XML Config가 공존** |
| 스키마 | `resources/com/arms/db/V*.sql`(Flyway) + `resources/com/arms/egovframework/mybatis/mapper/DynamicDBMakerDao.xml`(동적 테이블) | **두 곳이 정본. 한쪽만 고치면 깨진다** |

> ⚠️ `egovframework/` 하위는 도메인 요구로 고치지 않는다. 도메인 요구는 도메인 코드에서 해결한다.
> 부득이하게 고쳐야 하면 **영향 범위를 먼저 보고**하고 승인을 받는다.

### 형제 저장소와 헷갈리기 쉬운 주제

`REQADD` · `changeReqTableName` · 엑셀 업로드는 **두 저장소에 걸쳐 있다.** 어느 쪽인지 먼저 가른다.

| 주제 | Backend-Core (이 스킬) | Middle-Proxy (`middleproxy-expert` 스킬) |
|---|---|---|
| Kafka REQADD | **컨슈머**(`ReqAddConsumer`) | **프로듀서**(`ReqAddKafkaMessage` 발행) |
| `changeReqTableName` | Hibernate SQL 치환 대상 | 게이트웨이 경로 PathVariable |
| 엑셀 업로드 | 행 단위 트리 반영·콜백 | 파일 수신·Redis 락·requestId |
| 인증/권한 | 없음(게이트웨이가 처리) | Keycloak OIDC · `pathMatchers` |
| 스택 | MVC · JPA/Hibernate · `@Transactional` | WebFlux · Redis · 리액티브 |

화면·JS·CSS 는 `arms-frontend-web` 스킬(별도 저장소)이다. 여기서 만들지 않는다.
OpenSearch 색인·집계 자체(수집 전략·인덱스·aggregation)는 `engine-expert` 스킬(Engine-Fire) 소관이다.
Backend-Core 는 그 결과를 **Feign 으로 받아 쓰기만** 한다.

### 도메인은 두 가지 형태다

**(A) 트리 도메인** — `reqAdd`, `reqStatus`, `pdService`, `jiraServer`, `blog`, `wiki` …
`Controller extends TreeAbstractController` + `Service extends TreeService` +
`Entity extends TreeSearchEntity`. 공통 CRUD 12종을 상속으로 얻는다.

**(B) 집계/분석 도메인** — `analysis/*`, `dashboard`, `detail_dashboard`, `report/*`, `backoffice/*`
평범한 `@RestController` + `Service`/`ServiceImpl` + `VO`. DB 대신 **Feign으로 Engine-Fire에 위임**한다.

새 기능이 어느 쪽인지 먼저 정한다. 집계 화면 하나 붙이려고 트리 도메인을 만들지 않는다.

---

## 2. 트리 도메인 계약 (이 저장소의 핵심)

```
ReqAddController extends TreeAbstractController<ReqAdd, ReqAddDTO, ReqAddEntity>
  └ @PostConstruct initialize() { setTreeService(reqAdd); setTreeEntity(ReqAddEntity.class); }
        ↑ 이 두 줄이 없으면 상속받은 12개 엔드포인트가 전부 NPE

ReqAdd (interface) extends TreeService          ← 서비스명에 Service 접미사 없음 (Blog 계열은 있음)
ReqAddImpl extends TreeServiceImpl implements ReqAdd   ← @Service("reqAdd") 이름 지정 빈
ReqAddEntity extends TreeSearchEntity           ← @Entity @Table(name="T_ARMS_REQADD")
ReqAddDTO extends TreeBaseDTO
```

상속으로 얻는 엔드포인트(모두 `.do` 접미사):
`getNode` · `getChildNode` · `getNodesWithoutRoot` · `getPaginatedChildNode` · `searchNode` ·
`addNode` · `removeNode` · `updateNode` · `alterNode` · `alterNodeType` · `moveNode` ·
`analyzeNode` · `getMonitor`.

### 반드시 알아야 하는 동작 (`TreeServiceImpl`)

- **`addNode`** — `ref`(부모 c_id)를 받아 `c_position`/`c_left`/`c_right`/`c_level`을 **직접 계산**한다.
  `stretchLeft`/`stretchRight`가 형제·조상 노드의 left/right를 전부 UPDATE한다.
  → **`c_left`/`c_right`를 코드에서 직접 세팅하지 않는다.**
- **`updateNode`는 부분 업데이트다.** `ObjectUtils.isEmpty(value)` 인 필드는 **덮어쓰지 않는다.**
  즉 **필드를 null/빈값으로 되돌릴 수 없다.** 예외는 `TreeServiceImpl.updateNode`에 하드코딩된
  `fieldsToAlwaysUpdate` 4개(`c_issue_delete_date`, `c_etc`, `c_req_state_mapping_link`,
  `reqStateCategoryEntity`)뿐이다. 새 필드를 "비울 수 있게" 만들려면 공통 클래스를 고쳐야 하므로,
  **먼저 이 제약을 사용자에게 알리고** 도메인 전용 update 메서드를 만드는 쪽을 제안한다.
- **쓰기 메서드는 전부 `Isolation.SERIALIZABLE`**이다(`addNode`·`updateNode`·`updateField`·
  `removeNode`·`alterNode`·`alterNodeType`·`moveNode`·`overwriteNode`·`saveOrUpdateList`).
  동시 쓰기가 몰리면 락 경합이 난다. 대량 처리에 그대로 쓰지 않는다.
- **조회 실패는 null이 아니라 예외다.** `TreeAbstractDao.getUnique()`는 못 찾으면
  `TreeDaoException`을 던진다. `if (node == null)` 로 방어하는 코드는 동작하지 않는다.

### 검색 조건은 Hibernate Criteria다 (JPQL/QueryDSL 아님)

```java
ReqAddEntity e = new ReqAddEntity();
e.setWhere("c_parentid", parentId);                 // = 조건
e.setWhereLike("c_title", keyword);                 // %keyword%  (내부적으로 * 래핑)
e.setWhereIn("c_id", ids);
e.getCriterions().add(Restrictions.not(Restrictions.in("c_id",
        new Object[]{TreeConstant.ROOT_CID, TreeConstant.First_Node_CID})));  // 루트 2개 제외
e.setOrder(Order.asc("c_position"));                // setOrder는 add다 — 여러 번 호출하면 누적
List<ReqAddEntity> list = reqAdd.getChildNodeWithoutPaging(e);
```

`setWhere(String, Object)`에 넘긴 문자열은 `*` 접두/접미로 LIKE 매칭 모드가 **암묵적으로 바뀐다**
(`"*abc*"` → ANYWHERE, `"isNotNull..."` → IS NOT NULL). 사용자 입력을 그대로 넘기지 않는다.

상세는 `references/tree-framework.md`.

---

## 3. 제품별 동적 테이블 — 이 저장소에서 가장 자주 사고가 나는 지점

요구사항은 제품(`pdServiceId`)마다 **물리적으로 다른 테이블**에 저장된다:
`T_ARMS_REQADD_12`, `T_ARMS_REQSTATUS_12`, `T_ARMS_WIKI_12` …
엔티티에는 `@Table(name = "T_ARMS_REQADD")` 하나만 있고, **실행 시점에 SQL 문자열이 치환**된다.

```
① 컨트롤러 @RequestMapping 경로에 "T_ARMS_REQADD_" 가 들어간 PathVariable 이 있어야 하고
      @RequestMapping("/{changeReqTableName}/getNode.do")
② 서비스 호출 전후로 request attribute 를 세팅/제거해야 하고
      SessionUtil.setAttribute("getNode", changeReqTableName);
      ... reqAdd.getNode(entity) ...
      SessionUtil.removeAttribute("getNode");
③ 그 attribute 키가 RouteTableConfig 의 맵에 등록돼 있어야 한다
      reqAddRoute: "getNode.do" -> "getNode"
④ 그래야 RouteTableInterceptor(Hibernate EmptyInterceptor) 가 onPrepareStatement 에서
   "T_ARMS_REQADD" -> "T_ARMS_REQADD_12" 로 치환한다
```

**네 단계 중 하나라도 빠지면 조용히 공용 템플릿 테이블(`T_ARMS_REQADD`)을 읽고 쓴다.**
예외도 안 난다 — `RouteTableInterceptor`는 예외를 `log.info`로 삼킨다.

따라서 **새 엔드포인트를 추가할 때마다 `RouteTableConfig`에 키를 등록**해야 한다. 잊기 쉬운 1순위다.

### `SessionUtil`은 HTTP 요청 스레드에서만 동작한다

`RequestContextHolder` 기반이라 **Kafka 컨슈머 · `@Scheduled` · `@Async` 스레드에는 요청이 없다.**
그래서 이 저장소는 **자기 자신을 HTTP로 다시 호출한다**:

```java
@FeignClient(name = "loopback", url = "http://127.0.0.1:31313")   // InternalService
```

Kafka 컨슈머(`ReqAddConsumerService`)는 DB를 직접 건드리지 않고
`internalService.createFromKafka(tableName, dto)` 로 **자기 서버에 HTTP 요청을 만들어** 라우팅을 성립시킨다.
이 구조를 "비효율"이라며 직접 호출로 바꾸면 **전 제품 데이터가 한 테이블에 섞인다.** 건드리지 않는다.

`SessionUtil.removeAttribute()` 는 **반드시 `finally`에서** 호출한다. 잔류하면 같은 스레드의
후속 요청이 남의 제품 테이블을 조회한다(실제 사고 이력: commit `035302ec`).

상세는 `references/dynamic-table-routing.md`.

---

## 4. 응답 형태는 두 가지뿐이다

**(A) `jsonView` (트리 공통 · 레거시 `.do`)**
```java
ModelAndView mv = new ModelAndView("jsonView");
mv.addObject("result", list);
return mv;
```
`jsonView`는 `MappingJackson2JsonView` + `modelKey=result` + `extractValueFromSingleKeyModel=true`
(`context-common.xml`). 즉 **`result` 안의 값이 그대로 본문**이 된다. `{"result": …}` 로 감싸지지 않는다.

**(B) `CommonResponse.ApiResult<T>` (신규 REST)**
```java
return ResponseEntity.ok(CommonResponse.success(vo));   // {"success":true,"response":…,"error":null}
```

전역 예외 처리는 `ErrorControllerAdvice` 하나가 담당한다 —
`Exception`→500, `BaseException`→400(+Slack 알림), `BindException`/`MethodArgumentNotValid`→400.
**컨트롤러에서 try/catch로 500을 직접 만들지 않는다.**

> 신규 엔드포인트는 (B)를 쓴다. 기존 `.do` 엔드포인트를 (B)로 바꾸면 프론트가 깨진다
> (`Frontend-Web`이 `data.response` 유무로 구/신형을 구분한다).

---

## 5. 영속 계층은 셋이고, 섞여 있다

| 방식 | 적용 범위 | DataSource | 트랜잭션 매니저 |
|------|----------|-----------|----------------|
| **Hibernate 5 Criteria (TreeFramework)** | 도메인 대부분 (61개 서비스) | `onlyHibernateDataSource` | `transactionManager` (primary) |
| **Spring Data JPA** | **`com.arms.api.globaltreemap` 뿐** | `onlyJpaDataSource` | `transactionJpaManager` |
| **MyBatis** | **`util/dynamicdbmaker`, `util/samplemybastis` 뿐** | `onlyMybatisDataSource` (Hikari) | — |

- `@EnableJpaRepositories(basePackages="com.arms.api.globaltreemap.*")` 이므로 **다른 패키지에
  `JpaRepository`를 만들면 빈이 안 잡힌다.** "JPA로 간단히 짜자"는 판단이 여기서 깨진다.
- `@MapperScan("com.arms.api.util.**.mapper")` — `util` 밖의 `mapper` 패키지는 스캔되지 않는다.
  (`report/weekly/mapper/WeeklyReportMapper`는 MyBatis가 아니라 평범한 변환 클래스다.)
- Hibernate/JPA/JDBC DataSource는 **`DriverManagerDataSource`(커넥션 풀 없음)**다. Hikari는 MyBatis 전용.
  대량 반복 쿼리를 새로 짜기 전에 이 사실을 고려한다.
- `@Transactional`은 **`org.springframework.transaction.annotation`** 것을 쓰고, 트리 도메인은
  primary(`transactionManager`)를 탄다. `globaltreemap` 작업만 `transactionJpaManager`를 명시한다.

상세는 `references/persistence.md`.

---

## 6. 스키마 변경은 "템플릿 + 동적 DDL + 기존 테이블" 3종 세트다

DB 구성은 전부 `src/main/resources/com/arms/` 에서 확인할 수 있다. 추측하지 말고 읽는다.
Flyway `V1`~`V55`(`V33~36`·`V41` 결번, 다음은 **`V56`**) + `DynamicDBMakerDao.xml` 이 정본이다.
상세는 `references/schema-and-mappers.md`.

요구사항 계열 컬럼을 하나 추가하려면 **세 가지를 모두** 작성한다:

1. **템플릿 ALTER** — `db/V56__*.sql` 에서 `T_ARMS_REQADD` **와** `T_ARMS_REQADD_LOG` 둘 다.
2. **동적 DDL 갱신** — `egovframework/mybatis/mapper/DynamicDBMakerDao.xml` 의
   `ddlOrgExecute` / `ddlLogExecute` (**앞으로 생성될 제품 테이블용**).
3. **기존 제품 테이블 일괄 ALTER** — 같은 `V56` 파일 안에 `information_schema` 커서 프로시저를 넣는다.
   이 저장소의 정식 패턴이고 **`V13` · `V15` · `V19` 가 실제 사례**다(그대로 베끼면 된다).
   ```sql
   DECLARE cur CURSOR FOR
       SELECT table_name FROM information_schema.tables
        WHERE table_schema = DATABASE() AND table_name LIKE 'T_ARMS_REQADD%';
   -- 테이블마다 information_schema.columns 로 존재 확인 후 PREPARE/EXECUTE 로 ALTER
   ```
   `IF @column_exists = 0` 가드를 반드시 넣는다.

그리고 `ReqAddEntity` + `ReqAddDTO` 에 필드를 추가한다.

> ⚠️ **후기 마이그레이션은 3번을 빠뜨렸다.** `V42`(`c_req_priority_value`) ·
> `V48`(`c_req_importance_link`·`c_req_urgency_link`) · `V52~V54`(`c_req_def_id`) 는 템플릿만 바꿨다.
> 이 컬럼들이 **오래된 제품 테이블에 있는지는 운영 DB 확인이 필요**하다 — 관련 작업 시 사용자에게 묻는다.

기타 규칙:
- **트리거는 `DELIMITER $$ … END $$ DELIMITER ;`** 로 감싼다(Flyway 파서 때문. 기존 20개 파일 전부 그렇다).
  단 `DynamicDBMakerDao.xml` 쪽 트리거는 MyBatis 단일 문장 실행이라 `DELIMITER` 를 쓰지 않는다.
- 새 트리 테이블은 **루트 2행 seed** 필수. 자식 seed 를 추가할 때는 **부모의 `C_RIGHT` 를 함께 UPDATE**
  한다(`V3` 의 `SET C_RIGHT=14/13` 이 그 예다). 이 두 줄을 빠뜨리면 nested-set 이 깨진다.
- 트리거(`TG_INSERT/UPDATE/DELETE_*`)는 **트리 공통 컬럼 8개 + method/state/date 만** `_LOG` 에 복사한다.
  도메인 컬럼을 추가해도 **트리거는 고칠 필요가 없다.**
- 배포된 마이그레이션 파일은 **절대 수정하지 않는다**(체크섬 불일치 → 기동 실패). 새 번호로 추가한다.
- Flyway 설정(`spring.flyway.*`)은 저장소에 없다 — **Global-Config(Config Server)에 있다.**

---

## 7. 외부 연동은 전부 Feign이다 — 직접 붙지 않는다

| 클라이언트 | 대상 | 용도 |
|-----------|------|------|
| `EngineService` | Engine-Fire (`${arms.engine.url}`) | ALM 이슈 CRUD · ES 적재 · 서버 검증 |
| `AggregationService` | Engine-Fire (같은 URL, 이름만 `engine-dashboard`) | 대시보드·분석 집계 |
| `AiService` | AI 모듈 | 성과 리포트 생성·분석 |
| `MiddleProxyService` | Middle-Proxy | WBS·요구사항정의서 업로드 락/발행 |
| `GlobalConfigService` | Global-Config | 조직 링크 조회 |
| `GotenbergClientService` | Gotenberg | PPTX→PDF 변환 |
| `InternalService` / `TemplateInternalService` | **자기 자신 `127.0.0.1:31313`** | 동적 테이블 라우팅 성립용 |

- **OpenSearch·Jira에 직접 붙지 않는다.** 전부 Engine-Fire 책임이다.
- 타임아웃은 `OpenFeignConfig`에서 전역 **connect 30초 / read 60분**이다. 길게 잡혀 있으니
  "느리다"는 증상은 타임아웃이 아니라 상대 서비스를 먼저 의심한다.
- `EngineService`는 **한글 메서드·DTO명**을 쓴다(`이슈_생성하기`, `증분이슈수집RequestDTO`).
  기존 관례이므로 유지하고, 호출 전 이름을 정확히 확인한다.

상세는 `references/integration.md`.

---

## 8. 지켜야 하는 표기 규칙

전체는 `references/conventions.md` + 저장소의 `docs/ai/04_coding_standards/`. 위반이 잦은 것만:

- **Java 11 / Spring Boot 2.6.15 / Spring Cloud 2021.0.9.** `javax.*` 를 쓴다.
  `jakarta.*`, record, sealed, `var` 남용, Java 17+ 문법은 **컴파일되지 않거나 관례에 어긋난다.**
- **테이블 `T_ARMS_*`, 컬럼 `c_` + snake_case.** 필드명 = 컬럼명이어야 한다 —
  엔티티는 `@Id`가 **getter에 있어 PROPERTY 접근**이고, 필드의 `@Column`은 무시되어
  **프로퍼티 이름으로 암묵 매핑**된다. 이름을 어긋나게 지으면 런타임에 컬럼을 못 찾는다.
- 엔티티 관례 애노테이션: `@Entity @Getter @Setter @Builder @NoArgsConstructor @AllArgsConstructor`
  `@SelectBeforeUpdate(true) @DynamicInsert(true) @DynamicUpdate(true) @Cache(usage = NONE)`.
  파생 필드는 `@Transient` + `@ApiModelProperty(hidden = true)`.
- **경로 prefix:** Backend-Core 컨트롤러는 `/arms/**`(78) · `/admin/arms/**`(6) · `/anonymous/**`(4)를 쓴다.
  `/auth-user`, `/auth-admin` 같은 prefix는 **Middle-Proxy 게이트웨이가 붙였다 떼는 것**이고
  이 저장소 코드에는 없다. 새 컨트롤러에 `/auth-*` 를 직접 쓰지 않는다.
  (저장소 문서 `docs/ai/08_domain_glossary §8`이 이 점을 혼동시키니 주의.)
- **로깅:** `@Slf4j` + `log.info("[클래스 :: 메서드] :: 설명 => {}", 값)`. `System.out.println` 금지
  (공통 프레임워크에 남아 있는 것은 기존 코드다 — 따라하지 않는다).
- **의존성 주입:** 신규는 `@RequiredArgsConstructor` + `private final`.
  기존 도메인의 `@Autowired @Qualifier("reqAdd")` 필드 주입은 그대로 둔다.
- 루트의 **`313DEVGRP-Rule.txt`는 실제 코드와 어긋난다**(메서드명 파스칼 표기, 클래스명 한글 등).
  실질 정본은 `docs/ai/04_coding_standards/backend-core-coding-standards.md` + 주변 코드다.

---

## 9. 이 저장소에서 반복적으로 사람을 무는 함정

자세한 증상·우회법은 `references/pitfalls.md`. 요약:

1. **`RouteTableConfig` 등록 누락** → 새 엔드포인트가 공용 템플릿 테이블을 읽고 쓴다. 무증상. (§3)
2. **`SessionUtil.removeAttribute()` 누락/예외 경로 누락** → 같은 스레드 후속 요청이 남의 테이블 조회.
3. **`updateNode`로 값을 비울 수 없다** → "지웠는데 그대로예요" 버그의 단골 원인. (§2)
4. **`getUnique()`는 null이 아니라 예외를 던진다** → null 체크 방어 코드가 무력.
5. **`@PostConstruct initialize()` 누락** → 상속 엔드포인트 전부 NPE.
6. **`setOrder()`는 누적된다** — `TreeServiceImpl.getChildNode`가 내부에서 `Order.desc(c_id)`를
   **추가로** 붙인다. 컨트롤러에서 `Order.asc("c_position")`를 줘도 c_id 정렬이 함께 들어간다.
7. **`treeDao.setClazz()`는 ThreadLocal**이다(`TreeDaoImpl`). 서비스 메서드마다 호출해야 하고,
   `@Async`/스레드풀에서 재사용되는 스레드에 이전 값이 남는다.
8. **`hibernate.jdbc.batch_size=100` + `SERIALIZABLE`** 조합이라 대량 트리 조작은 느리고 락을 오래 문다.
9. **로컬 JDK가 11이 아니면 컴파일이 깨진다** (Lombok + JDK 17/21/25 → `ExceptionInInitializerError`). (§10)
10. **엔티티를 그대로 응답에 노출**하면 `@OneToOne` 지연로딩·순환참조로 직렬화가 터진다.
    `ReqAddController.getNodesWithoutRoot`가 `c_req_contents` 등 대용량 필드를 **응답 직전에 null로
    비우는** 이유도 같다. 신규는 VO/DTO로 응답한다.

---

## 10. 빌드하고 확인하기

```bash
cd Java-Service-Tree-Framework-Backend-Core
JAVA_HOME="C:/Program Files/Microsoft/jdk-11.0.32.101-hotspot" ./gradlew compileJava
```

- **JDK 11이 필수**다. 이 PC 기본 JVM은 25라서 `./gradlew compileJava`가
  `java.lang.ExceptionInInitializerError`로 죽는다(Lombok 애노테이션 프로세서).
  위처럼 `JAVA_HOME`을 넘기면 **BUILD SUCCESSFUL**(검증 완료, 42초).
- Gradle 6.9.1 / `build.gradle`은 Windows에서 `wget`을 건너뛰고 커밋된 `metadata.xml`로 버전을 계산한다.
  그래서 **버전 숫자가 로컬에서 의미 없게 나오는 것은 정상**이다.
- **자동화 테스트가 없다**(`src/test` 자체가 없음). `test` 태스크는 비어 있다.
  → 검증 기준은 **`compileJava` 성공 + 변경 지점의 논리 검토 + (가능하면) 로컬 기동 후 엔드포인트 호출**이다.
  "테스트를 돌렸다"고 쓰지 않는다.
- 기동에는 **Config Server(Global-Config)가 필요**하다. `application.yml`에는 앱 이름과 로깅뿐이고
  DB·Kafka·Feign URL·CORS·Flyway 설정이 전부 외부에서 주입된다.
  프로파일: `dev` / `stg` / `live` / `mklee` (`bootstrap-*.yml`, `logback/logback-*.xml`).

상세는 `references/build-and-run.md`.

---

## 11. 제출 전 자가 점검

- [ ] 트리 도메인 / 집계 도메인 중 맞는 형태를 골랐다
- [ ] 트리 도메인이면 `@PostConstruct initialize()` 에 `setTreeService`·`setTreeEntity` 가 있다
- [ ] 동적 테이블(reqAdd/reqStatus/wiki)을 건드렸다면 **`RouteTableConfig`에 라우트 키를 등록**했다
- [ ] `SessionUtil.setAttribute` 마다 `finally` 로 `removeAttribute` 를 짝지었다
- [ ] `c_left`/`c_right`/`c_level`/`c_position` 을 직접 계산해 넣지 않았다
- [ ] 값을 비워야 하는 필드가 있다면 `updateNode` 부분 업데이트 제약을 확인·보고했다
- [ ] 스키마를 바꿨다면 Flyway `V56__*.sql` + `DynamicDBMakerDao.xml` + **기존 제품 테이블 반영 계획**이 있다
- [ ] 외부 데이터는 Feign 위임이고, OpenSearch/Jira에 직접 붙지 않았다
- [ ] 응답 형태를 (A) `jsonView` / (B) `CommonResponse` 중 **기존 계약에 맞게** 유지했다
- [ ] `javax.*` / Java 11 문법만 썼다
- [ ] `JAVA_HOME`=JDK 11 로 `./gradlew compileJava` 가 통과한다
- [ ] 시크릿·크리덴셜을 새로 하드코딩하지 않았다
- [ ] `System.out.println`·임시 로그·주석 처리 코드를 남기지 않았다
- [ ] 요청 범위를 넘는 리팩토링·"개선"을 하지 않았다

---

## 12. 산출 및 인계

- 사용자 대상 설명은 **한국어**로 한다.
- **commit·push 하지 않는다.** 작업 요약과 커밋 메시지 초안만 제시하고 커밋은 사용자가 한다.
  이 저장소의 실제 컨벤션(YouTrack 연동, 브랜치 `dev`):
  ```
  feat : [ARMS-1160] #comment 담당자별 진행율 로직 추가
  fix : [ARMS-1160] #comment 월별, 주별 진척율 기간 오류 수정
  refactor : [ARMS-1134] #comment ReqAddController::moveNodeFromKafka 메소드 리팩토링 26.08.10 #close #time 1h +review SR @sevoon0909
  ```
- 확신이 없는 지점(Engine-Fire 응답 스펙, 운영 테이블 현황, 임계값)은 추측으로 메우지 말고
  **가정을 명시**하거나 질문한다. 특히 **운영 DB의 제품별 테이블 목록은 코드로 알 수 없다.**

---

## 13. 참조 파일 지도

이 스킬의 상세 자료 (`references/`):

| 파일 | 언제 읽나 |
|------|----------|
| `references/tree-framework.md` | 트리 도메인을 만들거나 공통 CRUD 동작이 궁금할 때 |
| `references/dynamic-table-routing.md` | reqAdd·reqStatus·wiki 를 건드릴 때 / 엉뚱한 테이블이 조회될 때 |
| `references/persistence.md` | 쿼리·트랜잭션·DataSource 선택 |
| `references/schema-and-mappers.md` | **DB 를 건드리기 전 필독** — Flyway 규칙·동적 테이블 일괄 ALTER 패턴·전체 테이블 목록·프리셋 시드 값·MyBatis 설정·엔티티↔DDL 정합성 |
| `references/integration.md` | Feign · Kafka · DWR · Slack · 메일 · 스케줄러 |
| `references/reporting-excel.md` | PPT/PDF 리포트 · 엑셀 업로드/다운로드 |
| `references/conventions.md` | 네이밍·응답·예외·로깅·Swagger 규칙 |
| `references/pitfalls.md` | 이상 동작이 보일 때 / 착수 전 함정 확인 |
| `references/build-and-run.md` | 빌드·기동·프로파일·배포 |
| `assets/tree-domain-template/` | 새 트리 도메인 5파일 골격 (복사해서 시작) |

저장소 자체 문서 `Java-Service-Tree-Framework-Backend-Core/docs/ai/` 도 살아 있는 정본이다.
용어는 `08_domain_glossary`, 리뷰 기준은 `07_review_checklist`, 변경 이력은 `11_changelog`.

> ⚠️ 단, 아래는 **문서가 현재 코드와 어긋남을 확인**했다. 코드를 정본으로 삼는다.
> - `README.md` 배지가 Spring Boot 2.3.12 / Hoxton.SR9 로 적혀 있으나 실제는 **2.6.15 / 2021.0.9**다.
> - `04_coding_standards §4` 와 `08_domain_glossary §8` 이 컨트롤러에 `/auth-user` 등 권한 prefix를
>   쓴다고 서술하지만, **Backend-Core 컨트롤러에는 그런 prefix가 없다**(§8 참조).
> - `04_coding_standards §9` 가 "복잡한 동적 조회·통계는 MyBatis"라고 하지만, 실제 MyBatis는
>   **`util/dynamicdbmaker`·`util/samplemybastis` 2곳뿐**이고 통계는 Feign 위임이다.
> - `12_known_issues §6` 이 "스키마 변경은 Flyway"라고만 하지만 **동적 테이블은 Flyway로 안 바뀐다**(§6).
> - 루트 `313DEVGRP-Rule.txt` 는 실제 코드와 상충하는 레거시 문서다.
