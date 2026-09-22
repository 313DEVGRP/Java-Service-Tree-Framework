# 리포트(PPT/PDF) · 엑셀 입출력

`com/arms/api/report/` 는 이 저장소에서 **가장 큰 단일 서브시스템**(Java 200여 파일)이다.
기능을 얹기 전에 어느 계층에 붙는 일인지부터 판별한다.

---

## 1. `report/` 하위 구조

| 패키지 | 성격 |
|---|---|
| `export_service/` | **PPTX/PDF 생성 엔진.** 템플릿 바인딩·차트·표·이미지·오버플로 처리 |
| `fulldata/` | 전체 데이터 엑셀 다운로드(스트리밍) |
| `weekly/` | 주간 업무보고 데이터 조립 (VO 중심, Feign 집계 사용) |
| `collaboratekpi/` | 주간 KPI 리포트 |
| `performance/` | 개인 성과 리포트(AI 모듈 연동) |
| `ptr/` | Portfolio Track Record |
| `reqtrace/` | 요구사항 추적 리포트 |
| `mail/` | 리포트 메일 발송/수신 로그 도메인 |

---

## 2. `export_service` — 템플릿 바인딩 파이프라인

```
요청 DTO (SimpleReportRequest / WeeklyReportRequest / MasterReportRequest / EditorExportRequest)
   │
   ├ TemplateLoader ← TemplateStorageProvider
   │                    ├ ClasspathTemplateStorage   (resources/templates/report/*.pptx = 시스템 템플릿)
   │                    ├ FileSystemTemplateStorage  (업로드된 사용자 템플릿)
   │                    └ CompositeTemplateStorage   (둘을 합침 · isSystemTemplate 로 구분)
   │
   ├ TemplateAnalyzerService → PlaceholderResolver → PlaceholderInfo
   │
   ├ TemplateBindService
   │     ├ TextBindingHandler      {{TEXT:id}}
   │     ├ ChartBindingHandler     {{CHART:id}}   → NativeChartGenerator / ChartImageGenerator
   │     ├ TableBindingHandler     {{TABLE:id}}   → TableOverflowHandler
   │     ├ ImageBindingHandler     {{IMAGE:id}}
   │     ├ AltTextBindingHandler   (도형 대체텍스트 기반 바인딩)
   │     ├ MasterBindingHandler    (마스터 슬라이드)
   │     └ OverflowHandler / TextOverflowHandler
   │
   ├ PptGenerator  → .pptx
   └ PptToPdfConverter / GotenbergPdfService → .pdf   (PdfMergeUtils 로 병합)
```

- **플레이스홀더 문법은 `{{TYPE:ID}}`** — `TEXT` · `CHART` · `TABLE` · `IMAGE` · `MARKDOWN`
  (`enums/PlaceholderType`). 알 수 없는 타입은 `UNKNOWN` 으로 떨어지고 무시된다.
- **출력 타입은 `ExportType` 2종뿐** — `PPT`(.pptx) · `PDF`(.pdf).
  프론트가 보내는 `"pptx"` 표기는 `fromStringOrDefault` 가 `PPT` 로 흡수한다.
  `fromString` 은 `"pptx"` 에서 예외를 던지니 **새 코드는 `fromStringOrDefault` 를 쓴다.**
- 시스템 템플릿은 `src/main/resources/templates/report/` 에 있다:
  `arms_default_template_1.pptx`, `default_template_simple_chart.pptx`,
  `default_template_simple_chart_table.pptx`, `default_template_textarea.pptx`,
  `personal-performance-{with,except}-analysis-v2.pptx`, `project-status-weekly.pptx`,
  `weekly-business-report.pptx`.
  **템플릿 pptx 를 수정하면 바인딩 코드가 찾는 플레이스홀더가 사라질 수 있다** — 짝으로 확인한다.
- 긴 응답은 `DeferredResult<ResponseEntity<byte[]>>` 로 비동기 반환한다
  (`/arms/export/reports/simple-report`, `/simple-report-v2`, `/weekly-report`).
  스레드를 막지 않도록 이 패턴을 유지한다.
- 예외는 `ReportExceptionHandler`(`@RestControllerAdvice`)가 따로 처리한다
  (`ReportExportException`, `TemplateNotFoundException`).

### Apache POI 함정 (실제 이력)

- **차트 앵커는 EMU 단위**다. 픽셀 값을 그대로 넣으면 앵커가 어긋난다.
- **`numRef` vs `numLit`** — 데이터 소스를 셀 참조로 둘지 리터럴로 둘지에 따라 렌더가 달라진다.
  템플릿이 어느 방식인지 먼저 확인한다.
