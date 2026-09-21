# -*- coding: utf-8 -*-
"""한 저장소의 산출 결과를 한 줄로 요약한다 (CATALOG_TASK 기준)."""
import io, os, json, glob
T = os.environ.get('CATALOG_TASK', 'tasks/api-catalog')
R = os.environ.get('CATALOG_REPO', '?')
inv = json.load(io.open(T + '/sources/inventory.json', encoding='utf-8'))
ch = json.load(io.open(T + '/sources/call_chains.json', encoding='utf-8'))
def cnt(ns): return sum(1 + cnt(n['children']) for n in ns)
csvs = [p for p in glob.glob(T + '/artifacts/*.csv') if not os.path.basename(p).startswith('_')]
rows = (sum(1 for _ in io.open(csvs[0], encoding='utf-8-sig')) - 1) if csvs else 0
per = inv['perController']
print('%-42s 컨트롤러 %3d · 엔드포인트 %5d (자체 %4d + 상속 %4d) · Feign %d · 체인 %5d · CSV %5d' % (
    R.replace('Java-Service-Tree-Framework-', ''), len(per),
    inv['totalEndpointInstances'],
    sum(v['own'] for v in per.values()), sum(v['inherited'] for v in per.values()),
    len(inv.get('feign', {})), sum(cnt(c['tree']) for c in ch), rows))
