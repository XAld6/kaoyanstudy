// 服务端同步 E2E 验证：配合后台已启动的前端(5188)与后端(8018)使用
// 阶段：online（水合/去抖推送/刷新持久/无多余 bump）→ offline（停后端后只读缓存）→ conflict（双标签页 409）
// 用法：node scripts/verify_sync.mjs        （默认 online）
//       VERIFY_PHASE=offline node scripts/verify_sync.mjs
//       VERIFY_PHASE=conflict node scripts/verify_sync.mjs
import { chromium } from "playwright";

const BASE = process.env.FOCUS_VERIFY_URL || "http://127.0.0.1:5188/";
const API = process.env.FOCUS_VERIFY_API || "http://127.0.0.1:8018";
const PHASE = process.env.VERIFY_PHASE || "online";
const TASK_TITLE = `E2E同步验证-${Date.now().toString(36)}`;
const results = [];

function pass(name, detail = "") {
  results.push({ name, ok: true, detail });
  console.log(`PASS  ${name}${detail ? ` — ${detail}` : ""}`);
}

function fail(name, detail = "") {
  results.push({ name, ok: false, detail });
  console.error(`FAIL  ${name}${detail ? ` — ${detail}` : ""}`);
}

async function serverState() {
  const headers = {};
  if (process.env.FOCUS_VERIFY_USER && process.env.FOCUS_VERIFY_PASS) {
    headers.Authorization = "Basic " + Buffer.from(`${process.env.FOCUS_VERIFY_USER}:${process.env.FOCUS_VERIFY_PASS}`).toString("base64");
  }
  const response = await fetch(`${API}/api/state`, { headers });
  return response.json();
}

async function serverPut(payload) {
  const headers = { "Content-Type": "application/json" };
  if (process.env.FOCUS_VERIFY_USER && process.env.FOCUS_VERIFY_PASS) {
    headers.Authorization = "Basic " + Buffer.from(`${process.env.FOCUS_VERIFY_USER}:${process.env.FOCUS_VERIFY_PASS}`).toString("base64");
  }
  const response = await fetch(`${API}/api/state`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload)
  });
  return response.status;
}

async function serverStateValue() {
  const headers = {};
  if (process.env.FOCUS_VERIFY_USER && process.env.FOCUS_VERIFY_PASS) {
    headers.Authorization = "Basic " + Buffer.from(`${process.env.FOCUS_VERIFY_USER}:${process.env.FOCUS_VERIFY_PASS}`).toString("base64");
  }
  const response = await fetch(`${API}/api/state`, { headers });
  return response.json();
}

async function waitHydrated(page) {
  // 水合完成后 loading 条消失；离线/冲突时条仍在
  await page.waitForSelector(".sync-notice", { state: "detached", timeout: 12000 }).catch(() => {});
  const text = await page.locator("body").innerText();
  if (text.includes("离线只读") || text.includes("数据冲突")) return false;
  return true;
}

async function addTask(page, title) {
  const input = page.locator("input[placeholder^='新增任务']");
  await input.fill(title);
  await input.press("Enter");
}

async function launch() {
  const browser = await chromium.launch({ headless: true }).catch(async (error) => {
    console.warn("default launch failed, trying chrome channel:", error.message);
    return chromium.launch({ headless: true, channel: "chrome" });
  });
  return browser;
}

function newPage(browser) {
  const contextOptions = {};
  if (process.env.FOCUS_VERIFY_USER && process.env.FOCUS_VERIFY_PASS) {
    contextOptions.httpCredentials = {
      username: process.env.FOCUS_VERIFY_USER,
      password: process.env.FOCUS_VERIFY_PASS
    };
  }
  return browser.newPage(contextOptions);
}

