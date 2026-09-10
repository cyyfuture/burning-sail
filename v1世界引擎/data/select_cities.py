# -*- coding: utf-8 -*-
"""
select_cities.py —— P0-1 任务：冻结 v1 世界引擎 120 城名单（48 一级 + 72 二级）。
唯一真源：
  - 工程2 1450 名册（538 城：zh/la/lon/lat/nation/tier/note）
  - 调研2 v4 城市库（125 城：四槽覆盖 粮价/工资/生存/补给）
  - 调研2 v4 生存篮 40 港表（I_生计给养总册 §3.3）
产出：cities.json（data/ 内唯一真源，build_engine.py 只读它渲染表页）。
重跑：python select_cities.py（幂等，覆盖写 cities.json）。
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_W2 = HERE.parents[2]  # W2_TheAgeofBruningSail
G2_CITIES = ROOT_W2 / "工程2-燃帆世界地图" / "data" / "historical" / "cities-1450.json"
S2_CITIES = ROOT_W2 / "调研" / "调研2-大航海时代物价体系" / "v4" / "03_港口谱系" / "cities_v4.json"
S2_SURVIVAL = ROOT_W2 / "调研" / "调研2-大航海时代物价体系" / "v4" / "08_生计给养" / "I_生计给养总册.md"

# ---------- 手工映射与补录（名字 → 工程2 1450 名册条目 / 手工坐标） ----------
# 游戏标准名 → 工程2名册内的匹配名（None = 名册中不存在，走手工坐标）
G2_ALIAS = {
    "瓦伦西亚": "巴伦西亚",
    "伊斯坦布尔": "君士坦丁堡",   # 1450 年仍在拜占庭手中；S3 起改名
    "苏州": "苏州",
    "霍尔木兹": "荷姆兹",
    "墨西哥城": "阿兹特-特诺奇提特兰",  # 同址；S3 起为西属墨西哥城
    "波托西": "波托西-塞罗里科",
    "巴伊亚": "巴伊亚-托多斯奥斯圣托斯",
    "亚历山大港": "亚历山大里亚",
    "的黎波里": "的黎波里-沙姆",
    "宁波": "宁波-明州",
    "圣多明各": "阿托-圣多明各",
    "韦拉克鲁斯": "韦拉克鲁斯-里卡",
}

# 名册中不存在、需要手工坐标的城（真实地点，按史实坐标；first_age 标注进入引擎的纪）
MANUAL_GEO = {
    # 欧洲（调研2 数据城但 1450 名册未收）
    "马德里":      (40.42, -3.70, "cas", "S1"),
    "莱比锡":      (51.34, 12.37, "sas", "S1"),
    "华沙":        (52.23, 21.01, "pol", "S1"),
    "牛津":        (51.75, -1.26, "eng", "S1"),
    "巴利亚多利德": (41.65, -4.72, "cas", "S1"),
    "马赛":        (43.30, 5.37, "fra", "S1"),
    "法马古斯塔":   (35.12, 33.94, "cyo", "S1"),   # 塞浦路斯，威尼斯殖民地
    # 1450 年后兴起 / 名册未收
    "长崎":        (32.75, 129.87, "jpx", "S2"),
    "摩卡":        (13.32, 43.25, "yem", "S1"),
    "科钦":        (9.93, 76.26, "kerala", "S1"),
    "马尼拉":      (14.60, 120.98, "tag", "S2"),
    "利马":        (-12.05, -77.04, "spa", "S3"),
    "哈瓦那":      (23.13, -82.37, "spa", "S2"),
    "卡塔赫娜":    (10.39, -75.51, "spa", "S3"),
    "巴达维亚":    (-6.21, 106.85, "bat", "S4"),
    "巴巴多斯":    (13.10, -59.62, "eng", "S4"),
    # 用户需求城：西非金路（坐标为估·代理，待用户核定）
    "甘杜":        (4.54, 12.55, "song", "S1"),
}

# ---------- 48 一级城（全参数） ----------
# 39 座生存港 + S1 补 7 城（威尼斯/热那亚/布鲁日/甘杜/泉州/杭州/亚历山大港）+ 开罗/卡利卡特
L1_NAMES = [
    # —— 生存 40 港（39 城，序=调研2 §3.3）——
    "伦敦", "阿姆斯特丹", "安特卫普", "巴黎", "斯特拉斯堡", "瓦伦西亚", "马德里",
    "佛罗伦萨", "那不勒斯", "奥格斯堡", "莱比锡", "维也纳", "但泽", "华沙", "克拉科夫",
    "塞维利亚", "里斯本", "汉堡", "哥本哈根", "斯德哥尔摩", "伊斯坦布尔", "莫斯科",
    "北京", "苏州", "广州", "京都", "长崎", "马尼拉", "巴达维亚", "马六甲", "果阿",
    "霍尔木兹", "摩卡", "墨西哥城", "波托西", "利马", "哈瓦那", "巴巴多斯", "巴伊亚",
    # —— S1 关键城补录（D5）——
    "威尼斯", "热那亚", "布鲁日", "甘杜", "泉州", "杭州", "亚历山大港",
    # —— 补足 48：S1 红海枢纽 + S2 达伽马目的地 ——
    "开罗", "卡利卡特",
]

# ---------- 72 二级城（简化参数） ----------
L2_NAMES = [
    # T1 余（5）
    "麦加", "罗马", "南京", "德里", "毗奢耶那伽罗",
    # T2 余（30）
    "好望角", "亚丁", "阿勒颇", "大马士革", "耶路撒冷", "突尼斯", "非斯",
    "阿德里安堡", "布达", "米兰", "巴塞罗那", "萨拉戈萨", "托莱多", "格拉纳达",
    "吕贝克", "爱丁堡", "布拉格", "维尔纽斯", "大不里士", "巴格达", "赫拉特",
    "撒马尔罕", "汉城", "阿瑜陀耶", "升龙", "勃固", "拉合尔", "高尔", "艾哈迈达巴德", "库斯科",
    # T3 与调研2补充（37）：北海—波罗的海 / 西欧 / 地中海 / 黑海 / 北非 / 西非—东非 / 红海—印度洋 / 东亚 / 东南亚 / 新大陆
    "布鲁塞尔", "莱顿", "里加", "卑尔根", "诺夫哥罗德",
    "波尔多", "拉罗谢尔", "波尔图", "牛津", "巴利亚多利德", "马赛",
    "巴勒莫", "法马古斯塔", "休达", "丹吉尔", "阿尔及尔", "的黎波里",
    "卡法", "塔纳",
    "廷巴克图", "加奥", "卡诺", "基尔瓦", "蒙巴萨", "马林迪", "索法拉",
    "吉达", "马斯喀特", "坎贝", "科钦",
    "那霸", "宁波", "堺", "万丹",
    "圣多明各", "韦拉克鲁斯", "卡塔赫娜",
]

# 游戏分区（写表页用；跨区城市取主要贸易归属）
REGION = {
    "西欧": ["伦敦", "牛津", "布鲁日", "安特卫普", "布鲁塞尔", "阿姆斯特丹", "莱顿",
             "加来", "巴黎", "斯特拉斯堡", "波尔多", "拉罗谢尔", "南特"],
    "伊比利亚": ["里斯本", "波尔图", "塞维利亚", "瓦伦西亚", "马德里", "巴利亚多利德",
                 "巴塞罗那", "萨拉戈萨", "托莱多", "格拉纳达"],
    "地中海": ["威尼斯", "热那亚", "佛罗伦萨", "那不勒斯", "罗马", "米兰", "马赛",
               "巴勒莫", "法马古斯塔", "休达", "丹吉尔", "阿尔及尔", "突尼斯", "的黎波里",
               "亚历山大港", "开罗", "麦加", "耶路撒冷", "大马士革", "阿勒颇", "阿德里安堡"],
    "黑海—东欧": ["君士坦丁堡", "伊斯坦布尔", "卡法", "塔纳", "布达", "维也纳", "布拉格",
                 "克拉科夫", "华沙", "维尔纽斯", "里加", "莫斯科", "诺夫哥罗德", "莱比锡",
                 "奥格斯堡", "但泽", "吕贝克", "汉堡", "卑尔根", "哥本哈根", "斯德哥尔摩", "爱丁堡"],
    "红海—波斯湾": ["霍尔木兹", "摩卡", "亚丁", "吉达", "马斯喀特", "巴格达", "大不里士"],
    "东非—西非": ["甘杜", "廷巴克图", "加奥", "卡诺", "基尔瓦", "蒙巴萨", "马林迪",
                  "索法拉", "好望角", "非斯"],
    "印度洋": ["开罗", "卡利卡特", "科钦", "坎贝", "艾哈迈达巴德", "果阿", "高尔",
               "毗奢耶那伽罗", "德里", "拉合尔", "赫拉特", "撒马尔罕"],
    "东南亚": ["马六甲", "万丹", "巴赛", "阿瑜陀耶", "升龙", "勃固", "马尼拉", "巴达维亚"],
    "东亚": ["广州", "泉州", "杭州", "苏州", "宁波", "南京", "北京", "那霸", "堺",
             "京都", "长崎", "汉城"],
    "加勒比—美洲": ["圣多明各", "哈瓦那", "卡塔赫娜", "韦拉克鲁斯", "墨西哥城", "波托西",
                   "利马", "库斯科", "巴巴多斯", "巴伊亚"],
}

# 调研2 城市名 → 引擎标准名（四槽与生存数据联接键）
S2_ALIAS = {"江南（苏州带）": "苏州", "苏州（江南）": "苏州", "爱丁堡（利斯）": "爱丁堡",
            "霍尔木兹/巴士拉-亚丁（红海波斯湾带）": "霍尔木兹",
            "摩卡（也门）": "摩卡", "巴巴多斯/加勒比糖岛": "巴巴多斯", "巴伊亚（巴西）": "巴伊亚"}


def _clean_surv(raw):
    """'**17.8**（V5直算…）' → ('17.8', 'V5直算…')；'8-12' → ('8-12', None)。"""
    if not raw:
        return None, None
    txt = raw.replace("*", "")
    m = re.match(r"^([\d\.\-–]+)(?:（(.*)）|\((.*)\))?$", txt.strip())
    if m:
        return m.group(1), (m.group(2) or m.group(3) or None) or None
    return txt, None


def region_of(name):
    for reg, names in REGION.items():
        if name in names:
            return reg
    # 次选：别名再试一次（伊斯坦布尔→君士坦丁堡 等）
    alias = {v: k for k, v in G2_ALIAS.items()}
    n2 = alias.get(name, name)
    for reg, names in REGION.items():
        if n2 in names or any(n2 in x for x in names):
            return reg
    return "待定"


def parse_survival():
    """从调研2 §3.3 抓 40 港单月最低生活费。"""
    text = S2_SURVIVAL.read_text(encoding="utf-8").splitlines()
    out = {}
    pat = re.compile(r"^\|\s*(\d{1,2})\s*\|\s*([^|]+?)\s*\|\s*[^|]*\|\s*([^|]+?)\s*\|")
    for line in text:
        m = pat.match(line)
        if not m:
            continue
        idx, name, val = m.group(1), m.group(2).strip(), m.group(3).strip()
        if name in ("港", "品") or idx in ("#",):
            continue
        name = S2_ALIAS.get(name, name)
        out[name] = val
    return out


# 显式 ASCII id（保证跨进程稳定；调研2 未覆盖的城全部在此登记）
ID_MAP = {
    "斯特拉斯堡": "strasbourg", "华沙": "warsaw", "京都": "kyoto", "巴伊亚": "bahia",
    "布鲁日": "bruges", "甘杜": "gandu", "泉州": "quanzhou", "杭州": "hangzhou",
    "亚历山大港": "alexandria", "卡利卡特": "calicut", "麦加": "mecca", "罗马": "rome",
    "南京": "nanjing", "德里": "delhi", "毗奢耶那伽罗": "vijayanagara", "好望角": "capetown",
    "亚丁": "aden", "阿勒颇": "aleppo", "大马士革": "damascus", "耶路撒冷": "jerusalem",
    "突尼斯": "tunis", "非斯": "fez", "阿德里安堡": "edirne", "布达": "buda",
    "萨拉戈萨": "zaragoza", "托莱多": "toledo", "格拉纳达": "granada", "布拉格": "prague",
    "维尔纽斯": "vilnius", "大里士": "tabriz", "巴格达": "baghdad", "赫拉特": "herat",
    "撒马尔罕": "samarkand", "汉城": "hanyang", "阿瑜陀耶": "ayutthaya", "升龙": "thanglong",
    "勃固": "pegu", "拉合尔": "lahore", "高尔": "gaur", "艾哈迈达巴德": "ahmedabad",
    "库斯科": "cusco", "卑尔根": "bergen", "拉罗谢尔": "larochelle", "波尔图": "porto",
    "巴勒莫": "palermo", "法马古斯塔": "famagusta", "休达": "ceuta", "丹吉尔": "tangier",
    "阿尔及尔": "algiers", "的黎波里": "tripoli", "卡法": "caffa", "塔纳": "tana",
    "廷巴克图": "timbuktu", "加奥": "gao", "卡诺": "kano", "基尔瓦": "kilwa",
    "蒙巴萨": "mombasa", "马林迪": "malindi", "索法拉": "sofala", "吉达": "jeddah",
    "马斯喀特": "muscat", "坎贝": "khambat", "科钦": "kochi", "那霸": "naha",
    "宁波": "ningbo", "堺": "sakai", "卡塔赫娜": "cartagena", "马德里": "madrid",
    "莱比锡": "leipzig", "牛津": "oxford", "巴利亚多利德": "valladolid", "马赛": "marseille",
    "长崎": "nagasaki", "摩卡": "mokha", "马尼拉": "manila", "利马": "lima",
    "哈瓦那": "havana", "巴达维亚": "batavia", "巴巴多斯": "barbados", "伊斯坦布尔": "istanbul",
    "瓦伦西亚": "valencia", "苏州": "suzhou", "霍尔木兹": "hormuz", "墨西哥城": "mexico",
    "波托西": "potosi", "开罗": "cairo", "威尼斯": "venice", "热那亚": "genoa",
}


def main():
    g2 = {c["zh"]: c for c in json.loads(G2_CITIES.read_text(encoding="utf-8"))["cities"]}
    s2_raw = json.loads(S2_CITIES.read_text(encoding="utf-8"))["cities"]
    s2 = {}
    for c in s2_raw:
        n = S2_ALIAS.get(c["name"], c["name"])
        s2[n] = c
    surv = parse_survival()

    def build(name, rank):
        g2name = G2_ALIAS.get(name)
        rec_g2 = g2.get(g2name) or g2.get(name)
        rec_s2 = s2.get(name)
        if rec_g2:
            lon, lat = rec_g2["lon"], rec_g2["lat"]
            nation = rec_g2["nation"]
            tier = rec_g2["tier"]
            geo_est = False
        elif name in MANUAL_GEO:
            lat, lon, nation, age = MANUAL_GEO[name]
            tier = 4  # 名册外城统一按地区城档，表页以 first_age 呈现
            geo_est = True
        else:
            raise KeyError(f"城市 {name} 既不在工程2名册也不在手工补录表中")
        first_age = MANUAL_GEO.get(name, (None, None, None, "S1"))[3] if name in MANUAL_GEO else "S1"
        surv_val, surv_note = _clean_surv(surv.get(name))
        entry = {
            "id": ID_MAP.get(name) or re.sub(r"\s+", "", (rec_s2 or {}).get("id") or "").lower(),
            "name": name,
            "rank": rank,
            "tier": tier,
            "nation_1450": nation,
            "lon": lon,
            "lat": lat,
            "region": region_of(name),
            "first_age": first_age,
            "geo_est": geo_est,
            "g2_match": rec_g2["zh"] if rec_g2 else None,
            "slots": (rec_s2 or {}).get("four"),
            "survival_gAg": surv_val,
            "survival_note": surv_note,
            "sea": (rec_s2 or {}).get("sea"),
            "note": (rec_g2 or {}).get("note") or (rec_s2 or {}).get("role") or "",
        }
        return entry

    cities = []
    dup = set()
    for n in L1_NAMES:
        if n in dup:
            raise ValueError(f"L1 重复：{n}")
        dup.add(n)
        cities.append(build(n, 1))
    for n in L2_NAMES:
        if n in dup:
            raise ValueError(f"L2 与 L1 重复：{n}")
        dup.add(n)
        cities.append(build(n, 2))

    # id 唯一化（空 id 或冲突时按 region+序号重排）
    seen = {}
    for c in cities:
        if not c["id"] or c["id"] in seen:
            c["id"] = f"{c['region'][:2].lower()}_{''.join(w[0] for w in c['name'])}".encode(
                "unicode_escape").decode("latin1")
        # 中文首字母无意义时直接用序号
        if not c["id"].isascii() or c["id"] in seen:
            c["id"] = f"c{len(seen) + 1:03d}"
        seen[c["id"]] = True

    # 覆盖度审计
    n_l1 = sum(1 for c in cities if c["rank"] == 1)
    n_l2 = sum(1 for c in cities if c["rank"] == 2)
    n_surv = sum(1 for c in cities if c["survival_gAg"])
    n_slots = sum(1 for c in cities if c["slots"] and sum(1 for s in c["slots"] if s == "●") >= 3)
    n_est = [c["name"] for c in cities if c["geo_est"]]
    out = {
        "_meta": {
            "说明": "《燃帆》v1 世界引擎城市名册（48 一级 + 72 二级，P0 冻结）。",
            "rank": "1=一级全参数（基价/工资/生存/建筑/发展/造船）；2=二级简化（基价修正带＋特色一行）",
            "tier": "沿用工程2 tier：1帝都 2王都 3大都会 4地区城 5城镇港砦",
            "slots": "调研2 v4 四槽覆盖：粮价/工资/生存/补给（●全 ◐缺 供给代理 缺）",
            "first_age": "该城进入引擎的纪（S1=1350 起即存在；S2+/S3+ = 需纪推进或事件后开放）",
            "geo_est": "true=坐标为估·代理（名册外手工补录），待核",
            "上游": {
                "工程2": "data/historical/cities-1450.json（538 城）",
                "调研2": "v4/03_港口谱系/cities_v4.json + v4/08_生计给养/I_生计给养总册.md §3.3",
            },
            "审计": {"一级": n_l1, "二级": n_l2, "有生存数据": n_surv,
                     "四槽≥3": n_slots, "估坐标城": n_est},
        },
        "cities": cities,
    }
    dest = HERE / "cities.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK cities.json: 一级 {n_l1} + 二级 {n_l2} = {len(cities)} 城")
    print(f"生存数据覆盖 {n_surv} 城；四槽≥3 有 {n_slots} 城；估坐标 {len(n_est)} 城：{'、'.join(n_est)}")
    # 名单自检：区域覆盖
    from collections import Counter
    print("分区分布:", dict(Counter(c["region"] for c in cities)))


if __name__ == "__main__":
    main()
