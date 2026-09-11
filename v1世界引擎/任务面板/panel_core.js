// panel_core.js —— KP任务面板纯逻辑模块。
// 两条加载路径：①build_panel.py 把本文件内嵌进 index.html（浏览器端全局常量）；
// ②smoke_test.js 直接 require 本文件做单元抽测。
"use strict";
const RISK = { "跑腿": 0.5, "常规": 1, "危险": 2, "生死": 4 };
const DUR = { "单场": 1, "短链": 2.5, "长线": 8 };
const SKILL = { "无": 1, "专业": 1.5, "大师": 2.5 };
const SCAR = { "遍地": 0.7, "常态": 1, "无人敢接": 2 };
const AGES = ["S1", "S2", "S3", "S4", "S5"];
const AGE_ZH = { S1: "疫火桨帆", S2: "发现的代价", S3: "白银洪流", S4: "特许公司", S5: "黄金时代" };
const ST = ["未接", "已接", "完成", "悔约"];

// 帷幕掷骰：crypto 随机源；2^32 对 n≤100 的模偏差 < 2.4e-8，桌面工具可忽略
const d = n => {
  const a = new Uint32Array(1);
  globalThis.crypto.getRandomValues(a);
  return a[0] % n + 1;
};
const pick = a => a[d(a.length) - 1];
const payOf = (r, k, sk, sc) => Math.min(10 * RISK[r] * DUR[k] * SKILL[sk] * SCAR[sc], 600);
// 泛型纪门控："全纪"恒可；含年份可查；"S2+"式按纪序判断
const avail = (g, age) => {
  const a = g.ages;
  if (a.startsWith("全纪")) return true;
  if (a.includes(age)) return true;
  const m = a.match(/S(\d)\+/);
  if (m) return AGES.indexOf(age) >= +m[1] - 1;
  return false;
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = { RISK, DUR, SKILL, SCAR, AGES, AGE_ZH, ST, d, pick, payOf, avail };
}
