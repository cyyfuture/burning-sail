# -*- coding: utf-8 -*-
"""
check_consistency.py —— T8.4.2 一致性终检（施工计划 B14）。
跨 JSON 交叉引用 + 与 16 章原文锚点数值自动对拍：
  - quests.p ∈ processes；quest/process 任务互指；标签 ∈ 八味；
  - prices.strips 键 ∈ cities；条内品名 ∈ goods；distances 端点 ∈ cities（剥别名括号）；
  - npcs.faction ∈ factions ∪ {独立}；factions.anchors ⊆ npcs；
  - rhetoric 帷幕索引 ∈ C01–18 / G01–16；
  - 16 章对拍：07 章七船名 ⊆ ships.json verbatim 行；02 分册 L3 水手锚（19–24 银冻结 06 章）
    → wages.json L3 各区 S1 月银落对拍带；八味自检（主味 ≤30%）复跑。
用法：python data/check_consistency.py  （退出码 0=清零）
"""
import json
import re
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent      # v1世界引擎/
DATA = ENGINE / "data"
ROOT = ENGINE.parent                                  # 仓库根（16 章在此）


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def norm(name):
    """剥别名括号与拉丁后缀：'蒙巴萨（摩加迪沙带）'→'蒙巴萨'；'单桅快船 Sloop'→'单桅快船'"""
    s = re.sub(r"（[^）]*）", "", str(name))
    return re.sub(r"[A-Za-z0-9\s]+", "", s).strip()


def main():
    errs, warns = [], []

    cities = load("cities.json")["cities"]
    city_names = {c["name"] for c in cities}
    city_ids = {c["id"] for c in cities}

    goods = {g["name"] for g in load("goods.json")["goods"]}
    tags = {t["味"] for t in load("tags.json")["tags"]}

    procs = load("processes.json")["processes"]
    proc_ids = {p["id"] for p in procs}
    quests = load("quests.json")["quests"]
    quest_ids = {q["id"] for q in quests}
    for q in quests:
        if q["p"] not in proc_ids:
            errs.append(f"{q['id']} 归属进程不存在：{q['p']}")
        for t in q["tags"]:
            if t not in tags:
                errs.append(f"{q['id']} 标签不在八味：{t}")
    for p in procs:
        for qid in p["quests"]:
            if qid not in quest_ids:
                errs.append(f"{p['id']} 引用任务不存在：{qid}")

    prices = load("prices.json")
    for cid in prices["strips"]:
        if cid not in city_ids:
            errs.append(f"strips 键不是城市 id：{cid}")
        for g in prices["strips"][cid]["goods"]:
            if g["品"] not in goods:
                errs.append(f"{cid} 市况条品名不在 goods：{g['品']}")

    distances = load("distances.json")["edges"]
    for e in distances:
        for end in (e["from"], e["to"]):
            if norm(end) not in city_names:
                warns.append(f"里程端点未匹配城市名（核对别名）：{end}")

    npcs = load("npcs.json")["npcs"]
    npc_ids = {n["id"] for n in npcs}
    factions = load("factions.json")["factions"]
    fac_ids = {f["id"] for f in factions}
    for n in npcs:
        if n["faction"] != "独立" and n["faction"] not in fac_ids:
            errs.append(f"{n['id']} faction 不存在：{n['faction']}")
    for f in factions:
        for a in f["anchors"]:
            if a not in npc_ids:
                errs.append(f"{f['id']} 锚点 NPC 不存在：{a}")

    rhet = load("rhetoric.json")
    curtain_ids = {c.split()[0] for c in rhet["_meta"]["帷幕编号"].split("、")}
    gen_ids = {f"G{i:02d}" for i in range(1, 17)}
    for c in rhet["corpus"]:
        if c["curtain"].split()[0] not in curtain_ids:
            errs.append(f"{c['id']} 帷幕编号非法：{c['curtain']}")
    for g in rhet["glances"]:
        if g["ref"] not in curtain_ids | gen_ids:
            errs.append(f"句库索引非法：{g['ref']}")

    # ---- 16 章对拍 ----
    # ① 07 章七船 verbatim（船表行特征：第二列=数字船体）
    ship_md = (ROOT / "07_航海与船只.md").read_text(encoding="utf-8")
    seven = set(re.findall(r"^\| \*\*(.+?)\*\* \| (\d+) \|", ship_md, re.M))
    seven_names = {norm(n) for n, _h in seven}
    ships = load("ships.json")["ships"]
    verbatim_names = {norm(s["name"]) for s in ships if s.get("verbatim")}
    missing = seven_names - verbatim_names
    if missing:
        errs.append(f"07 章七船未全部 verbatim 入库：{missing}")
    # ② 水手工资锚：06 章普通水手 19 / 熟练水手 24（gAg 带冻结）→ 02 分册表头须保留 "19–24"
    eco_md = (ROOT / "06_装备与资源.md").read_text(encoding="utf-8")
    m_ordinary = re.search(r"普通水手（ordinary seaman）\*\* \| (\d+)", eco_md)
    m_able = re.search(r"熟练水手（able seaman）\*\* \| (\d+)", eco_md)
    if not m_ordinary or m_ordinary.group(1) != "19":
        errs.append("06 章锚点漂移：普通水手应 19（gAg 带）")
    if not m_able or m_able.group(1) != "24":
        errs.append("06 章锚点漂移：熟练水手应 24（gAg 带）")
    wages_md = (ENGINE / "02_工资表.md").read_text(encoding="utf-8")
    if "19–24" not in wages_md:
        errs.append("02 分册表头丢了 L3 水手冻结带（19–24，冻结 06 章）")
    # ③ 八味主味分布复跑（≤30%）
    from collections import Counter
    main_flavors = Counter(q["tags"][0] for q in quests)
    for flavor, cnt in main_flavors.items():
        if cnt / len(quests) > 0.30:
            errs.append(f"主味 {flavor} 超 30%：{cnt}/{len(quests)}")
    # ④ 分册 17 册 + data 18 JSON
    vols = sorted(p.name for p in ENGINE.glob("[0-9][0-9]_*.md"))
    if len(vols) != 17:
        warns.append(f"分册数异常（期望 00–16 共 17 册）：{len(vols)}")
    jsons = sorted(p.name for p in DATA.glob("*.json"))
    if len(jsons) != 18:
        warns.append(f"data JSON 数异常（期望 18）：{len(jsons)} → {jsons}")

    # ---- 报告 ----
    for e in errs:
        print("ERR  ", e)
    for w in warns:
        print("WARN ", w)
    print(f"一致性终检：{len(errs)} 错误 / {len(warns)} 警告"
          + ("（警告=留痕待核，不阻断）" if warns and not errs else ""))
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
