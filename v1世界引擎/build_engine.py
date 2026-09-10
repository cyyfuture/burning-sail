# -*- coding: utf-8 -*-
"""
燃帆 v1 世界引擎 —— 数据表页渲染脚本
用法:
  python build_engine.py            # 渲染全部表页（整页生成 + 段落注入）
  python build_engine.py --check    # 只校验：报告过期/缺失的生成区，不写文件
  python build_engine.py --list     # 列出已注册的渲染器与目标
纪律（沿用调研2 master 的"数据即文本"）:
  - data/*.json 是唯一真源；生成页禁止手改，重跑本脚本覆盖。
  - 纯表分册（02工资/03生存/04物品/05货物）整页生成，文件头有 [生成页] 标记。
  - 混合分册（06船/07建筑/09跑商）用 <!-- ENGINE:名 -->…<!-- /ENGINE:名 --> 标记段落注入，
    标记之外的内容一概不动。
  - 无第三方依赖，仅标准库。
"""
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = (BASE_DIR / "data").resolve()
# 边界校验：读写都必须落在分册目录内
if DATA_DIR.parent != BASE_DIR:
    raise SystemExit("数据目录越界，已阻止")

GEN_TAG = "[生成页]"
OPEN, CLOSE = "<!-- ENGINE:", "/ENGINE -->"


def load_json(name):
    p = (DATA_DIR / name).resolve()
    if p.parent != DATA_DIR:
        raise SystemExit(f"数据路径越界：{name}")
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------- 渲染器注册表 ----------------
# 每个渲染器: dict(name=…, target=目标md相对路径, mode="full"|"section", render=fn(data)->str)
RENDERERS = []


def renderer(name, target, mode):
    def deco(fn):
        RENDERERS.append({"name": name, "target": target, "mode": mode, "render": fn})
        return fn
    return deco


# ---------------- 表格小工具 ----------------
def md_table(header, rows):
    """header: list[str]; rows: list[list] —— None 渲染为 —，bool 渲染为 ✓/✗。"""
    def cell(v):
        if v is None:
            return "—"
        if v is True:
            return "✓"
        if v is False:
            return "✗"
        return str(v)
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(cell(v) for v in r) + " |")
    return "\n".join(out)


# ---------------- ① 城市名册（09 分册注入段） ----------------
@renderer("城市名册", "09_跑商引擎.md", "section")
def render_cities(_deps):
    d = load_json("cities.json")
    if not d:
        return "<!-- data/cities.json 缺失，跑 data/select_cities.py 生成 -->"
    meta, cities = d["_meta"], d["cities"]
    lines = [f"### 9.x 城市名册（{len(cities)} 城，P0 冻结）", ""]
    lines.append(f"> 一级 {meta['审计']['一级']} 城全参数，二级 {meta['审计']['二级']} 城简化（基价修正带＋特色一行）。"
                 f"生存数据覆盖 {meta['审计']['有生存数据']} 城，估坐标 {len(meta['审计']['估坐标城'])} 城待核。")
    lines.append("")
    cur = None
    for rank, rlabel in ((1, "一级城（全参数）"), (2, "二级城（简化）")):
        lines.append(f"**{rlabel}**")
        lines.append("")
        rows = []
        for c in cities:
            if c["rank"] != rank:
                continue
            slots = "".join(c["slots"]) if c["slots"] else "—"
            rows.append([c["name"], c["region"], c["tier"],
                         c["nation_1450"], c["first_age"], slots,
                         c["survival_gAg"] or "—",
                         "†" if c["geo_est"] else ""])
        lines.append(md_table(["城", "分区", "tier", "政体(1450)", "入档纪", "四槽", "生存gAg/月", "†"], rows))
        lines.append("")
    lines.append("† = 坐标为估·代理（名册外手工补录），待核。四槽=调研2覆盖（粮价/工资/生存/补给）。")
    lines.append("")
    return "\n".join(lines)


