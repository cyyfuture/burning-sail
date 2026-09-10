# -*- coding: utf-8 -*-
"""
燃帆规则书 → 可视化单文件网站构建脚本
用法: python build_site.py
读取本目录 0*.md / 1*.md（00–15章），生成同目录 index.html（完全离线可用，双击即开）。
"""
import json, re, html, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT_PATH = (BASE_DIR / "index.html").resolve()
# 边界校验：输出必须落在本目录内
if OUT_PATH.parent != BASE_DIR:
    raise SystemExit("输出路径越界，已阻止")

# ---------------- 行内格式 ----------------
def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" class="int-link">\1</a>', s)
    return s

# ---------------- 块级解析 ----------------
CALLOUT_MAP = [
    ("示例", "example"), ("变体", "variant"), ("历史注", "history"),
    ("设计注", "design"), ("GM之眼", "gmeye"), ("GM侧栏", "gmeye"),
]

def render_md(text: str) -> str:
    lines = text.split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        st = line.strip()

        # 代码块
        if st.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append("<pre class='codeblock'><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lv, txt = len(m.group(1)), m.group(2).strip()
            out.append(f"<h{lv}>{inline(txt)}</h{lv}>")
            i += 1
            continue

        # 水平线
        if re.fullmatch(r"(-{3,}|\*{3,})", st):
            out.append("<hr>")
            i += 1
            continue

        # 表格
        if "|" in line and i + 1 < n and re.fullmatch(r"[\s|:\-]+", lines[i+1].strip()) and "-" in lines[i+1]:
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ["<div class='tbl'><table><thead><tr>"]
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue

        # 引用块
        if st.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            joined = "<br>".join(inline(b) for b in buf if b)
            cls = "quote"
            for key, name in CALLOUT_MAP:
                if buf and buf[0].replace(" ", "").startswith("【" + key):
                    cls = f"quote callout callout-{name}"
                    break
            if buf and all(x.startswith("*") and x.endswith("*") for x in buf if x):
                cls += " aside-voice"  # 全斜体 = GM朗读/旁白
            out.append(f"<blockquote class='{cls}'>{joined}</blockquote>")
            continue

        # 列表（含任务列表与二层嵌套）
        if re.match(r"^(\s*)([-*]|\d+\.)\s+", line):
            items = []  # (depth, ordered, text)
            while i < n:
                mm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if not mm: break
                depth = 1 if len(mm.group(1)) >= 2 else 0
                ordered = mm.group(2)[0].isdigit()
                items.append((depth, ordered, mm.group(3)))
                i += 1
            any_ord = any(o for _, o, _ in items)
            tag = "ol" if any_ord else "ul"
            parts, top, subs = [], None, []
            def flush():
                if top is None: return
                inner = inline(top)
                tm = re.match(r"^\[( |x)\]\s+(.*)$", top)
                if tm:
                    inner = (f"<label class='task'><input type='checkbox' disabled "
                             f"{'checked' if tm.group(1)=='x' else ''}> {inline(tm.group(2))}</label>")
                if subs:
                    stag = "ol" if any(o for _, o, _ in subs) else "ul"
                    inner += (f"<{stag} class='sub'>" +
                              "".join(f"<li>{inline(s)}</li>" for _, _, s in subs) +
                              f"</{stag}>")
                parts.append(f"<li>{inner}</li>")
            for depth, ordered, txt in items:
                if depth == 0:
                    flush(); top, subs = txt, []
                else:
                    subs.append((depth, ordered, txt))
            flush()
            out.append(f"<{tag} class='mdlist'>" + "".join(parts) + f"</{tag}>")
            continue

        # 空行
        if not st:
            i += 1
            continue

        # 普通段落（收集至空行或块级标记）
        buf = [line]
        i += 1
        while i < n:
            nx = lines[i].strip()
            if (not nx or nx.startswith(("#", ">", "```", "- ", "* ")) or
                    re.match(r"^\d+\.\s", nx) or re.fullmatch(r"(-{3,}|\*{3,})", nx) or
                    ("|" in nx and i + 1 < n and re.fullmatch(r"[\s|:\-]+", lines[i+1].strip()) and "-" in lines[i+1])):
                break
            buf.append(lines[i]); i += 1
        out.append("<p>" + "<br>".join(inline(b.strip()) for b in buf) + "</p>")

    return "\n".join(out)

def plain_text(html_src: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_src)).strip()

# ---------------- 章节收集 ----------------
VOLS = [
    ("卷首", ["00"]),
    ("卷一 · 玩家入门区", ["01", "02", "03", "04"]),
    ("卷二 · 系统核心区", ["05", "06", "07", "08", "09", "10"]),
    ("卷三 · 世界与主持区", ["11", "12", "13", "14"]),
    ("卷四 · 附录与工具区", ["15", "16"]),
]

GLOSS_FILE = BASE_DIR / "16_术语索引.md"

def parse_glossary(path) -> dict:
    """解析 '## 词条名' + 段落 的术语文件 → {term: html}"""
    gloss, cur, buf = {}, None, []
    for line in path.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if cur:
                gloss[cur] = render_md("\n".join(buf)).strip()
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur:
        gloss[cur] = render_md("\n".join(buf)).strip()
    return gloss

def build_chapters():
    chapters = []
    for path in sorted(BASE_DIR.glob("[0-1]*.md")):
        num = path.name[:2]
        raw = path.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+)$", raw, re.M)
        title = m.group(1).strip() if m else path.name
        # 章节头已单独渲染，去掉正文里的一级标题避免重复
        body = re.sub(r"^#[^\n]*\n", "", raw, count=1)
        title = re.sub(r"^第[^\s]*章\s*", "", title)
        if "：" in title:
            title = title.split("：", 1)[0]
        skeleton = "状态：骨架" in raw
        chapters.append({
            "num": num,
            "title": title,
            "vol": next(v for v, nums in VOLS if num in nums),
            "skeleton": skeleton,
            "html": render_md(body),
            "text": "",
        })
    for c in chapters:
        c["text"] = plain_text(c["html"])
    return chapters

