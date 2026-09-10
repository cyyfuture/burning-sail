# -*- coding: utf-8 -*-
"""
build_site_v1.py —— v1 世界引擎可视化站点（单文件离线 index.html）。
复用根目录 build_site.py 的整套视觉模板（CSS/JS/海景/夜航/d20），只替换：
  章节数据（v1 分册 md）、封面文案、冻结口径卡、搜索提示、构建印记。
用法：python build_site_v1.py
"""
import re
import sys
import datetime
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT_PATH = (BASE_DIR / "index.html").resolve()
if OUT_PATH.parent != BASE_DIR:
    raise SystemExit("输出路径越界，已阻止")

sys.path.insert(0, str(BASE_DIR.parent))
import build_site as bs  # noqa: E402  （复用 render_md / plain_text / parse_glossary / TEMPLATE）

VOLS_V1 = [
    ("引擎卷首", ["RM"]),
    ("卷一 · 纪 · 经济 · 人口", ["00", "01", "02", "03", "04", "05"]),
    ("卷二 · 船 · 时 · 海 · 商", ["06", "07", "08", "09"]),
    ("卷三 · 任务世界", ["10", "11", "12"]),
    ("试航包", ["TP"]),
]

ENGINE_MARKER = re.compile(r"(?m)^\s*<!--\s*/?ENGINE:.*?-->\s*$\n?")


def _short_title(t):
    t = re.sub(r"^\d{2}\s*", "", t)          # 去 "00 " 前缀
    if "——" in t:
        t = t.split("——", 1)[0].strip()       # 去副标题
    return t


def build_chapters():
    items = [(BASE_DIR / "README.md", "RM")] + [
        (p, p.name[:2]) for p in sorted(BASE_DIR.glob("[0-9]*.md"))
    ] + [(BASE_DIR / "试航包" / "试航包.md", "TP")]
    chapters = []
    for path, num in items:
        raw = path.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+)$", raw, re.M)
        title = _short_title(m.group(1).strip() if m else path.stem)
        body = re.sub(r"^#[^\n]*\n", "", raw, count=1)
        body = ENGINE_MARKER.sub("", body)   # 去掉引擎注入标记（内容保留）
        chapters.append({
            "num": num,
            "title": title,
            "vol": next(v for v, nums in VOLS_V1 if num in nums),
            "skeleton": False,
            "html": bs.render_md(body),
            "text": "",
        })
    for c in chapters:
        c["text"] = bs.plain_text(c["html"])
    return chapters


def customize(page):
    """替换模板中 v1 专属文案；每处断言恰好命中一次。"""
    subs = [
        # 标题与品牌
        ("<title>燃帆 · The Age of Burning Sail — 规则书</title>",
         "<title>燃帆 · v1 世界引擎 — 五纪数据分册</title>"),
        ("The Age of Burning Sail", "The World Engine · v1"),
        # 封面
        ('<div class="kick">大航海时代 · 角色扮演游戏</div>',
         '<div class="kick">五纪世界引擎 · 1350 – 1780</div>'),
        ('<div class="tagline">冒险 · 海战 · 探索 —— 一艘船，一片没画完的海图</div>',
         '<div class="tagline">五纪 · 物价 · 季风 —— 从疫火桨帆到蒸汽前夜</div>'),
        ('<div class="epigraph">桅杆在燃烧，罗盘在颤抖。地平线之外，是黄金、风暴，和从未被画进海图的东西。</div>',
         '<div class="epigraph">一银币五点五克银，一季九十一天，一百二十座港。世界在动，账本在烧——你的船在哪儿？</div>'),
        ("['① 立目标','② 航行','③ 遭遇','④ 收获','⑤ 回港']",
         "['① 选纪','② 择窗','③ 跑商','④ 季末','⑤ 推纪']"),
        ('<h2 class="sec-title"><span class="line"></span>全书结构<span class="line"></span></h2>',
         '<h2 class="sec-title"><span class="line"></span>分册结构<span class="line"></span></h2>'),
        ('<h2 class="sec-title"><span class="line"></span>已冻结的核心口径<span class="line"></span></h2>',
         '<h2 class="sec-title"><span class="line"></span>已冻结的引擎口径<span class="line"></span></h2>'),
        ('<div style="color:var(--ink2);font-size:13.5px">金点 = 完整成稿 · 空点 = 骨架撰写中</div>',
         '<div style="color:var(--ink2);font-size:13.5px">全部成稿 · 表页由 build_engine.py 从 data/ 渲染</div>'),
        ('<a class="cta" href="#ch02">✦ 二十分钟快速开始</a>',
         '<a class="cta" href="#ch00">✦ 翻开五纪总扉页</a>'),
        # 章节页眉：分册不称"章"
        ("${c.vol} · 第 ${c.num} 章 ${c.skeleton?'· 撰写中（骨架）':''}",
         "${c.vol} · ${c.num} ${c.skeleton?'· 撰写中（骨架）':''}"),
        # 搜索提示词
        ("['潮汐点','接舷','坏血病','私掠许可证','哗变','克拉肯','航段','声望']",
         "['黑胡椒','季风','库存轨','双轨钟','甘杜','垄断','卡拉维尔','砸盘']"),
    ]
    for old, new in subs:
        n = page.count(old)
        assert n >= 1, f"锚点未找到：{old[:40]}…"
        page = page.replace(old, new)

    frozen_old = """  const frozen = [
    ['核心判定','d20 + 属性 + 技能 ≥ DV'],
    ['难度阶梯','10 / 13 / 16 / 19 / 22'],
    ['生命值','HP = 6 + 筋骨×2'],
    ['命运资源','潮汐点 3（天赋上限 4）'],
    ['炮击齐射','DV 14 · 3d6 船体 · 装填 2 轮'],
    ['时间尺度','一昼夜 6 航段 · 海战轮 1 分钟'],
  ];"""
    frozen_new = """  const frozen = [
    ['货币锚','1 银 = 5.5 gAg · 1 金 = 10 银'],
    ['劳动锚','农夫 pop = 10 银/月（S1）'],
    ['行情骰','d6 六档 ×0.6 – 2.4'],
    ['双轨钟','微轨航段 4h · 宏轨 91 天/季'],
    ['三层物价塔','基价 × 库存轨 × 行情骰'],
    ['砸盘律','单港连抛 3 船 → 价 −40%'],
    ['船价公式','吨位 × 全装率 × 纪通胀'],
    ['利润判读','短程 10–20% · 远洋 30–36% · >40% 必有垄断'],
  ];"""
    assert frozen_old in page, "冻结卡块未找到"
    page = page.replace(frozen_old, frozen_new)
    return page


def main():
    chapters = build_chapters()
    glossary = bs.parse_glossary(bs.GLOSS_FILE) if bs.GLOSS_FILE.exists() else {}
    data_json = json.dumps(chapters, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    gloss_json = json.dumps(glossary, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = bs.TEMPLATE.replace("__CHAPTERS_JSON__", data_json).replace("__GLOSS_JSON__", gloss_json)
    page = customize(page)
    stamp = "引擎装配于 " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + f" · 分册 {len(chapters)} 册 · 数据 11 JSON"
    page = page.replace('id="buildStamp"></div>', 'id="buildStamp">' + stamp + "</div>")
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"OK 生成 {OUT_PATH}")
    print(f"  分册 {len(chapters)} 册，文件大小 {len(page)//1024} KB")


if __name__ == "__main__":
    main()