# ---------------- ② 工资表（02 分册整页） ----------------
@renderer("工资表", "02_工资表.md", "full")
def render_wages(_deps):
    d = load_json("wages.json")
    if not d:
        return None
    lines = ["## 八层职业档（基准·S1·西欧=1）", "",
             "L0 农夫/杂工（锚10银）→ L1 帮工（12–15）→ L2 熟练匠（20–35）→ L3 行家匠/水手（19–24，冻结06章）",
             "→ L4 大匠/船长级（50–90）→ L5 名匠/舰长/大商人（100–250）→ L6 官员贵族（300–1000+）→ L7 王侯（采邑计）。",
             "",
             "> 军官与 L4+ 受雇层**真实收入=名义×1.8–2.1**（特权私货）；谈薪交易检定 DV13 成功把私货份额+20% 明面化。",
             "", "## 14 区×五纪工资（月银=日gAg÷5.5×26；S1=V1×0.85 前溯）", ""]
    for reg in d["regions"]:
        lines.append(f"### {reg['region']}（锚城：{reg['anchor_city']}）")
        lines.append("")
        rows = []
        for r in reg["rows"]:
            ms = r["monthly_silver"]
            rows.append([r["job"], r["daily_gAg"]["V1"], r["daily_gAg"]["V3"], r["daily_gAg"]["V5"],
                         ms.get("S1"), ms.get("V1"), ms.get("V3"), ms.get("V5"), r["tag"]])
        lines.append(md_table(["职业", "日V1", "日V3", "日V5", "S1月银", "V1月银", "V3月银", "V5月银", "档"], rows))
        lines.append("")
        lines.append(f"上游：{reg['upstream']}")
        lines.append("")
    lines.append("## S1 前溯锚点卡（6 张）")
    lines.append("")
    for c in d["s1_anchor_cards"]:
        lines.append(f"- **{c['city']}（{c['region']}，{c['era']}）** {c['event']}：{c['wage']} ≈ {c['gAg_est']}。{c['source']}。")
    lines.append("")
    lines.append("> 特例行：波托西 peon 恒 12.8 gAg/日 ≈ 60.7 银/月（全球最高日薪带，秘鲁矿业官价）；"
                 "塞维利亚工匠 21–24（vellón 两口径并立取 22.5）。S1 列 s1_est 行为 [估·代理]（区代理卡逻辑见锚点卡）。")
    lines.append("")
    return "\n".join(lines)


# ---------------- ③ 生存开支（03 分册整页） ----------------
@renderer("生存开支表", "03_生存开支表.md", "full")
def render_survival(_deps):
    d = load_json("survival.json")
    if not d:
        return None
    m = d["_meta"]
    lines = ["## 生活档位四档（T1.3.1 冻结）", "",
             "| 档 | 系数 | 钱花在哪 |", "|---|---|---|",
             "| 赤贫 | ×1.0 | 80% 口粮 |", "| 温饱 | ×2.0 | 粮+燃料+季节衣 |",
             "| 体面 | ×4.0 | 房租5%+肉+酒+佣人1名 |", "| 奢华 | ×10+ | 马匹/仆从/礼物/捐赠 |",
             "",
             "> **PC 生活档位规则**：长期生活在低于 (学识+1) 档时，每次航段掷 d20≤8 得 1 级疲劳——体面人的身体撑不住赤贫。",
             "> **家庭赡养**：每供养 1 名不劳动者，按所在城赤贫档 70% 月扣；妻儿四口之家 = 城基准 ×2.9 当量。",
             "> **灾变修正**（T1.3.2.b）：围城饿殍型 ×5；瘟疫需求塌陷型 ×1.2（对接 09 分册城市事件字段）。",
             "", f"## 120 城生存基准（{m['审计']['直锚城']} 直锚 / {m['审计']['代理城']} 代理 / {m['审计']['Tier3城']} Tier3）", ""]
    for region in ["西欧", "伊比利亚", "地中海", "黑海—东欧", "红海—波斯湾", "东非—西非",
                   "印度洋", "东南亚", "东亚", "加勒比—美洲"]:
        rows = []
        for r in d["cities"]:
            if r["region"] != region:
                continue
            s4 = r["survival"]["S4"]["档银"]["赤贫"] if r["survival"]["S4"] else "—"
            s1 = r["survival"]["S1"]["档银"]["赤贫"] if r["survival"]["S1"] else "—"
            rows.append([r["name"], f"L{r['rank']}", f"tier{r['tier']}", r["base_gAg"],
                         s1, s4, r["method"]])
        if not rows:
            continue
        lines.append(f"**{region}**（月银：S1 赤贫 / S4 赤贫；基准 gAg=S4 带锚）")
        lines.append("")
        lines.append(md_table(["城", "级", "tier", "基准gAg", "S1赤贫银", "S4赤贫银", "方法"], rows))
        lines.append("")
    return "\n".join(lines)


