# -*- coding: utf-8 -*-
"""
build_panel.py —— KP 任务面板（帷幕用单文件离线网页）。
P7"面板双端"的任务侧提前切片：任务盘（15进程/60固定卡+状态追踪）、随机生成器
（16泛型六步链）、报酬计算器、素材库速查、存留池与季末收盘。
纪律：data/*.json 是唯一真源；本脚本只做"数据嵌入 + 界面装配"，改数据重跑即可。
用法：python build_panel.py → 生成 任务面板/index.html（单文件，可分发可打印）
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = (HERE / "..").resolve()
DATA = (ENGINE / "data").resolve()
OUT = HERE / "index.html"
if OUT.parent != HERE or DATA.parent != ENGINE:
    raise SystemExit("路径越界，已阻止")


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


PAYLOAD = {
    "processes": load("processes.json")["processes"],
    "quests": load("quests.json")["quests"],
    "materials": load("qst_materials.json"),
    "tags": load("tags.json")["tags"],
    "axes": {"强度轴": load("tags.json")["强度轴"], "时长轴": load("tags.json")["时长轴"],
             "配平": load("tags.json")["配平"]},
}

TEMPLATE = r"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>燃帆 · KP任务面板 —— 帷幕用</title>
<style>
:root{--bg:#121815;--card:#1c2420;--card2:#232d28;--ink:#e9e1c8;--dim:#9aa79b;--gold:#c9a227;--red:#c05b4d;--blue:#6b93b8;--green:#7ba05b;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 "Microsoft YaHei",system-ui,sans-serif}
header{padding:14px 18px 8px;border-bottom:2px solid var(--gold);background:linear-gradient(#182019,#121815)}
h1{margin:0;font-size:22px;color:var(--gold);letter-spacing:2px}
.sub{color:var(--dim);font-size:12.5px;margin-top:4px}
nav{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
nav button{background:var(--card);color:var(--ink);border:1px solid #33413a;padding:7px 16px;border-radius:8px 8px 0 0;cursor:pointer;font-size:15px}
nav button.on{background:var(--gold);color:#181410;font-weight:700}
main{padding:14px 18px 60px;max-width:1180px;margin:0 auto}
section{display:none}section.on{display:block}
button.act{background:#2c3a32;color:var(--ink);border:1px solid #46584d;border-radius:6px;padding:4px 12px;cursor:pointer;font-size:13.5px}
button.act:hover{border-color:var(--gold);color:var(--gold)}
button.dice{background:var(--gold);color:#181410;font-weight:700;border:none;border-radius:8px;padding:6px 16px;cursor:pointer;font-size:14px}
.card{background:var(--card);border:1px solid #31403a;border-radius:10px;padding:12px 14px;margin:10px 0}
.card h3{margin:0 0 6px;font-size:16px}
.mono{font-family:Consolas,monospace}
.dim{color:var(--dim)} .gold{color:var(--gold)} .red{color:var(--red)}
select,input[type=text],textarea{background:var(--card2);color:var(--ink);border:1px solid #46584d;border-radius:6px;padding:4px 8px;font-size:14px}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:8px 0}
th,td{border:1px solid #3a4a41;padding:5px 8px;text-align:left;vertical-align:top}
th{background:#26312a;color:var(--gold);font-weight:600}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:6px 0}
.pill{display:inline-block;background:#26312a;border:1px solid #3a4a41;border-radius:20px;padding:1px 10px;font-size:12.5px;margin:2px}
.pill.a{border-color:var(--gold);color:var(--gold)}
.qcard{border-left:4px solid var(--blue)}
.qcard.st1{border-left-color:var(--gold)} .qcard.st2{border-left-color:var(--green)} .qcard.st3{border-left-color:var(--red)}
.det{display:none;margin-top:8px;border-top:1px dashed #3a4a41;padding-top:8px}
.det.open{display:block}
.det dt{color:var(--gold);font-size:13px;margin-top:6px}
.det dd{margin:1px 0 0 0;font-size:14px}
.clue{margin:2px 0} .clue b{color:var(--gold)}
.stbtn{border-radius:6px;border:1px solid #46584d;background:transparent;color:var(--dim);padding:3px 10px;cursor:pointer;font-size:13px}
.stbtn.s0{color:var(--dim)} .stbtn.s1{color:var(--gold);border-color:var(--gold)} .stbtn.s2{color:var(--green);border-color:var(--green)} .stbtn.s3{color:var(--red);border-color:var(--red)}
.step{background:var(--card2);border-radius:8px;padding:8px 12px;margin:6px 0}
.step .lbl{color:var(--gold);font-size:13px}
.step .val{font-size:14.5px;margin-top:2px}
.pay{font-size:26px;color:var(--gold);font-weight:800}
.warn{color:var(--red);font-size:13px}
.tabbar{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.tabbar button{background:transparent;color:var(--dim);border:none;border-bottom:2px solid transparent;padding:4px 10px;cursor:pointer;font-size:14px}
.tabbar button.on{color:var(--gold);border-bottom-color:var(--gold)}
@media print{body{background:#fff;color:#111}header{border-color:#999}nav,.stbtn,button{display:none}.card{border-color:#bbb;background:#fff;color:#111}.det{display:block}th{background:#eee;color:#333}}
</style>
</head>
<body>
<header>
  <h1>⚓ 燃帆 · KP 任务面板</h1>
  <div class="sub">五纪任务世界 · 帷幕用单文件离线工具（数据与分册同源，由 build_panel.py 生成）｜六要素口诀：<b class="gold">钩子谁说、误差在哪、目标一句、主隐两障、代价先亮、回报四槽</b>——六缺一不上桌</div>
  <nav id="tabs">
    <button data-t="board" class="on">📋 任务盘</button>
    <button data-t="gen">🎲 随机生成器</button>
    <button data-t="pay">💰 报酬计算</button>
    <button data-t="mat">📚 素材库</button>
    <button data-t="pool">🧾 存留池·季末</button>
  </nav>
</header>
<main>
<section id="tab-board" class="on">
  <div class="row">
    <span class="dim">纪筛选：</span><span id="ageChips"></span>
    <label class="dim" style="margin-left:auto"><input type="checkbox" id="allQ"> 显示未激活进程的全部任务</label>
  </div>
  <div class="row">
    <span class="dim">筛选：</span>
    <select id="fFlavor"><option value="">主味：全部</option></select>
    <select id="fScale"><option value="">体量：全部</option><option>单场</option><option>短链</option><option>长线</option></select>
    <select id="fRisk"><option value="">风险：全部</option><option>跑腿</option><option>常规</option><option>危险</option><option>生死</option></select>
    <input type="text" id="fText" placeholder="搜任务名/钩子关键词…" style="flex:1;min-width:160px">
    <span class="dim">已激活进程 <b class="gold" id="actN">0</b>/3（季末掷/选 3 张）</span>
  </div>
  <div id="boardList"></div>
</section>

<section id="tab-gen">
  <div class="card">
    <div class="row">
      <button class="dice" id="gD16">🎲 掷 d16 泛型</button>
      <span class="dim">纪门控：</span><select id="gAge"><option>S1</option><option>S2</option><option>S3</option><option>S4</option><option>S5</option></select>
      <span class="dim">文化措辞：</span><select id="gRegion"></select>
      <button class="act" id="gAll">全部重掷</button>
      <button class="act" id="gCopy">📋 复制为任务卡文本</button>
    </div>
    <div id="gCard" class="dim">掷 d16 后按六步链生成：委托人→误差→障碍→环境→反转→报酬。</div>
  </div>
  <div id="gSteps"></div>
</section>

<section id="tab-pay">
  <div class="card">
    <h3>报酬公式：<span class="dim">10 银 × 风险 × 时长 × 技艺 × 稀缺（现金封顶 600 银）</span></h3>
    <div class="row">
      <label>风险 <select id="pRisk"><option>跑腿</option><option selected>常规</option><option>危险</option><option>生死</option></select></label>
      <label>时长 <select id="pDur"><option>单场</option><option selected>短链</option><option>长线</option></select></label>
      <label>技艺 <select id="pSkill"><option selected>无</option><option>专业</option><option>大师</option></select></label>
      <label>稀缺 <select id="pScar"><option>遍地</option><option selected>常态</option><option>无人敢接</option></select></label>
    </div>
    <div class="row"><span class="pay" id="pOut">25 银</span><span class="dim" id="pRef"></span></div>
    <div class="row">
      <span class="dim">浮动源（最多两源）：</span>
      <label><input type="checkbox" class="float"> 时效滑价（提前+20%／过窗40%）</label>
      <label><input type="checkbox" class="float"> 行情联动（按市况条）</label>
      <label><input type="checkbox" class="float"> 谈判空间（DV13 ±25–40%）</label>
      <span class="warn" id="pWarn"></span>
    </div>
    <div class="dim">悔约反噬：接单弃单 → 委托圈恶名+，同区任务档次降一级一季。生死长线可走总包口径（现金+股/货/产权，上限≈二手小船 300–600 金）。</div>
  </div>
  <div class="card"><h3>时限-价钱速查表</h3><div id="pTable"></div></div>
</section>

<section id="tab-mat">
  <div class="tabbar" id="matTabs">
    <button data-m="names" class="on">人名录</button><button data-m="errors">误差库</button>
    <button data-m="rev">反转库</button><button data-m="places">地物库</button>
    <button data-m="cult">文化措辞</button><button data-m="flavor">八味标签</button>
  </div>
  <div id="matBody"></div>
</section>

<section id="tab-pool">
  <div class="card">
    <h3>存留池（互联三法：人复用·物复用·因果实账）</h3>
    <div class="row">
      <input type="text" id="poolName" placeholder="名/物" style="width:140px">
      <select id="poolRel"><option>亏欠</option><option>结仇</option><option>合伙</option><option>复杂</option><option>记档</option></select>
      <input type="text" id="poolRole" placeholder="下季可出任什么" style="flex:1;min-width:180px">
      <button class="act" id="poolAdd">＋入池</button>
      <button class="act" id="poolExport">⬇ 导出</button>
      <button class="act" id="poolImport">⬆ 导入</button>
    </div>
    <textarea id="poolIO" placeholder="导出后此处生成 JSON——粘回别的机器点导入即可" style="width:100%;height:70px;display:none"></textarea>
    <div id="poolList"></div>
  </div>
  <div class="card">
    <h3>季末任务收盘 · 五分钟清单</h3>
    <div id="clList"></div>
  </div>
</section>
</main>

<script>const DATA = __DATA__;</script>
<script>
__CORE__
"use strict";
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
let S; try{S=JSON.parse(localStorage.getItem("bs_kp_v1")||"{}")}catch(e){S={}}
S.active=S.active||[]; S.qstat=S.qstat||{}; S.pool=S.pool||[]; S.cl=S.cl||{}; S.ages=S.ages||["S1"];
const save=()=>localStorage.setItem("bs_kp_v1",JSON.stringify(S));
const esc=t=>String(t??"").replace(/&/g,"&amp;").replace(/</g,"&lt;");
const qById=Object.fromEntries(DATA.quests.map(q=>[q.id,q]));
const PAYS=q=>q.pay??q._formula;

/* ---- 掷骰公平性：crypto.getRandomValues，模偏差可忽略（KP 桌面工具） ---- */

/* tabs */
$$("#tabs button").forEach(b=>b.onclick=()=>{
  $$("#tabs button").forEach(x=>x.classList.toggle("on",x===b));
  $$("main section").forEach(x=>x.classList.toggle("on",x.id==="tab-"+b.dataset.t));
});

/* ========== ① 任务盘 ========== */
function ageChips(){
  $("#ageChips").innerHTML=AGES.map(a=>`<span class="pill ${S.ages.includes(a)?"a":""}" data-age="${a}" style="cursor:pointer">${a} ${AGE_ZH[a]}</span>`).join("");
  $$("#ageChips .pill").forEach(p=>p.onclick=()=>{
    const a=p.dataset.age;
    S.ages=S.ages.includes(a)?S.ages.filter(x=>x!==a):[...S.ages,a];
    if(!S.ages.length)S.ages=[a]; save(); ageChips(); renderBoard();
  });
}
function qVisible(q){
  const proc=DATA.processes.find(p=>p.id===q.p);
  const on=S.active.includes(q.p)||$("#allQ").checked;
  if(!on)return false;
  if(!S.ages.includes(proc.age))return false;
  if($("#fFlavor").value&&q.tags[0]!==$("#fFlavor").value)return false;
  if($("#fScale").value&&q.scale!==$("#fScale").value)return false;
  if($("#fRisk").value&&q.risk!==$("#fRisk").value)return false;
  const kw=$("#fText").value.trim();
  if(kw&&!(q.name+q.hook+q.client).includes(kw))return false;
  return true;
}
function questHTML(q){
  const st=S.qstat[q.id]||0;
  const clues=q.clues.map((c,i)=>`<div class="clue"><b>线索${i+1}${i===0?"〔不掷骰可得〕":""}</b>：${esc(c[0])}　<span class="dim">场景：${esc(c[1])}｜备用：${esc(c[2])}</span></div>`).join("");
  return `<div class="card qcard st${st}" id="qc-${q.id}">
  <div class="row" style="margin:0">
    <b>${q.id} ${esc(q.name)}</b>
    <span class="pill">${q.scale}</span><span class="pill">${q.risk}</span><span class="pill a">${PAYS(q)} 银</span>
    <span class="pill">${q.tags.join("·")}｜${q.inten}</span>
    <button class="stbtn s${st}" data-q="${q.id}" style="margin-left:auto">${ST[st]}</button>
    <button class="act tgl" data-q="${q.id}">展开/收起</button>
  </div>
  <div class="dim" style="font-size:13px">钩子：${esc(q.hook)}</div>
  <div class="det">
    <dl>
      <dt>委托人（必有误差）</dt><dd>${esc(q.client)}　<span class="red">误差：${esc(q.err)}</span></dd>
      <dt>目标</dt><dd>${esc(q.goal)}</dd>
      <dt>障碍</dt><dd>主要——${esc(q.obs)}<br>隐藏——${esc(q.hid)}</dd>
      <dt>代价</dt><dd>${esc(q.cost)}</dd>
      <dt>回报</dt><dd>${esc(q.rew)}</dd>
      ${q.premium?`<dt>溢价/总包</dt><dd>${esc(q.premium)}（公式基准 ${q._formula} 银）</dd>`:""}
      ${q.nodes?`<dt>节点图</dt><dd>${esc(q.nodes)}</dd>`:""}
      <dt>三线索</dt><dd>${clues}</dd>
      <dt>标签 / 史实</dt><dd>${esc(q.tags.join("·"))}｜强度 ${q.inten}｜稀缺 ${q.scar}<br><span class="dim">${esc(q.hist)}</span></dd>
      <dt>存留钩（季末入池）</dt><dd>${esc(q.lingering)}　<button class="act toPool" data-q="${q.id}">＋入池</button></dd>
    </dl>
  </div></div>`;
}
function renderBoard(){
  $("#actN").textContent=S.active.length;
  const list=DATA.quests.filter(qVisible);
  let html="";
  if(!S.active.length&&!$("#allQ").checked)
    html+=`<div class="card dim">在下面勾选 3 张进程卡激活（剧本卡 15 选 3）；或勾选右上"显示未激活进程的全部任务"。</div>`;
  DATA.processes.forEach(p=>{
    const qs=list.filter(q=>q.p===p.id);
    if(!qs.length)return;
    const act=S.active.includes(p.id);
    html+=`<div class="card" style="border-left:4px solid ${act?"var(--gold)":"#31403a"}">
    <div class="row" style="margin:0">
      <label style="cursor:pointer"><input type="checkbox" data-p="${p.id}" ${act?"checked":""}> <b>${p.id} ${esc(p.name)}</b></label>
      <span class="pill">${p.age}｜${esc(p.window)}</span>
      <span class="dim" style="font-size:13px">${esc(p.drama)}</span>
    </div>
    <div class="dim" style="font-size:13px">📍${esc(p.geo)} ｜ ⚔${esc(p.factions)} ｜ 🧭深层锚：${esc(p.onion)}</div>`;
    if(act) html+=qs.map(questHTML).join("");
    html+=`</div>`;
  });
  $("#boardList").innerHTML=html;
  $$("#boardList input[data-p]").forEach(c=>c.onchange=()=>{
    const id=c.dataset.p;
    S.active=c.checked?[...new Set([...S.active,id])]:S.active.filter(x=>x!==id);
    save(); renderBoard();
  });
  $$("#boardList .stbtn").forEach(b=>b.onclick=()=>{
    const id=b.dataset.q; S.qstat[id]=((S.qstat[id]||0)+1)%4; save(); renderBoard();
  });
  $$("#boardList .tgl").forEach(b=>b.onclick=()=>{
    b.closest(".qcard").querySelector(".det").classList.toggle("open");
  });
  $$("#boardList .toPool").forEach(b=>b.onclick=()=>{
    const q=qById[b.dataset.q];
    S.pool.push({n:q.lingering.split("｜")[0],rel:q.lingering.split("｜")[1]||"复杂",role:q.lingering.split("｜")[2]||"",from:q.id});
    save(); alert("已入池："+q.lingering);
  });
}
["fFlavor","fScale","fRisk","fText","allQ"].forEach(id=>{
  const el=$("#"+id); el.addEventListener(id==="fText"?"input":"change",renderBoard);
});
$("#fFlavor").innerHTML="<option value=''>主味：全部</option>"+[...new Set(DATA.quests.map(q=>q.tags[0]))].map(f=>`<option>${f}</option>`).join("");

/* ========== ② 随机生成器 ========== */
let G=null, GS={};
function rollClient(){
  const c=pick(G.clients);
  const ns=DATA.materials.names.find(n=>n.区===($("#gRegion").value))||DATA.materials.names[0];
  const name=pick(ns.姓.split("／"))+pick(ns.名.split("、"));
  GS.client=`${name}（${c}）${"　绰号备选："+ns.绰号}`;
}
function renderGen(){
  if(!G){$("#gCard").innerHTML=`<span class="dim">掷 d16 后按六步链生成：委托人→误差→障碍→环境→反转→报酬。</span>`;$("#gSteps").innerHTML="";return;}
  $("#gCard").innerHTML=`<b class="gold">泛型${G.no} ${esc(G.name)}</b>（${esc(G.ages)}）　<span class="pill">${esc(G.pay_band)}</span><span class="pill">${G.tags.join("·")}</span>
  <div class="dim" style="font-size:13px">触发：${esc(G.trigger)}｜误差倾向：${esc(G.error)}<br>生成链：${esc(G.chain)}</div>`;
  const steps=[
    ["① 委托人 d6（配本区人名）",GS.client,"rollClient"],
    ["② 误差 d40（必有偏差）","（掷前不显示——误差当面揭穿时给委托人一个可理解的动机）","rollErr"],
    ["③ 主要障碍 d6",GS.obs,"rollObs"],
    ["④ 环境地物（场景挂钩）",GS.place,"rollPlace"],
    ["⑤ 反转 d6（＝核心真相）",GS.rev,"rollRev"],
  ];
  $("#gSteps").innerHTML=steps.map((s,i)=>`<div class="step"><div class="row" style="margin:0"><span class="lbl">${s[0]}</span>
    <button class="dice" data-step="${s[2]}" style="margin-left:auto;padding:3px 12px;font-size:13px">掷</button></div>
    <div class="val" id="sv-${i}">${s[1]}</div></div>`).join("")+
    `<div class="step"><div class="row" style="margin:0"><span class="lbl">⑥ 报酬＝10×风险×时长×技艺×稀缺</span>
      <select id="gR">${Object.keys(RISK).map(k=>`<option ${k==="危险"?"selected":""}>${k}</option>`).join("")}</select>
      <select id="gD">${Object.keys(DUR).map(k=>`<option ${k==="短链"?"selected":""}>${k}</option>`).join("")}</select>
      <select id="gK">${Object.keys(SKILL).map(k=>`<option ${k==="无"?"selected":""}>${k}</option>`).join("")}</select>
      <select id="gS">${Object.keys(SCAR).map(k=>`<option ${k==="常态"?"selected":""}>${k}</option>`).join("")}</select>
      <span class="pay" style="font-size:20px" id="gPay"></span></div></div>`;
  $$("#gSteps [data-step]").forEach(b=>b.onclick=()=>{ROLL[b.dataset.step]();paintSteps();});
  ["gR","gD","gK","gS"].forEach(id=>$("#"+id).onchange=payPaint);
  payPaint();
}
function payPaint(){const el=$("#gPay");if(el)el.textContent=payOf($("#gR").value,$("#gD").value,$("#gK").value,$("#gS").value)+" 银";}
const ROLL={
  rollClient(){rollClient()},
  rollErr(){GS.err=pick(DATA.materials.errors)+"　（"+pick(["委托人另有隐情","误差指向第三者","误差与报酬挂钩"])+"）"},
  rollObs(){GS.obs=pick(G.obstacles)},
  rollPlace(){const p=pick(DATA.materials.places);GS.place=`${p.名}——${p.特征}（${p.类}）`},
  rollRev(){const fam=Object.keys(DATA.materials.reversals);const f=pick(fam);GS.rev=`[${f}] ${pick(DATA.materials.reversals[f])}`},
};
function paintSteps(){
  const vals=[GS.client,GS.err,GS.obs,GS.place,GS.rev];
  vals.forEach((v,i)=>{const el=$("#sv-"+i);if(el)el.textContent=v||"（未掷）";});
}
$("#gD16").onclick=()=>{
  const age=$("#gAge").value;
  let pool=DATA.materials.generics.filter(g=>avail(g,age));
  G=pick(pool); GS={}; ROLL.rollClient();ROLL.rollErr();ROLL.rollObs();ROLL.rollPlace();ROLL.rollRev();
  renderGen();
};
$("#gAge").onchange=()=>{G=null;renderGen();};
$("#gAll").onclick=()=>{if(G){ROLL.rollClient();ROLL.rollErr();ROLL.rollObs();ROLL.rollPlace();ROLL.rollRev();paintSteps();payPaint();}};
$("#gCopy").onclick=()=>{
  if(!G)return alert("先掷 d16");
  const txt=`【随机任务卡】泛型${G.no} ${G.name}（${G.ages}）
委托人：${GS.client}
误差：${GS.err}
目标：（KP 六要素补全：一句可判定完成态）
主要障碍：${GS.obs}
环境：${GS.place}
反转（核心真相）：${GS.rev}
报酬：${payOf($("#gR").value,$("#gD").value,$("#gK").value,$("#gS").value)} 银（10×风险×时长×技艺×稀缺）
标签：${G.tags.join("·")}｜${G.pay_band}
——六缺一不上桌：上桌前补齐 目标/隐藏障碍/代价/回报`;
  navigator.clipboard.writeText(txt).then(()=>alert("已复制到剪贴板"));
};
$("#gRegion").innerHTML=DATA.materials.names.map(n=>`<option>${n.区}</option>`).join("");

/* ========== ③ 报酬计算 ========== */
function payCalc(){
  const f=payOf($("#pRisk").value,$("#pDur").value,$("#pSkill").value,$("#pScar").value);
  const n=$$(".float").filter(c=>c.checked).length;
  $("#pWarn").textContent=n>2?"护栏：最多启用两源！":n===2?"已启用两源（上限）":"";
  let out=f;
  if($("#pRisk").value==="生死"&&$("#pDur").value==="长线")
    $("#pRef").textContent="现金带封顶——生死长线可另谈总包（+股/货/产权，≈二手小船 300–600 金）";
  else $("#pRef").textContent="参照：常规短链≈水手两月薪（25–50 银）；危险短链≈半年饷带；生死长线≈一条船";
  $("#pOut").textContent=out+" 银";
}
["pRisk","pDur","pSkill","pScar"].forEach(id=>$("#"+id).onchange=payCalc);
$$(".float").forEach(c=>c.onchange=payCalc);
const pt=DATA.materials.paytable;
$("#pTable").innerHTML=`<table><tr>${pt.matrix.header.map(h=>`<th>${h}</th>`).join("")}</tr>`+
  pt.matrix.rows.map(r=>`<tr>${r.map((c,i)=>i?`<td>${c}</td>`:`<th>${c}</th>`).join("")}</tr>`).join("")+`</table>
  <div class="dim">${esc(pt.说明)}</div>`;

/* ========== ④ 素材库 ========== */
let matTab="names";
function renderMat(){
  $$("#matTabs button").forEach(b=>b.classList.toggle("on",b.dataset.m===matTab));
  const M=DATA.materials; let h="";
  if(matTab==="names"){
    h=`<div class="row"><span class="dim">14 文化区×姓/名/绰号；同城连续任务优先复用。</span><button class="dice" id="rollN">掷一人</button><span id="rollNo" class="gold"></span></div>
    <table><tr><th>区</th><th>姓</th><th>名</th><th>绰号</th></tr>`+
    M.names.map(n=>`<tr><td>${esc(n.区)}</td><td>${esc(n.姓)}</td><td>${esc(n.名)}</td><td>${esc(n.绰号)}</td></tr>`).join("")+`</table>`;
  }else if(matTab==="errors"){
    h=`<div class="row"><span class="dim">委托人必有误差（14 章红线）。</span><button class="dice" id="rollE">掷 d40</button><span id="rollEo" class="gold"></span></div>
    <table><tr><th>d40</th><th>误差</th><th>d40</th><th>误差</th></tr>`+
    M.errors.slice(0,20).map((e,i)=>`<tr><td>${i+1}</td><td>${esc(e)}</td><td>${i+21}</td><td>${esc(M.errors[i+20])}</td></tr>`).join("")+`</table>`;
  }else if(matTab==="rev"){
    h=Object.entries(M.reversals).map(([fam,items])=>`<div class="card"><b class="gold">${esc(fam)}</b>（掷 d8）
      <table><tr>${items.map((_,i)=>`<th>${i+1}</th>`).join("")}</tr><tr>${items.map(x=>`<td>${esc(x)}</td>`).join("")}</tr></table></div>`).join("");
  }else if(matTab==="places"){
    h=`<div class="row"><button class="dice" id="rollP">掷一地</button><span id="rollPo" class="gold"></span></div>
    <table><tr><th>类</th><th>名</th><th>特征</th></tr>`+
    M.places.map(p=>`<tr><td>${p.类}</td><td><b>${esc(p.名)}</b></td><td>${esc(p.特征)}</td></tr>`).join("")+`</table>`;
  }else if(matTab==="cult"){
    h=`<table><tr><th>素材</th><th>欧区</th><th>伊斯兰区</th><th>明区</th></tr>`+
    M.cultural_variants.map(c=>`<tr><td><b>${esc(c.素材)}</b></td><td>${esc(c.欧区)}</td><td>${esc(c.伊斯兰区)}</td><td>${esc(c.明区)}</td></tr>`).join("")+`</table>`;
  }else{
    h=`<div class="card">${DATA.axes.配平}</div>`+DATA.tags.map(t=>`<div class="card"><b class="gold">${t.味}</b>——${esc(t.定义)}
      <div class="dim" style="font-size:13px">旁白：${t.旁白.map(esc).join("／")}<br>索引：${esc(t.素材索引)}${t.安全!=="—"?"｜🛡"+esc(t.安全):""}</div></div>`).join("");
  }
  $("#matBody").innerHTML=h;
  const rn=$("#rollN"); if(rn)rn.onclick=()=>{const ns=pick(M.names);$("#rollNo").textContent=`${pick(ns.姓.split("／"))}${pick(ns.名.split("、"))}——${ns.区}｜绰号可取${ns.绰号}`;};
  const re=$("#rollE"); if(re)re.onclick=()=>$("#rollEo").textContent=`d40=${d(40)}：`+M.errors[d(40)-1];
  const rp=$("#rollP"); if(rp)rp.onclick=()=>{const p=pick(M.places);$("#rollPo").textContent=`${p.名}——${p.特征}`;};
}
$$("#matTabs button").forEach(b=>b.onclick=()=>{matTab=b.dataset.m;renderMat();});

/* ========== ⑤ 存留池·季末 ========== */
const CHECKS=["本季每个任务：完成？悔约？（悔约反噬落档）","存留 NPC 按各卡存留钩行记入存留池",
  "报酬中的实物货按市况条重估（行情联动）","标签分布统计：连续两季同主味→下季换味","掷/选 3 张新进程卡激活＋上季推进钩子兑现检查"];
function renderPool(){
  $("#poolList").innerHTML=S.pool.length?`<table><tr><th>名/物</th><th>关系</th><th>下季可出任</th><th>来自</th><th></th></tr>`+
    S.pool.map((p,i)=>`<tr><td><b>${esc(p.n)}</b></td><td>${esc(p.rel)}</td><td>${esc(p.role)}</td><td class="dim">${esc(p.from||"")}</td>
    <td><button class="act" data-del="${i}">删</button></td></tr>`).join("")+`</table>`
    :`<div class="dim">池子空着——从任务盘的"存留钩"一键入池，或手动添加。</div>`;
  $$("#poolList [data-del]").forEach(b=>b.onclick=()=>{S.pool.splice(+b.dataset.del,1);save();renderPool();});
  $("#clList").innerHTML=CHECKS.map((c,i)=>`<label class="row" style="margin:2px 0"><input type="checkbox" data-cl="${i}" ${S.cl[i]?"checked":""}> ${c}</label>`).join("");
  $$("#clList [data-cl]").forEach(c=>c.onchange=()=>{S.cl[c.dataset.cl]=c.checked;save();});
}
$("#poolAdd").onclick=()=>{
  const n=$("#poolName").value.trim(); if(!n)return alert("填个名字");
  S.pool.push({n,rel:$("#poolRel").value,role:$("#poolRole").value.trim(),from:"手动"});
  $("#poolName").value="";$("#poolRole").value=""; save(); renderPool();
};
$("#poolExport").onclick=()=>{
  const io=$("#poolIO"); io.style.display="block";
  io.value=JSON.stringify({pool:S.pool,qstat:S.qstat,active:S.active});
  io.select(); document.execCommand&&document.execCommand("copy"); alert("已生成并尝试复制——也可手动全选粘走");
};
$("#poolImport").onclick=()=>{
  const io=$("#poolIO"); io.style.display="block";
  if(!io.value.trim())return io.focus();
  try{const o=JSON.parse(io.value);
    if(o.pool)S.pool=o.pool; if(o.qstat)S.qstat=o.qstat; if(o.active)S.active=o.active;
    save(); renderPool(); renderBoard(); alert("导入成功");
  }catch(e){alert("JSON 解析失败："+e.message)}
};

/* init */
ageChips(); renderBoard(); renderGen(); payCalc(); renderMat(); renderPool();
</script>
</body>
</html>
"""

def main():
    data_json = json.dumps(PAYLOAD, ensure_ascii=False)
    assert "</script" not in data_json.lower(), "数据含脚本终止符，拒绝嵌入"
    core_js = (HERE / "panel_core.js").read_text(encoding="utf-8")
    html = TEMPLATE.replace("__CORE__", core_js).replace("__DATA__", data_json)
    OUT.write_text(html, encoding="utf-8")
    print(f"OK 任务面板/index.html：{len(html.encode('utf-8'))//1024} KB｜"
          f"{len(PAYLOAD['processes'])} 进程 / {len(PAYLOAD['quests'])} 卡 / "
          f"{len(PAYLOAD['materials']['generics'])} 泛型 / 素材库 {len(PAYLOAD['materials']['errors'])}+"
          f"{sum(len(v) for v in PAYLOAD['materials']['reversals'].values())}+{len(PAYLOAD['materials']['places'])} 条")


if __name__ == "__main__":
    main()
