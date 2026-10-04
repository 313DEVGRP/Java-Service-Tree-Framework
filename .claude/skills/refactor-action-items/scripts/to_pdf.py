# 액션 아이템 md → PDF (A4, 한글 폰트). 사용: python3 to_pdf.py <md 파일>  → 같은 위치에 .pdf
# 필요: pip install markdown pygments, Google Chrome
import sys, re, subprocess, markdown, os, tempfile
from pygments.formatters import HtmlFormatter
src = sys.argv[1]; pdf = src[:-3] + ".pdf"; html_path = os.path.join(tempfile.mkdtemp(), "action-items.html")
md = open(src, encoding="utf-8").read()
md = re.sub(r"([^\n])\n(\|[^\n]*\|\n\|[ :\-|]+\|)", r"\1\n\n\2", md)
md = re.sub(r"^(\*\*[^*\n]+\*\*(?: \(있을 때만\))?)\n", r"\1\n\n", md, flags=re.M)
body = markdown.markdown(md, extensions=["tables","fenced_code","codehilite","sane_lists"],
    extension_configs={"codehilite":{"guess_lang":False,"css_class":"hl"}})
body = body.replace("\\|", "|")  # 표 칸 안 코드의 이스케이프된 | 를 원래 글자로
css = HtmlFormatter(style="friendly").get_style_defs(".hl")
doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 16mm 15mm; }}
body {{ font-family:"Apple SD Gothic Neo",sans-serif; font-size:10pt; line-height:1.6; color:#1d2228; }}
h1 {{ font-size:17pt; color:#0e4f63; border-bottom:2px solid #0e4f63; padding-bottom:4px; }}
h2 {{ font-size:13.5pt; color:#0e4f63; margin-top:26px; border-bottom:1px solid #cfdde2; break-after:avoid; }}
h3 {{ font-size:11.5pt; background:#eef5f7; padding:5px 8px; border-left:4px solid #0e4f63; margin-top:22px; break-after:avoid; }}
p > strong:only-child {{ color:#0e4f63; }} p {{ margin:6px 0; orphans:3; widows:3; }}
table {{ border-collapse:collapse; width:100%; font-size:9pt; margin:8px 0; }}
th,td {{ border:1px solid #c9d3d8; padding:4px 6px; vertical-align:top; }} th {{ background:#e3eef1; }}
tr {{ break-inside:avoid; }} td:first-child,th:first-child,td:nth-child(5),th:nth-child(5) {{ white-space:nowrap; }} td:first-child {{ width:1%; }} p:has(> em:only-child) {{ break-after:avoid; margin-top:10px; }} em {{ color:#55707a; font-style:normal; font-weight:600; font-size:9pt; }}
code {{ font-family:Menlo,monospace; font-size:8.6pt; background:#f3f5f6; padding:0 3px; border-radius:3px; }}
.hl {{ border:1px solid #dde3e6; border-radius:4px; padding:6px 10px; font-size:8.4pt; break-inside:avoid; }}
.hl pre {{ margin:0; white-space:pre-wrap; }} .hl code {{ background:none; padding:0; }}
{css}</style></head><body>{body}</body></html>"""
open(html_path,"w",encoding="utf-8").write(doc)
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome","--headless=new","--disable-gpu",
  "--no-pdf-header-footer","--print-to-pdf="+pdf,"file://"+html_path],check=True,capture_output=True)
print(pdf)