# ---------------- ④ 物品纪门控（04 分册整页） ----------------
@renderer("物品纪门控表", "04_武器与物品五纪表.md", "full")
def render_availability(_deps):
    d = load_json("availability.json")
    if not d:
        return None
    lines = ["## 物品 × 纪 三态（无 / 稀缺+50%·购入交易DV13 / 普及）", ""]
    cats = []
    for it in d["items"]:
        if it["cat"] not in cats:
            cats.append(it["cat"])
    for cat in cats:
        rows = []
        for it in d["items"]:
            if it["cat"] != cat:
                continue
            cells = [it["name"]]
            for s in ["S1", "S2", "S3", "S4", "S5"]:
                cells.append(it["states"].get(s, ""))
            rows.append(cells)
        lines.append(f"### {cat}")
        lines.append("")
        lines.append(md_table(["物品", "S1", "S2", "S3", "S4", "S5"], rows))
        lines.append("")
        for it in d["items"]:
            if it["cat"] == cat and it["note"]:
                lines.append(f"- {it['name']}：{it['note']}" + (f"（{it['note2']}）" if it["note2"] else ""))
        lines.append("")
    lines.append("> 06 章价格原值不动；S1 开局买不到任何手持火器与望远镜。弹药：铅弹 0.1 银/发；"
                 "火药 0.5 银/发射（S2–S3 稀缺期 ×2）。")
    lines.append("")
    return "\n".join(lines)


# ---------------- ⑤ 货物与船格（05 分册整页） ----------------
@renderer("货物与船格表", "05_货物与船格表.md", "full")
def render_goods(_deps):
    d = load_json("goods.json")
    if not d:
        return None
    lines = ["## 舱位换算（T1.5.1.b 冻结）", "",
             "1 舱位 = 8–10 担标准货（约 4–5 吨轻货 / 6–8 吨重货）＝1 类商品（整批）｜2 段补给｜1 备料（三合一沿用）。",
             "堆因数：泡货 1 舱 = 0.6 倍量；重货 1 舱 = 1.5 倍量。1 担 = 60.45 kg。",
             "", "## 40 可交易品（基价=产地层 gAg；picul_silver=银/担）", ""]
    for cat in ["香料", "织物", "食货", "矿工", "船用品", "特殊"]:
        rows = []
        for gitem in d["goods"]:
            if not (gitem["cat"] == cat or gitem["cat"].startswith(cat)):
                continue
            h = gitem.get("hold", {})
            rows.append([gitem["name"], gitem["origin"], gitem["age"],
                         h.get("产地银"), h.get("到岸银"), h.get("tag", ""),
                         gitem["stow"], gitem["keep"], gitem["chain"]])
        if not rows:
            continue
        lines.append(f"### {cat}")
        lines.append("")
        lines.append(md_table(["品", "产地带", "解锁", "舱价·产地银", "舱价·到岸银", "档", "堆", "存", "链价示例（gAg）"], rows))
        lines.append("")
    lines.append("> 特殊货物规则（T1.5.2）：易腐受潮 −30%；活畜每舱日耗 0.5 份补给；违禁（军火入奥斯曼/"
                 "书入裁判区）走海关风险条；火药遇炮火加倍起火。银锭按本位平价不掷行情骰。")
    lines.append("")
    return "\n".join(lines)


# ---------------- ⑥ 船型总表（06 分册注入段） ----------------
@renderer("船型总表", "06_船只总表与建造.md", "section")
def render_ships(_deps):
    d = load_json("ships.json")
    if not d:
        return None
    m = d["_meta"]
    lines = ["### 6.x 五纪船型总表（40 行；verbatim=07 章原值）", "",
             f"> {m['船价公式']}。", ""]
    for age, zh in [("S1", "S1 疫火与桨帆"), ("S2", "S2 发现的代价"), ("S3", "S3 白银洪流"),
                    ("S4", "S4 特许公司"), ("S5", "S5 黄金时代与蒸汽前夜")]:
        rows = []
        for s in d["ships"]:
            if s["age"] != age:
                continue
            rows.append([("★" if s["verbatim"] else "") + s["name"], s["hull"], s["guns"], s["holds"],
                         s["draft"], f"{s['crew_min']}/{s['crew_max']}", s["speed"],
                         s["tons"], s["price_gold"], s["trait"]])
        lines.append(f"**{zh}**")
        lines.append("")
        lines.append(md_table(["型", "船体", "炮位", "货舱", "吃水", "编制", "速", "吨", "价(金)", "特性"], rows))
        lines.append("")
    lines.append("> ★ = 07 章表原值（参数一字不改）。每纪首行可作 GM 旗舰推荐。")
    lines.append("")
    lines.append("### 6.y 传说船（不可购买，仅进程卡调用）")
    lines.append("")
    lines.append(md_table(["船", "纪", "注", "用途"],
                          [[l["name"], l["age"], l["note"], l["use"]] for l in d["legends"]]))
    lines.append("")
    return "\n".join(lines)


