# -*- coding: utf-8 -*-
"""md -> html (A4 인쇄용). 사용: render.py <src.md> <out.html> <표지제목> <표지부제> <버전>"""
import io, os, sys, markdown

src, out, title, subtitle, ver = sys.argv[1:6]
body = markdown.markdown(io.open(src, encoding='utf-8').read(),
                         extensions=['tables','fenced_code','sane_lists','nl2br'])

CSS = """
@page{size:A4;margin:16mm 13mm}
body{font-family:"Malgun Gothic","맑은 고딕",sans-serif;font-size:10pt;line-height:1.55;color:#111}
h1{font-size:19pt;border-bottom:2px solid #333;padding-bottom:6px;page-break-after:avoid}
h2{font-size:14pt;margin-top:20px;border-bottom:1px solid #bbb;padding-bottom:4px;page-break-after:avoid}
h3{font-size:11.5pt;margin-top:14px;page-break-after:avoid}
table{border-collapse:collapse;width:100%;margin:9px 0;font-size:8.6pt;table-layout:fixed}
th,td{border:1px solid #999;padding:4px 5px;vertical-align:top;word-wrap:break-word;overflow-wrap:anywhere}
th{background:#e8ecf2;font-weight:bold;text-align:left}
thead{display:table-header-group}
tr{page-break-inside:avoid}
code{font-family:Consolas,monospace;font-size:8.2pt;background:#f2f2f2;padding:1px 3px;border-radius:2px;word-break:break-all}
pre{background:#f6f6f6;border:1px solid #ddd;padding:8px;font-size:8.6pt;overflow-x:auto}
pre code{background:none}
blockquote{border-left:4px solid #6a8caf;background:#f4f7fb;margin:9px 0;padding:7px 11px}
blockquote p{margin:3px 0}
ul,ol{padding-left:20px}
li{margin:3px 0}
del{color:#888}
hr{border:none;border-top:1px solid #ccc;margin:16px 0}
.cover{text-align:center;page-break-after:always;padding-top:70mm}
.cover .t{font-size:24pt;font-weight:bold;line-height:1.4}
.cover .s{font-size:13pt;margin-top:14px;color:#333}
.cover .m{font-size:11pt;margin-top:44px;line-height:2}
"""

import datetime
COVER = ('<div class="cover"><div class="t">%s</div><div class="s">%s</div>'
         '<div class="m">작성일 &nbsp;%s<br>버전 &nbsp;<b>%s</b><br>'
         '산출 &nbsp;%s</div></div>') % (
    title, subtitle,
    datetime.date.today().strftime('%Y-%m-%d'), ver,
    os.environ.get('CATALOG_REQID', '/REQ-RUN'))

html = ('<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><title>%s</title>'
        '<style>%s</style></head><body>%s%s</body></html>') % (title, CSS, COVER, body)
io.open(out, 'w', encoding='utf-8', newline='\n').write(html)
print('html', len(html))
