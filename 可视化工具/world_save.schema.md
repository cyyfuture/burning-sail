# world_save —— 世界存档 Schema（T7.1.1.b）

> 分册数据（`v1世界引擎/data/*.json`）是**出厂值**；本档是**战役值**。KP 面板读写、文件级同步（导出/导入 JSON 即"谁改了什么"）。

## 结构

```json
{
  "meta":    {"age": "S1–S5", "year": 1375, "season": "春|夏|秋|冬", "day": 1–91, "weather": "常|风暴季|无风带|疫风"},
  "cities":  {"<city_id>": {"exp": 0, "port_pool": ["N01"], "<品名>": 0–5}},
  "fleet":   {"船名","船型","班次","士气","备用物资","船体","炮位","货舱","海员"},
  "ledger":  {"银币","声望","恶名","潮汐","地产":[],"股单":[],"贷款":[]},
  "npcs":    {"N01": {"恩":0,"债":0,"last":"","situation":"","缺席":false}},
  "factions":{"<fid>": {"军","财","谍","钟":{"目标名":格数},"log":[]}},
  "quests":  {"visible":[任务文本],"pool":[存留池]},
  "ghosts":  [{"owner","from","to","depart旬","days"}],
  "discovered": ["city_id", …],
  "log":     [世界一瞥与事件流水]
}
```

## 字段映射表（01–05 部每张表的落点）

| 分册数据 | 落点 | 说明 |
|---|---|---|
| cities.json（120城） | `cities` 键集 + 内嵌地图 | 二级城惰性：PL 光顾时才建键 |
| wages.json / survival.json | GM 口算（02/03 分册表） | 面板不背工资账——纸表更快 |
| goods.json / prices.json strips | `cities.<id>.<品>`（库存轨 0–5） | 出厂轨=3；成交价=基价×城档×轨×行情骰 |
| availability.json | GM 口算（04 分册三态表） | 纪门控由 `meta.age` 表达 |
| ships.json | `fleet` + PL 端船型下拉 | 造船走 06 分册，面板只管运行时 |
| buildings.json | `ledger.地产/股单` | 等级联动走 07 分册 |
| distances/monsoon | PL 端"季风窗" + 幽灵航程端点 | 里程 GM 查 08 分册表 |
| processes/quests/qst_materials | `quests` + 任务台生成器 | 生成文本即卡面 |
| npcs.json / factions.json | `npcs` / `factions` | 出厂档案不复制进存档，只存变化量 |

## 纪律

- 存档人可读（JSON，带 `_说明` 头）；**禁止**把出厂数据整表拷进存档。
- KP/PL 共享同一份存档文件；投屏时 KP 用"玩家安全视图"（`?role=pl`）。
