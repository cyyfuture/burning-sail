# -*- coding: utf-8 -*-
"""
build_pack.py —— S1 试航包生成器（8.2.2 快速可玩切片）。
从 ../data/*.json 抽取：8 城名册+市况、4 船型、7 商品；拼装纪扉页/七步卡/季末卡为单文件。
用法：python build_pack.py → 生成 试航包.md
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = (HERE / ".." / "data").resolve()

CITIES_8 = ["威尼斯", "热那亚", "亚历山大港", "伊斯坦布尔", "马赛", "卡法", "布鲁日", "里斯本"]
SHIPS_4 = ["柯克 Cog", "威尼斯大加利 Great Galley", "拉丁单桅小船 Barque", "德夫 Dhow"]
GOODS_7 = ["黑胡椒", "生丝·中国", "藏红花", "葡萄酒", "鱼干", "盐", "银锭"]


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(v) if v is not None else "—" for v in r) + " |")
    return "\n".join(out)


def main():
    cities = {c["name"]: c for c in json.loads((DATA / "cities.json").read_text(encoding="utf-8"))["cities"]}
    ships = json.loads((DATA / "ships.json").read_text(encoding="utf-8"))["ships"]
    prices = json.loads((DATA / "prices.json").read_text(encoding="utf-8"))
    goods = {g["name"]: g for g in json.loads((DATA / "goods.json").read_text(encoding="utf-8"))["goods"]}
    surv = {c["name"]: c for c in json.loads((DATA / "survival.json").read_text(encoding="utf-8"))["cities"]}
    dist = json.loads((DATA / "distances.json").read_text(encoding="utf-8"))["edges"]
    procs = json.loads((DATA / "processes.json").read_text(encoding="utf-8"))
    quests = {t["id"]: t for t in json.loads((DATA / "quests.json").read_text(encoding="utf-8"))["quests"]}
    mats = json.loads((DATA / "qst_materials.json").read_text(encoding="utf-8"))

    L = []
    A = L.append
    AGE = {"S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5}
    TIER_MULT = {"产地": 0.6, "中转": 0.9, "消费": 1.6, "遥远": 2.2, "本位": 1.0}

    def strip_of(city):
        """一级/二级城统一：从 prices.grid 取本城基准（纪过滤）。"""
        sid = city["id"]
        rows = []
        for gname, cmap in prices["grid"].items():
            g = goods.get(gname)
            if not g or AGE[g["age"]] > 1:  # 试航包=S1
                continue
            cell = cmap.get(sid)
            if not cell:
                continue
            rows.append({"品": gname, "档": cell["tier"], "基价银": cell["base_silver"]})
        prio = {"产地": 0, "中转": 1, "本位": 2, "消费": 3, "遥远": 4}
        rows.sort(key=lambda r: (prio.get(r["档"], 9), -r["基价银"]))
        return rows[:8]
    A("# 《燃帆》S1 试航包 —— 1375，威尼斯的账期")
    A("")
    A("> 最小可玩版（8.2.2）：一张纪扉页＋8 城＋4 船＋7 货＋七步卡＋季末卡。够跑 3–5 团的微型战役。")
    A("> 只带本页＋06/07/09/10 章速查即可开团；详细规则在 v1世界引擎/ 分册。")
    A("")
    A("## 纪扉页 · S1 疫火与桨帆（1350–1449）")
    A("")
    A("黑死病扫过欧洲一代人：人口折半、工资暴涨、地价崩落。威尼斯与热那亚为黎凡特贸易打了二十年，"
      "基奥贾的火光刚熄。东方的香料仍走亚历山大港与红海；大明刚刚禁海；葡人刚在休达立足。"
      "罗盘刚下商船，火器还是攻城玩具。**一船人的尺度：你们是威尼斯账本上的一笔小注。**")
    A("")
    A("**大事年表**：1348 黑死病 ｜ 1378–81 基奥贾战争 ｜ 1380 明禁海 ｜ 1402 安卡拉 ｜ 1405–33 郑和七下西洋 ｜ 1415 葡取休达 ｜ 1449 君堡围城将至")
    A("")
    A("**可用水准**：罗盘（稀缺3金）／星盘稀缺／无印刷／火器=攻城玩具／无手持火器。")
    A("**解锁商品**：胡椒（经亚历山大×3）、生丝、藏红花、呢绒、西非金、卡法奴隶（制度阴影，见红线）。")
    A("**欧亚航路**：纯海路不通——走陆桥三走廊（威尼斯—亚历山大—红海／卡法—萨莱陆路／宁波私舶）。")
    A("")
    A("## 开局（GM 朗读）")
    A("")
    A("1375 年 3 月，威尼斯。你们合股租下（或被赏赐）一条船，账房给了 200 银周转金与一季的账期。"
      "热那亚人的桨帆船队上月劫了两艘大加利；教皇禁运名单上又添了三个名字；亚历山大的马穆鲁克税官涨价了。"
      "季风季（3–5 月）的黎凡特船班四月中发——你们有六周。")
    A("")
    A("## 8 城名册（市况条：品(城档·基价银)；库存轨初始=3）")
    A("")
    rows = []
    for n in CITIES_8:
        c = cities[n]
        s = surv[n]
        gtxt = "、".join(f"{g['品']}({g['档']}{g['基价银']}银)" for g in strip_of(c)) or "—"
        rows.append([n, f"tier{c['tier']}", s["survival"]["S1"]["档银"]["赤贫"], gtxt])
    A(md_table(["城", "规模", "S1赤贫生存(银/月)", "市况条"], rows))
    A("")
    A("> 城档：产地0.6／中转0.9／消费1.6／遥远2.2。成交价=基价×城档×库存带(3=×1.0)×行情骰d6(×0.6–1.7)。")
    A("")
    A("## 4 船型（S1 档）")
    A("")
    rows = []
    for n in SHIPS_4:
        s = [x for x in ships if x["name"] == n and x["age"] == "S1"][0]
        rows.append([s["name"], s["hull"], s["guns"], s["holds"], s["draft"],
                     f"{s['crew_min']}/{s['crew_max']}", s["speed"], f"{s['price_gold']}金", s["trait"]])
    A(md_table(["型", "船体", "炮位", "货舱", "吃水", "编制", "速", "价", "特性"], rows))
    A("")
    A("### S1 战斗速查（甲板与炮战）")
    A("")
    A("**甲板（9.1）**：无任何手持火器——弓弩与冷兵器的世纪。长弓 1d6／射程20格／每轮可射／列阵2d6（2–3银[确]）｜"
      "弩 1d8／射程15格／装填1轮／无视1点护甲（5银[评]）｜武装剑 1d8（10银）｜水手刀 1d6（4银）｜链甲 25银（护甲值2）｜"
      "火瓶 3d6 锥形、敌我不分（3银）。")
    A("**炮战（04分册4.2 单炮射击条款——齐射战术 S5 才普及）**：每门独立掷 `d20+学识或机敏+炮术` vs 船体14／帆索12／甲板16，"
      "伤害=炮卡值；同轮第2门起每门−2（上限−6）。轻型射石炮 2d8／装填3轮／炮组3｜重射石炮 3d10／装填4轮／炮组5（剧情级）。"
      "**S1 海战的主战手段是抢上风、接舷与火攻——炮是吓唬人的。**")
    A("")
    A("## 7 货（舱位整批价）")
    A("")
    rows = []
    for n in GOODS_7:
        g = goods[n]
        h = g.get("hold", {})
        rows.append([n, g["origin"], h.get("产地银"), h.get("到岸银"), g["stow"], g["keep"]])
    A(md_table(["品", "产地带", "产地银/舱", "到岸银/舱", "堆因数", "保存"], rows))
    A("")
    A("> 银锭=本位平价不掷骰。红线：无奴隶商品行——涉及时走 11 章安全工具与进程卡。")
    A("")
    A("## 航线速查（本包域内，中速档天）")
    A("")
    rows = []
    for e in dist:
        if e["from"] in CITIES_8 and e["to"] in CITIES_8:
            rows.append([f"{e['from']}↔{e['to']}", e["route"], e["nm"], e["days"]["中"], e["note"]])
    A(md_table(["边", "航线", "海里", "天(中)", "注"], rows))
    A("")
    A("## 跑商七步卡")
    A("")
    A("①情报（交易DV13问档）→②融资（海贷20–36%/航次）→③备航（1舱=2段补给）→④择窗（3–10月地中海可航；冬季封海）"
      "→⑤航程（打包掷1次事件骰）→⑥到货（市况×行情骰；每批<3舱不推轨）→⑦分账（10章账本）。")
    A("")
    A("## 季末卡（八步≤10分钟）")
    A("")
    A("①季风换向宣告→②每城行情骰重掷→③派系tick（初跑可略）→④城经验（靠港船数×舱位+PL投资）"
      "→⑤人物年轮（初跑可略）→⑥天气轮转→⑦城市事件d10→⑧世界一瞥三行。")
    A("")
    A("**世界一瞥句例**：'亚历山大的胡椒又贵了——马穆鲁克在囤。'／'老塞缪尔没熬过冬天，酒馆挂出了木牌。'／"
      "'热那亚的桨帆船在罗得岛外海烧了两条船。'")
    A("")
    A("## S1 任务速查（P5 任务世界切片）")
    A("")
    A("开局激活 3 张进程卡（剧本卡 15 选 3；S1 战役推荐 P01＋P02＋P03）。六要素口诀："
      "**钩子谁说、误差在哪、目标一句、主隐两障、代价先亮、回报四槽**——六缺一不上桌。")
    A("")
    qrows = []
    for p in procs["processes"]:
        if p["age"] != "S1":
            continue
        names = "；".join(f"{quests[qid]['name']}（{quests[qid]['scale']}·{quests[qid].get('pay') or quests[qid].get('_formula')}银）"
                          for qid in p["quests"])
        qrows.append([p["id"], p["name"], p["window"], p["drama"][:36] + "…", names])
    A(md_table(["进程", "名", "年窗", "人事尺度", "固定任务（体量·报酬银）"], qrows))
    A("")
    A("> 报酬公式：10 银×风险(0.5/1/2/4)×时长(单场1/短链2.5/长线8)×技艺(1/1.5/2.5)×稀缺(0.7/1/2)，现金封顶 600 银。"
      "浮动三源最多启两个；悔约=委托圈恶名+，同区任务降一档一季。")
    A("随机找活：掷 12 分册 d16 总触发表——S1 可用 15 种泛型（缉私查禁以'私掠反私掠'替代，捕鲸猎鲨 S3+）。"
      "委托人必有误差（误差库 40 条）；反转掷表＝核心真相，障碍池前两项即天然线索源。")
    A("")
    A("## 样板账（半页）")
    A("")
    A("大加利（1,000金合股租用 200金/季）8 舱丝货，威尼斯→亚历山大（23 天）：")
    A("购 6舱生丝×600=3,600｜薪饷 25人×19×2月=950｜给养 25×50天×0.9=1,125｜马穆鲁克税 12%=648｜"
      "售 亚历山大(中转0.9×链带1.5)≈6舱×810×行情骰。**平常×1.0 亏损约 600；紧俏×1.3 净利≈1,950**——"
      "这就是黎凡特航线的真实数学：薄利，除非你抢在热那亚人前面，或压港等风声。")
    A("")
    A("---")
    A("*试航包由 build_pack.py 从 data/ 生成；实跑 2 团后把问题清单（≥10 条）回填修订。*")

    (HERE / "试航包.md").write_text("\n".join(L), encoding="utf-8")
    print(f"OK 试航包.md：8 城＋4 船＋7 货＋{len(rows)} 航线")


if __name__ == "__main__":
    main()
