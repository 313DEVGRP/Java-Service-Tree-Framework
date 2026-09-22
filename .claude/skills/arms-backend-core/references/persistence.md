# 영속 계층 · 트랜잭션 · 스키마

---

## 1. 세 가지 영속 스택이 공존한다

| 스택 | 적용 범위 | 설정 위치 |
|------|----------|----------|
| **Hibernate 5 Criteria (TreeFramework)** | 도메인 대부분 (`TreeServiceImpl` 상속 61개) | `resources/com/arms/egovframework/spring/context-hibernate.xml` |
| **Spring Data JPA** | `com.arms.api.globaltreemap` **만** | `com/arms/config/SpringDataConfig.java` |
| **MyBatis** | `com.arms.api.util.**.mapper` **만** (`dynamicdbmaker`, `samplemybastis`) | `com/arms/config/MybatisConfig.java` |
| (보조) **JdbcTemplate** | `logJdbcTemplate` 빈 | `com/arms/config/JdbcConfig.java` |

```java
// SpringDataConfig
@EnableJpaRepositories(basePackages = {"com.arms.api.globaltreemap.*"},
        entityManagerFactoryRef = "entityManagerJpaFactory",
        transactionManagerRef = "transactionJpaManager")
// MybatisConfig
@MapperScan(basePackages = {"com.arms.api.util.**.mapper"}, sqlSessionTemplateRef = "sqlSessionTemplate")
```

> **다른 패키지에 `JpaRepository` 를 만들면 빈이 생성되지 않는다.**
> **`util` 밖에 `@Mapper` 를 만들면 스캔되지 않는다.**
> "간단하니까 JPA로/MyBatis로 짜자"는 판단은 이 두 줄 때문에 거의 항상 틀린다.
> 도메인은 TreeFramework 를 쓰거나, DB를 안 타는 집계 서비스(Feign 위임)로 만든다.

`report/weekly/mapper/WeeklyReportMapper` 는 MyBatis 매퍼가 **아니다** — 평범한 변환 클래스다.
이름만 보고 판단하지 않는다.

---

## 2. DataSource 4개 · 트랜잭션 매니저 2개

| 빈 | 타입 | 사용처 |
|----|------|--------|
| `onlyHibernateDataSource` | `DriverManagerDataSource` (**풀 없음**) | `sessionFactory` → TreeFramework 전체 |
| `onlyJpaDataSource` | `DriverManagerDataSource` (**풀 없음**) | `entityManagerJpaFactory` → globaltreemap |
| `onlyJdbcDataSource` | `DriverManagerDataSource` (**풀 없음**) | `logJdbcTemplate` |
| `onlyMybatisDataSource` | `HikariDataSource` | MyBatis |

| 트랜잭션 매니저 | 타입 | 기본 |
|---|---|---|
| `transactionManager` | `HibernateTransactionManager` | **primary** |
| `transactionJpaManager` | `JpaTransactionManager` | globaltreemap 전용 (`@Transactional("transactionJpaManager")` 명시 필요) |

`DriverManagerDataSource` 는 **요청마다 커넥션을 새로 연다.** 반복 쿼리를 루프로 도는 코드
(예: `stretchLeft`/`stretchRight` 가 노드 하나씩 `update`)는 그래서 비싸다.
대량 처리 기능을 새로 설계할 때 이 점을 먼저 고려하고, 필요하면 사용자에게 알린다.

Hibernate 설정(`context-hibernate.xml`):
`MySQL8Dialect` · `show_sql=false` · `max_fetch_depth=1` · `order_inserts/order_updates=true` ·
`jdbc.batch_size=100` · `packagesToScan=com.arms` · `entityInterceptor=RouteTableInterceptor`.

---

## 3. 트랜잭션 규칙

`TreeServiceImpl` 의 어노테이션 분포:

| 메서드군 | 어노테이션 |
|---|---|
| 조회 (`getNode`, `getChildNode*`, `getPaginated*`, `getNodesWithoutRoot*`) | `@Transactional(readOnly = true)` |
| **모든 쓰기** (`addNode`, `overwriteNode`, `removeNode`, `updateNode`, `updateField`, `saveOrUpdateList`, `alterNode`, `alterNodeType`, `moveNode`) | `@Transactional(rollbackFor = Exception.class, isolation = SERIALIZABLE, propagation = REQUIRED)` |
| `searchNode` | 없음 |

**`SERIALIZABLE` 이 기본이라는 점이 중요하다.** nested-set 은 노드 하나를 추가해도 트리 전체의
`c_left`/`c_right` 를 옮기므로 격리 수준을 올려 둔 것이다. 대신:

- 동시 쓰기에서 락 대기·데드락이 난다. 대량 등록(엑셀 업로드 등)은 **Kafka 로 직렬화**해 처리한다.
- 도메인 서비스에서 트리 쓰기 메서드를 여러 번 호출하면 `REQUIRED` 로 하나의 SERIALIZABLE 트랜잭션에 묶인다.
  트랜잭션이 길어지지 않게 호출 단위를 쪼갠다.
- 도메인 ServiceImpl 에 `@Transactional` 을 새로 붙일 때는 **`org.springframework.transaction.annotation`**
  패키지를 쓰고, primary 매니저를 탄다는 것을 전제한다.

---

## 4. 엔티티 매핑 규칙 (property access)

