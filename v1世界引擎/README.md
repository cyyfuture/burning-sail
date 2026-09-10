# v1 世界引擎 —— 施工进度与导航

> 《燃帆》世界引擎扩展包：14 世纪开局、五纪推进到蒸汽前夜。计划见 `../V1计划总纲/`；本目录是**产出物**。
> 纪律：`data/*.json` 是唯一真源；表页由 `build_engine.py` 渲染，禁止手改生成区（`<!-- ENGINE:名 -->` 标记内）。

## 当前状态（2026-09-10，P0–P4 + 试航包完成）

| 阶段 | 状态 | 交付物 |
|---|---|---|
| P0 基座冻结 | ✅ | cities.json（120城：一级48+二级72，id稳定幂等）；00_五纪总扉页；build_engine.py |
| P1 经济链 | ✅ | wages/survival/goods/availability 四 JSON；01–05 分册；三样板账（09§9.3） |
| P2 船与建筑 | ✅ | ships（40型，07章七船 verbatim，公式复算最大偏差8%）/shipyards（48城矩阵）/buildings（14型）；06–07 分册 |
| P3 时间与航行 | ✅ | distances（45边，史实回放8/8过±30%）/monsoon（6风区）；08 分册（双轨钟/季风五选/洋流八带/航道三态/试航四步） |
| P4 跑商引擎 | ✅ | prices（39品×120城档+48城市况条，砸盘模拟−40%过）；09 分册（七步卡/垄断六态/融资三件套/陆桥三走廊/城市发展/季末闸门） |
| S1 试航包 | ✅ | 试航包/试航包.md（8城+4船+7货+七步卡+季末卡+开局剧本）＋sandbox_test.py（季循环账目闭合自测） |
| P5 任务世界 | ⬜ 下一步 | 原子卡/15进程/16泛型/素材四库（计划04部） |
| P6 人物与AI | ⬜ | 维度/生死/三层AI（计划05部） |
| P7 文本与工具 | ⬜ | 语料/帷幕/面板/提示词（计划06-07部） |

## 构建命令

```
python data/select_cities.py        # 120城（P0，改名单后跑）
python data/extract_wages.py        # 工资（源数据在调研2 I册，改动需手改脚本内REGIONS）
python data/build_economy_data.py   # goods/survival/availability
python data/build_ships_data.py     # ships/shipyards/buildings（含船价公式复算DoD）
python data/build_time_data.py      # distances/monsoon（含史实回放8例）
python data/build_prices.py         # prices（含砸盘模拟）
python build_engine.py              # 渲染全部表页；--check 校验过期；--list 列渲染器
python 试航包/build_pack.py          # 试航包
python 试航包/sandbox_test.py        # 纸上沙盘机械化自测
```

## 关键设计决策（本轮新增，详见各分册对接条）

- **舱位双口径**：跑商用舱位整批价（10章冻结锚），查价差合理性用真实链价（gAg）——两套并存。
- **货源侧城市**：每品定义"产地+第一中转"（SOURCE_SIDE），货源侧按产地银、下游按到岸银——防止中转城假套利，还原黎凡特 ×3 价差。
- **行情敏感度**：骰档每 +0.1 乘数≈净利 +10–20pp——跑商博弈重心在择时与供需轨，不在选货。
- **史实校准**：船价公式（吨位×全装率×纪通胀）复算 06 章七船 ≤±8%；里程表 8 条史实航线 ±30% 内 8/8；砸盘模拟精确 −40%。

## 已知待办

- 甘杜坐标 [估·代理]（西非金路城，两库均无，待用户核定）；15 城估坐标标注 †。
- 马六甲档位/二级城市况靠四问法即兴（设计如此）。
- P5–P7 未开工；试航包需实跑 2 团回收问题清单（≥10 条）后修订。
