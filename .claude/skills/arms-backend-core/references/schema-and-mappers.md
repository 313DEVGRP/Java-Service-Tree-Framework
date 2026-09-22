# 스키마(Flyway) · MyBatis 매퍼 — `src/main/resources/com/arms/`

**초기 구성부터 현재까지 전부 이 디렉토리에서 확인 가능하다.** DB 상태를 추측하지 말고 여기를 읽는다.

```
src/main/resources/com/arms/
├── db/                                  ← Flyway 마이그레이션 (V1~V55, 50파일, 3,903줄)
└── egovframework/
    ├── mybatis/
    │   ├── mybatis-config.xml           ← MyBatis 전역 설정
    │   └── mapper/
    │       ├── DynamicDBMakerDao.xml    ← 제품별 동적 테이블 DDL 정본 (update 21개)
    │       └── MyBatisDao.xml           ← 샘플 (죽은 코드)
    ├── spring/                          ← context-common / context-hibernate / context-jdbc
    ├── property/globals.properties      ← 파일 경로 · DB 플레이스홀더
    ├── message/message-common_{ko,en}.properties   ← ⚠️ 참조되지 않는 egov 예제
    └── validator/{com-rules,validator-rules}.xml   ← ⚠️ Struts 레거시, 참조되지 않음
```

---

## 1. Flyway 마이그레이션 (`db/`)

| 항목 | 값 |
|---|---|
| 파일 수 | 50 (`V1` ~ `V55`, **`V33~V36`·`V41` 결번**) |
| 다음 번호 | **`V56`** |
| 명명 | `V<n>__init_aRMS.sql`(초기 계열) / `V<n>__<동사>_<대상>.sql`(예: `V51__add_user_group_table.sql`) |
| 설정(`spring.flyway.*`) | **저장소에 없음 — Global-Config(Config Server)에서 주입** |
| 총 DDL | `CREATE TABLE` 69, `CREATE TRIGGER` 약 150, 프리셋 `INSERT` 100여 |

### 작성 규칙 (기존 파일에서 귀납)

1. **본 테이블 + `_LOG` 테이블을 항상 함께** 바꾼다. (`V42`, `V48`, `V52`, `V55` 전부 쌍으로 ALTER)
2. `ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin`, 컬럼마다 한글 `COMMENT`.
3. 스키마 한정자 `` `aRMS`.`T_ARMS_XXX` `` 를 쓰는 파일과 안 쓰는 파일이 섞여 있다. **같은 파일 안에서만 일관되면 된다.**
4. **트리거는 반드시 `DELIMITER $$ … END $$ DELIMITER ;`** 로 감싼다.
   트리거가 있는 20개 파일 **전부** 이 형식이다(Flyway MySQL 파서가 `;` 로 잘라먹는 것을 막기 위함).
   ※ `DynamicDBMakerDao.xml` 의 트리거는 MyBatis 가 단일 문장으로 실행하므로 `DELIMITER` 를 쓰지 않는다. 혼동 금지.
5. **새 트리 테이블에는 루트 2행 seed 를 넣는다.** 그리고 **자식 seed 를 추가할 때는 부모의 `C_RIGHT` 를 함께 UPDATE** 한다.
   ```sql
   -- V1: 루트만 생성
   Values (1, 0, 0, 1, 4,  0, 'T_ARMS_REQPRIORITY', 'root');
   Values (2, 1, 0, 2, 3,  1, '요구사항 우선순위',   'drive');
   -- V3: 자식 5개를 넣기 전에 부모 경계부터 넓힌다  ★ 이 두 줄을 빠뜨리면 nested-set 이 깨진다
   UPDATE T_ARMS_REQPRIORITY SET C_RIGHT=14 WHERE C_ID=1;
   UPDATE T_ARMS_REQPRIORITY SET C_RIGHT=13 WHERE C_ID=2;
   Values (3, 2, 0, 3, 4, 2, '매우 낮음', 'default');   -- … 7까지
   ```
   (`T_ARMS_REQSTATE` 는 `V4` 가 `C_RIGHT=26/25` 로 같은 보정을 한다.)
6. **배포된 마이그레이션 파일은 절대 수정하지 않는다** (체크섬 불일치 → 기동 실패).
   `V53` → `V54` 가 같은 내용을 반복하는 것도 그래서다(수정 대신 새 파일).

---

## 2. ★ 기존 제품별 테이블을 일괄 변경하는 정식 패턴