`TreeBaseEntity` 는 `@MappedSuperclass` 이고, 도메인 엔티티는 `@Id` 를 **getter 에 붙인다**:

```java
@Entity
@Getter @Setter @Builder @NoArgsConstructor @AllArgsConstructor
@Table(name = "T_ARMS_REQADD")
@SelectBeforeUpdate(true) @DynamicInsert(true) @DynamicUpdate(true)
@Cache(usage = CacheConcurrencyStrategy.NONE)
public class ReqAddEntity extends TreeSearchEntity implements Serializable {

    @Override
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "c_id")
    public Long getC_id() { return super.getC_id(); }
    ...
}
```

`@Id` 가 getter 에 있으므로 **접근 타입이 PROPERTY** 다. 결과적으로:

- Hibernate 는 **getter/setter 를 통해** 모든 프로퍼티를 매핑한다.
- 필드에 붙인 `@Column(name="...")` 은 **읽히지 않는다.** 컬럼명은 프로퍼티 이름에서 유도된다.
  이 저장소는 **필드명 = 컬럼명**(`c_req_writer` 등)이라 우연히 맞아떨어진다.
  → **필드명을 컬럼명과 다르게 지으면 런타임에 컬럼을 못 찾는다.**
- 영속시키지 않을 파생 값은 **getter 에 `@Transient`** 를 붙인다(필드가 아니라 getter).
  `@ApiModelProperty(hidden = true)` 도 함께 붙이는 것이 관례다.
- 연관관계도 getter 에 붙인다:
  ```java
  @LazyCollection(LazyCollectionOption.FALSE)
  @JsonManagedReference
  @OneToOne
  @JoinColumn(name = "c_req_pdservice_link", referencedColumnName = "c_id")
  public PdServiceEntity getPdServiceEntity() { return pdServiceEntity; }
  ```
- **1:N 연관은 동적 테이블 엔티티에 걸지 않는다.** `ReqAddEntity` 의 주석대로
  "파티셔닝 엔티티 대상으로는 지원하지 않으므로 개별 처리 대상"이다. `@Transient` 로 두고
  서비스에서 따로 채운다.

---

## 5. Flyway

- 위치: `src/main/resources/com/arms/db/V*__*.sql`
- 현재 `V1` ~ `V55`. **`V33~V36`, `V41` 이 비어 있다**(정상 — Flyway 는 연속 번호를 요구하지 않는다).
  다음 번호는 **`V56`**.
- 파일명 관례: `V<n>__init_aRMS.sql`(초기 스키마 계열) 또는 `V<n>__<동사>_<대상>.sql`
  (`V51__add_user_group_table.sql`, `V53__modify_reqadd_req_def_id.sql`).
- **`spring.flyway.*` 설정은 저장소에 없다.** Global-Config(Config Server)에서 주입된다.
  로컬에서 마이그레이션이 안 돈다면 설정이 아니라 Config Server 연결을 먼저 본다.
- 작성 규칙:
  - 본 테이블과 **`_LOG` 테이블을 항상 함께** 바꾼다 (`V52`, `V55` 참조).
  - 테이블 `T_ARMS_*`, 컬럼 `c_` + snake_case, `COMMENT` 를 한글로 단다.
  - `ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin`.
  - **트리거는 `DELIMITER $$ … END $$ DELIMITER ;`** 로 감싼다 — 트리거가 있는 20개 파일 전부 그렇다.
  - 신규 트리 테이블은 **루트 2행 seed INSERT** 를 반드시 넣는다
    (`c_id=1 type='root' left=1 right=4`, `c_id=2 type='drive' left=2 right=3`).
    자식 seed 를 추가할 때는 **부모의 `C_RIGHT` 를 함께 UPDATE** 한다(`V3`·`V4` 참조).
  - 이미 배포된 마이그레이션 파일은 **절대 수정하지 않는다**(체크섬 불일치로 기동 실패).
- **동적 테이블(`T_ARMS_REQADD_<id>` 등)도 Flyway 로 바꾼다** — `information_schema` 커서 프로시저
  패턴(`V13`·`V15`·`V19`). 평범한 `ALTER TABLE` 로는 닿지 않는다.
  전체 코드·규칙은 `references/schema-and-mappers.md` §2.
- 스키마·시드·매퍼의 실제 내용은 전부 `src/main/resources/com/arms/` 에서 확인 가능하다.
  DB 상태를 추측하기 전에 `references/schema-and-mappers.md` 를 먼저 읽는다.

---

## 6. 쿼리를 새로 짤 때의 선택지

| 필요 | 방법 |
|------|------|
| 트리 도메인의 조건 조회 | `TreeSearchEntity.setWhere*` + `getChildNodeWithoutPaging` |
| 복잡한 OR/IN/범위 | `entity.getCriterions().add(Restrictions...)` 로 Hibernate `Criterion` 직접 조립 |
| 집계/통계 | **Feign 으로 Engine-Fire(`AggregationService`)에 위임** — 여기서 SQL 집계를 짜지 않는다 |
| DDL(동적 테이블 생성) | MyBatis `DynamicDBMakerDao` |
| 단순 로그 적재 | `logJdbcTemplate` (`analysis/cost/SalaryLog*` 참고) |

**새로 JPQL·네이티브 쿼리·QueryDSL 을 도입하지 않는다.** 이 저장소에는 존재하지 않는 패턴이다.
