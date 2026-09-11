// smoke_test.js —— KP任务面板冒烟测试（Node ≥18，无第三方依赖）。
// 覆盖：①index.html 装配完整（占位符已替换/五个页签齐全/数据块可解析且数量正确）；
//      ②panel_core.js 纯函数单元抽测（掷骰/报酬公式/封顶/纪门控）。
// 注：内嵌脚本的语法校验由 build_panel.py 构建时完成（见其 build() 的 --check 逻辑）。
// 用法：node smoke_test.js
"use strict";
const fs = require("fs");
const path = require("path");
const core = require("./panel_core.js");

const HERE = __dirname;
const html = fs.readFileSync(path.join(HERE, "index.html"), "utf-8");
const fail = msg => { console.error("FAIL：" + msg); process.exit(1); };
const assert = (cond, msg) => { if (!cond) fail(msg); };

// ---- ① 装配完整性 ----
assert(!html.includes("__DATA__") && !html.includes("__CORE__"), "占位符未替换");
["tab-board", "tab-gen", "tab-pay", "tab-mat", "tab-pool"].forEach(id =>
  assert(html.includes(`id="${id}"`), `缺页签 ${id}`));

const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
assert(scripts.length === 2, `应有两个 script 块，实得 ${scripts.length}`);
const dataLine = scripts[0].trim().replace(/^const DATA = /, "").replace(/;$/, "");
const DATA = JSON.parse(dataLine);
assert(DATA.quests.length === 60, `任务卡应 60，实得 ${DATA.quests.length}`);
assert(DATA.processes.length === 15, `进程应 15，实得 ${DATA.processes.length}`);
assert(DATA.materials.generics.length === 16, `泛型应 16，实得 ${DATA.materials.generics.length}`);
assert(DATA.quests.every(q => q.lingering && q.clues.length === 3), "存留钩或三线索有缺失");

// ---- ② panel_core 纯函数抽测 ----
for (let i = 0; i < 200; i++) { const v = core.d(6); assert(v >= 1 && v <= 6, `d6 越界：${v}`); }
assert(core.payOf("常规", "短链", "无", "常态") === 25, "常规短链应 25 银");
assert(core.payOf("危险", "短链", "无", "常态") === 50, "危险短链应 50 银");
assert(core.payOf("生死", "长线", "大师", "无人敢接") === 600,
  `封顶应 600，实得 ${core.payOf("生死", "长线", "大师", "无人敢接")}`);
const s1 = DATA.materials.generics.filter(g => core.avail(g, "S1")).length;
assert(s1 === 15, `S1 可用泛型应 15，实得 ${s1}`);
assert(core.avail(DATA.materials.generics[15], "S5") === true, "捕鲸 S5 应可用");
assert(core.avail(DATA.materials.generics[15], "S2") === false, "捕鲸 S2 应不可用");
assert(core.avail(DATA.materials.generics[0], "S1") === true, "护航全纪应可用");

console.log("OK 冒烟测试全绿：装配完整｜数据 60 卡/15 进程/16 泛型｜掷骰·公式·封顶·纪门控抽测通过");
