#!/usr/bin/env python3
"""리팩토링 후보 탐지기 (읽기 전용).

가이드북 카테고리(자바 RF-xx, 자바스크립트 JS-xx)에 해당할 수 있는 위치를 빠르게 찾는다.
결과는 '후보'일 뿐이다 — 액션 아이템으로 쓰기 전에 반드시 원문을 읽고 판단한다.

사용:
  scan.py <파일|폴더> [...]            지정 범위 전체
  scan.py --diff [--base REF] [<git 저장소 경로> ...]
                                       git 변경분(작업 트리 + 스테이징, 또는 REF 대비)에 걸친 후보만
"""
import argparse
import collections
import os
import re
import subprocess
import sys

SKIP_DIRS = {"node_modules", ".git", "build", "out", "target", "dist", "reference", "showdown", "jspreadsheet", "test", "tests"}
JAVA, JS = ".java", ".js"


# ---------------------------------------------------------------- 대상 수집
def collect(paths):
    files = []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
            continue
        for d, dirs, fs in os.walk(p):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            for f in fs:
                if f.endswith((JAVA, JS)) and ".min." not in f:
                    files.append(os.path.join(d, f))
    return files


def git_changed(repo, base):
    """{절대경로: set(변경된 줄 번호)} — 새 파일은 전체 줄."""
    cmd = ["git", "-C", repo, "diff", "-U0"] + ([base] if base else ["HEAD"])
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return {}
    top = subprocess.run(["git", "-C", repo, "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    changed, cur = {}, None
    for line in out.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            cur = None if path == "/dev/null" else os.path.join(top, path[2:] if path.startswith("b/") else path)
            if cur:
                changed.setdefault(cur, set())
        m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line)
        if m and cur:
            start, n = int(m.group(1)), int(m.group(2) or 1)
            changed[cur].update(range(start, start + max(n, 1)))
    # 아직 추적되지 않은 새 파일
    untracked = subprocess.run(["git", "-C", repo, "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True).stdout
    for f in untracked.splitlines():
        if f.endswith((JAVA, JS)):
            changed[os.path.join(top, f)] = None  # None = 파일 전체
    return {k: v for k, v in changed.items() if k.endswith((JAVA, JS))}


# ---------------------------------------------------------------- 공통 유틸
def indent(s):
    return len(s) - len(s.lstrip(" \t").replace("\t", "    ")) if s.strip() else 0


def block_end(lines, start):
    """선언 줄과 같은 들여쓰기의 닫는 '}' 를 찾는다 (문자열 속 중괄호에 속지 않도록 들여쓰기 기준)."""
    if lines[start].count("{") <= lines[start].count("}"):
        return start  # 한 줄짜리 함수 (function x() {})
    base = len(lines[start]) - len(lines[start].lstrip())
    head = lines[start][:base]
    for j in range(start + 1, len(lines)):
        l = lines[j]
        if l.startswith(head + "}") and len(l) - len(l.lstrip()) == base:
            return j
    return start


def max_depth(lines, s, e):
    base = len(lines[s].expandtabs(4)) - len(lines[s].expandtabs(4).lstrip())
    deep = 0
    for l in lines[s + 1:e]:
        t = l.expandtabs(4)
        if t.strip() and not t.strip().startswith(("//", "*", "/*")):
            deep = max(deep, (len(t) - len(t.lstrip()) - base) // 4)
    return deep


# ---------------------------------------------------------------- 자바
J_METHOD = re.compile(r"^\s*(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?[\w<>\[\],.? ]+\s+(\w+)\s*\(([^)]*)\)\s*(?:throws [\w., ]+)?\s*\{\s*$")


def scan_java(path, lines, hit):
    n = len(lines)
    if n > 500:
        hit(1, "RF-08", f"큰 클래스 {n}줄")
    is_controller = any("@RestController" in l or "@Controller" in l for l in lines[:60])
    switch_vars = collections.defaultdict(list)
    chains = collections.defaultdict(list)
    for i, l in enumerate(lines):
        ln, t = i + 1, l.strip()
        m = J_METHOD.match(l)
        if m:
            e = block_end(lines, i)
            length, depth = e - i + 1, max_depth(lines, i, e)
            params = [p for p in m.group(2).split(",") if p.strip()]
            if length > 60:
                hit(ln, "RF-03", f"긴 메소드 {m.group(1)}() {length}줄")
            if depth >= 5:
                hit(ln, "RF-03/RF-06", f"깊은 중첩 {m.group(1)}() 들여쓰기 {depth}단")
            if len(params) >= 5:
                hit(ln, "RF-04", f"인수 {len(params)}개 {m.group(1)}()")
            if re.search(r"\bboolean\s+\w+", m.group(2)) and len(params) >= 2:
                hit(ln, "RF-04", f"boolean 플래그 인수 {m.group(1)}()")
            if is_controller and length > 25:
                hit(ln, "RF-11", f"긴 컨트롤러 메소드 {m.group(1)}() {length}줄")
        sw = re.search(r"\bswitch\s*\(\s*([\w.()]+)\s*\)", t)
        if sw:
            switch_vars[sw.group(1)].append(ln)
        for c in re.findall(r"\b\w+\.get\w+\(\)\.get\w+\(\)", t):
            chains[c].append(ln)
        if re.match(r"//.*[;{}]\s*$", t) and not re.match(r"//\s*(TODO|FIXME|NOTE)", t):
            hit(ln, "RF-01", "주석 처리된 코드")
        if re.search(r"\b(TODO|FIXME)\b", t):
            hit(ln, "RF-01", "TODO/FIXME 남음")
        if re.search(r'"[A-Za-z0-9_\-가-힣]{1,20}"\.equals\(', t):
            hit(ln, "RF-07", "문자열 코드 비교")
        if re.search(r"(?<![\w.\"])(?:[2-9]\d{2,}|1\d{3,})(?![\w.\"])", t) and not t.startswith(("*", "//", "@", "import")) and "static final" not in t:
            hit(ln, "RF-07", "매직 넘버")
        if t == "return null;":
            hit(ln, "RF-09", "return null")
        if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", t):
            hit(ln, "RF-09", "빈 catch")
        if re.search(r"catch\s*\(\s*(Exception|Throwable)\s+\w+\s*\)", t):
            nxt = " ".join(x.strip() for x in lines[i + 1:i + 3])
            if re.search(r"return (false|null|0|-1)\s*;", nxt):
                hit(ln, "RF-09", "모든 예외를 잡아 false/null 반환")
        if re.match(r"(private|public|protected)?\s*static\s+(?!final)[\w<>, ]+\s+\w+\s*(=|;)", t):
            hit(ln, "RF-12", "static 가변 필드")
        if re.search(r'"https?://', t) and not t.startswith(("*", "//")):
            hit(ln, "RF-11", "하드코딩 URL")
    for v, lns in switch_vars.items():
        if len(lns) >= 2:
            hit(lns[0], "RF-06", f"같은 대상 switch({v}) {len(lns)}곳: 줄 {lns}")
    for c, lns in chains.items():
        if len(lns) >= 3:
            hit(lns[0], "RF-08", f"같은 getter 체인 {c} {len(lns)}곳")


# ---------------------------------------------------------------- 자바스크립트
JS_FN = re.compile(r"^\s*(?:async\s+)?(?:function\s+([\w$가-힣]+)\s*\(([^)]*)\)|(?:var|let|const)\s+([\w$가-힣]+)\s*=\s*(?:async\s+)?function\s*\(([^)]*)\))")


def scan_js(path, lines, hit, top_fns):
    n = len(lines)
    if n > 1500:
        hit(1, "JS-08", f"큰 파일 {n}줄")
    run_var, run_start, run_len = None, 0, 0
    for i, l in enumerate(lines):
        ln, t = i + 1, l.strip()
        m = JS_FN.match(l)
        if m and "{" in l:
            name = m.group(1) or m.group(3)
            params = [p for p in (m.group(2) or m.group(4) or "").split(",") if p.strip()]
            e = block_end(lines, i)
            if e > i and e - i + 1 > 60:
                hit(ln, "JS-03", f"긴 함수 {name}() {e - i + 1}줄")
            if len(params) >= 5:
                hit(ln, "JS-04", f"인수 {len(params)}개 {name}()")
            if l.startswith("function "):
                top_fns[name].append(f"{path}:{ln}")
        if re.search(r"console\.log\(", t) and not t.startswith("//"):
            hit(ln, "JS-01", "console.log")
        if re.match(r"//.*[;{}]\s*$", t) and not re.match(r"//\s*(TODO|ex|예)", t):
            hit(ln, "JS-01", "주석 처리된 코드")
        if re.search(r"catch\s*\(\s*\w*\s*\)\s*\{\s*\}", t):
            hit(ln, "JS-09", "빈 catch")
        if re.search(r"async\s*:\s*false", t):
            hit(ln, "JS-12", "동기 AJAX(async: false)")
        mt = re.search(r"setTimeout\([\s\S]*?,\s*(\d{3,})\s*\)", t)
        if mt and int(mt.group(1)) >= 1000:
            hit(ln, "JS-12", f"시간 대기 setTimeout {mt.group(1)}ms — 순서를 시간에 맡기는지 확인")
        elif re.search(r"\}\s*,\s*(\d{4,})\s*\)", t):
            hit(ln, "JS-12", "시간 대기 setTimeout — 순서를 시간에 맡기는지 확인")
        # HTML 태그가 든 문자열에 변수를 '+' 로 이어 붙이는데 이스케이프 흔적이 없음
        if re.search(r"[\"']\s*<\w|<\w[^\"']*[\"']", t) and re.search(r"\+\s*[A-Za-z_$][\w$]*(?:\.[\w$]+|\[[^\]]+\])*\s*\+", t) \
                and not re.search(r"(?i)esc|\.text\(|parseInt|toFixed|\bcolor\b|\bwidth\b|px", t) and not t.startswith("//"):
            hit(ln, "JS-10", "HTML 문자열에 값을 이어 붙임 — 바깥 값이면 이스케이프 필요")
        if re.search(r"[\"']/auth-(user|admin)/", t):
            hit(ln, "JS-11", "하드코딩 API 주소")
        if re.search(r"#(34d399|a4c6ff|fbbf24|f87171)\b", t, re.I):
            hit(ln, "JS-07", "상태 색상 직접 기재")
        ce = re.match(r"(?:\}\s*else\s+)?if\s*\(\s*([\w.$]+)\s*===?\s*['\"]", t)
        if ce:
            if t.startswith("}") and ce.group(1) == run_var:
                run_len += 1
            else:
                if run_len >= 4:
                    hit(run_start, "JS-06", f"{run_var} 값에 따른 if/else if {run_len}분기")
                run_var, run_start, run_len = ce.group(1), ln, 1
    if run_len >= 4:
        hit(run_start, "JS-06", f"{run_var} 값에 따른 if/else if {run_len}분기")


def similar_functions(lines, hit, cat):
    """같은 파일 안에서 30줄 이상 함수끼리, 짧은 줄(괄호 등)을 뺀 본문이 55% 이상 같으면 복사본 후보.
    (실측: 복사 후 고친 쌍 64%, 무관한 쌍 9%)"""
    import difflib
    pat = J_METHOD if cat == "RF-05" else JS_FN
    fns = []
    for i, l in enumerate(lines):
        m = pat.match(l)
        if m and "{" in l:
            e = block_end(lines, i)
            if e - i >= 30:
                name = next(g for g in m.groups() if g is not None)
                fns.append((i, e, name, [x.strip() for x in lines[i + 1:e] if len(x.strip()) > 4]))
    for a in range(len(fns)):
        for b in range(a + 1, len(fns)):
            x, y = fns[a], fns[b]
            if min(len(x[3]), len(y[3])) / max(len(x[3]), len(y[3])) < 0.6:
                continue
            sm = difflib.SequenceMatcher(None, x[3], y[3], autojunk=False)
            if sm.quick_ratio() >= 0.55 and sm.ratio() >= 0.55:
                hit(x[0] + 1, cat, f"{x[2]}() 와 {y[2]}()(줄 {y[0] + 1}) 본문 {int(sm.ratio() * 100)}% 같음 — 복사본 후보")


# ---------------------------------------------------------------- 실행
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", default=[])
    ap.add_argument("--diff", action="store_true", help="git 변경분에 걸친 후보만")
    ap.add_argument("--base", default=None, help="비교 기준 (기본: HEAD 대비 작업 트리)")
    ap.add_argument("--all", action="store_true", help="같은 유형도 줄이지 않고 후보를 전부 출력")
    a = ap.parse_args()

    if a.diff:
        changed = {}
        for repo in (a.targets or ["."]):
            changed.update(git_changed(repo, a.base))
        files = list(changed)
    else:
        if not a.targets:
            ap.error("대상 경로를 주거나 --diff 를 쓴다")
        files, changed = collect(a.targets), None

    found = collections.defaultdict(list)
    top_fns = collections.defaultdict(list)
    for f in files:
        if not os.path.isfile(f):
            continue
        lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
        allowed = None if changed is None else changed.get(f)

        def hit(ln, cat, msg, f=f, allowed=allowed):
            if allowed is None or ln in allowed or ln == 1:
                found[f].append((ln, cat, msg))

        (scan_java if f.endswith(JAVA) else lambda p, l, h: scan_js(p, l, h, top_fns))(f, lines, hit)
        similar_functions(lines, hit, "RF-05" if f.endswith(JAVA) else "JS-05")

    dup = {k: v for k, v in top_fns.items() if len(v) >= 2 and k not in ("execDocReady",)}
    total = sum(len(v) for v in found.values())
    print(f"# 리팩토링 후보 — 파일 {len(files)}개, 후보 {total}건 (후보일 뿐, 원문 확인 필수)\n")
    for f in sorted(found, key=lambda x: -len(found[x])):
        items = sorted(found[f])
        cats = collections.Counter(c for _, c, _ in items)
        print(f"## {f}  ({len(items)}건: " + ", ".join(f"{c} {n}" for c, n in cats.most_common()) + ")")
        shown = collections.Counter()
        for ln, cat, msg in items:
            shown[(cat, msg.split(" ")[0])] += 1
            if a.all or shown[(cat, msg.split(" ")[0])] <= 6:
                print(f"  {f}:{ln}  [{cat}] {msg}")
        more = 0 if a.all else sum(max(0, v - 6) for v in shown.values())
        if more:
            print(f"  … 같은 유형 {more}건 더")
        print()
    if dup:
        print("## 여러 파일에 같은 이름으로 선언된 전역 함수 (JS-05 · JS-13)")
        for k, v in sorted(dup.items(), key=lambda x: -len(x[1]))[:None if a.all else 15]:
            print(f"  {k}: {len(v)}곳 — " + ", ".join(v[:5]) + (" …" if len(v) > 5 else ""))


if __name__ == "__main__":
    sys.exit(main())
