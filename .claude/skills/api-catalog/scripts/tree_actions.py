# -*- coding: utf-8 -*-
"""백엔드 플랫 CSV 에서 'Tree 프레임워크가 제공하는 액션' 목록을 뽑는 공용 헬퍼.

endpoints_flat.py 의 `kind=inherited` 행이 곧 상속으로 생긴 URL 이다.
그 경로 suffix(`/addNode.do` 등)로 끝나는 프론트 호출은 Tree CRUD 를 부르는 것이므로
자체 도메인 API 와 구분해 `상속(<부모클래스>)` 으로 표기한다.
"""
import csv, io

def load(be_csv):
    """-> {경로 suffix: 부모 클래스명}"""
    out = {}
    for r in csv.DictReader(io.open(be_csv, encoding='utf-8-sig')):
        if r.get('kind') != 'inherited':
            continue
        out[r['path'].replace('{basePath}', '')] = r['controllerClass']
    return out

def match(url, actions):
    """프론트 URL 이 Tree 액션으로 끝나면 부모 클래스명, 아니면 None."""
    u = url.split('?')[0].split('#')[0].rstrip('/')
    best = None
    for suf, parent in actions.items():
        if u.endswith(suf) and (best is None or len(suf) > len(best[0])):
            best = (suf, parent)
    return best[1] if best else None
