# 함정 모음 (증상 → 원인 → 대응)

전부 **소스에서 직접 확인한 것**이다. 저장소의 `docs/ai/12_known_issues/backend-core-known-issues.md`
와 겹치는 항목은 표시했고, 그 문서에 없는 것이 더 많다.

---

## A. 동적 테이블 라우팅

### A1. 새 엔드포인트가 빈 결과를 돌려준다 / 저장이 반영되지 않는다
**원인:** `RouteTableConfig` 에 라우트 키를 등록하지 않아 치환이 일어나지 않고, 비어 있는 템플릿
테이블 `T_ARMS_REQADD` 를 읽고 쓴다. `RouteTableInterceptor` 는 예외를 `log.info` 로 삼키므로 **무증상**이다.
**대응:** `com/arms/config/RouteTableConfig.java` 의 해당 맵에
`map.put("<마지막 경로 세그먼트>", "<attribute 키>")` 추가.

### A2. 다른 제품의 데이터가 보인다
**원인:** `SessionUtil.removeAttribute()` 누락, 또는 예외 경로에서 호출되지 않아 attribute 가
톰캣 스레드에 잔류 → 같은 스레드를 재사용하는 다음 요청에 적용.
**대응:** `try { ... } finally { SessionUtil.removeAttribute(key); }`. (사고 이력: commit `035302ec`)

### A3. `SessionUtil :: getAttribute - requestAttributes is null`
**원인:** Kafka 컨슈머 / `@Async` / `@Scheduled` 스레드에는 `RequestContextHolder` 가 없다.
**대응:** `InternalService`(loopback Feign, `127.0.0.1:31313`)로 자기 서버를 HTTP 호출한다.
**직접 서비스 호출로 "최적화"하지 않는다.**

### A4. `Unknown column 'c_xxx' in field list`
**원인:** 해당 마이그레이션이 **템플릿 테이블만** 바꾸고 기존 `T_ARMS_REQADD_<id>` 는 건드리지 않았다.
`V42`(`c_req_priority_value`) · `V48`(`c_req_importance_link`·`c_req_urgency_link`) ·
`V52~V54`(`c_req_def_id`) 가 그 경우다.
**대응:** `information_schema` 커서 프로시저 패턴(`V13`·`V15`·`V19`)으로 일괄 ALTER 마이그레이션을
작성한다. 전체 코드는 `references/schema-and-mappers.md` §2.
(`docs/ai/12_known_issues §6` 은 "스키마 변경은 Flyway"라고만 해서 이 구분을 놓친다.)

---

## B. TreeFramework

### B1. 필드를 비우려고 `updateNode` 를 호출했는데 값이 그대로다
**원인:** `TreeServiceImpl.updateNode` 는 `ObjectUtils.isEmpty(value)` 인 필드를 건너뛴다.
예외는 하드코딩된 `fieldsToAlwaysUpdate` 4개(`c_issue_delete_date`, `c_etc`,
`c_req_state_mapping_link`, `reqStateCategoryEntity`)뿐.
**대응:** `updateField(entity, "필드명")` 을 쓰거나 도메인 전용 update 를 만든다.
`fieldsToAlwaysUpdate` 수정은 **전역 영향** → 사용자 승인 필요.

### B2. `if (node == null)` 방어가 동작하지 않는다
**원인:** `TreeAbstractDao.getUnique()` 는 못 찾으면 `TreeDaoException` 을 던진다.
**대응:** `TreeServiceUtils.getNodeOptional(service, cId, Clazz.class)` 또는 try/catch.

### B3. 상속받은 엔드포인트 전부 NPE
**원인:** `@PostConstruct initialize()` 에서 `setTreeService(...)`/`setTreeEntity(...)` 누락.

### B4. 정렬이 의도대로 안 된다
**원인:** `TreeSearchEntity.setOrder(Order)` 는 **리스트에 add** 한다. 게다가
`TreeServiceImpl.getChildNode` 가 내부에서 `Order.desc("c_id")` 를 **추가로** 붙인다.
**대응:** 순수 정렬이 필요하면 `getChildNodeWithoutPaging` 또는 DAO 를 직접 쓰거나,
서비스가 반환한 리스트를 자바에서 다시 정렬한다.

### B5. 검색어에 `*` 가 들어가면 결과가 이상하다
**원인:** `setWhere(String, Object)` 가 `*` 접두/접미를 LIKE 매칭 모드로 해석한다.
`"isNotNull"` 로 시작하면 IS NOT NULL 로 바뀐다. 빈 문자열·null 은 **조건이 조용히 누락**된다.
**대응:** 사용자 입력은 정제 후 넘기고, 조건이 반드시 필요하면 `Restrictions` 로 명시적으로 조립한다.

### B6. 엉뚱한 테이블/엔티티로 쿼리가 나간다
**원인:** `treeDao.setClazz()` 누락. `TreeDaoImpl` 은 싱글턴 + `ThreadLocal<Class<T>>` 라
그 스레드가 직전에 쓰던 타입이 남아 있다. `ThreadLocal.remove()` 는 호출되지 않는다.
**대응:** 도메인 ServiceImpl 에서 DAO 를 직접 쓸 일이 있으면 매번 `setClazz` 부터 호출한다.

