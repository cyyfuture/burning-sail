# -*- coding: utf-8 -*-
"""
build_gridmaps.py —— P7 格子图模板库（计划07部 T7.2.x，施工计划 B11）。
产出 gridmaps/ 下 14 个文件：
  甲板 6 型（加莱/柯克/卡拉维尔/卡拉克/盖伦/弗鲁特）——9 章六战位落点全标记；
  街区 4 风味（欧港/伊斯兰港/东亚港/殖民港，12×20）；
  室内 3 模板（官厅/酒馆/商馆，8×10）；
  tokens.svg（印刷标记物：4 PC + 12 NPC + 9 状态）＋ README.md（挂帷幕映射表）。
纪律：几何线稿 SVG（可打印可改色），网格层独立 <g> 可开关；美术升级走提示词库管线。
用法：python build_gridmaps.py
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "gridmaps"

CELL = 16          # 每格像素（1 格 = 1.5 米）
INK = "#3a3128"
GRID = "#b7a98c"
GOLD = "#8a6d1f"

# 六战位 → 甲板落点（格坐标，从船尾左下起算）；验证表见 README
STATIONS = {
    "掌": {"色": "#a33b2e", "注": "舵位（船尾中部）"},
    "帆": {"色": "#4a6b52", "注": "帆组（桅杆脚下）"},
    "炮": {"色": "#5a4a6b", "注": "炮组（舷侧炮位）"},
    "望": {"色": "#3b6b7a", "注": "瞭望（前桅/船首）"},
    "跳": {"色": "#8a6d1f", "注": "跳帮队（船首/舷侧）"},
    "医": {"色": "#7a4a3b", "注": "船医（甲板后部/舱口旁）"},
}

# 甲板六型：名、长宽（格）、桅位（x 格）、炮门数/舷、桨位（加莱）
DECKS = [
    {"名": "加莱galley", "L": 30, "W": 5, "masts": [7, 22], "guns": 2, "oars": True,
     "注": "桨帆战船：桨位两舷，接舷战主场"},
    {"名": "柯克cog", "L": 16, "W": 6, "masts": [8], "guns": 2, "oars": False,
     "注": "北商圆船：舱深炮少，接舷防御战"},
    {"名": "卡拉维尔caravel", "L": 18, "W": 6, "masts": [5, 12], "guns": 3, "oars": False,
     "注": "探险轻帆：浅水巡逻与测绘"},
    {"名": "卡拉克carrack", "L": 22, "W": 8, "masts": [5, 12, 19], "guns": 5, "oars": False,
     "注": "大帆商船：高尾楼，货重身沉"},
    {"名": "盖伦galleon", "L": 26, "W": 9, "masts": [6, 14, 22], "guns": 8, "oars": False,
     "注": "战商合体：S4 主力，炮位完整"},
    {"名": "弗鲁特fluyt", "L": 24, "W": 8, "masts": [7, 16], "guns": 3, "oars": False,
     "注": "联合省货船：舱大炮少，跑商首选"},
]


def svg_header(w, h, title, sub=""):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#f4ecd8"/>',
        f'<text x="20" y="34" font-size="20" font-weight="bold" fill="{INK}" font-family="serif">{title}</text>',
        f'<text x="20" y="54" font-size="12" fill="{INK}" opacity=".7">{sub}</text>',
    ]


def grid_layer(x0, y0, cols, rows, op="0.55"):
    lines = [f'<g id="grid" opacity="{op}">']
    for c in range(cols + 1):
        lines.append(f'<line x1="{x0+c*CELL}" y1="{y0}" x2="{x0+c*CELL}" y2="{y0+rows*CELL}" stroke="{GRID}" stroke-width="0.6"/>')
    for r in range(rows + 1):
        lines.append(f'<line x1="{x0}" y1="{y0+r*CELL}" x2="{x0+cols*CELL}" y2="{y0+r*CELL}" stroke="{GRID}" stroke-width="0.6"/>')
    lines.append("</g>")
    return lines


def station_marker(cx, cy, key):
    st = STATIONS[key]
    return (f'<g><circle cx="{cx}" cy="{cy}" r="9" fill="{st["色"]}"/>'
            f'<text x="{cx}" y="{cy+4}" font-size="10" fill="#f4ecd8" text-anchor="middle" font-weight="bold">{key}</text></g>')


def deck_svg(d):
    L, W = d["L"], d["W"]
    m = 40
    w = L * CELL + m * 2
    h = W * CELL + m * 2 + 46
    x0, y0 = m, m + 40
    cx_mid = x0 + L * CELL / 2
    out = svg_header(w, h, f"甲板图 · {d['名']}", f"1 格 = 1.5 米 · 船长 {L*1.5:.0f} m × 宽 {W*1.5:.0f} m · {d['注']}（网格打印时可关）")
    # 船体（六边形船壳：尖艏圆艉）
    bow = x0 + L * CELL
    pts = f"{x0+8},{y0+W*CELL/2} {x0+L*CELL*0.12},{y0-6} {bow-14},{y0-6} {bow},{y0+W*CELL/2} {bow-14},{y0+W*CELL+6} {x0+L*CELL*0.12},{y0+W*CELL+6}"
    out.append(f'<polygon points="{pts}" fill="#e8dcc0" stroke="{INK}" stroke-width="2"/>')
    # 艉楼/艏楼
    out.append(f'<rect x="{x0+6}" y="{y0-2}" width="{L*CELL*0.14}" height="{W*CELL+4}" fill="none" stroke="{INK}" stroke-dasharray="3 2"/>')
    out.append(f'<rect x="{bow-L*CELL*0.10}" y="{y0-2}" width="{L*CELL*0.10}" height="{W*CELL+4}" fill="none" stroke="{INK}" stroke-dasharray="3 2"/>')
    # 舱口
    for hx in (0.30, 0.52, 0.74):
        out.append(f'<rect x="{x0+L*CELL*hx}" y="{y0+W*CELL*0.25}" width="{CELL*2}" height="{W*CELL*0.5}" fill="none" stroke="{INK}" stroke-dasharray="2 2"/>')
        out.append(f'<text x="{x0+L*CELL*hx+2}" y="{y0+W*CELL*0.25+12}" font-size="10" fill="{INK}">舱</text>')
    # 桅杆
    for mx in d["masts"]:
        mxp = x0 + mx * CELL
        out.append(f'<circle cx="{mxp}" cy="{y0+W*CELL/2}" r="{CELL*0.9}" fill="#d9c9a3" stroke="{INK}" stroke-width="2"/>')
        out.append(f'<text x="{mxp}" y="{y0+W*CELL/2+3}" font-size="10" text-anchor="middle" fill="{INK}">桅</text>')
    # 炮位
    for i in range(d["guns"]):
        gx = x0 + (i + 1) * (L * CELL) / (d["guns"] + 1)
        out.append(f'<rect x="{gx-5}" y="{y0-3}" width="10" height="7" fill="#5a4a6b"/>')
        out.append(f'<rect x="{gx-5}" y="{y0+W*CELL-4}" width="10" height="7" fill="#5a4a6b"/>')
    # 桨位
    if d["oars"]:
        for r in range(1, L - 1, 2):
            out.append(f'<line x1="{x0+r*CELL}" y1="{y0-2}" x2="{x0+r*CELL}" y2="{y0-12}" stroke="{INK}" stroke-width="1.5"/>')
            out.append(f'<line x1="{x0+r*CELL}" y1="{y0+W*CELL+2}" x2="{x0+r*CELL}" y2="{y0+W*CELL+12}" stroke="{INK}" stroke-width="1.5"/>')
    # 六战位落点
    out.append(station_marker(x0 + L * CELL * 0.06, y0 + W * CELL / 2, "掌"))
    out.append(station_marker(x0 + d["masts"][0] * CELL + CELL * 0.9, y0 + W * CELL / 2, "帆"))
    out.append(station_marker(x0 + L * CELL * (0.62 if not d["oars"] else 0.5), y0 + W * CELL - 2, "炮"))
    out.append(station_marker(x0 + d["masts"][-1] * CELL - CELL * 0.9, y0 + W * CELL / 2, "望"))
    out.append(station_marker(bow - L * CELL * 0.10 - 10, y0 + W * CELL / 2, "跳"))
    out.append(station_marker(x0 + L * CELL * 0.17, y0 + W * CELL - 2, "医"))
    out += grid_layer(x0, y0, L, W)
    # 图例
    lx = x0
    ly = y0 + W * CELL + 30
    legend = "　".join(f"{k}＝{v['注']}" for k, v in STATIONS.items())
    out.append(f'<text x="{lx}" y="{ly}" font-size="11" fill="{INK}">战位六落点：{legend}</text>')
    out.append("</svg>")
    return "\n".join(out)


# 街区 4 风味（12×20 格）：块状布局参数（矩形块列表，格坐标）
def blocks_rects(spec):
    return spec


DISTRICTS = {
    "欧港_district": {"注": "欧洲港街区：栈桥＋市场广场＋仓库巷（对应 C07/C08/C09）",
                      "blocks": [(0, 0, 5, 4), (6, 0, 6, 3), (0, 5, 3, 5), (4, 5, 8, 4), (8, 10, 4, 5),
                                 (0, 11, 4, 4), (5, 10, 2, 6), (9, 0, 3, 4)],
                      "water": "left", "plaza": (4, 5, 8, 4)},
    "伊斯兰港_district": {"注": "伊斯兰港街区：清真寺院＋巴扎拱廊（对应 C07/C08/C10）",
                          "blocks": [(0, 0, 6, 3), (7, 0, 5, 3), (2, 4, 8, 6), (0, 11, 4, 4), (5, 12, 7, 3), (0, 4, 1, 6)],
                          "water": "bottom", "plaza": (2, 4, 8, 6), "dome": (5.5, 5.5)},
    "东亚港_district": {"注": "东亚港街区：市舶司＋桅林码头（对应 C07/C10/P04）",
                        "blocks": [(0, 0, 4, 5), (5, 0, 7, 3), (0, 6, 4, 6), (5, 4, 3, 8), (9, 4, 3, 8)],
                        "water": "right", "plaza": (5, 4, 3, 8), "gate": (5, 3)},
    "殖民港_district": {"注": "殖民港街区：堡塞角＋木栅＋码头仓（对应 C07/12.4 樱树港）",
                        "blocks": [(0, 0, 4, 4), (5, 0, 4, 4), (10, 0, 2, 7), (0, 5, 4, 7), (5, 5, 4, 4)],
                        "water": "bottom", "plaza": (5, 5, 4, 4), "fort": (0, 0, 4, 4)},
}

INTERIORS = {
    "官厅_hall": {"注": "官厅/总督府（C10 谒见）：高台＋文书列席＋屏退线",
                  "rooms": [(0, 0, 8, 3), (0, 3, 8, 7)], "props": [("台", 2.5, 0.5), ("席", 1, 5), ("席", 5, 5)]},
    "酒馆_tavern": {"注": "酒馆（C09 听闻）：吧台＋大桌＋炉角＋暗桌",
                    "rooms": [(0, 0, 8, 10)], "props": [("吧台", 0.5, 1), ("大桌", 3, 4), ("炉", 6.5, 8), ("暗桌", 6, 1)]},
    "商馆_factory": {"注": "商馆/账房（C08/C11 谈判）：柜台＋货架＋密谈间",
                     "rooms": [(0, 0, 8, 6), (5, 6, 3, 4)], "props": [("柜台", 1, 3), ("货架", 0.5, 0.5), ("密谈", 5.5, 7)]},
}


def district_svg(name, spec):
    C, R = 20, 12   # 20 宽 ×12 高（格）；建筑块坐标以 (x,y,w,h) 给出
    m = 40
    w = C * CELL + m * 2
    h = R * CELL + m * 2 + 30
    x0, y0 = m, m + 30
    out = svg_header(w, h, f"码头街区图 · {name.split('_')[0]}", f"1 格 = 1.5 米 · {spec['注']}")
    # 水面
    wx = {"left": (x0 - 12, y0, 12, R * CELL), "bottom": (x0, y0 + R * CELL, C * CELL, 12),
          "right": (x0 + C * CELL, y0, 12, R * CELL)}[spec["water"]]
    out.append(f'<rect x="{wx[0]}" y="{wx[1]}" width="{wx[2]}" height="{wx[3]}" fill="#c8d8dc" stroke="{INK}" stroke-dasharray="4 2"/>')
    out.append(f'<text x="{wx[0]+2}" y="{wx[1]+16}" font-size="11" fill="{INK}">水</text>')
    # 街区
    for (bx, by, bw, bh) in spec["blocks"]:
        out.append(f'<rect x="{x0+bx*CELL}" y="{y0+by*CELL}" width="{bw*CELL}" height="{bh*CELL}" fill="#e8dcc0" stroke="{INK}" stroke-width="1.2"/>')
    if spec.get("plaza"):
        px, py, pw, ph = spec["plaza"]
        out.append(f'<rect x="{x0+px*CELL}" y="{y0+py*CELL}" width="{pw*CELL}" height="{ph*CELL}" fill="#efe4c5" stroke="{GOLD}" stroke-dasharray="4 2"/>')
        out.append(f'<text x="{x0+(px+pw/2)*CELL}" y="{y0+(py+ph/2)*CELL}" font-size="12" text-anchor="middle" fill="{GOLD}">广场/巴扎</text>')
    if spec.get("fort"):
        fx, fy, fw, fh = spec["fort"]
        out.append(f'<circle cx="{x0+(fx+fw/2)*CELL}" cy="{y0+(fy+fh/2)*CELL}" r="{CELL*1.2}" fill="none" stroke="{INK}" stroke-width="1.5"/>')
        out.append(f'<text x="{x0+(fx+fw/2)*CELL}" y="{y0+(fy+fh/2)*CELL+4}" font-size="11" text-anchor="middle" fill="{INK}">堡</text>')
    if spec.get("gate"):
        gx, gy = spec["gate"]
        out.append(f'<rect x="{x0+gx*CELL}" y="{y0+gy*CELL}" width="{CELL*2}" height="{CELL}" fill="#d9c9a3" stroke="{INK}"/>')
        out.append(f'<text x="{x0+(gx+1)*CELL}" y="{y0+(gy+0.8)*CELL}" font-size="10" text-anchor="middle" fill="{INK}">门</text>')
    out += grid_layer(x0, y0, C, R)
    out.append("</svg>")
    return "\n".join(out)


def interior_svg(name, spec):
    C, R = 10, 8
    m = 40
    w = C * CELL + m * 2
    h = R * CELL + m * 2 + 30
    x0, y0 = m, m + 30
    out = svg_header(w, h, f"室内图 · {name.split('_')[0]}", f"1 格 = 1.5 米 · {spec['注']}")
    for (rx, ry, rw, rh) in spec["rooms"]:
        out.append(f'<rect x="{x0+rx*CELL}" y="{y0+ry*CELL}" width="{rw*CELL}" height="{rh*CELL}" fill="#e8dcc0" stroke="{INK}" stroke-width="1.5"/>')
    for (label, px, py) in spec["props"]:
        out.append(f'<rect x="{x0+px*CELL}" y="{y0+py*CELL}" width="{CELL*1.6}" height="{CELL*1.1}" fill="#d9c9a3" stroke="{INK}"/>')
        out.append(f'<text x="{x0+(px+0.8)*CELL}" y="{y0+(py+0.75)*CELL}" font-size="9" text-anchor="middle" fill="{INK}">{label}</text>')
    # 门（南墙中央）
    out.append(f'<rect x="{x0+C*CELL/2-10}" y="{y0+R*CELL-3}" width="20" height="6" fill="#f4ecd8" stroke="{INK}"/>')
    out += grid_layer(x0, y0, C, R)
    out.append("</svg>")
    return "\n".join(out)


def tokens_svg():
    cols = 8
    cell = 90
    npc_names = ["血鸦", "阿兰达", "范德米尔", "科瓦", "克鲁兹", "杜尔", "霍恩", "银库", "账房", "通事", "帕尔米贾诺", "秘书"]
    states = [("燃烧", "#a33b2e"), ("进水", "#3b6b7a"), ("倒地", "#555"), ("疲劳", "#8a6d1f"),
              ("装填", "#5a4a6b"), ("接舷", "#7a4a3b"), ("抛锚", "#4a6b52"), ("雾隐", "#888"), ("火炮就绪", "#c9a227")]
    rows = 3 + len(states) // cols + 1
    w = cols * cell + 80
    h = rows * cell + 120
    out = svg_header(w, h, "标记物 token 印刷页", "1 寸圆片底座：裁剪后贴硬卡。PC 金环 / NPC 灰环 / 状态彩环（≥9 章海战所需）")
    def token(cx, cy, label, ring, fill="#f4ecd8"):
        return (f'<circle cx="{cx}" cy="{cy}" r="30" fill="{fill}" stroke="{ring}" stroke-width="3"/>'
                f'<text x="{cx}" y="{cy+4}" font-size="11" text-anchor="middle" fill="{INK}">{label}</text>')
    for i in range(4):
        out.append(token(60 + i * cell, 100, f"PC{i+1}", GOLD))
    for i, nm in enumerate(npc_names):
        out.append(token(60 + (i % cols) * cell, 200 + (i // cols) * cell, nm, "#666"))
    ybase = 200 + 2 * cell + 20
    out.append(f'<text x="40" y="{ybase-10}" font-size="13" fill="{INK}">状态标记：</text>')
    for i, (nm, col) in enumerate(states):
        out.append(token(60 + (i % cols) * cell, ybase + (i // cols) * cell, nm, col))
    out.append("</svg>")
    return "\n".join(out)


README = """# 格子图模板库（gridmaps）

