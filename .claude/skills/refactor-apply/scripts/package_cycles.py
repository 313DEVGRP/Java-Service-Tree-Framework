#!/usr/bin/env python3
"""자바 소스의 패키지 import 그래프에서 순환(서로 import 하는 패키지 묶음)을 찾는다.

사용:
  python3 package_cycles.py <src/main/java> <패키지 접두어> [--class <클래스 FQN>]
  예) python3 package_cycles.py src/main/java com.arms.api.issue.almapi
      python3 package_cycles.py src/main/java com.arms.api.issue --class com.arms.api.issue.almapi.model.vo.IssueRecentId

- 접두어 아래 패키지끼리의 import 만 본다(같은 패키지 안 import·외부 라이브러리 제외).
- 와일드카드 import(a.b.*)는 패키지 a.b 의존으로 센다. static import 는 클래스의 패키지로 센다.
- --class 를 주면 그 클래스가 import 하는 패키지와, 그 클래스를 import 하는 패키지를 함께 보여 주고,
  그 클래스를 model/ 바로 아래로 옮겼을 때 순환이 생기는지(그 클래스가 같은 도메인 패키지를 import 하는지) 알려 준다.
- 순환이 있으면 종료 코드 1.
"""
import argparse
import os
import re
import sys
from collections import defaultdict

PKG = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)
IMP = re.compile(r"^\s*import\s+(static\s+)?([\w.]+)(\.\*)?\s*;", re.M)


def owner_package(name, is_static, wildcard, known):
    parts = name.split(".")
    if wildcard and not is_static:
        return name
    # 클래스(또는 static 멤버)를 떼고 실제 패키지를 찾는다
    for cut in range(len(parts) - 1, 0, -1):
        cand = ".".join(parts[:cut])
        if cand in known:
            return cand
    return ".".join(parts[:-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("prefix")
    ap.add_argument("--class", dest="cls")
    a = ap.parse_args()

    files = {}
    for root, _, names in os.walk(a.src):
        for n in names:
            if n.endswith(".java"):
                p = os.path.join(root, n)
                with open(p, encoding="utf-8", errors="ignore") as f:
                    files[p] = f.read()
    pkg_of = {}
    for p, text in files.items():
        m = PKG.search(text)
        if m:
            pkg_of[p] = m.group(1)
    known = set(pkg_of.values())

    edges = defaultdict(lambda: defaultdict(list))  # from_pkg -> to_pkg -> [파일]
    class_imports, imported_by = set(), set()
    for p, text in files.items():
        src_pkg = pkg_of.get(p)
        if not src_pkg or not src_pkg.startswith(a.prefix):
            continue
        fqcn = src_pkg + "." + os.path.basename(p)[:-5]
        for st, name, wc in IMP.findall(text):
            dst = owner_package(name, bool(st), bool(wc), known)
            if not dst.startswith(a.prefix) or dst == src_pkg:
                continue
            edges[src_pkg][dst].append(os.path.relpath(p, a.src))
            if a.cls and fqcn == a.cls:
                class_imports.add(dst)
            if a.cls and (name == a.cls or (wc and a.cls.rsplit(".", 1)[0] == name)):
                imported_by.add(src_pkg)

    # Tarjan SCC
    index, low, stack, on, sccs, counter = {}, {}, [], set(), [], [0]
    def visit(v):
        index[v] = low[v] = counter[0]; counter[0] += 1
        stack.append(v); on.add(v)
        for w in edges.get(v, {}):
            if w not in index:
                visit(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                sccs.append(sorted(comp))
    sys.setrecursionlimit(10000)
    for v in list(edges):
        if v not in index:
            visit(v)

    if a.cls:
        print(f"## {a.cls}")
        print("- 이 클래스가 import 하는 접두어 아래 패키지: " + (", ".join(sorted(class_imports)) or "없음"))
        print("- 이 클래스를 import 하는 패키지: " + (", ".join(sorted(imported_by)) or "없음"))
        if class_imports:
            print("- 판정: 이 클래스가 같은 도메인 패키지를 import 하므로 model/ 로 옮겨도 순환이 남을 수 있다. 먼저 그 의존(엔티티→값 변환 등)을 상대 쪽으로 옮길 것")
        else:
            print("- 판정: 자바 표준·외부 라이브러리만 의존 — model/ 바로 아래로 옮겨도 순환이 생기지 않는다")
        print()

    if not sccs:
        print(f"순환 없음 ({a.prefix} 아래 패키지 {len(edges)}개)")
        return
    print(f"순환 {len(sccs)}묶음")
    for comp in sccs:
        print("- " + " ↔ ".join(comp))
        for x in comp:
            for y in comp:
                if y in edges.get(x, {}):
                    ex = edges[x][y]
                    print(f"    {x} → {y}  ({len(ex)}파일, 예: {ex[0]})")
    sys.exit(1)


if __name__ == "__main__":
    main()