- 그룹 막대는 `BarGrouping.CLUSTERED` 등을 **명시**해야 한다.
- 한글 폰트는 `resources/font/NanumGothic.ttf` / `NanumGothicBold.ttf` 를 쓴다. 미지정 시 깨진다.
- POI 는 메모리를 많이 쓴다. 컨테이너 힙이 `-Xms2g -Xmx2g` 로 고정돼 있으니
  대용량 처리는 스트리밍 API 를 쓴다.

의존성: `poi 5.1.0` / `poi-ooxml 5.1.0` / `excel-streaming-reader 4.0.5` /
`pdfbox 3.0.1` / `boxable 1.7.0` / `jsoup 1.14.3` / `selenium 4.25.0` + `webdrivermanager`.

---

## 3. 엑셀 다운로드 — `treeframework/excel`

애노테이션 기반 매핑이다. VO 클래스에 붙인다:

```java
@ExcelClassAnnotation(sheetName = "요구사항", headerRowSize = 1,
                      headerTitleRowSize = 1, headerTitleName = "요구사항 목록")
public class SomeExcelVO {
    @ExcelFieldAnnotation(columnIndex = 0, headerName = "제목")
    private String title;

    @ExcelFieldAnnotation(columnIndex = 1, headerName = "시작일", formatting = "yyyy-MM-dd")
    private Date startDate;
}
```

| 클래스 | 용도 |
|---|---|
| `ExcelDown` | 일반 다운로드(메모리 적재) |
| `ExcelStreamDown` | **대용량 스트리밍 다운로드** (`FullDataExcelStreamDown` 이 상속) |
| `ExcelRead` / `ExcelReadWrapper` | 업로드 파싱 |
| `ExcelPoiFactory` | 워크북/셀 스타일 팩토리 |
| `CellTemplate` · `HeaderRange` · `MergeHeaderBox` · `ExcelKeyField` · `ExcelVersionEnum` | 헤더 병합·키 필드 처리 |

사용처: `analysis/cost/SalaryController`, `analysis/resource/ResourceController`,
`report/fulldata/FullDataController`, `requirement/reqadd/ReqAddImpl`.

**행 수가 수천 건을 넘을 가능성이 있으면 `ExcelStreamDown` 을 쓴다.**

---

## 4. 엑셀 업로드 — 요구사항정의서 / WBS

경로: `api/requirement/reqadd/excelupload/` (`ExcelGantUpload`, `WbsSchedule`)
+ `ReqAddImpl.reqAddByExcelUpload(...)` / `reqAddByReqDefExcelUpload(...)`

흐름:

```
프론트 → Middle-Proxy (파일 저장 · Redis 락 · requestId 발급)
        → Kafka REQADD (행 단위 메시지)
        → Backend-Core ReqAddConsumer → InternalService loopback → ReqAddController
        → 행별 콜백(ReqDefCallbackHandler / WbsCallbackHandler) → Middle-Proxy 진행률 통지
        → 완료 후 pruneEmptyFoldersFromUpload.do 로 빈 분류 폴더 정리
```

- 업로드 락(`/wbs/pd-service-id/{id}/lock`, `/req-def/...`)은 **Middle-Proxy 가 관리**한다.
  Backend-Core 는 `MiddleProxyService` 로 요청만 한다.
- 진행 상황은 DWR(`Chat`)로 화면에 푸시된다.
- 업로드 결과 조회: `reqAddByExcelUploadList(serviceId)` / `reqAddByReqDefExcelUploadList(serviceId)`.
- 파일 저장 경로는 `globals.properties` 의 `Globals.fileStorePath = /mnt` (컨테이너 볼륨).

**엑셀 업로드 로직을 고칠 때는 Middle-Proxy 쪽 계약도 함께 확인**한다. 두 저장소가 맞물려 있다.

---

## 5. 데이터가 없는 항목은 만들어내지 않는다

Engine-Fire 인덱스(AlmIssueEntity)에 다음이 **없다**
(`docs/ai/12_known_issues §7`, `docs/ai/06_domain_playbooks/kpi.md §6`):

- `duedate`(계획 마감일) → 계획 종료일·지연/임박 판정 불가
- FP 수치 (`cReqProperty` 에 이름만 존재)
- 상태 전환/QA 이력
- 위키·코드 활동

→ 리포트 VO 에 필드는 두되 **null / 0 / 빈 배열**로 응답한다. **임의 값·목업을 채우지 않는다.**
