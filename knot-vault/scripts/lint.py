#!/usr/bin/env python3
"""knot 기계 검사 — stdlib only.

사용: python3 scripts/lint.py [vault경로]   (기본 = 현재 디렉토리)
ERROR 존재 시 exit 1. 검사 범위는 schema.md "워크플로" 절 참조.
"""
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

TYPES = {"source", "entity", "concept", "note"}
REQUIRED = ["type", "created", "updated", "sources"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"\[\[([^\]|#\n]+?)(?:\|[^\]]*)?\]\]")
STALE_DAYS = 90
INBOX_DAYS = 7

errors, warns, infos = [], [], []


def parse_frontmatter(text):
    """frontmatter dict 반환. 형식 자체가 깨졌으면 None."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    fm, key = {}, None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return fm
        if re.match(r"^[A-Za-z_]+\s*:", line):
            key, _, val = line.partition(":")
            key = key.strip()
            fm[key] = val.split("#")[0].strip()
        elif key and line.strip().startswith("- "):  # 블록 리스트 항목
            fm[key] = (fm[key] + "," if fm[key] else "") + line.strip()[2:].strip()
    return None  # 닫는 --- 없음


def parse_list(val):
    """'[a, b]' 또는 'a,b' → 리스트. 빈 값 → []."""
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        val = val[1:-1]
    return [x.strip().strip("'\"") for x in val.split(",") if x.strip()]


def main():
    vault = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    if not vault.is_dir():
        print(f"ERROR: vault 경로 아님: {vault}")
        return 1

    # 스텁 3개가 schema.md를 가리키는지
    for stub in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        p = vault / stub
        if not p.is_file() or "schema.md" not in p.read_text(encoding="utf-8"):
            errors.append(f"{stub}: 스텁이 없거나 schema.md를 가리키지 않음")

    pages = sorted(p for p in (vault / "wiki").glob("*.md")) if (vault / "wiki").is_dir() else []
    slugs = {p.stem for p in pages}
    inbound = {s: 0 for s in slugs}  # wiki 본문 기준 피링크 수
    stale_cands = []

    for p in pages:
        text = p.read_text(encoding="utf-8")
        name = f"wiki/{p.name}"
        fm = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{name}: frontmatter 없음/형식 불량")
            fm = {}
        for k in REQUIRED:
            if k not in fm:
                errors.append(f"{name}: frontmatter 필수 필드 누락 — {k}")
        if "type" in fm and fm["type"] not in TYPES:
            errors.append(f"{name}: 잘못된 type 값 '{fm['type']}' (허용: {'/'.join(sorted(TYPES))})")
        for k in ("created", "updated"):
            if k in fm and not DATE_RE.match(fm[k]):
                errors.append(f"{name}: {k} 날짜 형식 불량 '{fm[k]}' (YYYY-MM-DD)")
        for src in parse_list(fm.get("sources", "")):
            if src.startswith("raw/") and not (vault / src).is_file():
                errors.append(f"{name}: sources 경로 미실재 — {src}")
        if "updated" in fm and DATE_RE.match(fm.get("updated", "")):
            age = (date.today() - datetime.strptime(fm["updated"], "%Y-%m-%d").date()).days
            if age > STALE_DAYS:
                stale_cands.append((p.stem, age))

        body = text.split("---", 2)[2] if text.startswith("---") and text.count("---") >= 2 else text
        for line in body.split("\n"):
            for m in LINK_RE.finditer(line):
                target = m.group(1).strip()
                if target in slugs:
                    if target != p.stem:
                        inbound[target] += 1
                elif "<!-- stub -->" in line:
                    infos.append(f"INFO: stub 링크(작성 후보) — [[{target}]] ({name})")
                else:
                    errors.append(f"{name}: 깨진 링크 [[{target}]] — wiki/{target}.md 없음 (의도면 <!-- stub --> 표기)")

    # index ↔ wiki 정합
    index_slugs = []
    idx = vault / "index.md"
    if idx.is_file():
        for line in idx.read_text(encoding="utf-8").split("\n"):
            if line.strip().startswith("- "):
                m = LINK_RE.search(line)
                if m:
                    index_slugs.append(m.group(1).strip())
    else:
        errors.append("index.md 없음")
    for s in index_slugs:
        if s not in slugs:
            errors.append(f"index.md: 파일 없는 항목 [[{s}]]")
    for s in sorted(slugs - set(index_slugs)):
        errors.append(f"index.md: 등재 누락 — [[{s}]]")
    for s in sorted({s for s in index_slugs if index_slugs.count(s) > 1}):
        errors.append(f"index.md: 중복 항목 [[{s}]]")

    # 고아: 다른 wiki 페이지로부터 피링크 0 (index 등재는 불충분)
    for s in sorted(slugs):
        if inbound.get(s, 0) == 0:
            warns.append(f"WARN: 고아 페이지 — [[{s}]] (다른 페이지에서 링크 없음)")

    for s, age in sorted(stale_cands, key=lambda x: -inbound.get(x[0], 0)):
        infos.append(f"INFO: stale 후보 — [[{s}]] (updated {age}일 경과, 피링크 {inbound.get(s, 0)})")

    inbox = vault / "inbox"
    if inbox.is_dir():
        for f in sorted(inbox.iterdir()):
            if f.name.startswith("."):
                continue
            days = int((time.time() - f.stat().st_mtime) // 86400)
            if days > INBOX_DAYS:
                infos.append(f"INFO: inbox 적체 — {f.name} ({days}일)")

    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(w)
    for i in infos:
        print(i)
    print(f"-- pages={len(pages)} errors={len(errors)} warns={len(warns)} infos={len(infos)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