`T_ARMS_REQADD_<pdServiceId>` 처럼 **런타임에 생성된 테이블**은 평범한 `ALTER TABLE T_ARMS_REQADD` 로는
바뀌지 않는다. 이 저장소는 이를 위해 **`information_schema` 커서 프로시저**를 쓴다.
`V13` · `V15` · `V19` 가 실제 사례다.

```sql
DELIMITER //
CREATE PROCEDURE AddDrawIOColumnsToReqAddTables()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE tableName VARCHAR(255);
    DECLARE cur CURSOR FOR
        SELECT table_name FROM information_schema.tables
         WHERE table_schema = DATABASE()
           AND table_name LIKE 'T_ARMS_REQADD%';       -- 템플릿·_LOG·제품별 전부 매칭
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    START TRANSACTION;
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO tableName;
        IF done THEN LEAVE read_loop; END IF;

        SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns
                               WHERE table_name = tableName AND column_name = 'c_drawio_contents');
        IF @column_exists = 0 THEN
            SET @alter_sql = CONCAT('ALTER TABLE ', tableName,
                ' ADD COLUMN c_drawio_contents LONGTEXT NULL COMMENT ''drawio xml'' AFTER c_req_contents');
            PREPARE stmt FROM @alter_sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
        END IF;
    END LOOP;
    CLOSE cur;
    COMMIT;
END//
DELIMITER ;

CALL AddDrawIOColumnsToReqAddTables();
```

| 파일 | 프로시저 | 대상 필터 |
|---|---|---|
| `V13` | `AddDrawIOColumnsToReqAddTables` | `LIKE 'T_ARMS_REQADD%'` (템플릿·`_LOG`·제품별 전부) |
| `V15` | `AddDrawDBColumnsToReqAddTables` | 〃 |
| `V19` | `AlterOrAddDrawDBAndDrawIOColumnTypeInReqAddTables` | `LIKE 'T_ARMS_REQADD%' AND NOT LIKE '%_LOG'` |

### 실무 규칙

- **요구사항 계열 컬럼을 추가할 때는 ① 템플릿 ALTER ② `DynamicDBMakerDao.xml` 수정 ③ 이 프로시저를
  세트로 작성**한다. `V13`/`V15`/`V19` 를 그대로 베끼면 된다.
- **`IF @column_exists = 0` 가드를 반드시 넣는다.** 넣지 않으면 일부 테이블에 이미 컬럼이 있을 때 통째로 실패한다.
- ⚠️ 세 파일 모두 **`DROP PROCEDURE` 를 하지 않아** 프로시저가 DB에 남는다. 새로 만들 때는
  `DROP PROCEDURE IF EXISTS <name>;` 를 앞에 두고, `CALL` 뒤에 `DROP PROCEDURE <name>;` 을 붙이는 편이 안전하다.
- ⚠️ **후기 마이그레이션은 이 패턴을 쓰지 않았다.** `V42`(`c_req_priority_value`) ·
  `V48`(`c_req_importance_link`·`c_req_urgency_link`) · `V52~V54`(`c_req_def_id`) 는 **템플릿만** 건드린다.
  → 이 컬럼들은 신규 생성 제품 테이블(`DynamicDBMakerDao.xml` 기준)에는 있지만,
  **그 이전에 만들어진 제품 테이블에 있는지는 운영 DB 확인이 필요**하다. 작업 시 사용자에게 확인을 요청한다.

---

## 3. `DynamicDBMakerDao.xml` — 동적 테이블의 정본

`DynamicDBMakerImpl.createSchema(pdServiceId)` 가 **제품 1개당 6테이블 + 9트리거**를 만든다.
매퍼 `update` 문 21개 = 3계열 × 7개(`ddl…Log`, `ddl…Org`, `dml…Org1`, `dml…Org2`, `trigger…Insert/Update/Delete`).

| 계열 | 테이블 | 컬럼 수 | 루트 seed |
|---|---|---|---|
| REQADD | `T_ARMS_REQADD_<id>` + `_LOG` | **47** | `(1,0,0,1,4,0,'REQADD Table','root')` / `(2,1,0,2,3,1,'요구사항','drive')` |
| REQSTATUS | `T_ARMS_REQSTATUS_<id>` + `_LOG` | **56** | `(…,'REQSTATUS Table','root')` / `(…,'요구사항 이슈 상태','drive')` |
| WIKI | `T_ARMS_WIKI_<id>` + `_LOG` | **14** | `(…,'Wiki Doc Table','root')` / `(…,'위키문서','drive')` |

