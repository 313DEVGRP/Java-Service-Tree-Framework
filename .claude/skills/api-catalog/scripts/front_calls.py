# -*- coding: utf-8 -*-
"""
Frontend-Web (arms/js · backoffice/js) REST API 호출 전수 추출 → 플랫 CSV.

표준 라이브러리만 사용. 대상 저장소는 읽기만 한다.
출력 : tasks/req-frontend-func-01/artifacts/frontend-web_api-calls_flat.csv

추출 대상
  1) 호출 프리미티브 : $.ajax · $.get · $.post · $.getJSON · fetch
  2) 플러그인/래퍼 config 의 url 지점 : key 경로에 ajax 가 있거나
     enclosing callee 가 fileupload/select2/ajaxPromise/fetchCached 인 것
URL 복원
  문자열 연결 · 템플릿 리터럴 · 파일 내 단일대입 식별자 · UrlBuilder 체인 ·
  삼항 분기 전개 · 공통 빌더(dataTable_build·jsTreeBuild 등) 호출부 인자 대입
"""
import io, os, re, csv, sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tree_actions

ROOT = os.environ.get("CATALOG_FRONT_REPO", "Java-Service-Tree-Framework-Frontend-Web")
_TASK = os.environ.get("CATALOG_TASK", "tasks/api-catalog")
OUT  = os.path.join(_TASK, "artifacts", "frontend-web_api-calls_flat.csv")
AREAS = ["arms/js", "backoffice/js"]
NAV = {"arms": "arms/html/template/page-navigation.html",
       "backoffice": "backoffice/html/template/page-sidebar.html"}

# ═══════════════════════════════════════════════════════════════════
# 1. JS 소스 마스킹 (문자열 · 주석 · 정규식리터럴 · 템플릿리터럴)
# ═══════════════════════════════════════════════════════════════════
CODE, STR, CMT = 0, 1, 2

def mask(src):
    n = len(src); m = [CODE] * n; i = 0; tstack = []
    while i < n:
        c = src[i]
        if tstack and c == '}' and tstack[-1] == 0:
            tstack.pop(); m[i] = STR; i += 1
            i = _tbody(src, i, m, tstack); continue
        if tstack:
            if c == '{': tstack[-1] += 1
            elif c == '}': tstack[-1] -= 1
        if c == '/' and i + 1 < n and src[i+1] == '/':
            j = src.find('\n', i); j = n if j < 0 else j
            for k in range(i, j): m[k] = CMT
            i = j; continue
        if c == '/' and i + 1 < n and src[i+1] == '*':
            j = src.find('*/', i + 2); j = n if j < 0 else j + 2
            for k in range(i, j): m[k] = CMT
            i = j; continue
        if c == '/':
            # 정규식 리터럴 : 직전 유효 코드 문자가 "값의 끝" 이 아니면 정규식
            k = i - 1
            while k >= 0 and (m[k] == CMT or src[k] in ' \t\r\n'): k -= 1
            prev = src[k] if k >= 0 else ''
            if not (prev.isalnum() or prev in '_$)]'):
                j = i + 1; incls = False
                while j < n:
                    ch = src[j]
                    if ch == '\\': j += 2; continue
                    if ch == '\n': break
                    if incls:
                        if ch == ']': incls = False
                    elif ch == '[': incls = True
                    elif ch == '/': break
                    j += 1
                if j < n and src[j] == '/':
                    j += 1
                    while j < n and src[j].isalpha(): j += 1
                    for kk in range(i, j): m[kk] = STR
                    i = j; continue
            i += 1; continue
        if c in '"\'':
            q = c; m[i] = STR; i += 1
            while i < n:
                m[i] = STR
                if src[i] == '\\':
                    if i + 1 < n: m[i+1] = STR
                    i += 2; continue
                if src[i] == q: i += 1; break
                if src[i] == '\n': break
                i += 1
            continue
        if c == '`':
            m[i] = STR; i += 1
            i = _tbody(src, i, m, tstack); continue
        i += 1
    return m

def _tbody(src, i, m, tstack):
    n = len(src)
    while i < n:
        if src[i] == '\\':
            m[i] = STR
            if i + 1 < n: m[i+1] = STR
            i += 2; continue
        if src[i] == '`': m[i] = STR; return i + 1
        if src[i] == '$' and i + 1 < n and src[i+1] == '{':
            m[i] = m[i+1] = STR; tstack.append(0); return i + 2
        m[i] = STR; i += 1
    return i

OPENB = {'(': ')', '[': ']', '{': '}'}
CLOSEB = set(')]}')

def match_bracket(src, m, i):
    depth = 0; n = len(src)
    while i < n:
        if m[i] == CODE:
            c = src[i]
            if c in OPENB: depth += 1
            elif c in CLOSEB:
                depth -= 1
                if depth == 0: return i
        i += 1
    return -1

def split_top(src, m, lo, hi, sep):
    out, depth, start, i = [], 0, lo, lo
    while i < hi:
        if m[i] == CODE:
            c = src[i]
            if c in OPENB: depth += 1
            elif c in CLOSEB: depth -= 1
            elif depth == 0 and src.startswith(sep, i):
                out.append((start, i)); i += len(sep) - 1; start = i + 1
        i += 1
    out.append((start, hi))
    return out

def code_text(src, m, lo, hi):
    return ''.join(src[k] if m[k] != CMT else ' ' for k in range(lo, hi)).strip()

def line_of(src, idx):
    return src.count('\n', 0, idx) + 1

# ═══════════════════════════════════════════════════════════════════
# 2. 표현식 → URL 패턴
# ═══════════════════════════════════════════════════════════════════
IDENT  = re.compile(r'^[A-Za-z_$][A-Za-z0-9_$]*$')
JQVAL  = re.compile(r'^\$\(\s*["\']#([A-Za-z0-9_\-]+)["\']\s*\)\s*\.\w+\(\s*\)$')
UNWRAP = re.compile(r'^(?:encodeURIComponent|encodeURI|String|Number|parseInt|trim)\s*\((.*)\)$', re.S)
ONEARG = re.compile(r'^[\w$.]+\(\s*["\']([A-Za-z0-9_\-]+)["\']\s*\)$')   # getCookie("locale") / .attr("id")
DOTTED = re.compile(r'^[A-Za-z_$][\w$]*(?:\s*\[[^\]]*\]|\s*\.\s*[A-Za-z_$][\w$]*|\s*\(\s*\))*$')