# ---------------- ⑦ 造船能力矩阵（06 分册注入段二） ----------------
@renderer("造船能力矩阵", "06_船只总表与建造.md", "section")
def render_shipyards(_deps):
    d = load_json("shipyards.json")
    if not d:
        return None
    m = d["_meta"]
    lines = ["### 6.z 造船能力矩阵（48 一级城 × 五纪）", "",
             f"> {m['说明']}", f"> 外发条款：{m['外发条款']}｜工期公式：{m['工期公式']}", ""]
    rows = []
    for c in d["cities"]:
        g = c["grades"]
        rows.append([c["name"], c["region"], g.get("S1"), g.get("S2"), g.get("S3"),
                     g.get("S4"), g.get("S5"), c["note"] or ""])
    lines.append(md_table(["城", "分区", "S1", "S2", "S3", "S4", "S5", "注"], rows))
    lines.append("")
    lines.append("找船坞速查：按等级反查——L5（S1–S3 威尼斯/热那亚；S4+ 阿姆斯特丹）；"
                 "L4（里斯本/伦敦/塞维利亚/果阿/广州 S4+）；L3（北欧汉萨带/明州福船线/马六甲）。")
    lines.append("")
    return "\n".join(lines)


# ---------------- ⑧ 建筑体系（07 分册注入段） ----------------
@renderer("建筑体系", "07_建筑与地产.md", "section")
def render_buildings(_deps):
    d = load_json("buildings.json")
    if not d:
        return None
    lines = ["### 7.x 建筑类型学（14 型四列参数）", ""]
    rows = []
    for b in d["buildings"]:
        rows.append([b["name"], b["price"]["陋"], b["price"]["常"], b["price"]["豪"],
                     b["maint"], b["ops"], b["lever"], b["req"]])
    lines.append(md_table(["型", "陋(银)", "常(银)", "豪(银)", "年维护", "运作", "PL博弈点", "前置"], rows))
    lines.append("")
    lines.append("### 7.y 城市等级 × 建筑解锁")
    lines.append("")
    lines.append(md_table(["城市等级", "解锁"],
                          [[u["等级"], u["解锁"]] for u in d["unlock"]]))
    lines.append("")
    lines.append(f"> 置业规则：{d['_meta']['置业规则']}")
    lines.append("> 超前建筑条款：低级城建高级楼可用但回报−50%，并开启市长剧情线。")
    lines.append("")
    return "\n".join(lines)


# ---------------- ⑨ 里程表（08 分册注入段） ----------------
@renderer("里程表", "08_时间与航海判定.md", "section")
def render_distances(_deps):
    d = load_json("distances.json")
    if not d:
        return None
    lines = ["### 8.x 五海区里程表（基准天=含常规停泊候风；快/中/慢=船速档）", "",
             f"> {d['_meta']['说明']}", ""]
    regions = [("地中海", ["威尼斯", "热那亚", "亚历山大港", "君士坦丁堡", "马赛", "瓦伦西亚", "卡法"]),
               ("北海—波罗的海", ["布鲁日", "伦敦", "汉堡", "但泽", "卑尔根", "波尔多"]),
               ("大西洋—西非—加勒比", ["里斯本", "好望角", "圣多明各", "哈瓦那", "韦拉克鲁斯（阿卡普尔科）", "巴伊亚", "巴巴多斯"]),
               ("印度洋", ["蒙巴萨（摩加迪沙带）", "亚丁", "霍尔木兹", "果阿", "卡利卡特", "科钦", "马六甲", "摩卡"]),
               ("东亚—东南亚", ["泉州", "广州", "宁波", "那霸", "长崎", "马尼拉", "万丹", "巴达维亚"])]
    for reg, hubs in regions:
        rows = []
        for e in d["edges"]:
            if e["from"] in hubs or e["to"] in hubs:
                rows.append([f"{e['from']}↔{e['to']}", e["route"], e["nm"],
                             e["days"]["快"], e["days"]["中"], e["days"]["慢"],
                             e["current"] or "—", e["knowledge_gate"], e["note"]])
        if not rows:
            continue
        lines.append(f"**{reg}**")
        lines.append("")
        lines.append(md_table(["边", "航线", "海里", "快(天)", "中(天)", "慢(天)", "洋流", "门控", "注"], rows))
        lines.append("")
    lines.append("> 门控=该边进入 PL 视图的纪（对表工程2 known-world）；S1 开局查不到绕非洲路径。跨块走枢纽换乘。")
    lines.append("")
    return "\n".join(lines)


