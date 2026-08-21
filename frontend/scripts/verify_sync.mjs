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
  conflict: phaseConflict
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