def param_name(expr):
    e = re.sub(r'\s+', ' ', expr).strip()
    for _ in range(4):
        mo = UNWRAP.match(e)
        if not mo: break
        e = mo.group(1).strip()
    mo = JQVAL.match(e)
    if mo: return mo.group(1)
    mo = ONEARG.match(e)
    if mo: return mo.group(1)
    if IDENT.match(e): return e
    if DOTTED.match(e):
        segs = re.findall(r'[A-Za-z_$][\w$]*', re.sub(r'\[[^\]]*\]', '', e))
        if segs: return segs[-1]
    mo = re.match(r'^([A-Za-z_$][\w$]*)\s*\(', e)
    if mo: return mo.group(1)
    return 'param'

def unquote(tok):
    q, body = tok[0], tok[1:-1]
    return body.replace('\\' + q, q).replace('\\\\', '\\')

class FileCtx:
    """파일 단위 : 식별자 → 대입 구간. 단일 대입만 신뢰한다."""
    def __init__(self, rel, src, m):
        self.rel, self.src, self.m = rel, src, m
        self.assigns = {}
        for mo in re.finditer(r'(?:(?:var|let|const)\s+)?([A-Za-z_$][\w$]*)\s*=(?!=|>)', src):
            if m[mo.start(1)] != CODE: continue
            lo = mo.end(); depth, j, n = 0, lo, len(src)
            while j < n:
                if m[j] == CODE:
                    c = src[j]
                    if c in OPENB: depth += 1
                    elif c in CLOSEB:
                        if depth == 0: break
                        depth -= 1
                    elif depth == 0 and c in ';,': break
                    elif depth == 0 and c == '\n':
                        tail = code_text(src, m, lo, j)
                        nxt = re.match(r'\s*([.)\]}])', src[j:])
                        if tail and not re.search(r'[+\-*/?:&|(,\[{=.]$', tail) \
                           and not (nxt and nxt.group(1) == '.'): break
                j += 1
            self.assigns.setdefault(mo.group(1), []).append((mo.start(1), lo, j))
        # 함수 파라미터 기본값( function f(locale = "ko") )은 대입이 아니다
        pspans = []
        for mo in re.finditer(r'(?:function\s*[A-Za-z_$][\w$]*\s*\(|function\s*\(|=>\s*\()', src):
            if m[mo.start()] != CODE: continue
            q = src.rfind('(', mo.start(), mo.end())
            e = match_bracket(src, m, q)
            if e > q: pspans.append((q, e))
        if pspans:
            for k in list(self.assigns):
                v = [a for a in self.assigns[k] if not any(x < a[0] < y for x, y in pspans)]
                if v: self.assigns[k] = v
                else: del self.assigns[k]

    def nearest(self, name, before):
        """pos 앞쪽 대입을 가까운 순서로."""
        return sorted([a for a in self.assigns.get(name, []) if a[0] < before],
                      key=lambda a: -a[0])

    def single(self, name, before):
        """이름이 파일 내에서 단 한 번만 대입될 때만 그 구간을 돌려준다."""
        a = self.assigns.get(name)
        if not a or len(a) != 1: return None
        return a[0] if a[0][0] < before else None

def tpl_pattern(src, m, lo, hi):
    out, i = [], lo + 1
    while i < hi - 1:
        if src[i] == '\\': out.append(src[i+1]); i += 2; continue
        if src[i] == '$' and i + 1 < hi and src[i+1] == '{':
            depth, j = 0, i + 2
            while j < hi:
                c = src[j]
                if m[j] == CODE:
                    if c == '{': depth += 1
                    elif c == '}': depth -= 1
                elif c == '}' and depth == 0: break
                j += 1
            out.append('{' + param_name(code_text(src, m, i + 2, j)) + '}')
            i = j + 1; continue
        out.append(src[i]); i += 1
    return ''.join(out)

MAXALT = 8   # 한 호출 지점이 만들 수 있는 최대 분기 수

class Unres(Exception):
    def __init__(self, reason): self.reason = reason

def resolve(src, m, lo, hi, ctx, depth=0, seen=frozenset(), top=True):
    """표현식 → URL 패턴 목록. 복원 불가 시 Unres."""
    if depth > 8: raise Unres('재귀 한도')
    txt = code_text(src, m, lo, hi)
    if not txt: raise Unres('빈 표현식')
    parts = split_top(src, m, lo, hi, '+')
    if len(parts) == 1: return _atom(src, m, lo, hi, ctx, depth, seen, top)
    acc = ['']
    for a, b in parts:
        try: pats = _atom(src, m, a, b, ctx, depth, seen, False)
        except Unres: pats = ['{' + param_name(code_text(src, m, a, b)) + '}']
        acc = [x + y for x in acc for y in pats]
        if len(acc) > MAXALT: raise Unres('분기 과다')
    return acc

