# v1 世界引擎 —— 施工进度与导航

> 《燃帆》世界引擎扩展包：14 世纪开局、五纪推进到蒸汽前夜。计划见 `../V1计划总纲/`；本目录是**产出物**。
> 纪律：`data/*.json` 是唯一真源；表页由 `build_engine.py` 渲染，禁止手改生成区（`<!-- ENGINE:名 -->` 标记内）。

## 当前状态（2026-09-12，**P0–P7 全部完成 + 集成回归就绪**）

| 阶段 | 状态 | 交付物 |
|---|---|---|
| P0 基座冻结 | ✅ | cities.json（120城：一级48+二级72，id稳定幂等）；00_五纪总扉页；build_engine.py |
| P1 经济链 | ✅ | wages/survival/goods/availability 四 JSON；01–05 分册；三样板账（09§9.3） |
| P2 船与建筑 | ✅ | ships（40型，07章七船 verbatim，公式复算最大偏差8%）/shipyards（48城矩阵）/buildings（14型）；06–07 分册 |
| P3 时间与航行 | ✅ | distances（45边，史实回放8/8过±30%）/monsoon（6风区）；08 分册（双轨钟/季风五选/洋流八带/航道三态/试航四步） |
| P4 跑商引擎 | ✅ | prices（39品×120城档+48城市况条，砸盘模拟−40%过）；09 分册（七步卡/垄断六态/融资三件套/陆桥三走廊/城市发展/季末闸门） |
| S1 试航包 | ✅ | 试航包/试航包.md（8城+4船+7货+七步卡+季末卡+开局剧本＋S1战斗/任务速查）＋sandbox_test.py（季循环账目+AI一季自测） |
| 战斗纪门控与武器物价 | ✅ | availability.json 51 项；04 分册混合页（单炮条款/铁炮/五纪速查/对接条） |
| P5 任务世界 | ✅ | processes.json（15进程卡）＋quests.json（60固定任务卡，价值公式回代 60/60 过±40%）＋qst_materials.json（四库+16泛型+文化措辞层）＋tags.json（八味）；10–12 分册 |
| **P6 人物与AI** | ✅ | **npcs.json（18具名：12章12锚点+S1起手6名，五轴/称号/效用三字段，脚本自检全绿）＋factions.json（16势力纪门控，军财谍/资产/行动池/联合省沙盘因果链）＋13_人物系统.md（三源对照/五轴20称号10挂点/三档面板/恩义血债/年龄曲线/婚育死亡/继承传承/年轮d20）＋14_世界AI.md（三层架构/行动表15族/幽灵航程/城市三数字/faction turn五步/四触点/沙漏预算≤10分钟）** |
| **P7 文本与工具** | ✅ | **rhetoric.json（40拆解卡+72句库+20选目，版权双标注硬闸）＋15_文本渲染库.md（三大环境桶/人物四桶/清单旁白5模板）＋16_帷幕速查与带团技艺.md（18帷幕卡+4深化+三层节奏律+播报术+安全三脚本）；`../可视化工具/`（KP/PL 双端单文件面板 panel/index.html + world_save Schema + 样例存档 + 14 张格子图 SVG + token 印刷页）；`../提示词库/`（语法变量表/12母场景/七类目录/SD备选与资源清单）** |
| **集成回归** | ✅（脚本侧） | **check_consistency.py（跨JSON交叉引用+16章锚点对拍：0错误/3警告留痕）＋全管线跑绿＋试航包/五日试炼.md（5团活体测试脚本+盲测记录表模板）**。人肉项待办：第三方 GM 盲测一团、实跑 2 团回收问题清单 |
| **KP任务面板**（任务侧专精，2026-09-12） | ✅ | **任务面板/（build_panel.py→index.html 单文件离线网页，双击即用）：任务盘（15进程/60固定卡·纪/味/体量/风险筛选·已接/完成/悔约状态追踪 localStorage）＋随机生成器（d16 触发＋16 泛型六步链逐掷＋文化措辞人名）＋报酬计算器（公式/封顶/两源护栏/速查表）＋素材库速查（人名录/误差40/反转32/地物32/文化措辞/八味）＋存留池与季末收盘（导出导入）。panel_core.js 纯逻辑模块＋smoke_test.js 自检；与 ../可视化工具/panel 双端面板互补——那边管存档与全系统向导，这边管任务专精** |