### B7. `folder` → `default` 타입 변경 실패
**원인:** `alterNodeType` 은 자식이 있으면
`RuntimeException("하위에 노드가 있는데 디폴트로 바꾸려고 함")` 을 던진다. 정상 동작이다.

### B8. `addNode` 가 `nodeByRef is default Type` 예외
**원인:** 부모로 지정한 `ref` 노드의 `c_type` 이 `default`(리프)다. 리프 밑에는 못 붙인다.

### B9. `/searchNode.do` 가 항상 전체를 돌려준다
**원인:** `TreeAbstractController.searchNode` 가 `request.getParameter("searchString")` 로 검증하고
정작 `parser.get("parser")` 로 값을 읽는다(오타). 즉 검색어가 전달되지 않는다.
**대응:** 도메인 컨트롤러에서 자체 검색 엔드포인트를 만든다. 공통 클래스 수정은 전역 영향.

---

### A5. 이력(`*Log`) 화면이 비어 있다
**원인 후보:** `*Log` 엔티티 6개가 실존하지 않거나 잘못된 테이블을 가리킨다 —
`T_ARMS_REQADDLOG` / `T_ARMS_REQCOMMENTLOG` / `T_ARMS_REQREVIEWLOG` / `T_ARMS_REQSTATUSLOG` /
`T_ARMS_JIRAISSUESTATUSLOG` (DDL 은 전부 `…_LOG` 로 언더바가 있다), 그리고
`ReqStateCategoryLogEntity` 는 `T_ARMS_REQSTATE_CATEGORY`(**본 테이블**)를 가리킨다.
`hibernate.hbm2ddl.auto` 가 `update` 면 Hibernate 가 빈 테이블을 자동 생성해 증상이 "비어 있음"으로 보인다.
**대응:** 임의로 고치지 않는다. 운영 DB 확인이 필요하고 고치면 조회 대상이 바뀐다.
발견 사실을 보고하고 판단을 받는다. 상세 표는 `references/schema-and-mappers.md` §8.

### A6. 트리거 DDL 이 Flyway 에서 깨진다
**원인:** `DELIMITER $$ … END $$ DELIMITER ;` 로 감싸지 않아 `;` 에서 문장이 잘렸다.
**대응:** 기존 20개 파일과 동일하게 감싼다. (`DynamicDBMakerDao.xml` 쪽 트리거는 MyBatis 단일 문장
실행이라 `DELIMITER` 를 쓰지 **않는다** — 두 경로를 혼동하지 말 것.)

## C. 영속 / 성능

### C1. 새로 만든 `JpaRepository` 가 빈으로 안 잡힌다
**원인:** `@EnableJpaRepositories(basePackages="com.arms.api.globaltreemap.*")`.
**대응:** 트리 도메인은 TreeFramework 를 쓴다. Spring Data JPA 를 확장하려면 설정 변경 승인이 필요하다.

### C2. 새로 만든 `@Mapper` 가 스캔되지 않는다
**원인:** `@MapperScan("com.arms.api.util.**.mapper")`.

### C3. 대량 트리 조작이 느리고 락을 오래 문다
**원인:** 모든 쓰기 메서드가 `Isolation.SERIALIZABLE` + `DriverManagerDataSource`(커넥션 풀 없음)
+ 노드 단건 UPDATE 루프(`stretchLeft`/`stretchRight`).
**대응:** 대량 등록은 Kafka 로 직렬화 처리(기존 설계). 새 배치 로직을 트랜잭션 하나에 몰지 않는다.

### C4. 엔티티를 응답에 그대로 넣었더니 직렬화가 터진다 / 응답이 수 MB다
**원인:** `@OneToOne` + `@LazyCollection(FALSE)` + 대용량 `longtext` 필드
(`c_req_contents`, `c_drawio_contents`, `c_drawio_image_raw`, `c_drawdb_contents`).
**참고:** `ReqAddController.getNodesWithoutRoot` 는 응답 직전에 이 4개를 `null` 로 비운다.
**대응:** 신규는 VO/DTO 로 응답한다.

### C5. DTO 필드가 매핑되지 않는다
**원인:** `modelMapper.map(dto, EntityClass)` 는 **이름이 같은 프로퍼티만** 매핑한다.
**대응:** DTO·Entity 필드명을 동일하게 맞춘다. 불가피하면 `PropertyMap` 을 명시한다.

---

## D. 빌드 / 환경

### D1. `./gradlew compileJava` 가 `java.lang.ExceptionInInitializerError` 로 죽는다
**원인:** 기본 JVM 이 JDK 17/21/25 라서 Lombok 애노테이션 프로세서가 깨진다(이 PC 기본은 **JDK 25**).
**대응:**
```bash
JAVA_HOME="C:/Program Files/Microsoft/jdk-11.0.32.101-hotspot" ./gradlew compileJava
```
→ BUILD SUCCESSFUL (검증 완료).