def _atom(src, m, lo, hi, ctx, depth, seen, top=True):
    while lo < hi and src[lo].isspace(): lo += 1
    while hi > lo and src[hi-1].isspace(): hi -= 1
    txt = code_text(src, m, lo, hi)
    if not txt: raise Unres('빈 표현식')
    # 문자열 리터럴
    if txt[0] in '"\'' and txt[-1] == txt[0] and len(txt) >= 2: return [unquote(txt)]
    # 템플릿 리터럴
    if txt[0] == '`' and txt[-1] == '`':
        i = lo
        while src[i] != '`': i += 1
        j = hi - 1
        while src[j] != '`': j -= 1
        return [tpl_pattern(src, m, i, j + 1)]
    # 괄호 : 삼항이면 분기 전개
    if txt.startswith('(') and txt.endswith(')'):
        i = lo
        while m[i] != CODE or src[i] != '(': i += 1
        j = match_bracket(src, m, i)
        if j == hi - 1 or code_text(src, m, j + 1, hi) == '':
            q = split_top(src, m, i + 1, j, '?')
            if len(q) == 2:
                alts = split_top(src, m, q[1][0], q[1][1], ':')
                if len(alts) == 2:
                    out = []
                    for a, b in alts: out += resolve(src, m, a, b, ctx, depth + 1, seen)
                    return out
            return resolve(src, m, i + 1, j, ctx, depth + 1, seen)
    # UrlBuilder 체인 :  <v>.build()  또는  new UrlBuilder()...build()
    mo = re.match(r'^([A-Za-z_$][\w$]*)\s*\.\s*build\(\s*\)$', txt)
    if mo:
        for a in ctx.nearest(mo.group(1), lo):
            try: return _urlbuilder(src, m, a[1], a[2], ctx, depth, seen)
            except Unres: continue
        raise Unres('UrlBuilder 변수 추적 실패:' + mo.group(1))
    if 'new UrlBuilder' in txt and txt.endswith('build()'):
        return _urlbuilder(src, m, lo, hi, ctx, depth, seen)
    # A || B  →  A 우선
    ors = split_top(src, m, lo, hi, '||')
    if len(ors) > 1:
        a, b = ors[0]
        try: return _atom(src, m, a, b, ctx, depth + 1, seen, top)
        except Unres: return ['{' + param_name(code_text(src, m, a, b)) + '}']
    # url: function (params) { return <expr>; }  (select2 등)
    if re.match(r'^(?:function\s*\(|\([^)]*\)\s*=>)', txt):
        k = lo
        while k < hi and not (m[k] == CODE and src[k] == '{'): k += 1
        if k < hi:
            e = match_bracket(src, m, k)
            body = code_text(src, m, k + 1, e)
            if body.count('return') == 1:
                r0 = src.index('return', k)
                r1 = r0 + 6
                d2, j2 = 0, r1
                while j2 < e:
                    if m[j2] == CODE:
                        c = src[j2]
                        if c in OPENB: d2 += 1
                        elif c in CLOSEB: d2 -= 1
                        elif d2 == 0 and c == ';': break
                    j2 += 1
                return resolve(src, m, r1, j2, ctx, depth + 1, seen)
        raise Unres('함수형 url — return 문 단일 추출 실패')
    # 식별자
    if IDENT.match(txt) and txt not in seen:
        if top:
            # url 전체가 식별자 : 앞쪽 대입을 가까운 순으로 시도 (경로처럼 보이는 것 채택)
            for a in ctx.nearest(txt, lo):
                try: got = resolve(src, m, a[1], a[2], ctx, depth + 1, seen | {txt})
                except Unres: continue
                if any('/' in g for g in got): return got
        else:
            # 연결 피연산자 : 감싼 블록 안의 대입들을 모두 분기로 전개
            #  - 빈 문자열 / 공백 포함(가드문구) 값은 버린다
            lo2 = lo
            for _ in range(6):
                b0, b1 = enclosing_func_span(src, m, max(0, lo2 - 1))
                cand = [a for a in ctx.nearest(txt, lo) if b0 <= a[0] <= b1]
                if cand:
                    vals = []
                    for a in cand:
                        try: got = resolve(src, m, a[1], a[2], ctx, depth + 1, seen | {txt})
                        except Unres: continue
                        for g in got:
                            if g.strip() and not re.search(r'\s', g) and g not in vals:
                                vals.append(g)
                    if vals:
                        if len(vals) <= 4: return vals
                        break
                lo2 = b0
                if lo2 <= 0: break
        a = ctx.single(txt, lo)
        if a: return resolve(src, m, a[1], a[2], ctx, depth + 1, seen | {txt})
        raise Unres('식별자 미해결:' + txt)
    raise Unres('표현식 미해결:' + re.sub(r'\s+', ' ', txt)[:60])

def _urlbuilder(src, m, lo, hi, ctx, depth, seen):
    chain = code_text(src, m, lo, hi)
    mo = re.search(r'setBaseUrl\s*\(', chain)
    if not mo: raise Unres('setBaseUrl 없음')
    p = lo + chain.index('setBaseUrl') + mo.end() - mo.start() - 1
    while m[p] != CODE or src[p] != '(': p += 1
    q = match_bracket(src, m, p)
    return resolve(src, m, p + 1, q, ctx, depth + 1, seen)

def query_keys(src, m, lo, hi, varname):
    """addQueryParam('k', ...) 키 목록 (note 용)."""
    body = src[lo:hi]
    return re.findall(r'addQueryParam\(\s*["\']([^"\']+)["\']', body)


# ── 같은 파일 안 함수 파라미터 → 호출부 인자로 전개 ────────────────────────
FUNCDEF = re.compile(r'(?:function\s+([A-Za-z_$][\w$]*)\s*\(|'
                     r'(?:var|let|const)?\s*([A-Za-z_$][\w$]*)\s*[:=]\s*function\s*\(|'
                     r'(?:var|let|const)?\s*([A-Za-z_$][\w$]*)\s*[:=]\s*\()')

def func_defs(src, m):
    """[(name, [params], def_pos, body_lo, body_hi)]"""
    out = []
    for mo in FUNCDEF.finditer(src):
        if m[mo.start()] != CODE: continue
        name = mo.group(1) or mo.group(2) or mo.group(3)
        if not name: continue
        p = mo.end() - 1
        if src[p] != '(': continue
        q = match_bracket(src, m, p)
        if q < 0: continue
        params = [re.sub(r'=.*$', '', x).strip() for x in code_text(src, m, p + 1, q).split(',')]
        params = [x for x in params if IDENT.match(x)]
        k = q + 1
        while k < len(src) and src[k] in ' \t\r\n=>': k += 1
        if k >= len(src) or src[k] != '{': continue
        e = match_bracket(src, m, k)
        if e < 0: continue
        out.append((name, params, mo.start(), k, e))
    return out