async function phaseOnline() {
  const browser = await launch();
  const page = await newPage(browser);
  page.setDefaultTimeout(15000);
  const downloads = [];
  page.on("download", (download) => downloads.push(download.suggestedFilename()));
  try {
    const online = await (async () => {
      await page.goto(BASE, { waitUntil: "networkidle" });
      return waitHydrated(page);
    })();
    if (online) pass("hydration: sync notice cleared");
    else fail("hydration: sync notice cleared");

    // 停后端前先断言服务器可达（空库播种走 800ms 去抖推送，轮询等待）
    let before = null;
    for (let i = 0; i < 10; i += 1) {
      before = await serverState();
      if (before.revision >= 1) break;
      await new Promise((resolve) => setTimeout(resolve, 400));
    }
    if (before.revision >= 1) pass("server has seeded data", `revision=${before.revision}`);
    else fail("server has seeded data", `revision=${before.revision}`);
    const seededCount = before.data?.tasks?.length ?? -1;
    if (seededCount > 0) pass("seed contains example tasks", `tasks=${seededCount}`);

    // 加任务 → 去抖后恰好一次 PUT（revision +1）
    await addTask(page, TASK_TITLE);
    await page.waitForTimeout(1800);
    const afterAdd = await serverState();
    const added = (afterAdd.data?.tasks ?? []).filter((task) => task.title === TASK_TITLE);
    if (added.length === 1) pass("task persisted to server (debounced PUT)", `revision=${before.revision} -> ${afterAdd.revision}`);
    else fail("task persisted to server", `found=${added.length}`);

    // 刷新 → 任务仍在（数据来自服务器），且 revision 不再 bump
    await page.reload({ waitUntil: "networkidle" });
    const onlineAfterReload = await waitHydrated(page);
    if (onlineAfterReload) pass("reload: hydration ok");
    await page.waitForTimeout(1600);
    const afterReload = await serverState();
    if (afterReload.revision === afterAdd.revision) pass("reload does not bump revision (no redundant PUT)", `revision=${afterReload.revision}`);
    else fail("reload does not bump revision", `${afterAdd.revision} -> ${afterReload.revision}`);
    const bodyText = await page.locator("body").innerText();
    if (bodyText.includes(TASK_TITLE)) pass("reload: task visible from server data");
    else fail("reload: task visible from server data");

    if (downloads.length) console.log(`INFO  captured downloads: ${downloads.join(", ")}`);
  } finally {
    await browser.close();
  }
}

async function phaseOffline() {
  const browser = await launch();
  const page = await newPage(browser);
  page.setDefaultTimeout(15000);
  try {
    await page.goto(BASE, { waitUntil: "networkidle" });
    await page.waitForSelector(".sync-notice.sync-offline", { timeout: 12000 });
    pass("offline banner shown");

    const bodyText = await page.locator("body").innerText();
    if (bodyText.includes("离线只读")) pass("offline label present");
    else fail("offline label present");

    // 缓存数据可见（示例数据或此前任务）
    const taskInput = page.locator("input[placeholder^='新增任务']");
    if ((await taskInput.count()) === 1) {
      // 编辑被锁：填入内容不产生新任务
      await taskInput.fill("offline 测试不应保存");
      await taskInput.press("Enter");
      await page.waitForTimeout(1200);
      const textAfter = await page.locator("body").innerText();
      if (!textAfter.includes("offline 测试不应保存")) pass("editing locked while offline");
      else fail("editing locked while offline", "input added content despite offline");
    } else {
      fail("editing locked while offline", "task input not found");
    }

    // P1-10：离线时番茄/计时结束不得改数据 —— 正计时 61 秒后结束，必须拒绝记入
    const startBtn = page.locator("button.minute-chip.focus-chip", { hasText: "开始" }).first();
    if ((await startBtn.count()) === 1) {
      await startBtn.click();
      await page.waitForSelector(".focus-sticky-bar", { timeout: 8000 });
      await page.waitForTimeout(61_500); // elapsed >= 1 分钟才会触发「记入」判断
      const msgBefore = await page.locator("body").innerText();
      await page.locator(".focus-sticky-bar").getByRole("button", { name: /结束并记入/ }).click();
      await page.waitForTimeout(800);
      const msgAfter = await page.locator("body").innerText();
      if (msgAfter.includes("未记入")) pass("offline focus finish refused (no data written)", "提示已展示");
      else fail("offline focus finish refused", "未出现拒绝提示");
      // 恢复后再验证任务分钟数未被污染
    } else {
      fail("offline focus finish refused", "no start button on today tasks");
    }
  } finally {
    await browser.close();
  }
}