`ReqAddImpl.ROOT_REF = 2L` 은 이 seed 의 `c_id=2`(`drive`)를 가리킨다.

### 동적 REQADD 47컬럼

```
c_id c_parentid c_position c_left c_right c_level c_title c_type
c_req_pdservice_link c_req_pdservice_versionset_link
c_req_reviewer01~05 + c_req_reviewer01~05_status        (10)
c_req_writer c_req_owner
c_req_create_date c_req_update_date c_req_start_date c_req_end_date
c_req_total_resource c_req_plan_resource c_req_total_time c_req_plan_time
c_req_plan_progress c_req_performance_progress c_req_manager c_req_output
c_req_priority_value c_req_priority_link c_req_state_link
c_req_difficulty_link c_req_importance_link c_req_urgency_link
c_drawio_contents c_drawio_image_raw c_drawdb_contents
c_req_def_id c_req_etc c_req_desc c_req_contents
```

### 동적 WIKI 14컬럼
```
트리공통 8 + c_wiki_title c_wiki_create_date c_wiki_update_date c_wiki_etc c_wiki_desc c_wiki_contents
```

### 트리거는 트리 공통 컬럼만 복사한다

`TG_INSERT/UPDATE/DELETE_<table>` 은 `_LOG` 에 `C_ID · C_PARENTID · C_POSITION · C_LEFT · C_RIGHT ·
C_LEVEL · C_TITLE · C_TYPE` + `C_METHOD · C_STATE · C_DATE` **만** 넣는다.
→ **도메인 컬럼을 추가해도 트리거는 고칠 필요가 없다.**

> ⚠️ `TG_INSERT_*` 가 `C_METHOD` 를 `'update'`, `C_STATE` 를 `'변경이전데이터'` 로 기록한다(INSERT인데).
> `_LOG` 를 해석할 때 감안한다. 요청 없이 고치지 않는다.

### grep 만으로 판단하지 말 것

`ddlOrgExecute`(47컬럼)와 Flyway 템플릿 `T_ARMS_REQADD`(V1 CREATE 29 + ALTER 15 = 44)를 **텍스트로만 비교하면
`c_drawio_contents`·`c_drawio_image_raw`·`c_drawdb_contents` 3개가 빠져 보인다.**
실제로는 `V13`/`V15`/`V19` 프로시저가 `LIKE 'T_ARMS_REQADD%'` 로 템플릿까지 함께 ALTER 하므로 **일치한다.**
정적 diff 로 "불일치"를 보고하기 전에 프로시저 파일을 먼저 확인한다.

---

## 4. 전체 테이블 목록 (`V*.sql` 기준 69개)

**본 테이블 + `_LOG` 짝**이 기본 구조다.

| 영역 | 테이블 |
|---|---|
| 트리맵 | `GLOBAL_TREE_MAP`, `GLOBAL_CONTENTS_TREE_MAP` (**`_LOG` 없음**, Spring Data JPA 전용) |
| 요구사항 | `T_ARMS_REQADD`, `T_ARMS_REQSTATUS`, `T_ARMS_REQCOMMENT`, `T_ARMS_REQREVIEW`, `T_ARMS_REQREVIEWCOMMENT` (+각 `_LOG`) |
| 요구사항 속성 | `T_ARMS_REQSTATE`, `T_ARMS_REQSTATE_CATEGORY`, `T_ARMS_REQPRIORITY`, `T_ARMS_REQDIFFICULTY`, `T_ARMS_REQIMPORTANCE`, `T_ARMS_REQURGENCY` (+각 `_LOG`) |
| 제품·버전 | `T_ARMS_PDSERVICE`, `T_ARMS_PDSERVICE_DETAIL`, `T_ARMS_PDSERVICEVERSION` (+`_LOG`) |
| ALM(Jira) | `T_ARMS_JIRASERVER`, `T_ARMS_JIRAPROJECT`, `T_ARMS_JIRAISSUETYPE`, `T_ARMS_JIRAISSUESTATUS`, `T_ARMS_JIRAISSUESTATUS_CATEGORY_MAP`, `T_ARMS_JIRAISSUEPRIORITY`, `T_ARMS_JIRAISSUERESOLUTION` (+각 `_LOG`) |
| 콘텐츠 | `T_ARMS_WIKI`, `T_ARMS_BLOG`, `T_ARMS_NEWSLETTER`, `T_ARMS_PATCHNOTE`, `T_ARMS_CLIENTCASE` (+각 `_LOG`) |
| 운영 | `T_ARMS_FILEREPOSITORY`, `T_ARMS_USER_GROUP`, `T_ARMS_HOLIDAY`, `T_ARMS_ANNUAL_INCOME`, `T_ARMS_SENDER_EMAIL`, `T_ARMS_RECEIVER_EMAIL` (+각 `_LOG`) |
| POC | `T_ARMS_POC`, `T_ARMS_POC_ASSIGNEE` (+각 `_LOG`) |