def expand_params(rel, pos, urls, S):
    """URL 의 {X} 가 감싼 함수의 파라미터면 같은 파일 호출부 인자로 치환."""
    src, m, ctx = S[rel]
    defs = [d for d in func_defs(src, m) if d[3] <= pos <= d[4]]
    if not defs: return urls
    name, params, dpos, blo, bhi = min(defs, key=lambda d: d[4] - d[3])
    need = [ph for ph in set(re.findall(r'\{([^}]+)\}', ' '.join(urls))) if ph in params]
    if not need: return urls
    out = urls
    for ph in need:
        idx = params.index(ph)
        vals, partial = [], False
        for mo in re.finditer(r'(?<![\w$.])%s\s*\(' % re.escape(name), src):
            if m[mo.start()] != CODE: continue
            if blo <= mo.start() <= bhi or mo.start() == dpos: continue
            if re.search(r'function\s+$', src[max(0, mo.start() - 12):mo.start()]): continue
            p = src.index('(', mo.end() - 1); q = match_bracket(src, m, p)
            if q < 0: continue
            args = split_top(src, m, p + 1, q, ',')
            if idx >= len(args): continue
            atxt = code_text(src, m, args[idx][0], args[idx][1])
            if IDENT.match(atxt):                 # 인자가 맨 식별자면 추적하지 않는다(과잉 구체화 방지)
                partial = True; continue
            try: got = resolve(src, m, args[idx][0], args[idx][1], ctx, top=False)
            except Unres: continue
            for g in got:
                if g.strip() and not re.search(r'\s', g) and g not in vals: vals.append(g)
        if not vals or len(vals) > 6: continue
        if partial: vals = vals + ['{' + ph + '}']     # 리터럴이 아닌 호출부가 있으면 일반형도 남긴다
        out = [u.replace('{' + ph + '}', v) for u in out for v in vals]
    return list(dict.fromkeys(out))

# ═══════════════════════════════════════════════════════════════════
# 3. 호출 지점 스캔
# ═══════════════════════════════════════════════════════════════════
PRIMS = ('ajax', 'get', 'post', 'getJSON')

def find_primitives(src, m):
    out = []
    for mo in re.finditer(r'\$\.(ajax|get|post|getJSON)\s*\(', src):
        if m[mo.start()] != CODE: continue
        p = src.index('(', mo.end() - 1); q = match_bracket(src, m, p)
        if q > 0: out.append(('$.' + mo.group(1), p + 1, q, mo.start()))
    for mo in re.finditer(r'(?<![\w.$])fetch\s*\(', src):
        if m[mo.start()] != CODE: continue
        p = src.index('(', mo.end() - 1); q = match_bracket(src, m, p)
        if q > 0: out.append(('fetch', p + 1, q, mo.start()))
    return out

def obj_key(src, m, lo, hi, keys):
    """객체 리터럴 [lo,hi] 의 최상위 key 값 구간 (lo 는 '{')."""
    for a, b in split_top(src, m, lo + 1, hi, ','):
        seg = code_text(src, m, a, b)
        if not seg: continue
        mo = re.match(r'^["\']?([A-Za-z_$][\w$]*)["\']?\s*:', seg)
        if not mo:
            if seg.rstrip(',') in keys:      # shorthand  { url, ... }
                return (seg.rstrip(','), None, None)
            continue
        if mo.group(1) in keys:
            k = a
            while k < b and not (m[k] == CODE and src[k] == ':'): k += 1
            return (mo.group(1), k + 1, b)
    return None

def http_method(src, m, obj_lo, obj_hi, default, ctx=None):
    r = obj_key(src, m, obj_lo, obj_hi, ('type', 'method'))
    if not r or r[1] is None: return default
    lo, hi = r[1], r[2]
    t = code_text(src, m, lo, hi).strip().rstrip(',')
    mo = re.match(r'^["\'](\w+)["\']$', t)
    if mo: return mo.group(1).upper()
    # 삼항 : "PUT" : "POST"
    q = split_top(src, m, lo, hi, '?')
    if len(q) == 2:
        alts = split_top(src, m, q[1][0], q[1][1], ':')
        if len(alts) == 2:
            vals = [re.match(r'^["\'](\w+)["\']$', code_text(src, m, a, b).rstrip(','))
                    for a, b in alts]
            if all(vals): return '|'.join(dict.fromkeys(v.group(1).upper() for v in vals))
    # 식별자 : 감싼 함수 안의 문자열 대입을 모두 모은다
    if ctx and IDENT.match(t):
        lo2, hi2 = lo, lo
        for _ in range(6):
            lo2, hi2 = enclosing_func_span(src, m, max(0, lo2 - 1))
            vals = []
            for ap, alo, ahi in ctx.assigns.get(t, []):
                if not (lo2 <= ap <= hi2) or ap > lo: continue
                v = re.match(r'^["\'](\w+)["\']$', code_text(src, m, alo, ahi).rstrip(','))
                if v: vals.append(v.group(1).upper())
            if vals: return '|'.join(dict.fromkeys(vals))
            if lo2 <= 0: break
    return '{' + param_name(t) + '}'

def enclosing(src, m, pos):
    """url: 지점의 key 경로 + 바깥 호출 이름."""
    path, i, depth = [], pos, 0
    while i >= 0:
        if m[i] == CODE:
            c = src[i]
            if c in CLOSEB: depth += 1
            elif c in OPENB:
                if depth > 0: depth -= 1
                else:
                    if c == '{':
                        head = code_text(src, m, max(0, i - 80), i)
                        mo = re.search(r'([A-Za-z_$][\w$.]*)\s*[:=]\s*$', head)
                        if mo: path.append(mo.group(1).split('.')[-1])
                    elif c == '(':
                        head = code_text(src, m, max(0, i - 80), i)
                        mo = re.search(r'([A-Za-z_$][\w$.\]\)]*)\s*$', head)
                        return ('.'.join(reversed(path)), mo.group(1) if mo else '')
        i -= 1
    return ('.'.join(reversed(path)), '')

CONFIG_CALLEES = ('fileupload', 'select2', 'ajaxPromise', 'fetchCached', 'jstree', 'DataTable', 'dataTable')

def find_config_urls(src, m, prim_spans):
    """프리미티브 바깥의 플러그인/래퍼 ajax config url 지점."""
    out = []
    for mo in re.finditer(r'(?m)^\s*url\s*:', src):
        if m[mo.start()] != CODE: continue
        p = mo.start()
        if any(a <= p <= b for a, b in prim_spans): continue
        keypath, callee = enclosing(src, m, p)
        cshort = callee.split('.')[-1]
        near = code_text(src, m, max(0, p - 300), p)
        is_ajax = ('ajax' in keypath.split('.')) or bool(re.search(r'\bajax\s*=\s*\{[^{}]*$', near))
        if not (is_ajax or cshort in CONFIG_CALLEES): continue
        k = src.index(':', p)
        e = p
        depth = 0
        while e < len(src):
            if m[e] == CODE:
                c = src[e]
                if c in OPENB: depth += 1
                elif c in CLOSEB:
                    if depth == 0: break
                    depth -= 1
                elif depth == 0 and c == ',': break
            e += 1
        label = (cshort + '(' if cshort else '(') + (keypath or 'url') + ')'
        out.append((label, k + 1, e, p))
    return out