### D2. `*** Windows is not support build` 메시지
**원인:** `build.gradle` 이 Windows 에서 `wget` 으로 Nexus `maven-metadata.xml` 받는 것을 건너뛴다.
커밋된 `metadata.xml` 을 읽어 버전을 계산하므로 **빌드는 정상 진행**된다. 버전 숫자만 의미가 없다.

### D3. 테스트를 돌리려는데 없다
**원인:** `src/test` 디렉토리가 아예 없다. `test` 태스크는 비어 있다.
**대응:** "테스트 통과"를 보고하지 않는다. 검증은 `compileJava` + 코드 검토 + 가능하면 수동 호출이다.

### D4. 로컬 기동이 안 된다
**원인:** DB·Kafka·Feign URL·Flyway 설정이 전부 **Config Server(Global-Config)** 에서 온다.
`bootstrap-dev.yml` 은 `http://www.313.co.kr:33133` 을 본다.
**대응:** Config Server 접근이 안 되면 기동 자체가 불가하다. 사용자에게 확인한다.

---

## E. 문서 vs 코드 불일치 (저장소 문서를 그대로 믿지 말 것)

| 문서 | 문서의 서술 | 실제 |
|---|---|---|
| `README.md` 배지 | Spring Boot 2.3.12 / Hoxton.SR9 | **2.6.15 / 2021.0.9** |
| `docs/ai/04_coding_standards §4` | 컨트롤러 경로에 `/auth-user` 등 권한 prefix | 실제는 `/arms`·`/admin/arms`·`/anonymous` 뿐 |
| `docs/ai/08_domain_glossary §8` | 같은 내용 | 게이트웨이(Middle-Proxy) 레벨 개념 |
| `docs/ai/04_coding_standards §9` | 복잡 조회·통계는 MyBatis | MyBatis 는 `util/dynamicdbmaker`·`util/samplemybastis` 2곳뿐. 통계는 Feign 위임 |
| `docs/ai/12_known_issues §6` | 스키마 변경은 Flyway | 동적 테이블은 Flyway 로 안 바뀐다 |
| `313DEVGRP-Rule.txt` | 메서드명 파스칼 표기, 클래스명 한글 등 | 실제 코드와 상충. 따르지 않는다 |
| `docs/ai/03_directory_structure` | (참고용) | `api/` 하위 도메인이 문서 작성 이후 늘었다 — 코드로 확인 |

---

## F. 기타

- **`MiddleProxyFeignConfig` 는 어디에도 연결돼 있지 않다.** `@FeignClient(configuration=...)` 로
  지정하지 않는 한 SESSION 쿠키 전달 인터셉터는 동작하지 않는다. 파일 주석도 "아직 사용하지 않음"이다.
- **`TG_INSERT_*` 트리거가 `c_method` 를 `'update'` 로 기록**한다(INSERT인데). `_LOG` 를 해석할 때 감안한다.
- `sonarqube` 블록에 계정이 평문으로 있다. **새로 추가하지 말고**, 기존 것도 요청 없이 건드리지 않는다.
- `ThreadPoolConfig` 의 `taskExecutor-arms` 는 core 5 / max 10 / queue 10 + `CallerRunsPolicy` 로 작다.
  `@Async` 대량 투입 시 호출 스레드가 직접 실행하며 요청이 밀린다.
- Feign 읽기 타임아웃이 **60분**이다. "응답이 안 와요"는 타임아웃이 아니라 상대 서비스를 먼저 본다.
- **`TemplateFileController` 의 `globals.properties` 경로 오타** — `"com/egovframework/property/globals.properties"`
  (실제는 `com/arms/egovframework/...`). 2곳(업로드·다운로드). 리소스가 없어
  `PropertiesReader` 의 `properties.load(null)` 에서 **NPE** 가 난다. 이 파일을 건드릴 때 함께 고친다.
- **`validator/com-rules.xml`·`validator-rules.xml` 은 Struts 레거시**로 코드 참조가 0건이다.
  새 검증은 Bean Validation(`@Validated` + `treeframework/validation/group/`)으로 한다.
- **`message/message-common_*.properties` 와 `EgovMessageSource` 는 아무도 쓰지 않는다.** 참고하지 않는다.
- **`MyBatisDao.xml` 의 `MYBATIS_SAMPLE` 테이블은 DDL 에 없다.** 새 매퍼의 본보기로 삼지 않는다.
- **`T_ARMS_CLIENTCASE`(+`_LOG`)는 DDL 에만 있고 코드 참조가 0건**인 고아 테이블이다.
- DDL 매퍼가 `${c_title}` **문자열 치환**을 쓴다. 외부 입력을 그대로 넘기면 SQL 인젝션이다 —
  `DynamicDBMakerImpl` 처럼 `접두사 + 숫자 ID` 로만 조립한다.