/** P0-1：新设备（无任何本地缓存）加载服务器统计后再记录专注，必须是叠加而不是覆盖 */
async function phaseStatsInherit() {
  const browser = await launch();
  const page = await newPage(browser);
  page.setDefaultTimeout(15000);
  try {
    // 预置服务器统计：今天已有 1000 分钟
    const today = new Date().toISOString().slice(0, 10);
    const putStatus = await serverPut({
      baseRevision: (await serverState()).revision,
      data: {
        version: 1,
        examDate: "2026-12-20",
        subjects: [{ id: "s1", name: "数学", color: "#ff0000", weeklyTargetHours: 10 }],
        tasks: [
          { id: "t1", subjectId: "s1", title: "高数强化", date: today, estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" }
        ],
        reviews: []
      },
      focusStats: { version: 1, byDate: { [today]: { date: today, focusMinutes: 1000, pomodoroCount: 10, sessionCount: 10 } } }
    });
    if (putStatus !== 200) fail("seed stats via API", `http ${putStatus}`);

    // 新 context：本地没有任何缓存（browser.newPage 默认干净上下文）
    await page.goto(BASE, { waitUntil: "networkidle" });
    if (!(await waitHydrated(page))) fail("stats-inherit: hydration");

    // 水合后本地缓存必须已同步服务器统计（否则后续 record 基于空缓存覆盖服务器）
    const cacheRaw = await page.evaluate(() => localStorage.getItem("kaoyan-study-console:focus-stats-cache:v1") ?? "");
    if (cacheRaw.includes('"focusMinutes":1000')) pass("hydration syncs focus stats cache", "cache has 1000");
    else fail("hydration syncs focus stats cache", cacheRaw.slice(0, 120) || "cache empty");

    // 新设备记录一次正计时（>=1 分钟）→ 服务器统计必须叠加
    const startBtn = page.locator("button.minute-chip.focus-chip", { hasText: "开始" }).first();
    await startBtn.click();
    await page.waitForSelector(".focus-sticky-bar", { timeout: 8000 });
    await page.waitForTimeout(61_500);
    await page.locator(".focus-sticky-bar").getByRole("button", { name: /结束并记入/ }).click();
    await page.waitForTimeout(2500); // 去抖推送
    const after = await serverState();
    const todayStats = after.focusStats?.byDate?.[today];
    if (todayStats && todayStats.focusMinutes >= 1001) {
      pass("new device session adds to server history", `focusMinutes=${todayStats.focusMinutes} (>= 1001)`);
    } else {
      fail("new device session adds to server history", `got ${todayStats?.focusMinutes} (覆盖 bug)`);
    }
  } finally {
    await browser.close();
  }
}

/** P0-3：「用本机版本覆盖」按钮必须真实发出 PUT 并成功覆盖服务器 */
async function phaseConflictOverwrite() {
  const browser = await launch();
  const pageA = await newPage(browser);
  const pageB = await newPage(browser);
  pageA.setDefaultTimeout(15000);
  pageB.setDefaultTimeout(15000);
  try {
    await pageA.goto(BASE, { waitUntil: "networkidle" });
    await pageB.goto(BASE, { waitUntil: "networkidle" });
    if (!(await waitHydrated(pageA))) fail("page A hydration");
    if (!(await waitHydrated(pageB))) fail("page B hydration");
    const revB0 = (await serverState()).revision;

    const titleA = `${TASK_TITLE}-overwrite-A`;
    await addTask(pageA, titleA);
    await pageA.waitForTimeout(1800);
    const revA1 = (await serverState()).revision;
    if (revA1 > revB0) pass("page A push succeeded", `revision ${revB0} -> ${revA1}`);

    const titleB = `${TASK_TITLE}-overwrite-B`;
    await addTask(pageB, titleB);
    await pageB.waitForSelector(".sync-notice.sync-conflict", { timeout: 10000 });
    pass("conflict banner shown on page B");

    // 点「用本机版本覆盖」→ 必须发出 PUT（allowConflict）并以服务器最新 revision 为基准
    await pageB.getByRole("button", { name: /用本机版本覆盖/ }).click();
    await pageB.waitForSelector(".sync-notice.sync-conflict", { state: "detached", timeout: 10000 });
    const after = await serverState();
    const tasks = (after.data?.tasks ?? []).map((task) => task.title);
    if (after.revision > revA1) pass("overwrite issued real PUT (revision bumped)", `${revA1} -> ${after.revision}`);
    else fail("overwrite issued real PUT", `revision stayed ${after.revision}`);
    if (tasks.includes(titleB)) pass("server now has B's data after overwrite");
    else fail("server now has B's data after overwrite", tasks.join(" | ").slice(0, 120));
    const bText = await pageB.locator("body").innerText();
    if (bText.includes(titleB) && !bText.includes("数据冲突")) pass("page B shows own data and sync restored");
    else fail("page B shows own data and sync restored");
  } finally {
    await browser.close();
  }
}

async function phaseConflict() {
  const browser = await launch();
  const pageA = await newPage(browser);
  const pageB = await newPage(browser);
  pageA.setDefaultTimeout(15000);
  pageB.setDefaultTimeout(15000);
  const downloadsB = [];
  pageB.on("download", (download) => downloadsB.push(download.suggestedFilename()));
  try {
    await pageA.goto(BASE, { waitUntil: "networkidle" });
    await pageB.goto(BASE, { waitUntil: "networkidle" });
    if (!(await waitHydrated(pageA))) fail("page A hydration");
    if (!(await waitHydrated(pageB))) fail("page B hydration");
    const revB0 = (await serverState()).revision;
    pass("both pages hydrated", `revision=${revB0}`);

    // A 加任务并推送成功
    const titleA = `${TASK_TITLE}-A`;
    await addTask(pageA, titleA);
    await pageA.waitForTimeout(1800);
    const revA1 = (await serverState()).revision;
    if (revA1 > revB0) pass("page A push succeeded", `revision ${revB0} -> ${revA1}`);
    else fail("page A push succeeded", `revision unchanged ${revA1}`);

    // B 用过期 baseRevision 推 → 409 → 冲突条 + 两个选择按钮
    const titleB = `${TASK_TITLE}-B`;
    await addTask(pageB, titleB);
    await pageB.waitForSelector(".sync-notice.sync-conflict", { timeout: 10000 });
    pass("conflict banner shown on page B");
    const bText = await pageB.locator("body").innerText();
    if (bText.includes("数据冲突")) pass("conflict label present");
    else fail("conflict label present");

    const loadBtn = pageB.getByRole("button", { name: "加载服务器版本" });
    const overwriteBtn = pageB.getByRole("button", { name: /用本机版本覆盖/ });
    if ((await loadBtn.count()) === 1 && (await overwriteBtn.count()) === 1) pass("both conflict buttons present");
    else fail("both conflict buttons present", `load=${await loadBtn.count()}, overwrite=${await overwriteBtn.count()}`);

    // 加载服务器版本 → 冲突解除，页面显示 A 的任务
    await loadBtn.click();
    await pageB.waitForSelector(".sync-notice.sync-conflict", { state: "detached", timeout: 8000 }).catch(() => {});
    const bTextAfter = await pageB.locator("body").innerText();
    if (bTextAfter.includes(titleA)) pass("server version loaded on B (shows A's task)");
    else fail("server version loaded on B (shows A's task)");
    if (!bTextAfter.includes(titleB)) pass("B's own unsaved task not shown after loading server version");
    else fail("B's own unsaved task not shown after loading server version");
    const revAfter = (await serverState()).revision;
    if (revAfter === revA1) pass("loading server version does not bump revision");
    else fail("loading server version does not bump revision", `${revA1} -> ${revAfter}`);

    if (downloadsB.length) console.log(`INFO  conflict auto-download captured: ${downloadsB.join(", ")}`);
  } finally {
    await browser.close();
  }
}

const phases = {
  online: phaseOnline,
  offline: phaseOffline,
  conflict: phaseConflict,
  "conflict-overwrite": phaseConflictOverwrite,
  "stats-inherit": phaseStatsInherit
};

phases[PHASE]().catch((error) => {
  console.error("VERIFY CRASHED:", error);
  process.exit(1);
}).finally(() => {
  const failed = results.filter((item) => !item.ok);
  console.log("\n=== SUMMARY ===");
  console.log(`passed=${results.filter((i) => i.ok).length} failed=${failed.length} total=${results.length}`);
  if (failed.length) {
    for (const item of failed) console.log(` - ${item.name}: ${item.detail}`);
    process.exitCode = 1;
  }
});