# ═══════════════════════════════════════════════════════════════════
# 4. 공통 빌더(디스패처) : 파라미터 URL 을 호출부 인자로 치환
# ═══════════════════════════════════════════════════════════════════
# name → (정의 파일, 인자 인덱스 후보)  ※ 인자 인덱스는 0-base
DISPATCHERS = {
    'dataTable_extendBuild':               ('arms/js/common.js',    {'ajaxUrl': [1]}),
    'dataTable_build':                     ('arms/js/common.js',    {'ajaxUrl': [1]}),
    'jsTreeBuild':                         ('arms/js/common.js',    {'serviceNameForURL': [1],
                                                                     'serviceNameForSyncURL': [2],
                                                                     'syncURL': [2, 1]}),
    'jira_server_request_create_or_update':('arms/js/jiraServer.js', {'url': [0]}, 1),
    'handleStreamResponse':                ('arms/js/aiChat.js',     {'url': [0]}),
}

def func_range(src, m, name):
    for pat in (r'function\s+%s\s*\(' % re.escape(name),
                r'%s\s*=\s*function\s*\(' % re.escape(name)):
        mo = re.search(pat, src)
        if not mo or m[mo.start()] != CODE: continue
        i = src.index('(', mo.end() - 1); j = match_bracket(src, m, i)
        k = j + 1
        while k < len(src) and not (m[k] == CODE and src[k] == '{'): k += 1
        e = match_bracket(src, m, k)
        return (mo.start(), e)
    return None

# ═══════════════════════════════════════════════════════════════════
# 5. 메뉴 매핑
# ═══════════════════════════════════════════════════════════════════
# ── 메뉴명: 네비게이션 라벨 → 페이지 content-header → 페이지 키 ──────────
#    js/{page}.js 는 html/{page}/ 와 1:1 이다(docs/ai/03_directory_structure).
#    네비게이션에 없는 페이지도 html/{page}/content-header.html 의 breadcrumb·h3 로
#    실제 화면명을 얻는다. 추정하지 않는다 — 출처를 menusource 에 남긴다.
def _txt(h):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h).replace('&nbsp;', ' ')).strip()

class NavParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.cur = None; self.buf = []; self.out = {}
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            h = dict(attrs).get('href', '') or ''
            mo = re.search(r'page=([A-Za-z0-9_]+)', h)
            self.cur = mo.group(1) if mo else None; self.buf = []
    def handle_endtag(self, tag):
        if tag == 'a' and self.cur:
            t = re.sub(r'\s+', ' ', ''.join(self.buf)).strip()
            if t and (self.cur not in self.out or not self.out[self.cur]):
                self.out[self.cur] = t
            self.cur = None
    def handle_data(self, d):
        if self.cur: self.buf.append(d)

def load_nav():
    nav = {}
    for area, f in NAV.items():
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            nav[area] = {}; continue
        pr = NavParser(); pr.feed(io.open(p, encoding='utf-8', errors='replace').read())
        nav[area] = {k: v for k, v in pr.out.items() if v}
    return nav

def load_headers():
    """html/<page>/content-header.html → breadcrumb(active) 또는 h3 제목."""
    hdr = {}
    for area in ('arms', 'backoffice'):
        m, base = {}, os.path.join(ROOT, area, 'html')
        if os.path.isdir(base):
            for d in sorted(os.listdir(base)):
                f = os.path.join(base, d, 'content-header.html')
                if not os.path.exists(f):
                    continue
                s = io.open(f, encoding='utf-8', errors='replace').read()
                cr = [c for c in (_txt(x) for x in
                      re.findall(r'<li[^>]*class="active"[^>]*>(.*?)</li>', s, re.S)) if c]
                if cr:
                    m[d] = ' > '.join(cr)
                else:
                    h3 = re.search(r'<h3[^>]*>(.*?)(?:<button|<ol)', s, re.S)
                    if h3 and _txt(h3.group(1)):
                        m[d] = _txt(h3.group(1))
        hdr[area] = m
    return hdr

def page_key(rel):
    """arms/js/foo/bar.js → foo ,  arms/js/foo.js → foo"""
    sub = rel.split('/js/', 1)[1]
    return sub.split('/')[0][:-3] if '/' not in sub else sub.split('/')[0]

COMMON = {'common', 'util', 'data', 'analysis'}

def menu_of(rel, nav, hdr):
    """-> (menuname, page, menusource)"""
    area = 'arms' if rel.startswith('arms/') else 'backoffice'
    key = page_key(rel)
    if nav[area].get(key):
        return nav[area][key], key, '네비게이션'
    if hdr[area].get(key):
        return hdr[area][key], key, 'content-header'
    if key in COMMON:
        return '공통 모듈', key, '공통'
    return key, key, '페이지키'

