#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REQ-MAPPING-FUNC-01 — Frontend-Web 호출 <-> Backend-Core 엔드포인트 미매핑 추출.

입력 2본을 게이트웨이 경로 규칙으로 대조해 '매핑되지 않는 것만' CSV 1본으로 출력한다.
표준 라이브러리만 사용. 읽기 전용(출력 CSV 1본만 씀).
"""
import csv, io, os, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tree_actions

ROOT    = os.environ.get("CATALOG_ROOT", os.getcwd())
_TASK   = os.environ.get("CATALOG_TASK", "tasks/api-catalog")
BE_CSV  = os.environ["CATALOG_BE_CSV"]          # backend  endpoints_flat.csv
FE_CSV  = os.environ["CATALOG_FE_CSV"]          # frontend api-calls_flat.csv
OUT_CSV = os.path.join(_TASK, "artifacts", "fe-be_mapping-gaps.csv")

# ── 게이트웨이 규칙 (sources/gateway-rules.md) ────────────────────────────────
AUTH_PREFIX = {"auth-anon": "/anonymous", "auth-user": "", "auth-manager": "/manager", "auth-admin": "/admin"}
TARGET_SERVICE = "api"                                    # Backend-Core
OTHER_SERVICE  = {"ai": "AI", "yml": "Global-Config", "search": "Engine-Fire", "hub": "Broker-Hub"}

OUT_HEADER = ["menuname", "direction", "provider", "backendurl", "frontendurl", "httpMethod",
              "jsfile", "line", "controllerClass", "판정", "note"]

# Middle-Proxy 가 같은 외부 경로를 자기 컨트롤러로 직접 처리하는 구간.
# 서비스 세그먼트가 api 여도 Backend-Core 가 아니므로 '미사용 호출' 로 오독되지 않게 사실을 남긴다.
MP_ROOT = os.environ.get("CATALOG_PROXY_REPO",
          os.path.join(ROOT, "Java-Service-Tree-Framework-Middle-Proxy")) + "/src/main/java"

def middle_proxy_bases():
    out = {}
    for dp, _, fn in os.walk(MP_ROOT):
        for f in fn:
            if not f.endswith(".java"):
                continue
            path = os.path.join(dp, f)
            src = io.open(path, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r'@RequestMapping\("(/auth-[^"]+)"\)', src):
                out[m.group(1)] = os.path.relpath(path, ROOT)
    return out

VAR_RE = re.compile(r"\{[^}]*\}")


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ── 경로 유틸 ────────────────────────────────────────────────────────────────
def segs(path):
    return [s for s in path.split("/") if s != ""]


def is_var(seg):
    """세그먼트가 변수 자리인가. '{x}' 뿐 아니라 'T_ARMS_REQADD_{id}' 같은 혼합도 변수로 본다."""
    return "{" in seg


def strip_query(url):
    url = url.split("#", 1)[0].split("?", 1)[0]
    if len(url) > 1 and url.endswith("/"):
        url = url.rstrip("/")
    return url


def norm_methods(m):
    """FE httpMethod 문자열 -> 비교용 메서드 집합. '{type}'=동적(전체 허용), HEAD=GET 으로 흡수."""
    m = (m or "").strip()
    if not m or VAR_RE.search(m):
        return {"GET", "POST", "PUT", "DELETE", "PATCH"}, True   # (집합, 동적여부)
    out = set()
    for part in m.split("|"):
        part = part.strip().upper()
        if part == "HEAD":
            part = "GET"
        if part:
            out.add(part)
    return out, False


# ── 1. 백엔드 전개 ───────────────────────────────────────────────────────────
def build_backend(be_rows):
    own      = [r for r in be_rows if r["kind"] == "own"]
    inherit  = [r for r in be_rows if r["kind"] == "inherited"]
    # 오버라이드 판정용: (컨트롤러, 자바메서드) -> own 존재
    own_sig = {(r["controllerClass"], r["javaMethod"]) for r in own}

    eps, overridden = [], []
    for r in own:
        eps.append({"path": r["path"], "method": r["httpMethod"].upper(), "basePath": r["basePath"],
                    "controllerClass": r["controllerClass"], "kind": "own", "javaMethod": r["javaMethod"]})
    expanded = 0
    for r in inherit:
        suffix = r["path"].replace("{basePath}", "", 1)
        for entry in r["inheritedBy"].split(";"):
            entry = entry.strip()
            if not entry:
                continue
            cls, _, base = entry.partition("@")
            expanded += 1
            if (cls, r["javaMethod"]) in own_sig:
                overridden.append(base + suffix)          # 하위 클래스가 재정의 -> 부모 매핑 소멸
                continue
            eps.append({"path": base + suffix, "method": r["httpMethod"].upper(), "basePath": base,
                        "controllerClass": cls, "kind": "inherited(%s)" % r["controllerClass"],
                        "javaMethod": r["javaMethod"]})
    # 동일 (method, path) 중복 제거
    seen, uniq = set(), []
    for e in eps:
        k = (e["method"], e["path"])
        if k in seen:
            continue
        seen.add(k)
        e["segs"] = segs(e["path"])
        uniq.append(e)
    return uniq, {"own": len(own), "inherited_rows": len(inherit), "expanded": expanded,
                  "overridden": len(overridden), "deduped": len(eps) - len(uniq), "effective": len(uniq)}


# ── 2. 프론트 정규화 ─────────────────────────────────────────────────────────
def normalize_front(url):
    """-> (상태, 내부경로|사유). 상태: 'ok' | 'skip'"""
    raw = (url or "").strip()
    if not raw:
        return "skip", "URL 비어 있음"
    if raw.startswith("UNRESOLVED:"):
        return "skip", "정적 해석 불가(런타임 변수)"
    u = strip_query(raw)
    if not u.startswith("/"):
        return "skip", "정적 리소스·상대경로(게이트웨이 경유 아님)"
    s = segs(u)
    if s and s[0] == "dwr":
        return "skip", "/dwr/** — 게이트웨이 무변환 전달, DWR 서블릿(엔드포인트 카탈로그 밖)"
    if not s or s[0] not in AUTH_PREFIX:
        return "skip", "게이트웨이 권한 프리픽스 없음(%s)" % (("/" + s[0]) if s else "/")
    if len(s) < 2:
        return "skip", "서비스 세그먼트 없음"
    svc = s[1]
    if svc != TARGET_SERVICE:
        return "skip", "대상 외 서비스: %s%s" % (svc, (" (%s)" % OTHER_SERVICE[svc]) if svc in OTHER_SERVICE else "")
    internal = AUTH_PREFIX[s[0]] + "/" + "/".join(s[2:]) if len(s) > 2 else AUTH_PREFIX[s[0]] + "/"
    return "ok", internal


# ── 3. 대조 ─────────────────────────────────────────────────────────────────
def seg_match(fs, bs):
    """세그먼트 단위 비교 -> None(불일치) | 'exact' | 'var' | 'fuzzy'"""
    if len(fs) != len(bs):
        return None
    grade = "exact"
    for a, b in zip(fs, bs):
        if a == b:
            continue
        av, bv = is_var(a), is_var(b)
        if av and bv:
            grade = "var" if grade == "exact" else grade          # {x} <-> {y}
        elif av or bv:
            lit = b if av else a
            if lit.endswith(".do"):
                return None                                        # .do 액션 자리는 변수로 안 봄
            grade = "fuzzy"                                        # T_ARMS_X_{id} <-> {changeReqTableName} 등
        else:
            return None
    return grade


def find_match(fseg, fmethods, backend):
    """반환: (best_endpoint, grade, method_ok). 경로는 맞는데 메서드만 다른 건도 잡아서 돌려준다."""
    order = {"exact": 0, "var": 1, "fuzzy": 2}
    best = None
    for e in backend:
        g = seg_match(fseg, e["segs"])
        if g is None:
            continue
        mok = e["method"] in fmethods
        cand = (0 if mok else 1, order[g], e)
        if best is None or cand[:2] < best[:2]:
            best = cand
    if best is None:
        return None, None, False
    return best[2], {v: k for k, v in order.items()}[best[1]], best[0] == 0


def mp_note(url, bases):
    """프론트 URL 이 Middle-Proxy 컨트롤러 담당 구간이면 그 사실 한 줄."""
    u = url.split("?")[0]
    best = max((b for b in bases if u == b or u.startswith(b + "/")), key=len, default=None)
    if not best:
        return []
    return ["같은 외부 경로를 Middle-Proxy 가 직접 처리: %s (%s) — Backend-Core 미존재는 맞으나 미사용 호출은 아님"
            % (best, bases[best])]


def main():
    be_rows, fe_rows = read_csv(BE_CSV), read_csv(FE_CSV)
    mp_bases = middle_proxy_bases()
    # 프론트가 Tree CRUD 를 부르는 호출도 '상속' 으로 표기한다(자체 도메인 API 와 구분).
    tree_acts = tree_actions.load(BE_CSV)
    fe_provider = lambda u: ('상속(%s)' % tree_actions.match(u, tree_acts)) \
        if tree_actions.match(u, tree_acts) else '프론트 호출' 
    backend, be_stats = build_backend(be_rows)
    base_paths = sorted({e["basePath"] for e in backend if e["basePath"]}, key=len, reverse=True)

    out, stat = [], Counter()
    matched_be = set()
    menu_by_base = defaultdict(Counter)

    def owning_base(path):
        """내부경로를 감싸는 가장 긴 백엔드 basePath (없으면 None)."""
        for bp in base_paths:
            if path == bp or path.startswith(bp + "/"):
                return bp
        return None

    fe_norm = []
    for r in fe_rows:
        state, val = normalize_front(r["apiurl"])
        fe_norm.append((r, state, val))
        if state == "ok":
            bp = owning_base(val)
            if bp:
                menu_by_base[bp][r["menuname"]] += 1

    # 3-1. FE -> BE
    for r, state, val in fe_norm:
        if state != "ok":
            stat["FE_대상외"] += 1
            continue
        stat["FE_대조대상"] += 1
        fmethods, dynamic = norm_methods(r["httpMethod"])
        ep, grade, mok = find_match(segs(val), fmethods, backend)
        if ep is not None and mok:
            matched_be.add((ep["method"], ep["path"]))
            stat["FE_매핑성립_" + grade] += 1
            continue
        if ep is not None and not mok:
            stat["FE_메서드불일치"] += 1
            notes = ["경로는 일치(%s), HTTP 메서드만 다름 — 백엔드 %s / 프론트 %s"
                     % (grade, ep["method"], r["httpMethod"])]
            if r["note"]:
                notes.append("추출메모: " + r["note"])
            out.append({"menuname": r["menuname"], "direction": "FE→BE없음", "backendurl": ep["path"],
                        "frontendurl": r["apiurl"], "httpMethod": r["httpMethod"], "jsfile": r["jsfile"],
                        "line": r["line"], "controllerClass": ep["controllerClass"],
                        "판정": "메서드 불일치", "provider": fe_provider(r["apiurl"]),
                        "note": " / ".join(notes + mp_note(r["apiurl"], mp_bases))})
            continue
        stat["FE_백엔드없음"] += 1
        bp = owning_base(val)
        notes = ["게이트웨이 변환 결과 내부경로 %s 에 대응하는 Backend-Core 매핑 없음" % val,
                 ("basePath %s 는 존재 — 그 하위 경로만 미존재" % bp) if bp else "대응 basePath 자체가 카탈로그에 없음"]
        if dynamic:
            notes.append("httpMethod 가 런타임 변수 — 전체 메서드로 대조")
        if "?" in r["apiurl"]:
            notes.append("쿼리스트링 제거 후 대조")
        if any(is_var(s) for s in segs(val)):
            notes.append("변수 세그먼트 포함 — 세그먼트 수·자리 기준 비교")
        if r["note"]:
            notes.append("추출메모: " + r["note"])
        out.append({"menuname": r["menuname"], "direction": "FE→BE없음", "backendurl": "(없음)",
                    "frontendurl": r["apiurl"], "httpMethod": r["httpMethod"], "jsfile": r["jsfile"],
                    "line": r["line"], "controllerClass": "", "판정": "백엔드 미존재",
                    "provider": fe_provider(r["apiurl"]),
                    "note": " / ".join(notes + mp_note(r["apiurl"], mp_bases))})

    # 3-2. BE -> FE
    for e in backend:
        if (e["method"], e["path"]) in matched_be:
            stat["BE_호출됨"] += 1
            continue
        stat["BE_호출없음"] += 1
        # TreeAbstractController·TreeMapAbstractController 상속분은 TreeFramework 가
        # 공통 제공하는 트리 CRUD 다. 목록에는 남기되 provider 에 '상속' 으로 표기한다.
        if e["kind"].startswith("inherited"):
            stat["BE_상속분"] += 1
        menus = menu_by_base.get(e["basePath"])
        if menus:
            # 추정하지 않는다 — 같은 basePath 를 실제로 호출하는 메뉴를 호출 건수 순으로 전부 적는다.
            names = [m for m, _ in menus.most_common()]
            menuname = ";".join(names)
            menu_note = "같은 basePath(%s) 를 호출하는 프론트 메뉴 %d개 (호출 건수 순)" % (e["basePath"], len(names))
        else:
            menuname = "(호출 메뉴 없음) " + (e["basePath"] or e["controllerClass"])
            menu_note = "해당 basePath 를 부르는 프론트 호출이 한 건도 없음"
        notes = ["Frontend-Web 에서 호출하는 곳 없음", menu_note]
        if e["kind"].startswith("inherited"):
            notes.append("상속 전개 엔드포인트(%s)" % e["kind"])
        if any(is_var(s) for s in e["segs"]):
            notes.append("경로 변수 포함")
        out.append({"menuname": menuname, "direction": "BE→호출없음",
                    "provider": ("상속(%s)" % e["kind"][10:-1]) if e["kind"].startswith("inherited") else "자체 선언",
                    "backendurl": e["path"],
                    "frontendurl": "(호출 없음)", "httpMethod": e["method"], "jsfile": "", "line": "",
                    "controllerClass": e["controllerClass"], "판정": "프론트 호출 없음",
                    "note": " / ".join(notes)})

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_HEADER)
        w.writeheader()
        for row in sorted(out, key=lambda x: (x["direction"], x["menuname"], x["backendurl"], x["frontendurl"])):
            w.writerow(row)

    print("backend  :", dict(be_stats))
    print("frontend : rows=%d" % len(fe_rows))
    for k in sorted(stat):
        print("   %-22s %d" % (k, stat[k]))
    print("output   : %d rows -> %s" % (len(out), OUT_CSV))


if __name__ == "__main__":
    sys.exit(main())
