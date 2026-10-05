# 액션 아이템 md → 엑셀(xlsx). 아이템 하나가 한 행이 되어 담당자·상태를 적어 가며 관리할 수 있다.
# 사용: python3 to_xlsx.py <md 파일> [<md 파일> ...] [-o 출력.xlsx]
#   - md 하나면 기본 출력은 같은 위치의 같은 이름 .xlsx
#   - md 여러 개면 한 파일로 합친다 (-o 필수). "대상" 열로 구분된다.
# 필요: pip install openpyxl
import sys, re, os, argparse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

def clean(text):
    text = text.replace("<br>", "\n").replace("\\|", "|").replace("`", "")
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text).strip()

def parse(path):
    md = open(path, encoding="utf-8").read()
    title = re.search(r"^# 리팩토링 액션 아이템 — (.+)$", md, re.M)
    meta = dict(re.findall(r"^- (점검 대상|점검일): (.+)$", md, re.M))
    doc = {"대상": title.group(1).strip() if title else os.path.basename(path),
           "점검 대상": clean(meta.get("점검 대상", "")), "점검일": meta.get("점검일", "").strip()}

    def sections(heading):
        m = re.search(r"^## " + heading + r"\n(.*?)(?=^## |\Z)", md, re.M | re.S)
        return m.group(1) if m else ""

    def blocks(body, prefix):
        out = []
        for b in re.split(r"^### ", body, flags=re.M)[1:]:
            head, _, rest = b.partition("\n")
            if not head.startswith(prefix):
                continue
            row = {"head": head.strip()}
            for label, value in re.findall(r"^\| \*\*(.+?)\*\* \| (.*) \|$", rest, re.M):
                row[label] = clean(value)
            for cap, code in re.findall(r"^\*(원문|바꾼 모습)\*.*?\n\n```[^\n]*\n(.*?)\n```", rest, re.M | re.S):
                row[cap] = code
            out.append(row)
        return out

    items = []
    for r in blocks(sections("액션 아이템"), "A-"):
        m = re.match(r"(A-\d+) \[(.+?)\] (.+?) — 우선순위 (\S+)$", r["head"])
        no, cat, name, prio = m.groups() if m else (r["head"], "", "", "")
        items.append([doc["대상"], no, cat, prio, name, r.get("위치", ""), r.get("무엇이 문제인가", ""),
                      r.get("왜 수정이 필요한가", ""), r.get("이렇게 바꾼다", ""), r.get("먼저 할 것", ""),
                      r.get("주의", ""), r.get("원문", ""), r.get("바꾼 모습", ""), "", "미착수", ""])
    findings = []
    for r in blocks(sections("리팩토링이 아닌 발견"), "F-"):
        m = re.match(r"(F-\d+) \[(.+?)\] (.+)$", r["head"])
        no, kind, name = m.groups() if m else (r["head"], "", "")
        findings.append([doc["대상"], no, kind, name, r.get("위치", ""), r.get("내용", ""), r.get("권고", ""), "", "미착수", ""])
    others = []
    for line in sections("그 밖의 후보").splitlines():
        m = re.match(r"^- (.+?) \[(.+?)\] (.+)$", line)
        if m:
            others.append([doc["대상"], clean(m.group(1)), m.group(2), clean(m.group(3))])
        elif line.startswith("- "):   # 폴더 순위 요약처럼 [카테고리] 형식이 아닌 줄도 빠뜨리지 않는다
            others.append([doc["대상"], "", "", clean(line[2:])])
    targets = [[doc["대상"], doc["점검 대상"], doc["점검일"], len(items), len(findings)]]
    return items, findings, others, targets

STATUS = '"미착수,진행 중,완료,보류,하지 않음"'
SHEETS = [
    ("액션 아이템", ["대상", "#", "카테고리", "우선순위", "제목", "위치", "무엇이 문제인가", "왜 수정이 필요한가",
                  "이렇게 바꾼다", "먼저 할 것", "주의", "원문", "바꾼 모습", "담당자", "상태", "비고"],
     [18, 7, 16, 9, 34, 38, 50, 44, 50, 38, 34, 50, 50, 10, 10, 20], "O"),
    ("리팩토링이 아닌 발견", ["대상", "#", "구분", "제목", "위치", "내용", "권고", "담당자", "상태", "비고"],
     [18, 7, 12, 36, 38, 60, 44, 10, 10, 20], "I"),
    ("그 밖의 후보", ["대상", "위치", "카테고리", "내용"], [18, 40, 14, 70], None),
    ("점검 대상", ["대상", "점검 대상", "점검일", "액션 아이템", "리팩토링이 아닌 발견"], [24, 70, 12, 12, 18], None),
]
PRIO_FILL = {"높음": "F8D7DA", "중간": "FFF3CD", "낮음": "E2EFDA"}

def write(rows_by_sheet, out):
    wb = Workbook(); wb.remove(wb.active)
    thin = Side(style="thin", color="C9D3D8")
    for (name, header, widths, status_col), rows in zip(SHEETS, rows_by_sheet):
        ws = wb.create_sheet(name)
        ws.append(header)
        for row in rows:
            ws.append(row)
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="0E4F63")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                cell.border = Border(top=thin, bottom=thin, left=thin, right=thin)
                if header[cell.column - 1] in ("원문", "바꾼 모습"):
                    cell.font = Font(name="Menlo", size=9)
                if header[cell.column - 1] == "우선순위" and cell.value in PRIO_FILL:
                    cell.fill = PatternFill("solid", fgColor=PRIO_FILL[cell.value])
        ws.freeze_panes = "C2"
        if rows:
            ws.auto_filter.ref = ws.dimensions
        if status_col and rows:
            dv = DataValidation(type="list", formula1=STATUS, allow_blank=True)
            ws.add_data_validation(dv)
            dv.add(f"{status_col}2:{status_col}{len(rows) + 1}")
    wb.save(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md", nargs="+")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    if len(a.md) > 1 and not a.out:
        sys.exit("md 파일이 여러 개면 -o 로 출력 파일을 지정하세요.")
    out = a.out or a.md[0][:-3] + ".xlsx"
    merged = [[], [], [], []]
    for path in a.md:
        for acc, part in zip(merged, parse(path)):
            acc.extend(part)
    write(merged, out)
    print(f"{out}  (액션 아이템 {len(merged[0])}건, 리팩토링이 아닌 발견 {len(merged[1])}건, 그 밖의 후보 {len(merged[2])}건)")

if __name__ == "__main__":
    main()