> `T_ARMS_REQADD`/`T_ARMS_REQSTATUS`/`T_ARMS_WIKI` 는 **템플릿**이고 운영 데이터는 `_<pdServiceId>` 테이블에 있다.

---

## 5. 프리셋 시드 값 (도메인 상수 — 코드에서 하드코딩하지 말고 이 값을 조회한다)

### `T_ARMS_REQSTATE_CATEGORY` (요구사항 상태 카테고리 · ARMS 전용)

| c_id | 제목 | `c_closed` | 아이콘 |
|---|---|---|---|
| 3 | 열림 | false | `fa-folder-o text-danger` |
| 4 | 진행중 | false | `fa-fire` (#E49400) |
| 5 | 해결됨 | **true** | `fa-fire-extinguisher text-success` |
| 6 | 닫힘 | **true** | `fa-folder text-primary` |
| 7 | 기타 | false | `fa-ellipsis-h text-muted` |

`c_closed='true'` 인 카테고리가 "완료"로 집계된다(`ReqState.완료상태조회()`).

### `T_ARMS_REQSTATE` (요구사항 상태, c_id 3~14)

`제안(3) · 승인(4) · A-RMS 전파(5) · 구현(6) · 검증(7) · 삭제(8) · 반려(9) ·
열림(10) · 진행중(11) · 해결됨(12) · 닫힘(13) · 기타(14)`
— `c_state_category_mapping_id` 로 위 카테고리에 매핑. `c_check` 는 `V17` 이 10·11·12 를 `true` 로 설정.

### 5단 척도 4종 (전부 c_id 3~7)

| 테이블 | 값 (c_id 3→7) |
|---|---|
| `T_ARMS_REQPRIORITY` | 매우 낮음 · 낮음 · 중간 · 높음 · **매우 높음** |
| `T_ARMS_REQDIFFICULTY` | 매우 어려움 · 어려움 · 보통 · 쉬움 · 매우 쉬움 |
| `T_ARMS_REQIMPORTANCE` | 매우 중요 · 중요 · 보통 · 낮음 · 매우 낮음 |
| `T_ARMS_REQURGENCY` | 매우 긴급 · 긴급 · 보통 · 검토 · 보류 |

> 정렬 방향이 테이블마다 다르다(우선순위는 낮음→높음, 난이도/중요도는 높음→낮음).
> 화면 정렬이나 점수 계산을 만들 때 **c_id 순서를 그대로 등급 순서로 가정하지 않는다.**

---

## 6. MyBatis 설정

`mybatis-config.xml`:

| 설정 | 값 | 의미 |
|---|---|---|
| `mapUnderscoreToCamelCase` | **true** | `post_title` → `postTitle` 자동 매핑 |
| `callSettersOnNulls` | **true** | null 필드도 결과에 포함(키 누락 방지) |
| `jdbcTypeForNull` | **NULL** | null 파라미터 전달 시 오류 방지 |

- 매퍼 위치: `classpath:com/arms/egovframework/mybatis/mapper/**/*.xml` (`MybatisConfig`)
- 인터페이스 스캔: `com.arms.api.util.**.mapper` — **그 밖에 `@Mapper` 를 만들면 잡히지 않는다.**
- `MyBatisDao.xml` 은 `MYBATIS_SAMPLE` 테이블을 SELECT 하는 샘플인데 **그 테이블은 DDL 어디에도 없다.**
  죽은 코드다. 새 매퍼의 본보기로 삼지 않는다.
- `mapUnderscoreToCamelCase=true` 인데 이 저장소의 컬럼은 `c_title` 형태라
  결과 VO 필드명이 `cTitle` 로 매핑된다. **동적 테이블 DDL 매퍼는 `${c_title}` 을 파라미터로만 쓰므로 무관**하지만,
  새 조회 매퍼를 만들 때는 이 변환을 감안해 `resultType` VO 필드명을 정한다.
- DDL 매퍼가 `${c_title}`(문자열 치환)을 쓴다. **외부 입력을 그대로 넘기면 SQL 인젝션**이다.
  `DynamicDBMakerImpl` 처럼 `접두사 + 숫자 ID` 형태로만 조립한다.

---

## 7. 기타 리소스

| 파일 | 상태 |
|---|---|
| `property/globals.properties` | **사용 중.** `Globals.fileStorePath=/mnt`, `system.uploadpath=/mnt`. `database.*`/`hibernate.*` 는 `${…}` 플레이스홀더(Config Server 주입) |
| `message/message-common_{ko,en}.properties` | ⚠️ egovFramework 예제 문구. `EgovMessageSource` 는 정의만 있고 **어디서도 쓰이지 않는다** |
| `validator/com-rules.xml`, `validator-rules.xml` | ⚠️ **Struts Validator 레거시.** 코드 참조 0건. 새 검증에 쓰지 않는다 — Bean Validation(`@Validated` + `validation/group/`)을 쓴다 |

`PropertiesReader` 로 `globals.properties` 를 읽는 곳: `PdServiceImpl` · `PdServiceDetailImpl` ·
`FileRepositoryController` · `BlogController` · `TemplateFileController`.

> ⚠️ `TemplateFileController` 는 경로를 **`"com/egovframework/property/globals.properties"`** 로 적어
> `arms/` 가 빠져 있다(2곳: 업로드·다운로드). 해당 리소스가 없으므로
> `PropertiesReader` 의 `properties.load(null)` 에서 **NPE** 가 난다. 이 컨트롤러를 건드릴 때 함께 고친다.

---

## 8. 엔티티 ↔ DDL 정합성 (실측)

- 엔티티 `@Table` **51개** vs DDL 테이블 **69개**.
- `_LOG` 테이블은 대부분 트리거 전용이라 엔티티가 없다(정상).
- `T_ARMS_CLIENTCASE`(+`_LOG`) 는 **DDL 에만 있고 코드 참조가 0건**이다(고아 테이블).
- `PocEntity` 는 `@Entity` 가 아닌 평범한 POJO 다 — `T_ARMS_POC` 는 JPA 로 매핑되지 않는다.
- `DynamicDBMakerEntity` 는 `@Table(name="T_ARMS_DYNAMICDBMAKER")` 인데 **그 테이블의 DDL 이 없다.**
  DDL 실행용 파라미터 홀더로만 쓰이므로 실제 조회는 일어나지 않는다.

### ⚠️ `*Log` 엔티티 5개 + 1개가 존재하지 않는/잘못된 테이블을 가리킨다

| 엔티티 | `@Table` | DDL 실제 이름 |
|---|---|---|
| `ReqAddLogEntity` | `T_ARMS_REQADDLOG` | `T_ARMS_REQADD_LOG` |
| `ReqCommentLogEntity` | `T_ARMS_REQCOMMENTLOG` | `T_ARMS_REQCOMMENT_LOG` |
| `ReqReviewLogEntity` | `T_ARMS_REQREVIEWLOG` | `T_ARMS_REQREVIEW_LOG` |
| `ReqStatusLogEntity` | `T_ARMS_REQSTATUSLOG` | `T_ARMS_REQSTATUS_LOG` |
| `JiraIssueStatusLogEntity` | `T_ARMS_JIRAISSUESTATUSLOG` | `T_ARMS_JIRAISSUESTATUS_LOG` |
| `ReqStateCategoryLogEntity` | `T_ARMS_REQSTATE_CATEGORY` | `T_ARMS_REQSTATE_CATEGORY_LOG` ← **로그가 아니라 본 테이블을 가리킨다** |

나머지 12개(`JIRAISSUETYPE_LOG`, `JIRAPROJECT_LOG`, `PDSERVICE_LOG`, `FILEREPOSITORY_LOG` …)는 정상이다.

**판단 기준:**
- `hibernate.hbm2ddl.auto` 가 Config Server 값이라 `update` 로 설정돼 있으면 Hibernate 가
  `T_ARMS_REQADDLOG` 를 **자동 생성**해 왔을 수 있다(그 경우 트리거가 쓰는 `_LOG` 와 **별개의 빈 테이블**이 존재).
- 즉 "화면에 이력이 안 나온다"는 증상의 유력한 원인이다.
- **이 6개를 임의로 고치지 않는다.** 운영 DB 확인이 필요하고, 고치는 순간 조회 대상 테이블이 바뀐다.
  발견 사실을 보고하고 사용자 판단을 받는다. 특히 `ReqStateCategoryLogEntity` 는
  로그 컨트롤러가 **실 카테고리 테이블에 쓰기**를 할 수 있으므로 우선 확인 대상이다.