# ═══════════════════════════════════════════════════════════════════
# 6. 수작업 보정 — 기계 복원 불가분 (근거 주석 필수)
#    key = (rel, line) → [(apiurl, httpMethod|None, note), ...]
#    apiurl 이 None 이면 그 행을 버린다 (다른 행으로 대체됨).
# ═══════════════════════════════════════════════════════════════════
MANUAL = {
 # --- 래퍼 디스패치 지점 : 실제 URL 은 래퍼 호출부 행에 있다 → 행 삭제 ---
 ('arms/js/common/api/topMenuCoreApi.js', 41): [],   # $.ajax(options) — ajaxPromise() 호출부 12건이 실 URL
 ('arms/js/aiSupport.js', 1146):              [],   # $.ajax($.extend(..,options)) — fetchCached() 호출부가 실 URL

 # --- 배열 인덱싱 : base_url + batch_url_list[n-1] (batchManualControlApi.js:4,6-15) ---
 ('arms/js/reqStatus/batchManualControlApi.js', 42): [
   ("/auth-admin/yml/schedule/server_info_backup", "GET", "base_url+batch_url_list[0]"),
   ("/auth-admin/yml/schedule/sequentially_issue_es_store", "GET", "base_url+batch_url_list[1]"),
   ("/auth-admin/yml/schedule/increment/sequentially_issue_es_store", "GET", "base_url+batch_url_list[2]; batch_num==3 이면 /withDateRange?startDate={date_timepicker_start}&endDate={date_timepicker_end} 가 덧붙음"),
   ("/auth-admin/yml/schedule/issue_es_load", "GET", "base_url+batch_url_list[3]"),
   ("/auth-admin/yml/schedule/retry-failed-req-status-creation-to-elasticsearch", "GET", "base_url+batch_url_list[4]"),
   ("/auth-admin/yml/schedule/cache-status-mapping-data", "GET", "base_url+batch_url_list[5]"),
   ("/auth-admin/yml/schedule/update-arms-state-category", "GET", "base_url+batch_url_list[6]"),
   ("/auth-admin/yml/schedule/sync-atlassian-directory-users", "GET", "base_url+batch_url_list[7]"),
 ],
 # --- $targets 배열 3원소 (accessControl.js:78-108) ---
 ('backoffice/js/accessControl.js', 121): [
   ("/auth-admin/realms/master/roles", "GET", "$target.getUrl — $targets[0] (role)"),
   ("/auth-admin/realms/master/access-control/users", "GET", "$target.getUrl — $targets[1] (user)"),
   ("/auth-admin/realms/master/access-control/groups", "GET", "$target.getUrl — $targets[2] (group)"),
 ],
 ('backoffice/js/accessControl.js', 167): [
   ("/auth-admin/realms/master/role/{name}", "PUT", "$target.updateUrl+data[$target.key] — $targets[0] (key=name)"),
   ("/auth-admin/realms/master/user/{id}", "PUT", "$target.updateUrl+data[$target.key] — $targets[1] (key=id)"),
   ("/auth-admin/realms/master/groups/{id}", "PUT", "$target.updateUrl+data[$target.key] — $targets[2] (key=id)"),
 ],
 # --- getVectorApiUrl(path) = ndjson 여부로 2분기 (vectorIndexing.js:120-122) ---
 ('backoffice/js/vectorIndexing.js', 401): [
   ("/auth-user/ai/admin/vector/ndjson/classify", "GET", "getVectorApiUrl(path) — ndjson 파일"),
   ("/auth-user/ai/admin/vector/classify", "GET", "getVectorApiUrl(path) — 그 외 파일"),
 ],
 ('backoffice/js/vectorIndexing.js', 628): [
   ("/auth-user/ai/admin/vector/ndjson", "POST", "grouped key = getVectorApiUrl(item.path) — ndjson 파일"),
   ("/auth-user/ai/admin/vector", "POST", "grouped key = getVectorApiUrl(item.path) — 그 외 파일"),
 ],
 # --- 복원 불가 (REST 아님 / 미사용) ---
 ('arms/js/adms/editor-operation.js', 136): [
   ("UNRESOLVED:imgSrc.data", "GET", "draw.io 이미지의 src(data/blob URL) 재요청 — REST 엔드포인트 아님"),
 ],
 ('arms/js/common.js', 619): [
   ("UNRESOLVED:loadPlugin(url)", "GET", "dataType:script 정적 플러그인 로더 — 인자는 reference/ 하위 js·css 경로, REST 아님"),
 ],
 ('arms/js/common.js', 1068): [
   ("UNRESOLVED:ajaxGet(url)", "GET", "getJsonForPrototype 전용 유틸 — 저장소 내 호출부 없음"),
 ],
 # --- 분기 변수 (jiraServer.js) ---
 ('arms/js/jiraServer.js', 691): [
   ("/auth-user/api/arms/jiraServerPure/verifyNewAccount.do", "POST", "verifyPopupAccountApiEndpoint — 등록 팝업(:550) 및 :683 분기"),
   ("/auth-user/api/arms/jiraServerPure/verifyAccount.do", "POST", "verifyPopupAccountApiEndpoint — 수정 팝업(:564)"),
 ],
 ('arms/js/jiraServer.js', 776): [
   ("/auth-user/api/arms/jiraServerPure/verifyNewAccount.do", "POST", "verifyTabAccountApiEndpoint — :768 분기"),
   ("/auth-user/api/arms/jiraServerPure/verifyAccount.do", "POST", "verifyTabAccountApiEndpoint — 수정 탭 초기값"),
 ],
 ('arms/js/jiraServer.js', 1232): [
   ("/auth-user/api/arms/jiraServer/{refreshTarget}/renewNode.do", "PUT", "refreshTarget = selectedTab 값(almProject·issuePriority·issueStatus·issueType) — 생성 HTML onClick(:1015) 에서 전달"),
 ],
 ('arms/js/jiraServer.js', 1532): [
   ("/auth-user/api/arms/jiraProject/{selectedTab}/makeDefault.do", "PUT", "ajax_url — :1522,1525 분기"),
   ("/auth-user/api/arms/jiraServer/{selectedTab}/makeDefault.do", "PUT", "ajax_url — :1529 분기"),
 ],
 # --- url += 로 조건 분기하는 생성/수정 폼 (securityRole.js:86-94 / securityUser.js:293-313) ---
 ('backoffice/js/securityRole.js', 96): [
   ("/auth-admin/realms/master/role", "POST", "선택 role 없음 → 신규 생성"),
   ("/auth-admin/realms/master/role/{name}", "PUT", "selectedData 있으면 url += '/'+selectedData.name, type='PUT'"),
 ],
 ('backoffice/js/securityUser.js', 315): [
   ("/auth-admin/realms/master/user", "POST", "선택 user 없음 → 신규 생성"),
   ("/auth-admin/realms/master/user/{id}", "PUT", "selectedData 있으면 url += '/'+selectedData.id, type='put'"),
 ],
 ('arms/js/common.js', 1958): [
   ("UNRESOLVED:ajax_sample()", "{type}", "문서용 $.ajax 샘플 함수 — url 값이 '요청을 보낼 URL' 설명문"),
 ],
}

# ═══════════════════════════════════════════════════════════════════
# 7. 실행
# ═══════════════════════════════════════════════════════════════════
def js_files():
    out = []
    for area in AREAS:
        for dp, dn, fn in os.walk(os.path.join(ROOT, area)):
            for f in fn:
                if f.endswith('.js'):
                    out.append(os.path.relpath(os.path.join(dp, f), ROOT))
    return sorted(out)