# ---------------- ⑩ 风历总表（08 分册注入段二） ----------------
@renderer("风历总表", "08_时间与航海判定.md", "section")
def render_monsoon(_deps):
    d = load_json("monsoon.json")
    if not d:
        return None
    lines = ["### 8.y 风历总表（海区 × 12 月）", "",
             f"> {d['_meta']['说明']}", ""]
    rows = []
    for z in d["zones"]:
        rows.append([z["zone"]] + z["months"])
    lines.append(md_table(["风区"] + [f"{m}月" for m in range(1, 13)], rows))
    lines.append("")
    for z in d["zones"]:
        lines.append(f"- **{z['zone']}**：{z['note']}")
    lines.append("")
    lines.append(f"> 读风接口：{d['_meta']['读风接口']}。")
    return "\n".join(lines)


# ---------------- ⑪ 一级城市况条（09 分册注入段二） ----------------
@renderer("市况条", "09_跑商引擎.md", "section")
def render_strips(_deps):
    d = load_json("prices.json")
    if not d:
        return None
    lines = ["### 9.10 一级 48 城市况条（每城 8–12 品；库存轨初始=3，格=基价银×城档）", ""]
    rows = []
    for cid, s in d["strips"].items():
        goods_txt = "、".join(f"{g['品']}({g['档']}·{g['基价银']}银)" for g in s["goods"])
        rows.append([s["name"], s["region"], goods_txt])
    lines.append(md_table(["城", "分区", "市况条（品(城档·基价银)…）"], rows))
    lines.append("")
    lines.append("> 城档：产地0.6/中转0.9/消费1.6/遥远2.2；成交价=基价×城档×库存带×行情骰。"
                 "二级城 GM 按四问法即兴（产地问'周围种什么'/中转问'谁必经'/消费问'谁有钱'/"
                 "孤立问'封锁没有'——30 秒定价）。")
    return "\n".join(lines)


# ---------------- 写入机制 ----------------
def splice_section(text, name, body):
    """把 body 注入 <!-- ENGINE:name --> … <!-- /ENGINE:name --> 区；无标记则追加到文末。"""
    open_m = f"{OPEN}{name} -->"
    close_m = f"<!-- {CLOSE.replace('/ENGINE -->', '')}"  # 占位，下面统一拼
    open_tag = f"<!-- ENGINE:{name} -->"
    close_tag = f"<!-- /ENGINE:{name} -->"
    if open_tag in text and close_tag in text:
        before, rest = text.split(open_tag, 1)
        _, after = rest.split(close_tag, 1)
        return before + open_tag + "\n" + body + "\n" + close_tag + after
    return text.rstrip("\n") + "\n\n" + open_tag + "\n" + body + "\n" + close_tag + "\n"


def build(check_only=False):
    ok, stale, missing = 0, [], []
    for r in RENDERERS:
        target = (BASE_DIR / r["target"]).resolve()
        if target.parent != BASE_DIR:
            raise SystemExit(f"目标路径越界：{r['target']}")
        body = r["render"]({})
        if body is None:
            missing.append(r["name"])
            continue
        if r["mode"] == "full":
            header = f"# {r['name']}\n\n{GEN_TAG} 本页由 build_engine.py 从 data/ 渲染，禁止手改。\n\n"
            new = header + body + "\n"
            old = target.read_text(encoding="utf-8") if target.exists() else ""
            if old == new:
                ok += 1
            elif check_only:
                stale.append(r["target"])
            else:
                target.write_text(new, encoding="utf-8")
                ok += 1
        else:  # section
            old = target.read_text(encoding="utf-8") if target.exists() else ""
            open_tag = f"<!-- ENGINE:{r['name']} -->"
            if open_tag in old:
                import hashlib
                cur = old.split(open_tag, 1)[1].split(f"<!-- /ENGINE:{r['name']} -->", 1)[0]
                new_body = "\n" + body + "\n"
                if cur.strip() == body.strip():
                    ok += 1
                    continue
            if check_only:
                stale.append(f"{r['target']}#{r['name']}")
            else:
                target.write_text(splice_section(old, r["name"], body), encoding="utf-8")
                ok += 1
    return ok, stale, missing


def main():
    args = sys.argv[1:]
    if "--list" in args:
        for r in RENDERERS:
            print(f"{r['mode']:<8} {r['name']:<10} → {r['target']}")
        return
    ok, stale, missing = build(check_only=("--check" in args))
    verb = "校验" if "--check" in args else "渲染"
    print(f"{verb}完成：{ok} 个渲染器最新" + (f"，{len(stale)} 个过期：{stale}" if stale else "")
          + (f"，缺数据：{missing}" if missing else ""))
    if "--check" in args and stale:
        sys.exit(1)


if __name__ == "__main__":
    main()
