# -*- coding: utf-8 -*-
"""
build_panel.py —— P7 可视化面板（计划07部 T7.1.x，施工计划 B10）。
产出：
  panel/index.html           KP/PL 双端单文件静态面板（数据构建期内嵌，双击即开）
  样例存档_S1_1375.json      S1 开局样例战役存档（world_save 格式）
  world_save.schema.md       存档 Schema 与 01–05 部字段映射表
设计（T7.1.1.a 决议）：纯前端静态、无服务器、?role=kp|pl 双视图、localStorage + 文件导入导出；
地图为内嵌 SVG 点阵（不接在线瓦片）；KP 端含季末八步向导 / 派系 tick 向导 / 泛型任务生成器。
用法：python build_panel.py
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENGINE_DATA = (BASE.parent / "v1世界引擎" / "data").resolve()
if not ENGINE_DATA.is_dir():
    raise SystemExit("找不到 v1世界引擎/data")
OUT_DIR = BASE / "panel"


def load(name):
    return json.loads((ENGINE_DATA / name).read_text(encoding="utf-8"))


# ---------------- 内嵌数据裁剪 ----------------
cities_raw = load("cities.json")["cities"]
cities = [{"id": c["id"], "name": c["name"], "lon": c["lon"], "lat": c["lat"],
           "region": c["region"], "rank": c["rank"], "tier": c["tier"],
           "age": c["first_age"]} for c in cities_raw]
strips = load("prices.json")["strips"]
strip_map = {cid: [{"品": g["品"], "档": g["档"], "基价银": g["基价银"], "轨": 3}
                    for g in s["goods"]] for cid, s in strips.items()}
npcs = load("npcs.json")
factions = load("factions.json")
mats = load("qst_materials.json")
rhet = load("rhetoric.json")
monsoon = load("monsoon.json")
ships = load("ships.json")["ships"]

EMBED = {
    "cities": cities, "strips": strip_map,
    "npcs": npcs["npcs"], "axes": npcs["五轴"], "titles": npcs["组合称号表"],
    "factions": factions["factions"],
    "generics": mats["generics"], "errors": mats["errors"], "reversals": mats["reversals"],
    "names": mats["names"], "glances": rhet["glances"],
    "curtains": rhet["_meta"]["帷幕编号"], "monsoon": monsoon["zones"],
    "ships": [{"name": s["name"], "age": s["age"], "holds": s["holds"],
               "crew": s["crew_max"], "guns": s["guns"]} for s in ships],
}

# ---------------- S1 样例存档 ----------------
def init_save():
    return {
        "_说明": "燃帆 v1 世界存档（world_save 格式）；出厂值见 data/*.json，本档为战役运行时值。",
        "meta": {"age": "S1", "year": 1375, "season": "春", "day": 1, "weather": "常"},
        "cities": {cid: {"exp": 0, "port_pool": []} for cid in strip_map},
        "fleet": {"船名": "圣乌尔苏拉号", "船型": "大加利", "班次": 25, "士气": 2,
                  "备用物资": 3, "船体": 10, "炮位": 4, "货舱": 5, "海员": 25},
        "ledger": {"银币": 400, "声望": 0, "恶名": 0, "潮汐": 3, "地产": [], "股单": [], "贷款": []},
        "npcs": {n["id"]: {"恩": 0, "债": 0, "last": "", "situation": n["situation"], "缺席": False}
                 for n in npcs["npcs"]},
        "factions": {f["id"]: {"军": f["attrs"]["军"], "财": f["attrs"]["财"], "谍": f["attrs"]["谍"],
                               "钟": {g["名"]: 0 for g in f["goals"]}, "log": []}
                     for f in factions["factions"]},
        "quests": {"visible": [], "pool": []},
        "ghosts": [],
        "discovered": ["venice", "alexandria", "genoa", "bruges", "constantinople"],
        "log": [],
    }


# ---------------- HTML 模板 ----------------
TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>燃帆 v1 · 主持面板（KP/PL 双端）</title>
<style>
:root{--bg:#171310;--panel:#221c17;--ink:#e8dcc8;--ink2:#9c8d74;--gold:#c9a227;--red:#a33b2e;--line:#3a3128}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 "Microsoft YaHei",system-ui,sans-serif}
header{display:flex;gap:12px;align-items:center;padding:10px 16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5;flex-wrap:wrap}
header h1{font-size:16px;margin:0;color:var(--gold);font-weight:600}
.btn{background:var(--panel);border:1px solid var(--line);color:var(--ink);padding:4px 10px;border-radius:6px;cursor:pointer;font-size:13px}
.btn:hover{border-color:var(--gold)}.btn.gold{color:var(--gold);border-color:var(--gold)}
main{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px}
@media(max-width:1000px){main{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}
.card h2{margin:0 0 8px;font-size:14px;color:var(--gold);border-bottom:1px dashed var(--line);padding-bottom:6px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border:1px solid var(--line);padding:3px 6px;text-align:left}
th{color:var(--ink2);font-weight:500}
select,input{background:#14100d;color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:2px 6px;font-size:13px}
.svgmap{width:100%;height:auto;background:#101a22;border-radius:8px}
.dot{cursor:pointer}.dot:hover{stroke:#fff;stroke-width:1.5}
.bar{display:inline-block;width:70px}.bar a{display:inline-block;width:12px;height:16px;margin-right:1px;background:#3a3128;cursor:pointer;border-radius:2px}
.bar a.on{background:var(--gold)}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.65);display:none;overflow:auto;z-index:9}
.modal .box{max-width:720px;margin:40px auto;background:var(--panel);border:1px solid var(--gold);border-radius:10px;padding:16px}
.step h3{color:var(--gold);margin:4px 0 8px}
.log{max-height:180px;overflow:auto;font-size:12.5px;color:var(--ink2);white-space:pre-wrap}
.tag{display:inline-block;border:1px solid var(--line);border-radius:4px;padding:0 6px;font-size:12px;color:var(--ink2);margin-right:4px}
.small{font-size:12px;color:var(--ink2)}
textarea{width:100%;background:#14100d;color:var(--ink);border:1px solid var(--line);border-radius:6px;min-height:110px;font:13px/1.5 inherit}
.kp-only.pl,.pl-only.kp{display:none}
</style>
</head>
<body>
<header>
  <h1>⚓ 燃帆 v1 主持面板</h1>
  <span id="meta" class="small"></span>
  <span style="flex:1"></span>
  <button class="btn" id="roleBtn"></button>
  <button class="btn" id="seasonBtn">季末向导 →</button>
  <button class="btn" onclick="exportSave()">导出存档</button>
  <label class="btn">导入存档<input type="file" id="importFile" accept=".json" style="display:none"></label>
  <button class="btn" onclick="if(confirm('重置为出厂 S1 开局？')){resetSave()}">重置</button>
</header>
<main id="kp" class="kp-only">
  <div class="card"><h2>① 世界图（纪门控迷雾 · 幽灵航程线）</h2>
    <div id="mapBox"></div>
    <div class="small">纪 <select id="ageSel"></select>（改纪即切迷雾与在编势力）· 点城开城市卡</div>
  </div>
  <div class="card"><h2>② 日历条（宏轨 91 格 · 双轨钟）</h2>
    <div id="cal"></div>
    <div class="small" id="calNote">一格=一天；点击跳日。月头提示：派系 tick×3；季末走向导。</div>
  </div>
  <div class="card"><h2>③ 城市卡（市况条滑块 · 城经验 · 驻港池）</h2>
    <div class="small">选择城市：<select id="citySel"></select></div>
    <div id="cityBox"></div>
  </div>
  <div class="card"><h2>④ NPC 池（具名卡 · 年轮 · 恩义/血债 · 幽灵航程）</h2>
    <div class="small">筛选：<select id="npcSel"></select></div>
    <div id="npcBox"></div>
  </div>
  <div class="card"><h2>⑤ 派系钟（月 tick 五步 · 进度钟）</h2>
    <div id="facBox"></div>
  </div>
  <div class="card"><h2>⑥ 任务台（泛型生成器 · d16 + d6×3 + 误差 d40）</h2>
    <button class="btn gold" onclick="genQuest()">🎲 掷一张泛型任务</button>
    <div id="qBox"></div>
    <hr style="border-color:var(--line)"><h2>任务板管理</h2>
    <div class="small">玩家可见：<div id="qVis"></div>存留池：<div id="qPool"></div></div>
  </div>
  <div class="card"><h2>⑦ 速查</h2>
    <div class="small">货币锚 1银=5.5gAg · 1金=10银｜行情骰 d6 ×0.6–2.4｜DV 阶梯 10/13/16/19/22｜船价=吨位×全装率×纪通胀｜砸盘：单港连抛3船→−40%<br>
    帷幕：__CURTAINS__<br>GM 季末预算 ≤10 分钟/≤25 掷（14 分册 §14.1）。玩家永只经四触点看世界。</div>
  </div>
  <div class="card"><h2>日志 / 世界一瞥存档</h2><div class="log" id="logBox"></div></div>
</main>
<main id="pl" class="pl-only">
  <div class="card"><h2>① 我的船（船卡八项）</h2><div id="shipBox"></div></div>
  <div class="card"><h2>② 海图（只见已发现港 · 传闻自标）</h2><div id="mapBox2"></div>
    <div class="small">已发现 <span id="discN"></span> 港；点位点击可自标传闻（记入日志）。</div></div>
  <div class="card"><h2>③ 账本（银币/声望/恶名/潮汐 · 地产股单）</h2><div id="ledgerBox"></div></div>
  <div class="card"><h2>④ 任务板（KP 勾选“玩家可见”后出现在此）</h2><div id="plQuests"></div></div>
  <div class="card"><h2>⑤ 伙伴（具名船员 · 技/缘）</h2><div id="crewBox"></div>
    <div class="small">招募：KP 在 NPC 池标记入伙后此处可见。<select id="crewSel"></select> <button class="btn" onclick="addCrew()">上船</button></div></div>
  <div class="card"><h2>⑥ 骰桌（d20 · DV 阶梯判读；实体骰优先）</h2>
    <button class="btn gold" onclick="rollDice()">🎲 掷 d20</button>
    DV <input id="dv" type="number" value="13" style="width:60px">
    <div id="diceOut" class="small"></div>
    <div class="small">阶梯：10 易 / 13 常规 / 16 难 / 19 极难 / 22 传说；≥1 成功，+5 良，+10 佳。</div></div>
  <div class="card"><h2>季风窗（本季可航带）</h2><div class="small" id="monsoonBox"></div></div>
</main>
<div class="modal" id="modal"><div class="box" id="modalBox"></div></div>
<script>
const DATA = __DATA__;
const AGES=["S1","S2","S3","S4","S5"];
const SEASONS=["春","夏","秋","冬"];
const YULE={1:"平安",2:"平安",3:"平安",4:"平安",5:"平安",6:"平安",7:"平安",8:"平安",9:"得子",10:"得子",11:"疾病（下季属性−1）",12:"疾病（下季属性−1）",13:"婚嫁（关系网变动）",14:"破财（资产降级/失100–500银）",15:"得财（得100–500银）",16:"学艺（随机技能+1）",17:"结仇（血债+1）",18:"遇险（下季缺席）",19:"奇遇（GM 埋钩）",20:"大变（身份跃迁）"};
const DEATH=t=>t<55?2:(t<65?5:8);
const CITY={};DATA.cities.forEach(c=>CITY[c.id]=c);
let ROLE=location.search.includes("role=pl")?"pl":"kp";
let S=load();

function blank(){return __SAVE__;}
function load(){try{const r=localStorage.getItem("burningsail_save");return r?JSON.parse(r):blank()}catch(e){return blank()}}
function save(){localStorage.setItem("burningsail_save",JSON.stringify(S))}
function resetSave(){S=blank();save();render()}
function exportSave(){const b=new Blob([JSON.stringify(S,null,1)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="world_save_"+S.meta.age+"_"+S.meta.year+".json";a.click()}
document.getElementById("importFile").onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{S=JSON.parse(r.result);save();render()};r.readAsText(f)};

/* ---------- 世界图 ---------- */
function drawMap(elId, fog){
  const W=960,H=520;
  const X=lon=>(lon+25)/165*W, Y=lat=>(62-lat)/105*H;
  let s=`<svg class="svgmap" viewBox="0 0 ${W} ${H}">`;
  s+=`<rect width="${W}" height="${H}" fill="#101a22"/>`;
  for(let g=-40;g<=80;g+=20)s+=`<line x1="0" y1="${Y(g)}" x2="${W}" y2="${Y(g)}" stroke="#1c2833"/><text x="4" y="${Y(g)-3}" fill="#31465a" font-size="10">${g}°N</text>`;
  for(let g=-20;g<=140;g+=20)s+=`<line x1="${X(g)}" y1="0" x2="${X(g)}" y2="${H}" stroke="#1c2833"/><text x="${X(g)+2}" y="12" fill="#31465a" font-size="10">${g}°E</text>`;
  const ageIdx=AGES.indexOf(S.meta.age);
  (S.ghosts||[]).forEach(g=>{const a=CITY[g.from],b=CITY[g.to];if(!a||!b)return;
    if(fog&&!(S.discovered||[]).includes(g.from)&&!(S.discovered||[]).includes(g.to))return;
    s+=`<line x1="${X(a.lon)}" y1="${Y(a.lat)}" x2="${X(b.lon)}" y2="${Y(b.lat)}" stroke="#a33b2e" stroke-dasharray="4 3" opacity=".8"/>`;
    s+=`<text x="${(X(a.lon)+X(b.lon))/2}" y="${(Y(a.lat)+Y(b.lat))/2-4}" fill="#a33b2e" font-size="10">${g.owner}（第${g旬(g)}旬出）</text>`;});
  DATA.cities.forEach(c=>{
    const known=AGES.indexOf(c.age)<=ageIdx;
    const disc=(S.discovered||[]).includes(c.id);
    if(!known)return; if(fog&&!disc){s+=`<circle cx="${X(c.lon)}" cy="${Y(c.lat)}" r="1.6" fill="#31465a"/>`;return}
    const col=c.rank===1?"#c9a227":"#7f8fa0";
    s+=`<circle class="dot" data-c="${c.id}" cx="${X(c.lon)}" cy="${Y(c.lat)}" r="${c.rank===1?4:2.6}" fill="${col}"/>`;
    if(c.rank===1||disc)s+=`<text x="${X(c.lon)+5}" y="${Y(c.lat)+3}" fill="#9c8d74" font-size="10">${c.name}</text>`;
  });
  s+="</svg>";
  document.getElementById(elId).innerHTML=s;
  document.querySelectorAll("#"+elId+" .dot").forEach(d=>d.onclick=()=>{const id=d.dataset.c;
    if(ROLE==="kp")openCity(id);else{markSight(id)}});
}
const g旬=g=>g.depart旬||1;
function markSight(id){const c=CITY[id];const t=prompt(`自标传闻点：${c.name}（写一句传闻，留空取消）`);if(t){S.log.push(`【传闻】${c.name}：${t}`);save();render()}}

/* ---------- KP：日历 ---------- */
function drawCal(){
  const d=S.meta.day;let h=`<div>`;
  for(let i=1;i<=91;i++){const on=i===d;h+=`<a class="${on?"on":""}" style="display:inline-block;width:8px;height:18px;margin:0 1px;background:${on?"#c9a227":"#3a3128"};cursor:pointer" onclick="setDay(${i})"></a>`;if(i%28===0)h+=`<span class="small">｜月</span>`}
  h+=`</div><div class="small">第 ${d} 天 / 91 · ${S.meta.season}季 · ${S.meta.year} 年 · ${S.meta.age} 纪 · 天气带：${S.meta.weather}</div>`;
  document.getElementById("cal").innerHTML=h;
}
function setDay(i){S.meta.day=i;save();render()}

/* ---------- KP：城市卡 ---------- */
function openCity(id){document.getElementById("citySel").value=id;renderCity();window.scrollTo({top:0,behavior:"smooth"})}
function renderCity(){
  const id=document.getElementById("citySel").value;if(!id){document.getElementById("cityBox").textContent="（选择城市）";return}
  const c=CITY[id],st=S.cities[id]||{exp:0,port_pool:[]};
  let h=`<div class="small">${c.name}｜${c.region}｜rank${c.rank}·tier${c.tier}｜入档 ${c.age}｜城经验 ${st.exp}</div>`;
  h+=`<table><tr><th>品</th><th>城档</th><th>基价银</th><th>库存轨(0–5)</th></tr>`;
  (DATA.strips[id]||[]).forEach((g,i)=>{const tr=(st[g["品"]]??3);
    h+=`<tr><td>${g["品"]}</td><td>${g["档"]}</td><td>${g["基价银"]}</td><td><span class="bar">${
      [0,1,2,3,4,5].map(v=>`<a class="${v<=tr?"on":""}" onclick="setTrack('${id}','${g["品"]}',${v})"></a>`).join("")}</span> <span class="small">×${[1.8,1.3,1.1,1.0,0.8,0.6][tr]}</span></td></tr>`});
  h+=`</table><div class="small">驻港池：<select onchange="addPool('${id}',this.value)"><option value="">＋从具名池抽…</option>${
    DATA.npcs.map(n=>`<option value="${n.id}">${n.name}</option>`).join("")}</select> ${
    (st.port_pool||[]).map(pid=>`<span class="tag">${DATA.npcs.find(n=>n.id===pid).name} <a onclick="delPool('${id}','${pid}')" style="cursor:pointer">✕</a></span>`).join("")}</div>`;
  h+=`<div class="small">城经验 +<input id="expAdd" type="number" value="1" style="width:50px"> <button class="btn" onclick="addExp('${id}')">记一笔（交易/任务/建设）</button></div>`;
  document.getElementById("cityBox").innerHTML=h;
}
function setTrack(cid,g,v){S.cities[cid][g]=v;save();renderCity()}
function addPool(cid,pid){if(!pid)return;const st=S.cities[cid];st.port_pool=st.port_pool||[];if(!st.port_pool.includes(pid))st.port_pool.push(pid);save();renderCity()}
function delPool(cid,pid){S.cities[cid].port_pool=S.cities[cid].port_pool.filter(x=>x!==pid);save();renderCity()}
function addExp(cid){S.cities[cid].exp=(S.cities[cid].exp||0)+ +document.getElementById("expAdd").value;save();renderCity()}

/* ---------- KP：NPC 池 ---------- */
function renderNpc(){
  const id=document.getElementById("npcSel").value;if(!id){document.getElementById("npcBox").textContent="（选择 NPC）";return}
  const n=DATA.npcs.find(x=>x.id===id),st=S.npcs[id];
  const ax=Object.entries(n.axes).map(([k,v])=>k+(v>0?"+":"")+v).join(" ");
  let h=`<b>${n.name}</b> <span class="small">${n.era.join("–")}｜${n.home}｜${n.means}档｜野心类：${n.amb_class}${n.title?"｜"+n.title:""}</span>`;
  h+=`<div class="small">属性 ${Object.entries(n.attrs).map(([k,v])=>k+v).join(" ")}｜技艺 ${n.skills.join("/")}｜${n.age} 岁｜五轴 ${ax}</div>`;
  h+=`<div class="small">野心：${n.ambition}<br>处境：${st.situation}</div>`;
  h+=`<div class="small">恩义 <input type="number" style="width:50px" value="${st["恩"]}" onchange="S.npcs['${id}']['恩']=+this.value;save()"> 血债 <input type="number" style="width:50px" value="${st["债"]}" onchange="S.npcs['${id}']['债']=+this.value;save()"> <span class="small">≥5 过命/死敌（13 分册）</span></div>`;
  h+=`<div class="small">处境更新 <input style="width:60%" value="${st.situation.replace(/"/g,"&quot;")}" onchange="S.npcs['${id}'].situation=this.value;save()"></div>`;
  h+=`<div style="margin:6px 0"><button class="btn gold" onclick="yule('${id}')">🎲 年轮 d20</button> <span id="yuleOut" class="small"></span> <span class="small">（死亡表：阈值 ≤${DEATH(n.age)}${n.age>=55?"（55+ 加压）":""}）</span></div>`;
  h+=`<div class="small"><b>幽灵航程登记</b>：从 <select id="gFrom">${DATA.cities.filter(c=>c.rank===1).map(c=>`<option ${c.id===n.home?"hidden":""}>${c.id}</option>`).join("")}</select> ↔ 至 <select id="gTo">${DATA.cities.filter(c=>c.rank===1).map(c=>`<option>${c.id}</option>`).join("")}</select> 第 <input id="g旬" type="number" value="1" min="1" max="6" style="width:40px"> 旬出，历时 <input id="gDays" type="number" value="30" style="width:50px"> 天 <button class="btn" onclick="addGhost('${id}')">登记</button></div>`;
  h+=`<div class="small">秘密（GM 之眼）：${n.secret}</div><div class="small">↳ 改：${n.affects}${n.note?"<br>注："+n.note:""}</div>`;
  document.getElementById("npcBox").innerHTML=h;
}
function yule(id){const n=DATA.npcs.find(x=>x.id===id);const r=1+Math.floor(Math.random()*20);
  let out=`d20=${r}：${YULE[r]}`;
  const dr=1+Math.floor(Math.random()*20);out+=`｜死亡表 d20=${dr}（≤${DEATH(n.age)} 则殁）`;
  if(dr<=DEATH(n.age))out+=" ——殁！走 13 分册死亡三准备。";
  document.getElementById("yuleOut").textContent=out;S.log.push(`【年轮】${n.name}：${out}`);save();render()}
function addGhost(pid){const f=document.getElementById("gFrom").value,t=document.getElementById("gTo").value;
  S.ghosts.push({owner:DATA.npcs.find(x=>x.id===pid).name,from:f,to:t,depart旬:+document.getElementById("g旬").value,days:+document.getElementById("gDays").value});
  S.log.push(`【幽灵航程】${DATA.npcs.find(x=>x.id===pid).name}：${f}↔${t}`);save();render()}

/* ---------- KP：派系 ---------- */
function renderFac(){
  const ageIdx=AGES.indexOf(S.meta.age);
  document.getElementById("facBox").innerHTML=DATA.factions.filter(f=>AGES.indexOf(f.ages[0])<=ageIdx&&AGES.indexOf(f.ages[f.ages.length-1])>=ageIdx).map(f=>{
    const st=S.factions[f.id];
    const clocks=Object.entries(st["钟"]).map(([k,v])=>`${k} ${v}/${f.goals.find(g=>g["名"]===k)["钟"]}格 <a style="cursor:pointer" onclick="clockUp('${f.id}','${k}')">＋</a>`).join("　");
    return `<div style="margin-bottom:8px"><b>${f.name}</b> <span class="small">军<input type="number" style="width:36px" value="${st["军"]}" onchange="S.factions['${f.id}']['军']=+this.value;save()"> 财<input type="number" style="width:36px" value="${st["财"]}" onchange="S.factions['${f.id}']['财']=+this.value;save()"> 谍<input type="number" style="width:36px" value="${st["谍"]}" onchange="S.factions['${f.id}']['谍']=+this.value;save()"></span><br>
    <span class="small">${clocks}</span> <button class="btn" onclick="facTurn('${f.id}')">月 tick 向导</button> <button class="btn" onclick="facAct('${f.id}')">🎲 行动掷</button> <span id="facOut_${f.id}" class="small"></span></div>`}).join("");
}
function clockUp(fid,k){S.factions[fid]["钟"][k]++;save();renderFac()}
function facAct(fid){const f=DATA.factions.find(x=>x.id===fid),st=S.factions[fid];
  const pool=+prompt("掷哪个属性的行动？军/财/谍","财");const v=st[pool];
  const r=1+Math.floor(Math.random()*20),dc=v*2+4,ok=r<=dc;
  const act=f.actions[pool][Math.floor(Math.random()*f.actions[pool].length)];
  document.getElementById("facOut_"+fid).textContent=`d20=${r} ≤${dc}（${pool}${v}）→ ${ok?"成":"败"}：【${act["名"]}】${act["效"]}`;
  st.log.push(`${pool}行动【${act["名"]}】${ok?"成功":"失败"}`);save()}
function facTurn(fid){const f=DATA.factions.find(x=>x.id===fid),st=S.factions[fid];
  const income=(DATA.factions.find(x=>x.id===fid).assets.length)*25*st["财"]/2;
  const steps=["①收入：财资产产出 ≈"+Math.round(income)+" 银（心记即可）","②维护：付不起的资产降级一档","③目标推进：钟＋1（上面按钮）","④行动：掷属性骰 d20 ≤ 属性×2+4","⑤PL接口：涉及玩家海区→生成任务（四触点）"];
  alert(`${f.name} 月 tick\n\n`+steps.join("\n")+"\n\n沙盘因果链（联合省示例）：\n"+(f.sandbox||"（见 14 分册）"))}

/* ---------- KP：任务台 ---------- */
let LASTQ="";
function genQuest(){
  const r16=1+Math.floor(Math.random()*16),g=DATA.generics[r16-1];
  const pick=a=>a[Math.floor(Math.random()*6)];
  const err=DATA.errors[Math.floor(Math.random()*40)];
  const rev=pick(DATA.reversals[Object.keys(DATA.reversals)[Math.floor(Math.random()*Object.keys(DATA.reversals).length)]]);
  const nm=DATA.names[Math.floor(Math.random()*DATA.names.length)];
  const qname=nm["姓"]+nm["名"][Math.floor(Math.random()*nm["名"].length)];
  LASTQ=`【泛型${g.no} ${g.name}】（标签 ${g.tags.join("·")}｜${g.pay_band}）\n委托人：${qname}（${pick(g.clients)}）\n目标：${g.name}委托——障碍：${pick(g.obstacles)}\n反转：${rev}\n委托误差：${err}\n生成链：${g.chain}`;
  document.getElementById("qBox").innerHTML=`<pre style="white-space:pre-wrap;color:var(--ink)">${LASTQ}</pre>
  <button class="btn" onclick="navigator.clipboard.writeText(LASTQ)">复制</button>
  <button class="btn gold" onclick="S.quests.visible.push(LASTQ);save();render()">✓ 玩家可见</button>
  <button class="btn" onclick="S.quests.pool.push(LASTQ);save();render()">入存留池</button>`;
}
function renderQuests(){
  document.getElementById("qVis").innerHTML=S.quests.visible.map((q,i)=>`<div class="small">· ${q.split("\n")[0]} <a style="cursor:pointer" onclick="S.quests.visible.splice(${i},1);save();render()">✕</a></div>`).join("")||"<span class='small'>（空）</span>";
  document.getElementById("qPool").innerHTML=S.quests.pool.map((q,i)=>`<div class="small">· ${q.split("\n")[0]} <a style="cursor:pointer" onclick="S.quests.pool.splice(${i},1);save();render()">✕</a></div>`).join("")||"<span class='small'>（空）</span>";
}

/* ---------- 季末八步向导 ---------- */
function seasonWizard(){
  const box=document.getElementById("modalBox");let step=1;
  function draw(){
    let h="<div class='step'><h3>季末八步向导（≤10 分钟）— 第 "+step+"/8 步</h3>";
    if(step===1)h+=`<p>①季风换向：查风历（08 分册）。当前季：${S.meta.season}。</p><div class="small">${DATA.monsoon.map(z=>z.zone+"："+z.months.join(" ")).join("<br>")}</div>`;
    if(step===2)h+=`<p>②行情骰重掷：对光顾过的城市，每品掷 d6（×0.6–2.4）。可在城市卡手动改轨。</p><button class="btn" onclick="this.after(d6())">掷</button> <span class='small'></span>`;
    if(step===3)h+=`<p>③派系 tick：在编势力各跑一次月 tick×3（或简并为 1 次）。用⑤模块的向导。</p>`;
    if(step===4)h+=`<p>④城经验：在城市卡为靠港城记经验（流量/枢纽/投资）。</p>`;
    if(step===5)h+=`<p>⑤人物年轮：对在场重要 NPC 掷（④模块年轮钮；含死亡表）。</p>`;
    if(step===6)h+=`<p>⑥天气轮转：</p><select id="wx"><option>常</option><option>风暴季（风险+1）</option><option>无风带</option><option>疫风</option></select> <button class="btn" onclick="S.meta.weather=document.getElementById('wx').value;save()">定</button>`;
    if(step===7)h+=`<p>⑦城市事件：对事件城掷 d10 → 09 分册事件表（灾疫/丰登/节庆/封锁…）。</p><button class="btn" onclick="this.after('d10='+d10())">掷</button>`;
    if(step===8){const lines=drawGlances();h+=`<p>⑧世界一瞥（念三行）：</p><pre style="white-space:pre-wrap">${lines}</pre><button class="btn" onclick="navigator.clipboard.writeText(${JSON.stringify(lines)})">复制</button>`;
      h+=`<button class="btn gold" onclick="nextSeason()">✔ 入档并进入下一季</button>`}
    h+=`<div style="margin-top:10px">${step<8?`<button class="btn gold" onclick="nw()">下一步 →</button>`:""} <button class="btn" onclick="closeModal()">关闭</button></div></div>`;
    box.innerHTML=h;
  }
  window.nw=()=>{step++;draw()};
  window.d6=()=>1+Math.floor(Math.random()*6);
  window.d10=()=>1+Math.floor(Math.random()*10);
  draw();document.getElementById("modal").style.display="block";
}
function drawGlances(){
  const qs=["编年史腔","酒馆腔","密报腔"];let out=[];
  qs.forEach(q=>{const pool=DATA.glances.filter(g=>g["腔"]===q);out.push("◆ "+pool[Math.floor(Math.random()*pool.length)].text)});
  return out.join("\n");
}
function nextSeason(){
  S.log.push(`—— ${S.meta.year} ${S.meta.season}季 结算入档 ——`);
  let si=SEASONS.indexOf(S.meta.season)+1;
  if(si>3){si=0;S.meta.year++}
  S.meta.season=SEASONS[si];S.meta.day=1;
  Object.values(S.factions).forEach(st=>st.log=[]);
  save();closeModal();render();
}
function closeModal(){document.getElementById("modal").style.display="none"}

/* ---------- PL 端 ---------- */
function renderShip(){
  const f=S.fleet;
  document.getElementById("shipBox").innerHTML=`<table>${Object.entries(f).map(([k,v])=>`<tr><th>${k}</th><td><input type="${typeof v==="number"?"number":"text"}" value="${v}" onchange="S.fleet['${k}']=${typeof v==="number"?"+this.value":'this.value'};save()"></td></tr>`).join("")}</table>`;
}
function renderLedger(){
  const l=S.ledger;
  document.getElementById("ledgerBox").innerHTML=`<table><tr><th>银币</th><th>声望</th><th>恶名</th><th>潮汐</th></tr><tr>${["银币","声望","恶名","潮汐"].map(k=>`<td>${l[k]}</td>`).join("")}</tr></table>
  <div class="small">地产：${l["地产"].join("、")||"无"}｜股单：${l["股单"].join("、")||"无"}｜贷款：${l["贷款"].join("、")||"无"}</div>
  <div class="small">记账（KP 口头宣布后自记）：<input id="lgK" placeholder="科目" style="width:80px"> <input id="lgV" type="number" style="width:70px" placeholder="±银"> <button class="btn" onclick="const k=document.getElementById('lgK').value;S.ledger[k]=(S.ledger[k]||0)+ +document.getElementById('lgV').value;save();render()">记账</button></div>`;
}
function renderCrew(){
  document.getElementById("crewBox").innerHTML=(S.crew||[]).map((id,i)=>{const n=DATA.npcs.find(x=>x.id===id);
    return n?`<div class="small">· ${n.name}｜${n.means}档｜${n.skills.join("/")} 恩${S.npcs[id]["恩"]} 债${S.npcs[id]["债"]} <a style="cursor:pointer" onclick="S.crew.splice(${i},1);save();render()">✕</a></div>`:""}).join("")||"<span class='small'>（船上无具名伙伴）</span>";
}
function addCrew(){const id=document.getElementById("crewSel").value;if(!id)return;S.crew=S.crew||[];if(!S.crew.includes(id))S.crew.push(id);save();render()}
function rollDice(){const r=1+Math.floor(Math.random()*20),dv=+document.getElementById("dv").value,m=r-dv;
  document.getElementById("diceOut").textContent=`d20=${r} vs DV${dv} → ${m>=0?"成功（+"+m+"）":"失败（"+m+"）"}${m>=10?"【佳】":m>=5?"【良】":""}`}
function renderMonsoon(){
  document.getElementById("monsoonBox").innerHTML=DATA.monsoon.map(z=>`<b>${z.zone}</b>：${z.months.join(" ")}<br>`).join("");
}

/* ---------- 总渲染 ---------- */
function render(){
  document.getElementById("meta").textContent=`${S.meta.age}纪 ${S.meta.year}年 ${S.meta.season}季 · 第${S.meta.day}天 · ${ROLE==="kp"?"KP 主持视图":"PL 玩家视图"}`;
  document.getElementById("roleBtn").textContent=ROLE==="kp"?"切到 PL 端":"切到 KP 端";
  document.body.className=ROLE;
  document.querySelectorAll(".kp-only").forEach(e=>e.classList.toggle("pl",ROLE!=="kp"));
  document.querySelectorAll(".pl-only").forEach(e=>e.classList.toggle("kp",ROLE!=="pl"));
  drawCal();
  if(ROLE==="kp"){
    drawMap("mapBox",false);
    document.getElementById("ageSel").innerHTML=AGES.map(a=>`<option ${a===S.meta.age?"selected":""}>${a}</option>`).join("");
    document.getElementById("citySel").innerHTML=DATA.cities.filter(c=>c.rank===1).map(c=>`<option value="${c.id}">${c.name}</option>`).join("");
    document.getElementById("npcSel").innerHTML=DATA.npcs.map(n=>`<option value="${n.id}">${n.id} ${n.name}</option>`).join("");
    renderCity();renderNpc();renderFac();renderQuests();
    document.getElementById("logBox").textContent=S.log.slice(-40).join("\n");
  }else{
    drawMap("mapBox2",true);
    document.getElementById("discN").textContent=(S.discovered||[]).length;
    renderShip();renderLedger();renderCrew();renderMonsoon();
    document.getElementById("plQuests").innerHTML=S.quests.visible.map(q=>`<pre style="white-space:pre-wrap;margin:4px 0">${q}</pre>`).join("")||"<span class='small'>（暂无可见任务）</span>";
    document.getElementById("crewSel").innerHTML=DATA.npcs.map(n=>`<option value="${n.id}">${n.name}</option>`).join("");
  }
  save();
}
document.getElementById("roleBtn").onclick=()=>{ROLE=ROLE==="kp"?"pl":"kp";history.replaceState(null,"",ROLE==="pl"?"?role=pl":"?role=kp");render()};
document.getElementById("seasonBtn").onclick=seasonWizard;
document.getElementById("ageSel").onchange=e=>{S.meta.age=e.target.value;save();render()};
document.getElementById("citySel").onchange=renderCity;
document.getElementById("npcSel").onchange=renderNpc;
render();
</script>
</body>
</html>
"""

SCHEMA_MD = """# world_save —— 世界存档 Schema（T7.1.1.b）

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
"""


def main():
    OUT_DIR.mkdir(exist_ok=True)
    page = TEMPLATE.replace("__DATA__", json.dumps(EMBED, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    page = page.replace("__SAVE__", json.dumps(init_save(), ensure_ascii=False, separators=(",", ":")))
    page = page.replace("__CURTAINS__", EMBED["curtains"])
    out = OUT_DIR / "index.html"
    out.write_text(page, encoding="utf-8")
    (BASE / "样例存档_S1_1375.json").write_text(json.dumps(init_save(), ensure_ascii=False, indent=1), encoding="utf-8")
    (BASE / "world_save.schema.md").write_text(SCHEMA_MD, encoding="utf-8")
    print(f"OK 生成 {out}（{len(page.encode('utf-8')) // 1024} KB）+ 样例存档 + Schema")


if __name__ == "__main__":
    main()