# ---------------- 页面模板 ----------------
TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>燃帆 · The Age of Burning Sail — 规则书</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='46' fill='%23101d2e'/%3E%3Cpath d='M50 10 L58 42 L90 50 L58 58 L50 90 L42 58 L10 50 L42 42 Z' fill='%23d8a93d'/%3E%3Ccircle cx='50' cy='50' r='6' fill='%238c2f39'/%3E%3C/svg%3E">
<style>
:root{
  --navy:#101d2e; --navy2:#1b2c44; --navy3:#24385a;
  --paper:#f3ead6; --paper2:#ecdfc3; --paper3:#e2d2ae;
  --ink:#2c2214; --ink2:#5a4a33;
  --gold:#b8860b; --gold2:#8a6508; --gold3:#d8a93d;
  --red:#8c2f39; --green:#3e6b4f; --blue:#2c5d8a; --purple:#6b4a8c;
  --line:rgba(90,74,51,.28);
  --serif:"Noto Serif SC","Source Han Serif SC","STSong","SimSun",serif;
  --kai:"STKaiti","KaiTi","Noto Serif SC",serif;
  --shadow:0 2px 14px rgba(16,29,46,.18);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
:focus-visible{outline:2px solid var(--gold3);outline-offset:2px;border-radius:4px}
body{font-family:var(--serif);background:var(--navy);color:var(--ink);font-size:16px;line-height:1.85}

/* ===== 布局 ===== */
.app{display:flex;min-height:100vh}
aside{width:300px;flex-shrink:0;background:linear-gradient(180deg,var(--navy) 0%,var(--navy2) 100%);color:#d8cdb2;position:fixed;top:0;bottom:0;left:0;overflow-y:auto;z-index:50;display:flex;flex-direction:column;transition:transform .25s;box-shadow:1px 0 0 rgba(216,169,61,.25),10px 0 30px rgba(4,9,17,.35)}
main{margin-left:300px;flex:1;min-width:0;background:var(--paper);min-height:100vh;
  background-image:radial-gradient(120% 90% at 50% 38%,transparent 58%,rgba(59,42,20,.09)),
  url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E"),
  radial-gradient(ellipse at 50% -10%,rgba(255,248,220,.65),transparent 60%),
  repeating-linear-gradient(0deg,transparent 0 34px,rgba(90,74,51,.035) 34px 35px)}
@media(max-width:960px){
  aside{transform:translateX(-100%)}
  body.side-open aside{transform:translateX(0);box-shadow:0 0 60px rgba(0,0,0,.6)}
  main{margin-left:0}
}

/* ===== 侧栏 ===== */
.brand{padding:26px 22px 18px;border-bottom:1px solid rgba(216,205,178,.15);text-align:center}
.brand svg{width:74px;height:74px;opacity:.95}
.brand h1{font-family:var(--kai);font-size:30px;letter-spacing:.35em;margin-top:6px;color:var(--gold3);text-indent:.35em}
.brand .en{font-size:11px;letter-spacing:.28em;color:#8fa3bd;text-transform:uppercase;margin-top:2px}
.searchbox{padding:14px 16px 4px}
.searchbox input{width:100%;background:rgba(255,255,255,.07);border:1px solid rgba(216,205,178,.25);color:#e9dfc6;border-radius:6px;padding:8px 12px;font-family:var(--serif);font-size:14px;outline:none}
.searchbox input:focus{border-color:var(--gold3)}
.searchbox input::placeholder{color:#9db0c6}
#searchResults{padding:4px 10px}
#searchResults .sr{display:block;padding:7px 10px;border-radius:6px;color:#cfc4a6;font-size:13px;line-height:1.5;text-decoration:none;border-bottom:1px dashed rgba(216,205,178,.12)}
#searchResults .sr:hover{background:rgba(216,169,61,.12)}
#searchResults .sr b{color:var(--gold3);font-weight:600}
#searchResults .sr .frag{display:block;color:#8fa3bd;font-size:12px;margin-top:2px}
nav{flex:1;padding:10px 14px 20px}
.vol{font-size:12px;letter-spacing:.18em;color:var(--gold3);margin:18px 8px 6px;font-family:var(--kai);display:flex;align-items:center;gap:8px}
.vol::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(216,169,61,.5),transparent)}
nav a.ch{display:flex;align-items:baseline;gap:8px;padding:7px 10px;border-radius:6px;color:#cfc4a6;text-decoration:none;font-size:14.5px;line-height:1.5}
nav a.ch:hover{background:rgba(216,169,61,.12);color:#f0e6cb}
nav a.ch.active{background:rgba(216,169,61,.18);color:var(--gold3)}
nav a.ch .no{font-size:11.5px;color:#8fa3bd;min-width:20px;font-variant-numeric:tabular-nums}
nav a.ch .st{margin-left:auto;width:8px;height:8px;border-radius:50%;flex-shrink:0;align-self:center}
.st.full{background:var(--gold3);box-shadow:0 0 6px rgba(216,169,61,.8)}
.st.skel{border:1.5px solid #6b7d94;background:transparent}
nav a.ch.skel{color:#7e8ea3}
.side-foot{padding:12px 18px;font-size:11px;color:#8296ad;border-top:1px solid rgba(216,205,178,.12)}

/* ===== 顶栏 ===== */
.topbar{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:14px;padding:12px 28px;
  background:linear-gradient(180deg,rgba(243,234,214,.97),rgba(243,234,214,.9));backdrop-filter:blur(4px);
  border-bottom:2px solid var(--gold);box-shadow:0 2px 10px rgba(16,29,46,.08)}
body.night .topbar{background:linear-gradient(180deg,rgba(20,31,48,.97),rgba(20,31,48,.9))}
.topbar .crumb{font-family:var(--kai);font-size:17px;color:var(--ink2);flex:1}
.topbar .crumb b{color:var(--gold2)}
.hamb,.theme{background:none;border:1px solid var(--line);border-radius:6px;width:36px;height:36px;font-size:17px;cursor:pointer;color:var(--ink2);display:inline-flex;align-items:center;justify-content:center;padding:0}
.hamb svg,.theme svg{display:block}
.hamb{display:none}
@media(max-width:960px){.hamb{display:block}}

/* ===== 内容 ===== */
.page{max-width:880px;margin:0 auto;padding:44px 40px 110px}
@media(max-width:960px){.page{padding:30px 20px 90px}}
.page h2{font-family:var(--kai);font-size:27px;color:var(--navy);margin:46px 0 18px;padding-bottom:10px;
  border-bottom:2px solid var(--gold);position:relative}
.page h2::before{content:"";display:inline-block;width:16px;height:16px;margin-right:10px;vertical-align:-2px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8860b' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='5' r='3'/%3E%3Cpath d='M12 22V8'/%3E%3Cpath d='M5 12H2a10 10 0 0 0 20 0h-3'/%3E%3C/svg%3E") no-repeat center/contain}
.page h3{font-family:var(--kai);font-size:21px;color:var(--navy2);margin:34px 0 12px;padding-left:12px;border-left:4px solid var(--gold)}
.page h4{font-size:17px;color:var(--gold2);margin:24px 0 8px}
.page p{margin:12px 0}
.page a{color:var(--blue);text-decoration:none;border-bottom:1px dashed rgba(44,93,138,.55);padding-bottom:1px;transition:color .15s,border-color .15s}
.page a:hover{color:var(--gold2);border-bottom-color:var(--gold2)}
.page hr{position:relative;border:none;height:0;border-top:1px dashed rgba(184,134,11,.5);margin:40px auto;width:72%;opacity:1}
.page hr::after{content:"✦";position:absolute;left:50%;top:0;transform:translate(-50%,-54%);background:var(--paper);padding:0 14px;color:var(--gold);font-size:12px}
.page strong{color:#1c2f47}
code{background:rgba(184,134,11,.14);border:1px solid rgba(184,134,11,.25);border-radius:4px;padding:1px 6px;font-size:.88em;color:#6b4a12;font-family:Consolas,monospace}
.codeblock{background:var(--navy);color:#d8cdb2;border-radius:8px;padding:16px 18px;margin:16px 0;overflow-x:auto;font-size:13.5px;line-height:1.7;font-family:Consolas,monospace;box-shadow:var(--shadow)}
.codeblock code{background:none;border:none;color:inherit;padding:0}

/* 表格 */
.tbl{overflow-x:auto;margin:18px 0;box-shadow:var(--shadow);border-radius:8px;border:1px solid var(--line)}
.tbl table{width:100%;border-collapse:collapse;font-size:14.5px;background:#faf4e4}
.tbl th{background:linear-gradient(180deg,var(--navy2),#15233a);color:var(--gold3);font-family:var(--kai);font-weight:600;padding:9px 13px;text-align:left;white-space:nowrap;letter-spacing:.05em;border-bottom:2px solid var(--gold)}
.tbl td{padding:8px 13px;border-top:1px solid var(--line);vertical-align:top;font-variant-numeric:tabular-nums}
.tbl tbody tr:nth-child(even){background:rgba(184,134,11,.05)}

/* 列表 */
.mdlist{margin:12px 0 12px 26px}
.mdlist li{margin:5px 0}
.mdlist ul.sub,.mdlist ol.sub{margin:4px 0 6px 24px;opacity:.92}
.task{display:flex;gap:8px;align-items:baseline}
.task input{accent-color:var(--gold)}

/* 引用块与边栏 */
blockquote{margin:20px 0;padding:14px 20px;border-left:4px solid var(--gold);background:var(--paper2);border-radius:0 8px 8px 0;font-size:15px}
blockquote p{margin:6px 0}
blockquote.aside-voice{font-style:italic;background:linear-gradient(180deg,var(--paper2),var(--paper3));position:relative;padding-left:42px;color:#4a3a20}
blockquote.aside-voice::before{content:"❝";position:absolute;left:12px;top:6px;font-size:22px;color:var(--gold);opacity:.5}
blockquote.aside-voice::after{content:"❞";position:absolute;right:12px;bottom:0;font-size:22px;color:var(--gold);opacity:.45}
.callout{border-radius:8px;border:1px solid;border-left-width:5px}
.callout-example::before,.callout-variant::before,.callout-history::before,.callout-design::before,
.callout-gmeye::before{display:block;font-size:11.5px;letter-spacing:.18em;margin-bottom:4px;font-family:var(--kai)}
.callout-example{border-color:#c9a86a;background:#f7efdb;border-left-color:var(--gold)}
.callout-example::before{content:"✒ 示 例";color:var(--gold2)}
.callout-variant{border-color:#c5b3dd;background:#f2ecfa;border-left-color:var(--purple)}
.callout-variant::before{content:"❖ 变 体 规 则";color:var(--purple)}
.callout-history{border-color:#a9c4dc;background:#ecf3fa;border-left-color:var(--blue)}
.callout-history::before{content:"❧ 历 史 注";color:var(--blue)}
.callout-design{border-color:#a9c9b4;background:#ecf6ef;border-left-color:var(--green)}
.callout-design::before{content:"✦ 设 计 注";color:var(--green)}
.callout-gmeye{border-color:#d3a0a6;background:#f8edef;border-left-color:var(--red)}
.callout-gmeye::before{content:"† 仅 GM 可 见";color:var(--red)}

/* ===== 封面 ===== */
.cover{min-height:calc(100vh - 62px);text-align:center;padding:60px 30px 90px;position:relative;overflow:hidden}
.cover-frame{position:absolute;inset:12px;pointer-events:none;opacity:.55;border:1px solid rgba(184,134,11,.25);
  background:
    linear-gradient(var(--gold),var(--gold)) left 0 top 0/24px 2.5px,
    linear-gradient(var(--gold),var(--gold)) left 0 top 0/2.5px 24px,
    linear-gradient(var(--gold),var(--gold)) right 0 top 0/24px 2.5px,
    linear-gradient(var(--gold),var(--gold)) right 0 top 0/2.5px 24px,
    linear-gradient(var(--gold),var(--gold)) left 0 bottom 0/24px 2.5px,
    linear-gradient(var(--gold),var(--gold)) left 0 bottom 0/2.5px 24px,
    linear-gradient(var(--gold),var(--gold)) right 0 bottom 0/24px 2.5px,
    linear-gradient(var(--gold),var(--gold)) right 0 bottom 0/2.5px 24px;
  background-repeat:no-repeat}
body.night .cover-frame{opacity:.4}
.stars{position:absolute;top:0;left:0;right:0;height:46vh;pointer-events:none;display:none}
body.night .stars{display:block}
.stars i{position:absolute;width:2px;height:2px;border-radius:50%;background:#eee6cd;opacity:.6;animation:twinkle var(--t,3.2s) ease-in-out infinite alternate;animation-delay:var(--d,0s)}
.stars i.big{width:3px;height:3px;box-shadow:0 0 6px rgba(238,230,205,.9)}
@keyframes twinkle{from{opacity:.12}to{opacity:.85}}
.cover .compass{width:150px;height:150px;margin:0 auto;animation:spin 90s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.cover .kick{letter-spacing:.5em;color:var(--gold2);font-size:13px;text-transform:uppercase;margin-top:22px;text-indent:.5em}
.cover h1{font-family:var(--kai);font-size:76px;letter-spacing:.3em;color:var(--navy);margin:8px 0 2px;text-indent:.3em}
.cover .en-title{font-size:15px;letter-spacing:.3em;color:var(--ink2);text-transform:uppercase}
.cover .tagline{margin:16px auto 6px;font-size:17px;color:var(--gold2);font-family:var(--kai)}
.cover .epigraph{max-width:560px;margin:26px auto 0;font-style:italic;color:#6b5a3d;font-size:15px;line-height:2}
.cover .epigraph::before{content:"—— ";opacity:.5}
.cover .epigraph::after{content:" ——"}
.wave{display:block;margin:34px auto 0;opacity:.6}
.loop{display:flex;flex-wrap:wrap;justify-content:center;gap:6px;max-width:760px;margin:8px auto 0}
.loop span{background:var(--navy2);color:#e9dfc6;padding:7px 16px;border-radius:20px;font-size:14px;font-family:var(--kai)}
.loop i{align-self:center;color:var(--gold);font-style:normal;font-size:16px}
h2.sec-title{display:flex;align-items:center;gap:14px;justify-content:center;border:none;margin:44px 0 6px;max-width:960px}
h2.sec-title::before{content:none}
h2.sec-title .line{flex:0 0 60px;height:1px;background:var(--gold)}
.volcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr));gap:16px;margin:26px auto 0;max-width:960px;text-align:left}
.vcard{background:#faf4e4;border:1px solid var(--line);border-top:4px solid var(--gold);border-radius:10px;padding:18px 20px;box-shadow:var(--shadow)}
.vcard h3{border:none;padding:0;margin:0 0 10px;font-size:17px;color:var(--navy)}
.vcard a{display:flex;justify-content:space-between;gap:10px;padding:5px 0;font-size:14px;color:var(--ink2);text-decoration:none;border-bottom:1px dashed rgba(90,74,51,.15)}
.vcard a:hover{color:var(--gold2)}
.vcard a .badge{font-size:11px;padding:1px 8px;border-radius:10px;white-space:nowrap;align-self:center}
.badge.full{background:rgba(184,134,11,.18);color:var(--gold2);border:1px solid rgba(184,134,11,.4)}
.badge.skel{background:transparent;color:#8a7a5c;border:1px dashed #b5a684}
.frozen{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(240px,100%),1fr));gap:12px;max-width:960px;margin:24px auto 0;text-align:left}
.fcard{background:var(--navy2);color:#e9dfc6;border-radius:10px;padding:14px 18px;box-shadow:var(--shadow)}
.fcard .k{font-size:12px;letter-spacing:.12em;color:var(--gold3);font-family:var(--kai)}
.fcard .v{font-size:15px;margin-top:4px;color:#f4ecd8}
.cta{display:inline-block;margin-top:36px;background:var(--gold);color:#1c1503;font-family:var(--kai);font-size:18px;letter-spacing:.2em;padding:13px 44px;border-radius:32px;text-decoration:none;box-shadow:0 4px 18px rgba(184,134,11,.45);transition:transform .15s}
.cta:hover{transform:translateY(-2px);background:var(--gold3)}

/* 章节头部 */
.ch-head{margin-bottom:8px}
.ch-head .kicker{font-size:12.5px;letter-spacing:.22em;color:var(--gold2);font-family:Consolas,"Courier New",var(--kai);display:flex;align-items:center;gap:12px}
.ch-head .kicker::before{content:"";width:36px;height:1px;background:linear-gradient(90deg,transparent,var(--gold))}
.ch-head .kicker::after{content:"";width:36px;height:1px;background:linear-gradient(270deg,transparent,var(--gold))}
.ch-head h1{font-family:var(--kai);font-size:40px;color:var(--navy);margin:6px 0 0;letter-spacing:.06em}
.ch-head .rule{height:3px;margin-top:16px;background:linear-gradient(90deg,var(--gold),transparent 75%);border-radius:2px}
.pager{display:flex;justify-content:space-between;margin-top:64px;gap:12px}
.pager a{flex:1;text-align:center;padding:13px 10px;border:1px solid var(--line);border-radius:8px;text-decoration:none;color:var(--ink2);font-size:14.5px;background:#faf4e4}
.pager a:hover{border-color:var(--gold);color:var(--gold2)}
.pager a b{display:block;font-size:12px;color:var(--gold2);letter-spacing:.2em;margin-bottom:3px;font-weight:400}

/* ===== 海之背景（三幕轮换：浪 / 风 / 岸） ===== */
.sea{position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden;
  --sink:#1b2c44;--sink2:#2c5d8a}
body.night .sea{--sink:#d6c9a8;--sink2:#7fa8cc}
.sea .scene{position:absolute;inset:0;opacity:0;animation:sceneCycle 72s ease-in-out infinite}
.sea .s-wave{color:var(--sink)}
.sea .s-wind{color:var(--sink2);animation-delay:24s}
.sea .s-coast{color:var(--sink);animation-delay:48s}
@keyframes sceneCycle{0%{opacity:0}6%{opacity:1}32%{opacity:1}40%{opacity:0}100%{opacity:0}}
.s-wave svg{position:absolute;left:0;width:200%;display:block}
.s-wave .wl1{bottom:13vh;height:34px;fill:none;stroke:currentColor;stroke-width:1.6;opacity:.16;animation:drift 30s linear infinite}
.s-wave .wl2{bottom:8vh;height:40px;fill:none;stroke:currentColor;stroke-width:1.4;opacity:.11;animation:drift 44s linear infinite reverse}
.s-wave .wl3{bottom:2vh;height:52px;fill:currentColor;opacity:.07;animation:drift 20s linear infinite}
@keyframes drift{to{transform:translateX(-50%)}}
.s-wind svg{position:absolute;inset:0;width:100%;height:100%}
.s-wind path{fill:none;stroke:currentColor;stroke-width:1.4;stroke-linecap:round;
  stroke-dasharray:10 18;stroke-opacity:.28;animation:flow 9s linear infinite,breathe 7s ease-in-out infinite}
.s-wind path.wb{animation-delay:1.2s,-2.5s}
.s-wind path.wc{animation-delay:2.4s,-4s}
@keyframes flow{to{stroke-dashoffset:-280}}
@keyframes breathe{0%,100%{opacity:.3}50%{opacity:.7}}
.s-coast svg{position:absolute;bottom:0;left:0;width:100%;height:26vh}
.s-coast .f{fill:currentColor}
.s-coast .st{stroke:currentColor;fill:none;stroke-linecap:round}
/* --- 海鸥 / 云 / 鱼跃 --- */
.gull{position:absolute;opacity:.42;animation:gullFly var(--t,64s) linear infinite;animation-delay:var(--d,0s)}
.gull.rev{animation-name:gullFlyRev}
.gull .bb{display:block;animation:gullBob 3.8s ease-in-out infinite alternate}
.gull svg{display:block;width:100%;color:inherit;animation:flap 1.5s ease-in-out infinite;transform-origin:50% 55%}
.gull svg path{stroke:currentColor}
@keyframes gullFly{from{transform:translateX(106vw)}to{transform:translateX(-10vw)}}
@keyframes gullFlyRev{from{transform:translateX(-10vw) scaleX(-1)}to{transform:translateX(106vw) scaleX(-1)}}
@keyframes gullBob{from{transform:translateY(0)}to{transform:translateY(-11px)}}
@keyframes flap{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.45)}}
.cloud{position:absolute;height:15px;border-radius:999px;background:currentColor;opacity:.07;filter:blur(4px);animation:cloudDrift linear infinite;animation-delay:var(--d,0s)}
.cloud::before{content:"";position:absolute;left:24%;top:-8px;width:44%;height:17px;border-radius:999px;background:inherit}
.cloud.c1{top:13%;width:150px;animation-duration:140s}
.cloud.c2{top:33%;width:96px;opacity:.05;animation-duration:180s}
@keyframes cloudDrift{from{transform:translateX(-24vw)}to{transform:translateX(112vw)}}
.fish{position:absolute;left:56vw;bottom:5vh;width:20px;color:inherit;opacity:0;animation:leap 13s ease-in-out infinite;animation-delay:6s}
@keyframes leap{
  0%,70%{opacity:0;transform:translate(0,0) rotate(0)}
  74%{opacity:.5;transform:translate(2px,-5px) rotate(-26deg)}
  80%{opacity:.55;transform:translate(10px,-15px) rotate(6deg)}
  86%{opacity:.5;transform:translate(18px,-4px) rotate(36deg)}
  90%,100%{opacity:0;transform:translate(20px,2px) rotate(42deg)}
}
/* ===== 封面海平线 ===== */
.horizon{max-width:430px;margin:30px auto 0;opacity:.8}
.horizon svg{width:100%;display:block;color:var(--gold2)}
.horizon .boat{animation:rock 6s ease-in-out infinite;transform-origin:210px 34px}
@keyframes rock{0%,100%{transform:rotate(-2deg)}50%{transform:rotate(2.5deg) translateY(-2px)}}
/* ===== d20 掷骰 ===== */
.dice-btn{position:fixed;right:26px;bottom:26px;width:58px;height:58px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#e8c66a,#b8860b 72%);border:2px solid #8a6508;
  box-shadow:0 6px 20px rgba(184,134,11,.5),inset 0 2px 4px rgba(255,255,255,.4);
  cursor:pointer;z-index:60;display:flex;align-items:center;justify-content:center;
  font-family:var(--kai);font-size:21px;font-weight:bold;color:#3a2a05;transition:transform .15s}
.dice-btn:hover{transform:translateY(-3px) rotate(12deg)}
.dice-btn.rolling{animation:tumble .72s linear}
@keyframes tumble{25%{transform:rotate(90deg) scale(1.08)}55%{transform:rotate(210deg) scale(.92)}85%{transform:rotate(330deg) scale(1.05)}}
.roll-pop{position:fixed;right:98px;bottom:30px;background:var(--navy2);color:#f0e6cb;border:1px solid var(--gold);
  border-radius:12px;padding:12px 20px;box-shadow:var(--shadow);z-index:60;min-width:170px;text-align:center;
  opacity:0;transform:translateY(8px);transition:.25s;pointer-events:none}
.roll-pop.show{opacity:1;transform:translateY(0)}
.roll-pop .num{font-size:34px;font-family:var(--kai);color:var(--gold3);line-height:1.25}
.roll-pop .num.crit{color:#e05a4e}
.roll-pop .num.crit-bad{color:#9db4c9}
.roll-pop .verdict{font-size:12.5px;color:#bfae8a;margin-top:2px}
/* ===== 航海更次 ===== */
.watchbar{margin:10px 14px;padding:9px 12px;border:1px solid rgba(216,169,61,.3);border-radius:8px;
  background:rgba(216,169,61,.07);font-size:12px;line-height:1.65}
.watchbar .wt{font-family:Consolas,"Courier New",var(--kai);color:var(--gold3);font-size:12.5px;letter-spacing:.08em}
.watchbar .wtxt{color:#9db0c5}
/* ===== 内容进场与表格手感 ===== */
#view>.page,#view>.cover{animation:fadeUp .5s ease both}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.tbl tbody tr{transition:background .15s}
.tbl tbody tr:hover{background:rgba(184,134,11,.13)}
.brand svg{transition:transform .2s linear}

/* ===== 航行进度条（帆船随阅读进度） ===== */
.topbar .voyage{position:absolute;left:0;right:0;bottom:-1px;height:14px;pointer-events:none}
.voyage .vline{position:absolute;bottom:2px;left:0;height:2px;width:0;background:linear-gradient(90deg,var(--gold),var(--gold3));border-radius:1px;box-shadow:0 0 6px rgba(216,169,61,.5)}
.voyage .vboat{position:absolute;bottom:5px;left:0;width:17px;height:17px;transform:translateX(-50%);filter:drop-shadow(0 1px 2px rgba(16,29,46,.35))}

/* ===== 滚动浮现 ===== */
.rv{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.rv.on{opacity:1;transform:none}

/* ===== 封面入场编排 ===== */
.cover h1.ct{animation:titleIn 1.15s cubic-bezier(.2,.7,.3,1) both .15s}
@keyframes titleIn{from{opacity:0;letter-spacing:.8em;text-indent:.8em;filter:blur(3px)}to{opacity:1;letter-spacing:.3em;text-indent:.3em;filter:none}}
.loop span,.loop i{animation:popIn .5s cubic-bezier(.3,1.4,.5,1) both;animation-delay:calc(var(--i,0)*.07s + .55s)}
@keyframes popIn{from{opacity:0;transform:scale(.6) translateY(8px)}to{opacity:1;transform:none}}
.volcards .vcard,.frozen .fcard{animation:fadeUp .55s ease both;animation-delay:calc(var(--i,0)*.08s + .4s)}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}

/* ===== 掷骰特效 ===== */
.fx-flash{position:fixed;inset:0;pointer-events:none;z-index:65;opacity:0;background:radial-gradient(circle at 50% 62%,rgba(232,198,106,.55),rgba(232,198,106,.12) 45%,transparent 70%)}
.fx-flash.go{animation:flashFX .8s ease-out}
@keyframes flashFX{0%{opacity:0}16%{opacity:.95}100%{opacity:0}}
body.shake #view{animation:shakeFX .5s ease}
@keyframes shakeFX{12%{transform:translate(-5px,2px)}28%{transform:translate(4px,-3px)}46%{transform:translate(-3px,1px)}64%{transform:translate(3px,2px)}82%{transform:translate(-2px,-1px)}}
.roll-pop .hist{margin-top:7px;padding-top:6px;border-top:1px dashed rgba(216,169,61,.3);font-size:11px;color:#8fa3bd;letter-spacing:.06em}

/* ===== 日落换幕（主题切换过渡） ===== */
.dusk{position:fixed;inset:0;pointer-events:none;z-index:80;opacity:0;background:linear-gradient(180deg,#241436 0%,#7c3f1c 48%,#101d2e 100%)}
.dusk.go{animation:duskFX .95s ease}
@keyframes duskFX{0%{opacity:0}38%{opacity:.85}100%{opacity:0}}

/* ===== 回到桅顶 ===== */
.top-btn{position:fixed;right:32px;bottom:98px;width:46px;height:46px;border-radius:50%;border:1.5px solid var(--gold);
  background:rgba(250,244,228,.92);color:var(--gold2);font-size:19px;cursor:pointer;z-index:60;
  box-shadow:0 4px 14px rgba(16,29,46,.25);opacity:0;pointer-events:none;transform:translateY(10px);transition:.25s;font-family:var(--kai)}
.top-btn.show{opacity:1;pointer-events:auto;transform:none}
.top-btn:hover{background:var(--gold);color:#1c1503}
body.night .top-btn{background:rgba(27,41,64,.92);color:var(--gold3)}
body.night .top-btn:hover{background:var(--gold);color:#1c1503}

/* ===== 侧栏指示 ===== */
nav a.ch{position:relative;transition:background .15s,color .15s,transform .15s}
nav a.ch:hover{transform:translateX(3px)}
nav a.ch::before{content:"";position:absolute;left:-2px;top:22%;bottom:22%;width:3px;border-radius:2px;background:var(--gold3);opacity:0;transition:opacity .18s}
nav a.ch.active::before{opacity:1}
#searchResults .sr{animation:srIn .22s ease both}
@keyframes srIn{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}

/* ===== 减少动效偏好 ===== */
@media (prefers-reduced-motion: reduce){
  .sea,.dusk,.fx-flash,.gull,.fish,.cloud{display:none !important}
  .rv{opacity:1;transform:none;transition:none}
  *,*::before,*::after{animation-duration:.01ms !important;animation-iteration-count:1 !important;transition-duration:.01ms !important}
}

/* ===== 手机端适配 ===== */
@media (hover:none){
  .wiki{border-bottom-width:2px}
}
@media (max-width:640px){
  .topbar{padding:9px 14px}
  .topbar .crumb{font-size:14.5px}
  .hamb,.theme{width:40px;height:40px}
  nav a.ch{padding:10px 12px}
  .brand{padding:16px 14px 12px}
  .brand svg{width:54px;height:54px}
  .brand h1{font-size:22px}
  aside{width:min(84vw,300px)}
  .page{padding:28px 18px 96px}
  .ch-head h1{font-size:29px}
  .page h2{font-size:21.5px;margin-top:36px}
  .page h3{font-size:18.5px}
  .cover{padding:34px 14px 64px}
  .cover .compass{width:100px;height:100px}
  .cover h1{font-size:46px}
  .cover .epigraph{font-size:13.5px}
  .horizon{max-width:290px}
  .loop span{padding:5px 10px;font-size:12px}
  .loop i{font-size:12px}
  .volcards{grid-template-columns:1fr}
  .frozen{grid-template-columns:1fr 1fr}
  .pager{flex-direction:column}
  .dice-btn{right:calc(14px + env(safe-area-inset-right,0px));bottom:calc(14px + env(safe-area-inset-bottom,0px));width:52px;height:52px;font-size:18px}
  .top-btn{right:calc(19px + env(safe-area-inset-right,0px));bottom:calc(84px + env(safe-area-inset-bottom,0px));width:42px;height:42px}
  .roll-pop{left:12px;right:12px;bottom:calc(76px + env(safe-area-inset-bottom,0px));min-width:0}
  .gloss-pop{max-width:calc(100vw - 20px)}
  .watchbar{margin:8px 10px}
  .s-coast svg{height:18vh}
}
@media (max-width:420px){
  .frozen{grid-template-columns:1fr}
  .cover h1{font-size:38px}
  .cover .tagline{font-size:14px}
}

/* ===== Wiki 术语悬浮 ===== */
.wiki{border-bottom:1.5px dashed var(--gold);cursor:help;text-decoration:none;color:inherit;padding-bottom:1px;transition:background .15s,color .15s}
.wiki:hover{color:var(--gold2);background:rgba(184,134,11,.1)}
.gloss-pop{position:fixed;z-index:70;max-width:330px;background:#faf4e4;border:1px solid var(--gold);border-top:3px solid var(--gold);border-radius:10px;box-shadow:0 10px 34px rgba(16,29,46,.3);padding:11px 15px 12px;font-size:13.5px;line-height:1.8;color:var(--ink);opacity:0;transform:translateY(6px);transition:opacity .18s,transform .18s;pointer-events:none}
.gloss-pop.show{opacity:1;transform:none;pointer-events:auto}
.gloss-pop .gt{font-family:var(--kai);color:var(--gold2);font-size:15.5px;margin-bottom:3px;display:flex;align-items:center;gap:6px}
.gloss-pop .gt::before{content:"⚓";font-size:12px;opacity:.7}
.gloss-pop .gd p{margin:0}
body.night .gloss-pop{background:#1b2940;color:#d6c9a8}
body.night .gloss-pop .gt{color:var(--gold3)}

/* 夜航模式 */
body.night{--paper:#141f30;--paper2:#1b2940;--paper3:#22334e;--ink:#d6c9a8;--ink2:#a89877;--line:rgba(214,201,168,.22);--navy:#0b1420;--navy2:#16233a;--gold:#c69c3a;--gold2:#d8a93d;--blue:#7fa8cc}
body.night main{background-image:radial-gradient(120% 90% at 50% 38%,transparent 55%,rgba(0,0,0,.32)),
  url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)' opacity='0.07'/%3E%3C/svg%3E"),
  radial-gradient(ellipse at 50% -10%,rgba(60,90,140,.25),transparent 60%),
  repeating-linear-gradient(0deg,transparent 0 34px,rgba(214,201,168,.03) 34px 35px)}
body.night .page h2,body.night .page h3,body.night .cover h1,body.night .ch-head h1,body.night .vcard h3{color:#e9dfc6}
body.night .page strong{color:#f0e6cb}
body.night .tbl table,body.night .vcard,body.night .pager a{background:#1b2940}
body.night code{background:rgba(198,156,58,.15);color:#e0bd6a;border-color:rgba(198,156,58,.3)}
body.night blockquote{background:var(--paper2)}
body.night blockquote.aside-voice{color:#c4b591}
body.night .cover .epigraph,body.night .cover .en-title{color:#a89877}
::selection{background:rgba(184,134,11,.35)}
aside::-webkit-scrollbar{width:10px}
aside::-webkit-scrollbar-thumb{background:#2e4262;border-radius:5px}
html{scrollbar-width:thin;scrollbar-color:rgba(90,74,51,.35) var(--paper2)}
html::-webkit-scrollbar{width:11px}
html::-webkit-scrollbar-track{background:var(--paper2)}
html::-webkit-scrollbar-thumb{background:rgba(90,74,51,.32);border-radius:6px;border:3px solid var(--paper2)}
html::-webkit-scrollbar-thumb:hover{background:rgba(90,74,51,.5)}
html:has(body.night){scrollbar-width:thin;scrollbar-color:rgba(214,201,168,.3) #141f30}
html:has(body.night)::-webkit-scrollbar-track{background:#141f30}
html:has(body.night)::-webkit-scrollbar-thumb{background:rgba(214,201,168,.28);border-color:#141f30}
@media print{aside,.topbar,.pager{display:none}main{margin:0}}
</style>
</head>
<body>
<div class="app">
<aside id="sidebar">
  <div class="brand">
    <svg viewBox="0 0 100 100" fill="none">
      <circle cx="50" cy="50" r="46" stroke="#d8a93d" stroke-width="1.6" opacity=".8"/>
      <circle cx="50" cy="50" r="38" stroke="#8fa3bd" stroke-width=".8" stroke-dasharray="2 4" opacity=".7"/>
      <path d="M50 6 L56 44 L94 50 L56 56 L50 94 L44 56 L6 50 L44 44 Z" fill="#d8a93d" opacity=".9"/>
      <path d="M50 22 L53.5 46.5 L78 50 L53.5 53.5 L50 78 L46.5 53.5 L22 50 L46.5 46.5 Z" fill="#f3ead6" opacity=".25"/>
      <circle cx="50" cy="50" r="4.5" fill="#8c2f39"/>
      <text x="50" y="17" text-anchor="middle" fill="#d8a93d" font-size="9" font-family="serif">N</text>
    </svg>
    <h1>燃帆</h1>
    <div class="en">The Age of Burning Sail</div>
  </div>
  <div class="searchbox"><input id="searchBox" type="search" placeholder="搜索规则全文…（如：潮汐点）"></div>
  <div id="searchResults"></div>
  <nav id="toc"></nav>
  <div class="watchbar" id="watchBar"></div>
  <div class="side-foot" id="buildStamp"></div>
</aside>
<main>
  <div class="topbar">
    <button class="hamb" id="hamb" title="目录" aria-label="打开目录"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="18" height="18"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>
    <div class="crumb" id="crumb">燃帆</div>
    <button class="theme" id="themeBtn" title="夜航模式" aria-label="切换夜航模式"></button>
    <div class="voyage" aria-hidden="true"><div class="vline" id="vLine"></div><svg class="vboat" id="vBoat" viewBox="0 0 20 20"><path d="M10 1.5 L10 13" stroke="#8a6508" stroke-width="1.4"/><path d="M9.5 3 L9.5 11.5 L3.5 11.5 Z" fill="#b8860b"/><path d="M11 5 L11 11.5 L16.5 11.5 Z" fill="#d8a93d"/><path d="M4 14.5 Q10 17.5 16 14.5 L14.2 16.8 L5.8 16.8 Z" fill="#8a6508"/></svg></div>
  </div>
  <div class="sea" aria-hidden="true">
    <div class="stars"><i style="top:6%;left:12%;--t:2.8s;--d:-.4s"></i><i class="big" style="top:11%;left:34%;--t:4.2s;--d:-1.6s"></i><i style="top:5%;left:57%;--t:3.1s;--d:-2.2s"></i><i style="top:15%;left:74%;--t:2.6s;--d:-1s"></i><i class="big" style="top:8%;left:88%;--t:3.8s;--d:-3s"></i><i style="top:22%;left:6%;--t:3.4s;--d:-2.8s"></i><i style="top:26%;left:47%;--t:2.9s;--d:-.8s"></i><i style="top:19%;left:63%;--t:4.6s;--d:-2s"></i><i style="top:31%;left:23%;--t:3.6s;--d:-3.4s"></i><i class="big" style="top:29%;left:82%;--t:3s;--d:-1.3s"></i></div>
    <div class="scene s-wave">
      <div class="gull" style="top:9%;width:13px;--t:105s;--d:-40s"><span class="bb"><svg viewBox="0 0 24 10"><path d="M1 8 Q6 1 12 7 Q18 1 23 8" fill="none" stroke-width="1.5" stroke-linecap="round"/></svg></span></div>
      <svg class="wl1" viewBox="0 0 1200 60" preserveAspectRatio="none"><path d="M0 30 Q30 12 60 30 T120 30 T180 30 T240 30 T300 30 T360 30 T420 30 T480 30 T540 30 T600 30 T660 30 T720 30 T780 30 T840 30 T900 30 T960 30 T1020 30 T1080 30 T1140 30 T1200 30"/></svg>
      <svg class="wl2" viewBox="0 0 1200 60" preserveAspectRatio="none"><path d="M0 28 Q30 46 60 28 T120 28 T180 28 T240 28 T300 28 T360 28 T420 28 T480 28 T540 28 T600 28 T660 28 T720 28 T780 28 T840 28 T900 28 T960 28 T1020 28 T1080 28 T1140 28 T1200 28"/></svg>
      <svg class="wl3" viewBox="0 0 1200 60" preserveAspectRatio="none"><path d="M0 34 Q30 8 60 34 T120 34 T180 34 T240 34 T300 34 T360 34 T420 34 T480 34 T540 34 T600 34 T660 34 T720 34 T780 34 T840 34 T900 34 T960 34 T1020 34 T1080 34 T1140 34 T1200 34 L1200 60 L0 60 Z"/></svg>
    </div>
    <div class="scene s-wind">
      <div class="cloud c1"></div>
      <div class="cloud c2"></div>
      <div class="gull" style="top:19%;width:24px;--t:58s;--d:-12s"><span class="bb"><svg viewBox="0 0 24 10"><path d="M1 8 Q6 1 12 7 Q18 1 23 8" fill="none" stroke-width="1.6" stroke-linecap="round"/></svg></span></div>
      <div class="gull" style="top:30%;width:17px;--t:76s;--d:-38s"><span class="bb" style="animation-delay:-1.2s"><svg viewBox="0 0 24 10"><path d="M1 8 Q6 1 12 7 Q18 1 23 8" fill="none" stroke-width="1.5" stroke-linecap="round"/></svg></span></div>
      <div class="gull rev" style="top:44%;width:14px;--t:88s;--d:-55s"><span class="bb" style="animation-delay:-2.4s"><svg viewBox="0 0 24 10"><path d="M1 8 Q6 1 12 7 Q18 1 23 8" fill="none" stroke-width="1.5" stroke-linecap="round"/></svg></span></div>
      <svg viewBox="0 0 1200 400" preserveAspectRatio="none">
        <path d="M-60 110 Q 250 55 600 105 T 1260 85"/>
        <path class="wb" d="M-60 235 Q 300 170 700 225 T 1260 200"/>
        <path class="wc" d="M-60 330 Q 350 285 800 320 T 1260 295"/>
      </svg>
      <div class="fish"><svg viewBox="0 0 22 12"><path d="M2 6 Q9 1 14 6 Q16 8 19 7 L17 10 Q11 12 7 9 Q4 8 2 6 Z" fill="currentColor"/></svg></div>
    </div>
    <div class="scene s-coast">
      <div class="gull" style="top:12%;width:19px;--t:70s;--d:-25s"><span class="bb"><svg viewBox="0 0 24 10"><path d="M1 8 Q6 1 12 7 Q18 1 23 8" fill="none" stroke-width="1.6" stroke-linecap="round"/></svg></span></div>
      <svg viewBox="0 0 1200 220" preserveAspectRatio="xMidYMax slice">
        <ellipse class="f" cx="180" cy="178" rx="120" ry="13" opacity=".28"/>
        <g class="f" opacity=".4" transform="translate(700,158)">
          <path d="M0 12 Q12 19 26 12 L21 19 L5 19 Z"/>
          <path d="M12 -20 L12 11 L1 11 Z"/>
          <path d="M15 -11 L15 11 L24 11 Z"/>
        </g>
        <path class="f" opacity=".7" d="M0 220 L0 170 Q160 142 300 164 T620 154 Q760 138 900 166 T1200 160 L1200 220 Z"/>
        <g transform="translate(298,146)" opacity=".8">
          <path class="st" stroke-width="3" d="M0 24 Q-2 10 2 -4"/>
          <path class="st" stroke-width="2" d="M2 -4 Q-12 -13 -22 -7"/>
          <path class="st" stroke-width="2" d="M2 -4 Q15 -15 26 -9"/>
          <path class="st" stroke-width="2" d="M2 -4 Q-5 -19 -15 -17"/>
          <path class="st" stroke-width="2" d="M2 -4 Q11 -19 20 -15"/>
        </g>
        <g transform="translate(906,120)" opacity=".85">
          <path class="f" d="M-7 46 L-4 2 L4 2 L7 46 Z"/>
          <rect class="f" x="-6" y="-7" width="12" height="8"/>
          <circle cx="0" cy="-3" r="2.6" fill="#e8c66a"/>
          <path class="st" stroke-width="1.2" opacity=".5" d="M-9 -3 L-48 -10"/>
          <path class="st" stroke-width="1.2" opacity=".5" d="M9 -3 L48 -10"/>
        </g>
      </svg>
    </div>
  </div>
  <div id="view"></div>
</main>
<div class="dice-btn" id="diceBtn" title="掷一枚d20（也可打开 #d20 自动掷）" role="button" tabindex="0" aria-label="掷一枚二十面骰">d20</div>
<div class="roll-pop" id="rollPop"><div class="num" id="rollNum">–</div><div class="verdict" id="rollVerdict"></div><div class="hist" id="rollHist">首掷尚未开始</div></div>
<div class="fx-flash" id="fxFlash" aria-hidden="true"></div>
<div class="dusk" id="duskFx" aria-hidden="true"></div>
<button class="top-btn" id="topBtn" title="回到桅顶" aria-label="回到页面顶部"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="19" height="19"><circle cx="12" cy="5" r="3"/><path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/></svg></button>
</div>
<script id="book-data" type="application/json">__CHAPTERS_JSON__</script>
<script id="gloss-data" type="application/json">__GLOSS_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('book-data').textContent);
const $ = s => document.querySelector(s);
const VOLS = [...new Set(DATA.map(c=>c.vol))];

/* ---------- 侧栏 ---------- */
function buildToc(){
  let h = '';
  VOLS.forEach(v=>{
    const chs = DATA.filter(c=>c.vol===v);
    h += `<div class="vol">${v}</div>`;
    chs.forEach(c=>{
      h += `<a class="ch ${c.skeleton?'skel':''}" href="#ch${c.num}" data-num="${c.num}">
        <span class="no">${c.num}</span><span>${c.title}</span>
        <span class="st ${c.skeleton?'skel':'full'}" title="${c.skeleton?'骨架':'完整'}"></span></a>`;
    });
  });
  $('#toc').innerHTML = h;
}

/* ---------- 封面 ---------- */
function coverHTML(){
  const loop = ['① 立目标','② 航行','③ 遭遇','④ 收获','⑤ 回港'];
  const loopHTML = loop.map((s,i)=>(i?`<i style="--i:${i*2-1}">⇢</i>`:'')+`<span style="--i:${i*2}">${s}</span>`).join('') + '<i style="--i:10">⟲</i>';
  const frozen = [
    ['核心判定','d20 + 属性 + 技能 ≥ DV'],
    ['难度阶梯','10 / 13 / 16 / 19 / 22'],
    ['生命值','HP = 6 + 筋骨×2'],
    ['命运资源','潮汐点 3（天赋上限 4）'],
    ['炮击齐射','DV 14 · 3d6 船体 · 装填 2 轮'],
    ['时间尺度','一昼夜 6 航段 · 海战轮 1 分钟'],
  ];
  const volcards = VOLS.map((v,idx)=>{
    const chs = DATA.filter(c=>c.vol===v);
    return `<div class="vcard" style="--i:${idx}"><h3>${v}</h3>` + chs.map(c=>
      `<a href="#ch${c.num}"><span>${c.num} · ${c.title}</span>
       <span class="badge ${c.skeleton?'skel':'full'}">${c.skeleton?'骨架':'完整'}</span></a>`).join('') + '</div>';
  }).join('');
  return `<div class="cover">
    <div class="cover-frame" aria-hidden="true"></div>
    <svg class="compass" viewBox="0 0 100 100" fill="none">
      <circle cx="50" cy="50" r="46" stroke="#b8860b" stroke-width="1.4"/>
      <circle cx="50" cy="50" r="38" stroke="#b8860b" stroke-width=".7" stroke-dasharray="2 4"/>
      <path d="M50 6 L56 44 L94 50 L56 56 L50 94 L44 56 L6 50 L44 44 Z" fill="#b8860b" opacity=".85"/>
      <path d="M50 22 L53.5 46.5 L78 50 L53.5 53.5 L50 78 L46.5 53.5 L22 50 L46.5 46.5 Z" fill="#f3ead6" opacity=".3"/>
      <circle cx="50" cy="50" r="4.5" fill="#8c2f39"/>
    </svg>
    <div class="kick">大航海时代 · 角色扮演游戏</div>
    <h1 class="ct">燃 帆</h1>
    <div class="en-title">The Age of Burning Sail</div>
    <div class="tagline">冒险 · 海战 · 探索 —— 一艘船，一片没画完的海图</div>
    <div class="epigraph">桅杆在燃烧，罗盘在颤抖。地平线之外，是黄金、风暴，和从未被画进海图的东西。</div>
    <div class="horizon" aria-hidden="true"><svg viewBox="0 0 420 56">
      <line x1="0" y1="40" x2="420" y2="40" stroke="currentColor" stroke-width="1.2" opacity=".5"/>
      <path d="M0 40 Q 26 36 52 40 T 104 40 T 156 40 T 260 40 T 312 40 T 364 40 T 420 40" stroke="currentColor" fill="none" stroke-width="1" opacity=".35"/>
      <g class="boat">
        <path d="M196 36 Q208 42 224 36 L218 42 L202 42 Z" fill="currentColor"/>
        <path d="M209 8 L209 34 L196 34 Z" fill="currentColor" opacity=".85"/>
        <path d="M212 15 L212 34 L224 34 Z" fill="currentColor" opacity=".6"/>
        <path d="M209 8 L209 3 L216 5 Z" fill="#8c2f39"/>
      </g>
    </svg></div>
    <svg class="wave" width="360" height="18" viewBox="0 0 360 18"><path d="M0 9 Q15 0 30 9 T60 9 T90 9 T120 9 T150 9 T180 9 T210 9 T240 9 T270 9 T300 9 T330 9 T360 9" stroke="#b8860b" fill="none" stroke-width="1.6"/></svg>
    <div class="loop">${loopHTML}</div>
    <h2 class="sec-title"><span class="line"></span>全书结构<span class="line"></span></h2>
    <div style="color:var(--ink2);font-size:13.5px">金点 = 完整成稿 · 空点 = 骨架撰写中</div>
    <div class="volcards">${volcards}</div>
    <h2 class="sec-title"><span class="line"></span>已冻结的核心口径<span class="line"></span></h2>
    <div class="frozen">${frozen.map((f,i)=>`<div class="fcard" style="--i:${i}"><div class="k">${f[0]}</div><div class="v">${f[1]}</div></div>`).join('')}</div>
    <a class="cta" href="#ch02">✦ 二十分钟快速开始</a>
  </div>`;
}

/* ---------- 章节渲染 ---------- */
function chapterHTML(c, prev, next){
  return `<div class="page">
    <div class="ch-head">
      <div class="kicker">${c.vol} · 第 ${c.num} 章 ${c.skeleton?'· 撰写中（骨架）':''}</div>
      <h1>${c.title}</h1><div class="rule"></div>
    </div>
    ${c.html}
    <div class="pager">
      ${prev?`<a href="#ch${prev.num}"><b>◀ 上一章</b>${prev.title}</a>`:'<a href="#cover"><b>◀ 返回</b>封面</a>'}
      ${next?`<a href="#ch${next.num}"><b>下一章 ▶</b>${next.title}</a>`:'<a href="#cover"><b>返回</b>封面 ⚓</a>'}
    </div></div>`;
}

/* ---------- 路由 ---------- */
function navigate(){
  const h = location.hash.replace('#','');
  const view = $('#view');
  let crumb = '燃帆', cur = null;
  if(h && h.startsWith('ch')){
    const num = h.slice(2);
    const i = DATA.findIndex(c=>c.num===num);
    if(i>=0){
      cur = DATA[i];
      view.innerHTML = chapterHTML(cur, DATA[i-1], DATA[i+1]);
      crumb = `第 ${cur.num} 章 · <b>${cur.title}</b>`;
    }
  }
  if(!cur){ view.innerHTML = coverHTML(); crumb = '燃帆 · <b>卷首</b>'; }
  $('#crumb').innerHTML = crumb;
  wikify(view);
  if(cur) reveal(view);
  document.querySelectorAll('#toc a.ch').forEach(a=>a.classList.toggle('active', !!cur && a.dataset.num===cur.num));
  document.body.classList.remove('side-open');
  window.scrollTo({top:0});
}

/* ---------- 搜索 ---------- */
const escHTML = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
$('#searchBox').addEventListener('input', e=>{
  const q = e.target.value.trim();
  const box = $('#searchResults');
  if(q.length<1){ box.innerHTML=''; return; }
  const hits = [];
  DATA.forEach(c=>{
    const idx = c.text.indexOf(q);
    if(idx>=0){
      const s = Math.max(0, idx-18);
      const frag = (s>0?'…':'') + escHTML(c.text.slice(s, idx+q.length+34)) + '…';
      hits.push(`<a class="sr" href="#ch${c.num}">
        ${c.num} · ${escHTML(c.title)}
        <span class="frag">${frag.split(q).join(`<b>${q}</b>`)}</span></a>`);
    }
  });
  box.innerHTML = hits.length ? hits.slice(0,8).join('') : '<span class="sr">海图上没有这片水域…（无结果）</span>';
});

/* ---------- 主题 / 移动端 ---------- */
const ICON_MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="17" height="17"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
const ICON_SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="17" height="17"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4"/></svg>';
function applyTheme(t, silent){
  document.body.classList.toggle('night', t==='night');
  $('#themeBtn').innerHTML = t==='night' ? ICON_SUN : ICON_MOON;
  localStorage.setItem('bf-theme', t);
  if(!silent){ const d = $('#duskFx'); d.classList.remove('go'); void d.offsetWidth; d.classList.add('go'); }
}
$('#themeBtn').onclick = ()=> applyTheme(document.body.classList.contains('night')?'day':'night');
$('#hamb').onclick = ()=> document.body.classList.toggle('side-open');
document.addEventListener('click', e=>{ if(document.body.classList.contains('side-open') && !e.target.closest('aside') && !e.target.closest('#hamb')) document.body.classList.remove('side-open'); });
applyTheme(localStorage.getItem('bf-theme') || (matchMedia('(prefers-color-scheme: dark)').matches?'night':'day'), true);
window.addEventListener('hashchange', navigate);
/* ---------- 风味：d20 掷骰 ---------- */
const diceBtn = $('#diceBtn'), rollPop = $('#rollPop'), rollNum = $('#rollNum'), rollVerdict = $('#rollVerdict');
const rollHist = $('#rollHist'), fxFlash = $('#fxFlash');
const HIST = [];
let rollTick = null, rollHide = null;
diceBtn.onclick = () => {
  diceBtn.classList.add('rolling');
  rollPop.classList.add('show');
  clearInterval(rollTick); clearTimeout(rollHide);
  rollTick = setInterval(()=>{ rollNum.textContent = 1 + Math.floor(Math.random()*20); rollNum.className = 'num'; }, 70);
  setTimeout(()=>{
    clearInterval(rollTick);
    const r = 1 + Math.floor(Math.random()*20);
    rollNum.textContent = r;
    rollNum.className = 'num' + (r===20 ? ' crit' : r===1 ? ' crit-bad' : '');
    let v;
    if(r===20){
      v = '自然20 —— 大成功！海神在微笑';
      fxFlash.classList.remove('go'); void fxFlash.offsetWidth; fxFlash.classList.add('go');
    }else if(r===1){
      v = '自然1 —— 大失败…愿海神怜悯';
      document.body.classList.remove('shake'); void document.body.offsetWidth; document.body.classList.add('shake');
    }else{
      const LADDER = [[22,'传奇'],[19,'极难'],[16,'困难'],[13,'普通'],[10,'简单']];
      const hit = LADDER.find(x=> r>=x[0]);
      v = hit ? `可成事于「${hit[1]}（DV ${hit[0]}）」` : '连最简单的缆结也没系上';
    }
    rollVerdict.textContent = v;
    HIST.unshift(r); if(HIST.length > 7) HIST.pop();
    rollHist.textContent = '最近掷骰：' + HIST.join(' · ');
    diceBtn.classList.remove('rolling');
    rollHide = setTimeout(()=> rollPop.classList.remove('show'), 9000);
  }, 740);
};

diceBtn.addEventListener('keydown', e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); diceBtn.onclick(); }});
if(location.hash === '#d20') setTimeout(()=> diceBtn.onclick(), 500);

/* ---------- 风味：航海更次（一昼夜六段） ---------- */
const WATCHES = [
  [3,'晨更 · Morning Watch','东方泛白，新的一天从淡水与硬饼开始。'],
  [7,'午前更 · Forenoon Watch','日头爬高，甲板晒出盐霜的味道。'],
  [11,'午后更 · Afternoon Watch','最困倦的时辰，故事与谣言在甲板流传。'],
  [15,'黄昏更 · Dog Watch','落日把帆染成金色——也许只是火烧云。'],
  [19,'头更 · First Watch','夜色接管海面，值更的水手裹紧外套。'],
  [23,'中更 · Middle Watch','半船人睡着，海浪替他们数更。'],
];
function renderWatch(){
  const h = new Date().getHours();
  let w = WATCHES[WATCHES.length-1];
  for(const x of WATCHES){ if(h >= x[0]) w = x; }
  const end = String((w[0]+4)%24).padStart(2,'0');
  $('#watchBar').innerHTML = `<div class="wt">✦ ${w[1]}（${String(w[0]).padStart(2,'0')}:00–${end}:00）</div><div class="wtxt">${w[2]}</div>`;
}
renderWatch(); setInterval(renderWatch, 60000);

/* ---------- 风味：搜索框提示轮换 ---------- */
const HINTS = ['潮汐点','接舷','坏血病','私掠许可证','哗变','克拉肯','航段','声望'];
let hintI = 0;
setInterval(()=>{ $('#searchBox').placeholder = '搜索规则全文…（如：' + HINTS[hintI++ % HINTS.length] + '）'; }, 4000);

/* ---------- 风味：航行进度 / 罗盘 / 回桅顶（统一滚动处理） ---------- */
const brandSvg = document.querySelector('.brand svg');
const vLine = $('#vLine'), vBoat = $('#vBoat'), topBtn = $('#topBtn');
let scrollTick = false;
function onScroll(){
  const st = window.scrollY;
  const max = document.documentElement.scrollHeight - innerHeight;
  const p = max > 0 ? Math.min(1, st / max) : 0;
  vLine.style.width = (p * 100) + '%';
  vBoat.style.left = 'calc(' + (p * 100) + '%)';
  topBtn.classList.toggle('show', st > 600);
  brandSvg.style.transform = 'rotate(' + (st * 0.03 % 360) + 'deg)';
}
window.addEventListener('scroll', ()=>{
  if(scrollTick) return;
  scrollTick = true;
  requestAnimationFrame(()=>{ onScroll(); scrollTick = false; });
}, {passive:true});
topBtn.onclick = ()=> window.scrollTo({top:0, behavior:'smooth'});
onScroll();

/* ---------- 滚动浮现（章节元素进入视口一次性淡入） ---------- */
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const rvIO = (!REDUCED && 'IntersectionObserver' in window)
  ? new IntersectionObserver(es=>es.forEach(en=>{
      if(en.isIntersecting){ en.target.classList.add('on'); rvIO.unobserve(en.target); }
    }), {threshold:.06, rootMargin:'0px 0px -4% 0px'})
  : null;
function reveal(root){
  if(!rvIO || !root) return;
  root.querySelectorAll('h2,h3,blockquote,.tbl').forEach(el=>{
    el.classList.add('rv');
    rvIO.observe(el);
  });
}

/* ---------- 键盘：←/→ 翻章，Esc 收起 ---------- */
document.addEventListener('keydown', e=>{
  if(e.target.matches('input,textarea')){
    if(e.key === 'Escape') e.target.blur();
    return;
  }
  if(e.key === 'Escape'){
    glossHide(); rollPop.classList.remove('show');
    document.body.classList.remove('side-open');
  }
  if(e.key === 'ArrowRight' || e.key === 'ArrowLeft'){
    const h = location.hash.replace('#','');
    let i = h.startsWith('ch') ? DATA.findIndex(c=>c.num === h.slice(2)) : -1;
    i = e.key === 'ArrowRight' ? i + 1 : i - 1;
    if(i < -1) i = -1;
    if(i >= DATA.length) i = DATA.length - 1;
    location.hash = i < 0 ? '#cover' : 'ch' + DATA[i].num;
  }
});

/* ---------- Wiki 术语悬浮索引 ---------- */
const GLOSS = JSON.parse(document.getElementById('gloss-data').textContent);
const GLOSS_KEYS = Object.keys(GLOSS).sort((a,b)=>b.length-a.length);
const GLOSS_RX = GLOSS_KEYS.length
  ? new RegExp('(' + GLOSS_KEYS.map(k=>k.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&')).join('|') + ')','g')
  : null;
const glossPop = document.createElement('div');
glossPop.className = 'gloss-pop';
document.body.appendChild(glossPop);
let glossEnterT = null, glossHideT = null, glossCur = null;

function glossShow(term, el){
  const g = GLOSS[term]; if(!g) return;
  glossPop.innerHTML = `<div class="gt">${term}</div><div class="gd">${g}</div>`;
  glossPop.style.visibility = 'hidden';
  glossPop.classList.add('show');
  const r = el.getBoundingClientRect(), vw = innerWidth, pw = glossPop.offsetWidth;
  let x = Math.max(10, Math.min(r.left + r.width/2 - pw/2, vw - pw - 10));
  let y = r.top - glossPop.offsetHeight - 10;
  if(y < 66) y = r.bottom + 10;
  glossPop.style.left = x + 'px';
  glossPop.style.top = y + 'px';
  glossPop.style.visibility = '';
  glossCur = term;
}
function glossHide(){ glossPop.classList.remove('show'); glossCur = null; }

/* 把章节正文里的术语包成 .wiki 标记；同一章内每个术语只标首次出现 */
function wikify(root){
  if(!GLOSS_RX || !root) return;
  const seen = new Set();
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(n){
      const p = n.parentElement;
      return (p && !p.closest('code,pre,.wiki,h1,h2,h3,h4,button,label')) ? NodeFilter.ACCEPT : NodeFilter.REJECT;
    }
  });
  const texts = [];
  while(walker.nextNode()) texts.push(walker.currentNode);
  texts.forEach(node=>{
    const t = node.nodeValue;
    GLOSS_RX.lastIndex = 0;
    if(!GLOSS_RX.test(t)) return;
    GLOSS_RX.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let last = 0, m, changed = false;
    while((m = GLOSS_RX.exec(t))){
      const term = m[0];
      if(seen.has(term)) continue;
      seen.add(term); changed = true;
      if(m.index > last) frag.appendChild(document.createTextNode(t.slice(last, m.index)));
      const s = document.createElement('span');
      s.className = 'wiki'; s.dataset.term = term; s.textContent = term;
      frag.appendChild(s);
      last = m.index + term.length;
    }
    if(changed){
      if(last < t.length) frag.appendChild(document.createTextNode(t.slice(last)));
      node.parentNode.replaceChild(frag, node);
    }
  });
}

/* 悬停约0.35秒弹出释义；移开稍候关闭；弹窗自身可悬停；点击立即开合（触屏友好） */
document.addEventListener('mouseover', e=>{
  const w = e.target.closest('.wiki');
  if(!w) return;
  clearTimeout(glossHideT); clearTimeout(glossEnterT);
  if(glossCur !== w.dataset.term) glossEnterT = setTimeout(()=> glossShow(w.dataset.term, w), 350);
});
document.addEventListener('mouseout', e=>{
  if(e.target.closest('.wiki')){
    clearTimeout(glossEnterT);
    glossHideT = setTimeout(glossHide, 220);
  }
});
glossPop.addEventListener('mouseenter', ()=> clearTimeout(glossHideT));
glossPop.addEventListener('mouseleave', ()=>{ glossHideT = setTimeout(glossHide, 220); });
document.addEventListener('click', e=>{
  const w = e.target.closest('.wiki');
  if(w){ clearTimeout(glossEnterT); clearTimeout(glossHideT); glossShow(w.dataset.term, w); return; }
  if(!e.target.closest('.gloss-pop')) glossHide();
});
addEventListener('scroll', glossHide, {passive:true});
addEventListener('resize', glossHide);

buildToc(); navigate();
</script>
</body>
</html>
"""

def main():
    chapters = build_chapters()
    glossary = parse_glossary(GLOSS_FILE) if GLOSS_FILE.exists() else {}
    data_json = json.dumps(chapters, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    gloss_json = json.dumps(glossary, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = TEMPLATE.replace("__CHAPTERS_JSON__", data_json).replace("__GLOSS_JSON__", gloss_json)
    stamp = "海图勘定于 " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + f" · 全书 {len(chapters)} 章"
    page = page.replace('id="buildStamp"></div>', 'id="buildStamp">' + stamp + "</div>")
    OUT_PATH.write_text(page, encoding="utf-8")
    full = sum(1 for c in chapters if not c["skeleton"])
    print(f"OK 生成 {OUT_PATH}")
    print(f"  共 {len(chapters)} 章：完整 {full} / 骨架 {len(chapters)-full}，文件大小 {len(page)//1024} KB")

if __name__ == "__main__":
    main()