> 参数化生成（`python build_gridmaps.py`，改 `DECKS/DISTRICTS/INTERIORS` 常量重跑即可调型）。
> 纪律：几何线稿、可打印、网格层独立 `<g id="grid">`（浏览器打印前可删该节点得到无网格版）。

## 文件清单与挂帷幕映射（哪场戏用哪张）

| 文件 | 用途 | 挂帷幕 |
|---|---|---|
| 甲板_加莱galley.svg | 桨帆接舷战（S1 地中海主场） | C05/C06 |
| 甲板_柯克cog.svg | 北商圆船防御战 | C05/C06 |
| 甲板_卡拉维尔caravel.svg | 浅水巡逻/测绘遭遇 | C03/C05 |
| 甲板_卡拉克carrack.svg | 大帆商船（货重身沉） | C04/C06 |
| 甲板_盖伦galleon.svg | S4 主力战商船 | C05/C06 |
| 甲板_弗鲁特fluyt.svg | 联合省货船（跑商首选） | C06（被劫戏） |
| 街区_欧港_district.svg | 欧港栈桥/市场/仓库巷 | C07/C08/C09 |
| 街区_伊斯兰港_district.svg | 巴扎拱廊/清真寺院 | C07/C08/C10 |
| 街区_东亚港_district.svg | 市舶司/桅林码头 | C07/C10 |
| 街区_殖民港_district.svg | 堡塞/木栅/码头仓 | C07/C09 |
| 室内_官厅_hall.svg | 谒见/审讯 | C10/C11 |
| 室内_酒馆_tavern.svg | 听闻/招募/接头 | C09/C17 |
| 室内_商馆_factory.svg | 商约/密谈 | C08/C11 |
| tokens.svg | 标记物印刷页（4 PC+12 NPC+9 状态） | 全部战术图 |

