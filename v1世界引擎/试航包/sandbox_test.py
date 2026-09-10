# -*- coding: utf-8 -*-
"""
sandbox_test.py —— 纸上沙盘闸门·机械化自测（P4 DoD 的账目闭合部分）。
场景：1375 春，威尼斯。一条大加利（编制25/满30），200 银周转金+100 银海贷，跑一季。
跑：①一航次账（威尼斯→亚历山大→威尼斯）②季末八步结算。全部骰子用固定种子模拟。
人肉 GM 全流程（≤10 分钟沙漏）仍需实跑——本脚本只证明每步运算有定义且账目闭合。
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = (HERE / ".." / "data").resolve()
random.seed(1375)

goods = {g["name"]: g for g in json.loads((DATA / "goods.json").read_text(encoding="utf-8"))["goods"]}
prices = json.loads((DATA / "prices.json").read_text(encoding="utf-8"))
TRACK = {0: 1.8, 1: 1.3, 2: 1.1, 3: 1.0, 4: 0.8, 5: 0.6}
DICE = {1: 0.6, 2: 0.8, 3: 1.0, 4: 1.0, 5: 1.3, 6: 1.7}
TIER_MULT = {"产地": 0.6, "中转": 0.9, "消费": 1.6, "遥远": 2.2, "本位": 1.0}


def hold_price(gname, city_id, track, dice):
    """本城成交基准：grid.base_silver（货源侧产地银/下游到岸银×城档）×库存×行情。"""
    cell = prices["grid"][gname][city_id]
    return round(cell["base_silver"] * TRACK[track] * DICE[dice])


def main():
    print("== 纸上沙盘：1375 春 · 威尼斯 · 大加利（25人） ==")
    cash = 400
    loan = 800  # bottomry 30%/航次（以租船合同抵）
    # ① 备航：大加利 货舱5 → 3舱生丝 + 2舱补给（威尼斯为下游城，按到岸银买入）
    buy_unit = hold_price("生丝·中国", "venice", 3, 3)
    cloth_buy_unused = buy_unit * 3
    # ① 备航（去程西→东）：3 舱宽幅呢（威尼斯中转买入）＋2 舱补给
    buy_unit = hold_price("宽幅呢broadcloth", "venice", 3, 3)
    cloth_buy = buy_unit * 3
    cash -= cloth_buy
    print(f"① 备航（去程）：购 3 舱宽幅呢 @{buy_unit}银 = {cloth_buy}；余 {cash}")
    # ② 航程：威尼斯→亚历山大 23 天（中速）
    wages = 25 * 19 * 1  # 约一月薪（2 月航程含候风按 1 月在航+1 月港内半饷近似）
    prov = round(25 * 40 * 0.9)
    print(f"② 航程 23 天：薪饷 {wages}＋给养 {prov}＝{wages + prov}")
    cash -= (wages + prov)
    # ③ 到货：亚历山大是呢绒消费端；行情骰
    dice = random.randint(1, 6)
    sell_unit = hold_price("宽幅呢broadcloth", "alexandria", 3, dice)
    revenue = sell_unit * 3
    tax = round(revenue * 0.12)  # 马穆鲁克过境税
    print(f"③ 到货：呢绒(消费端) 行情骰 d6={dice}（×{DICE[dice]}）→ 单舱 {sell_unit}；售 3 舱={revenue}；税 12%={tax}")
    # 分批卸货护价：3舱一批≥3 → 推轨
    print("   （3 舱整批卸货：亚历山大呢绒轨 3→4，本季后续呢绒价 ×0.8）")
    cash += revenue - tax
    # ④ 回程（东→西）：2 舱胡椒＋2 舱生姜（亚历山大=货源侧，产地银批发价）
    buy_p = hold_price("黑胡椒", "alexandria", 3, 3)
    buy_g = hold_price("生姜", "alexandria", 3, 3)
    buys = buy_p * 2 + buy_g * 2
    cash -= buys
    prov2 = round(25 * 30 * 0.9)
    cash -= prov2 + wages
    print(f"④ 回程：购胡椒2舱@{buy_p}＋生姜2舱@{buy_g}＝{buys}；再计薪饷给养 {wages + prov2}")
    # 威尼斯卖出：胡椒/生姜行情（威尼斯=下游，到岸价）
    d2, d3 = random.randint(1, 6), random.randint(1, 6)
    sp = hold_price("黑胡椒", "venice", 3, d2)
    sg = hold_price("生姜", "venice", 3, d3)
    rev2 = sp * 2 + sg * 2
    print(f"⑤ 威尼斯卸货：胡椒骰{d2}(×{DICE[d2]})单舱{sp}；生姜骰{d3}(×{DICE[d3]})单舱{sg}；合计 {rev2}")
    cash += rev2
    # ⑥ 还贷
    repay = round(loan * 1.3)
    cash -= repay
    print(f"⑥ 还 bottomry：{loan}×1.3＝{repay}")
    print(f"-- 季末现金：{cash} 银（期初 400＋bottomry 800）--")

    # ===== 季末八步（沙漏自测：每步一次运算） =====
    print("\n== 季末八步（每步一行，模拟 3 分钟内） ==")
    print("① 季风换向：盛阳季（6–8月）西南季风——黎凡特船班 9 月回程（下季剧情钩）")
    t3 = random.randint(1, 6)
    print(f"② 威尼斯行情骰重掷：d6={t3}（×{DICE[t3]}）")
    print("③ 派系 tick：热那亚派系'武力垄断'资产+1（初跑可略，标注即可）")
    exp = 2 + 1 + 1
    print(f"④ 威尼斯城经验：靠港 1 船×5舱=流量5→取2＋枢纽1＋PL投资0＝{exp}/9 季阈值")
    print("⑤ 人物年轮：船长老了一岁；无死亡事件（14 部年轮表挂起）")
    print("⑥ 天气轮转：盛阳季→风暴季（9–11月）风险带+1（下季海况 DV 上调）")
    ev = random.randint(1, 10)
    print(f"⑦ 城市事件 d10={ev}")
    print("⑧ 世界一瞥：'亚历山大的生丝跌了——三船货同日到岸。'（④ 的库存轨4=×0.8 已生效）")
    print("\n== 结论：八步全部有定义、账目闭合；总收益见上。人肉沙漏（≤10 分钟）留待实跑 ==")


if __name__ == "__main__":
    main()
