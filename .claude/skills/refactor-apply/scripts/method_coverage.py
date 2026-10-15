#!/usr/bin/env python3
"""JaCoCo XML 에서 지정한 메소드들의 라인·브랜치 커버리지를 표로 뽑는다.

사용:
  python3 method_coverage.py <jacocoTestReport.xml> <대상> [<대상> ...] [--min 80] [-o out.md]

대상 형식(클래스는 소스 경로 기준 '/' 구분, .java 없이):
  com/arms/api/issue/almapi/service/IssueService:deleteIfDoesNotExistDoc,lambda$deleteIfDoesNotExistDoc$
  com/arms/api/issue/almapi/model/IssueRecentId:*        (클래스의 모든 메소드)
메소드 이름이 '$' 로 끝나면 접두어로 비교한다(람다 lambda$메소드$N 용).
--min 을 주면 라인 합계가 그 %% 미만일 때 종료 코드 1.
"""
import argparse
import sys
import xml.etree.ElementTree as ET


def parse_targets(specs):
    targets = {}
    for spec in specs:
        cls, _, methods = spec.partition(":")
        targets.setdefault(cls.replace(".", "/"), []).extend(m for m in methods.split(",") if m)
    return targets


def matches(name, patterns):
    if "*" in patterns:
        return True
    return any(name == p or (p.endswith("$") and name.startswith(p)) for p in patterns)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xml")
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--min", type=float)
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    targets = parse_targets(args.targets)
    root = ET.parse(args.xml).getroot()
    rows, found = [], set()
    lc = lm = bc = bm = 0
    for cls in root.iter("class"):
        name = cls.get("name")
        if name not in targets:
            continue
        for m in cls.findall("method"):
            if not matches(m.get("name"), targets[name]):
                continue
            found.add(name)
            c = {x.get("type"): (int(x.get("covered")), int(x.get("missed"))) for x in m.findall("counter")}
            l1, l2 = c.get("LINE", (0, 0))
            b1, b2 = c.get("BRANCH", (0, 0))
            lc, lm, bc, bm = lc + l1, lm + l2, bc + b1, bm + b2
            rows.append(f"| {name.split('/')[-1]} | {m.get('name')} | {l1}/{l1 + l2} | {b1}/{b1 + b2} |")

    line_pct = 100 * lc / (lc + lm) if lc + lm else 0.0
    branch_pct = 100 * bc / (bc + bm) if bc + bm else 100.0
    out = ["| 클래스 | 메소드 | 라인 | 브랜치 |", "|---|---|---|---|", *rows, "",
           f"**라인 {lc}/{lc + lm} = {line_pct:.1f}%**, 브랜치 {bc}/{bc + bm} = {branch_pct:.1f}%"]
    missing = sorted(set(targets) - found)
    if missing:
        out.append("")
        out.append("리포트에서 찾지 못한 대상(이름 오타·테스트가 클래스를 로드하지 않음): " + ", ".join(missing))
    text = "\n".join(out)
    print(text)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    if args.min is not None and (line_pct < args.min or missing):
        sys.exit(1)


if __name__ == "__main__":
    main()