def main():
    nav = load_nav()
    hdr = load_headers()
    files = js_files()
    S = {}
    for rel in files:
        src = open(os.path.join(ROOT, rel), encoding='utf-8', errors='replace').read()
        m = mask(src)
        S[rel] = (src, m, FileCtx(rel, src, m))

    # 디스패처 정의 구간 + 호출부 인덱싱
    drange, dcalls = {}, {}
    for name, dsp in DISPATCHERS.items():
        dfile = dsp[0]
        src, m, _c = S[dfile]
        r = func_range(src, m, name)
        if r: drange[name] = (dfile, r)
        calls = []
        for rel in files:
            s2, m2, c2 = S[rel]
            for mo in re.finditer(r'(?<![\w$.])%s\s*\(' % re.escape(name), s2):
                if m2[mo.start()] != CODE: continue
                if rel == dfile and r and r[0] <= mo.start() <= r[1] and \
                   re.match(r'function\s', s2[mo.start()-9:mo.start()] or '') is None and mo.start() < r[0] + 40:
                    continue                      # 정의 자신
                p = s2.index('(', mo.end() - 1); q = match_bracket(s2, m2, p)
                if q < 0: continue
                if rel == dfile and r and r[0] <= mo.start() <= r[0] + 30: continue
                calls.append((rel, mo.start(), p, q))
        dcalls[name] = calls

    rows = []
    stats = {'prim': 0, 'config': 0, 'manual': 0, 'dispatch': 0, 'unres': 0}

    for rel in files:
        src, m, ctx = S[rel]
        prims = find_primitives(src, m)
        spans = [(p, b) for _, _, b, p in prims]
        sites = []
        for pat, a, b, pos in prims:
            first = code_text(src, m, *split_top(src, m, a, b, ',')[0])
            if pat == '$.ajax' and first.startswith('{'):
                i = a
                while m[i] != CODE or src[i] != '{': i += 1
                j = match_bracket(src, m, i)
                u = obj_key(src, m, i, j, ('url',))
                if u is None:
                    continue
                if u[1] is None:                       # { url, ... } shorthand
                    ulo, uhi = None, None
                    sites.append((pat, pos, None, None, http_method(src, m, i, j, 'GET', ctx), 'shorthand'))
                    continue
                sites.append((pat, pos, u[1], u[2], http_method(src, m, i, j, 'GET', ctx), None))
            else:
                args = split_top(src, m, a, b, ',')
                dflt = {'$.get': 'GET', '$.getJSON': 'GET', '$.post': 'POST', 'fetch': 'GET', '$.ajax': 'GET'}[pat]
                meth = dflt
                if len(args) > 1:
                    i = args[1][0]
                    while i < args[1][1] and not (m[i] == CODE and src[i] == '{'): i += 1
                    if i < args[1][1]:
                        j = match_bracket(src, m, i)
                        if j > 0: meth = http_method(src, m, i, j, dflt, ctx)
                sites.append((pat, pos, args[0][0], args[0][1], meth, None))
        for label, ulo, uhi, pos in find_config_urls(src, m, spans):
            enc_lo = pos
            j = pos
            # config 지점의 method 는 대개 없음 → GET
            sites.append((label, pos, ulo, uhi, 'GET', None))

        for pat, pos, ulo, uhi, meth, flag in sites:
            ln = line_of(src, pos)
            key = (rel, ln)
            if key in MANUAL:
                for u, mm, note in MANUAL[key]:
                    rows.append(mkrow(rel, ln, pat, mm or meth, u, note, nav, hdr))
                stats['manual'] += 1
                continue
            # 디스패처 파라미터 치환
            expanded = try_dispatch(rel, pos, ulo, uhi, src, m, ctx, S, drange, dcalls)
            if expanded is not None:
                for crel, cln, u, note in expanded:
                    if not u.strip():
                        stats['clientside'] = stats.get('clientside', 0) + 1
                        continue          # ajaxUrl="" → 클라이언트 사이드 테이블(호출 없음)
                    rows.append(mkrow(crel, cln, pat + ' via ' + note[0],
                                      (note[2] if len(note) > 2 and note[2] else meth), u, note[1], nav, hdr))
                stats['dispatch'] += 1
                continue
            if ulo is None:
                rows.append(mkrow(rel, ln, pat, meth, 'UNRESOLVED:url shorthand', 'url 축약 프로퍼티', nav, hdr))
                stats['unres'] += 1
                continue
            note = ''
            try:
                urls = resolve(src, m, ulo, uhi, ctx)
            except Unres as e:
                rows.append(mkrow(rel, ln, pat, meth,
                                  'UNRESOLVED:' + re.sub(r'\s+', ' ', code_text(src, m, ulo, uhi))[:70],
                                  e.reason, nav, hdr))
                stats['unres'] += 1
                continue
            raw = code_text(src, m, ulo, uhi)
            if 'UrlBuilder' in raw or '.build()' in raw:
                mo = re.match(r'^([A-Za-z_$][\w$]*)\s*\.\s*build\(\)$', raw.rstrip(','))
                vr = ctx.single(mo.group(1), ulo) if mo else None
                span = (vr[1], vr[2]) if vr else (ulo, uhi)
                fn = enclosing_func_span(src, m, ulo)
                qk = query_keys(src, m, fn[0], fn[1], None)
                if qk: note = 'UrlBuilder 쿼리파라미터: ' + ' '.join(sorted(set(qk)))
            urls2 = expand_params(rel, pos, urls, S)
            if urls2 != urls:
                note = (note + '; ' if note else '') + '파라미터 → 같은 파일 호출부 인자 대입'
            for u in urls2:
                rows.append(mkrow(rel, ln, pat, meth, u, note, nav, hdr))
            stats['prim' if pat.startswith(('$.', 'fetch')) else 'config'] += 1

    # 같은 menuname 이 여러 page 를 덮으면(content-header 공유) page 를 덧붙여 구분한다.
    # 추정이 아니라 화면이 실제로 같은 제목을 쓰는 것이므로 이름은 남기고 괄호만 붙인다.
    bypage = {}
    for r in rows:
        bypage.setdefault(r['menuname'], set()).add(r['page'])
    for r in rows:
        if len(bypage[r['menuname']]) > 1 and r['menusource'] != '공통':
            r['menuname'] = '%s (%s)' % (r['menuname'], r['page'])

    # 중복 제거 (같은 파일·라인·URL·메서드)
    seen, out = set(), []
    for r in rows:
        k = (r['jsfile'], r['line'], r['httpMethod'], r['apiurl'])
        if k in seen: continue
        seen.add(k); out.append(r)
    out.sort(key=lambda r: (r['area'], r['jsfile'], r['line'], r['apiurl']))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # 백엔드 카탈로그가 주어지면 Tree CRUD 호출을 '상속' 으로 표기한다.
    be_csv = os.environ.get('CATALOG_BE_CSV')
    acts = tree_actions.load(be_csv) if be_csv and os.path.exists(be_csv) else {}
    for r in out:
        parent = tree_actions.match(r['apiurl'], acts) if acts else None
        r['provider'] = ('상속(%s)' % parent) if parent else ('일반 호출' if acts else '')
    cols = ['menuname', 'page', 'menusource', 'area', 'provider', 'jsfile', 'line',
            'httpMethod', 'apiurl', 'callPattern', 'note']
    with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out: w.writerow(r)

    bad = [r for r in out if r['apiurl'].endswith('/')]
    blank = [r for r in out if not r['menuname'] or not r['jsfile'] or not r['apiurl']]
    unres = [r for r in out if r['apiurl'].startswith('UNRESOLVED')]
    print("rows=%d  files=%d  trailing-slash=%d  blank=%d  unresolved=%d" %
          (len(out), len(files), len(bad), len(blank), len(unres)))
    print("stats:", stats)
    for r in unres: print("  UNRES", r['jsfile'], r['line'], r['apiurl'], '|', r['note'])
    for r in bad: print("  SLASH", r['jsfile'], r['line'], r['apiurl'])