## 构建命令

```
python data/select_cities.py          # 120城（P0）
python data/extract_wages.py          # 工资
python data/build_economy_data.py     # goods/survival/availability
python data/build_ships_data.py       # ships/shipyards/buildings（含船价公式复算DoD）
python data/build_time_data.py        # distances/monsoon（含史实回放8例）
python data/build_prices.py           # prices（含砸盘模拟）
python data/build_quests_data.py      # processes/quests（含六要素/公式回代/主味分布自检）
python data/build_quest_materials.py  # qst_materials/tags（含库容量自检）
python data/build_npcs.py             # npcs（18具名，含12锚点全建档/轴值-称号自洽自检）
python data/build_factions.py         # factions（16势力，含属性/行动池/沙盘链自检）
python data/build_rhetoric.py         # rhetoric（40拆解卡+72句库，含版权标注/帷幕索引自检）
python data/check_consistency.py      # T8.4.2 一致性终检（交叉引用+16章锚点对拍）
python build_engine.py                # 渲染全部表页（22渲染器）；--check 校验过期；--list 列渲染器
python 试航包/build_pack.py            # 试航包
python 试航包/sandbox_test.py          # 纸上沙盘自测（季循环账目+AI一季沙盘）
python ../可视化工具/build_panel.py     # KP/PL 双端面板（panel/index.html）
python ../可视化工具/build_gridmaps.py  # 格子图模板（14 SVG）
python 任务面板/build_panel.py         # KP任务面板（任务侧专精单文件网页）
node 任务面板/smoke_test.js            # 面板冒烟测试（Node ≥18）
python build_site_v1.py               # 本目录离线站点 index.html
```

## 关键设计决策（P6/P7 新增，详见各分册对接条）

- **五轴性格=AI 权重**：胆量±2 直改军族成败分布（沙盘实测差 22pp）；血债≥5 自动锁"复仇"族——性格不是贴纸，是决策表（13/14 分册）。
- **NPC 三档不全量**：路人零数字/具名七字段/重要人物全卡；`npcs.json` 出厂 18 名重要（12 章 12 锚点 + S1 起手 6 名虚构锚点），其余 GM 现挂。
- **派系层双轨**：12 章八势力（双帝国并卡）S4–S5 主场 + S1 起五家（威尼斯/热那亚/马穆鲁克/汉萨/明廷）；每卡带"前史形态"字段跨纪平移；联合省单 tick 沙盘可复现"护航卡特尔→保费上涨"。
- **野心类归档**：野心自由文本 + 五类归档（发财/复仇/扬名/安稳/权势）查行动表；行动成败=d20+权重 ≥12。
- **语料版权双标注**：`[公版原文]` 仅 4 处可核实名句，其余全为 `[技法仿写]`（自写示范句）——构建脚本硬闸，无标注不出库。
- **句库 72 条三腔**：编年史/酒馆/密报 ×24，18 帷幕与 16 泛型各 ≥2 条覆盖；季末播报"每行一个钩子+追问预算"。
- **面板双端一档**：`?role=kp|pl` 同一存档（world_save.json，文件级同步）；数据构建期内嵌（双击即开）；季末八步向导+泛型生成器+派系 tick 向导。
- **build_engine 防护**：ENGINE 标记未闭合/重复即报错拒写（防注入吃尾）。

## 已知待办

- 甘杜坐标 [估·代理]（待用户核定）；15 城估坐标标注 †；里程端点"马德拉/佛得角锚地"为路线留痕名（check_consistency WARN 级，不阻断）。
- 武器物价：长弓/弩与 S1–S2 射石炮数值 `[评]` 补档，待实跑校准。
- 任务系统：14 张 premium/总包卡期权作价折算表（依赖 P6 人物档案——已具备，可在下一轮补表）；60 卡待实跑回收。
- **人肉验收**：第三方 GM 用试航包盲测一团（T8.4.3，`试航包/五日试炼.md` 末尾有记录表模板）；实跑 2 团回收 ≥10 条问题清单后修订。