## 9 章六战位落点验证表（DoD）

| 战位 | 甲板落点 | 白名单节选（09 章） |
|---|---|---|
| 掌舵位 | 艉部舵位（图例「掌」） | 保持航向/急转/抢风/贴礁走位 |
| 帆组位 | 主桅脚下（「帆」） | 换帆档/海上修帆/砍索 |
| 炮组位 | 舷侧炮门（「炮」） | 装填/瞄准/射击（9.5 流程） |
| 瞭望位 | 后桅/船首（「望」） | 观察/报距/抢天气 |
| 跳帮队位 | 艏楼（「跳」） | 接舷突击/登舷/夺舵 |
| 船医位 | 艉楼旁舱口（「医」） | 救治/止血/疫病检定 |

状态标记 9 种（燃烧/进水/倒地/疲劳/装填/接舷/抛锚/雾隐/火炮就绪）≥ 9 章海战所需全部状态——DoD 达成。

## 标记物方案（T7.2.1.b）

- **印刷版**：tokens.svg 按 1 寸圆片打印裁剪；PC 金环、NPC 灰环、状态彩环。
- **数字版**：KP 面板骰桌/城市卡已含位置语义（P2 优先级，见 panel/index.html）。
"""


def main():
    OUT.mkdir(exist_ok=True)
    n = 0
    for d in DECKS:
        (OUT / f"甲板_{d['名']}.svg").write_text(deck_svg(d), encoding="utf-8")
        n += 1
    for name, spec in DISTRICTS.items():
        (OUT / f"街区_{name}.svg").write_text(district_svg(name, spec), encoding="utf-8")
        n += 1
    for name, spec in INTERIORS.items():
        (OUT / f"室内_{name}.svg").write_text(interior_svg(name, spec), encoding="utf-8")
        n += 1
    (OUT / "tokens.svg").write_text(tokens_svg(), encoding="utf-8")
    n += 1
    (OUT / "README.md").write_text(README, encoding="utf-8")
    print(f"gridmaps 生成：{n} 个文件 + README（甲板 6 / 街区 4 / 室内 3 / tokens 1）")


if __name__ == "__main__":
    main()