def enclosing_func_span(src, m, pos):
    i, depth = pos, 0
    while i >= 0:
        if m[i] == CODE:
            if src[i] == '}': depth += 1
            elif src[i] == '{':
                if depth: depth -= 1
                else: return (i, match_bracket(src, m, i))
        i -= 1
    return (0, len(src))

def dispatcher_at(rel, pos, ident, S, drange):
    """(rel,pos) 가 어떤 디스패처 본문 안이고 ident 가 그 파라미터인지."""
    for name, dsp in DISPATCHERS.items():
        dfile, pmap = dsp[0], dsp[1]
        if rel != dfile or name not in drange: continue
        lo, hi = drange[name][1]
        if lo <= pos <= hi and ident in pmap:
            return name, pmap[ident]
    return None, None

def caller_urls(name, idxs, S, drange, dcalls, chain, hops=0):
    """디스패처 name 의 각 호출부에서 인자 URL 을 복원. 파라미터 전달이면 한 단계 더 올라간다."""
    if hops > 3: return []
    out = []
    for crel, cpos, p, q in dcalls[name]:
        s2, m2, c2 = S[crel]
        args = split_top(s2, m2, p + 1, q, ',')
        done = False
        for idx in idxs:
            if idx >= len(args): continue
            try:
                for g in resolve(s2, m2, args[idx][0], args[idx][1], c2):
                    out.append((crel, line_of(s2, cpos), g, chain + [name]))
                done = True; break
            except Unres:
                atxt = code_text(s2, m2, args[idx][0], args[idx][1]).rstrip(',')
                if IDENT.match(atxt):
                    up, upidx = dispatcher_at(crel, cpos, atxt, S, drange)
                    if up and up not in chain:
                        sub = caller_urls(up, upidx, S, drange, dcalls, chain + [name], hops + 1)
                        if sub: out += sub; done = True; break
        if done: continue
    return out

def try_dispatch(rel, pos, ulo, uhi, src, m, ctx, S, drange, dcalls):
    if ulo is None: return None
    txt = code_text(src, m, ulo, uhi).rstrip(',')
    head = re.match(r'^([A-Za-z_$][\w$]*)', txt)
    if not head: return None
    name, idxs = dispatcher_at(rel, pos, head.group(1), S, drange)
    if not name: return None
    suffix = txt[len(head.group(1)):]
    if suffix and not re.match(r'^\s*\+', suffix): return None
    tail = ''
    if suffix:
        parts = split_top(src, m, ulo, uhi, '+')
        if len(parts) > 1:
            try: tail = ''.join(resolve(src, m, a, b, ctx, top=False)[0] for a, b in parts[1:])
            except Unres: tail = ''
    res = caller_urls(name, idxs, S, drange, dcalls, [])
    if not res: return None
    midx = DISPATCHERS[name][2] if len(DISPATCHERS[name]) > 2 else None
    mmap = {}
    if midx is not None:
        for crel, cpos, p2, q2 in dcalls[name]:
            s2, m2, _c = S[crel]
            a2 = split_top(s2, m2, p2 + 1, q2, ',')
            if midx < len(a2):
                v = re.match(r'^["\'](\w+)["\']$', code_text(s2, m2, a2[midx][0], a2[midx][1]).rstrip(','))
                if v: mmap[(crel, line_of(s2, cpos))] = v.group(1).upper()
    dline = line_of(src, pos)
    out = []
    for crel, cline, g, chain in res:
        out.append((crel, cline, g + tail,
                    ('->'.join(chain) + '(arg%d)' % idxs[0],
                     '%s:%d %s 경유' % (os.path.basename(rel), dline, '->'.join(chain)),
                     mmap.get((crel, cline)))))
    return out

def mkrow(rel, ln, pat, meth, url, note, nav, hdr):
    if not url.startswith('UNRESOLVED') and url[-1:] in ('/', '?', '&'):
        trimmed = url.rstrip('/?&')
        note = (note + '; ' if note else '') + '원문 말미 %s 제거(경로 정규화)' % url[len(trimmed):]
        url = trimmed
    mn, pg, src = menu_of(rel, nav, hdr)
    return {'menuname': mn, 'page': pg, 'menusource': src,
            'area': 'arms' if rel.startswith('arms/') else 'backoffice',
            'jsfile': rel, 'line': ln, 'httpMethod': meth,
            'apiurl': url, 'callPattern': pat, 'note': note}

if __name__ == '__main__':
    main()
