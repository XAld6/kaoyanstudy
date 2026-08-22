import { chromium } from "playwright";

const BASE = process.env.FOCUS_VERIFY_URL || "http://127.0.0.1:5188/";
const results = [];

function pass(name, detail = "") {
  results.push({ name, ok: true, detail });
  console.log(`PASS  ${name}${detail ? ` — ${detail}` : ""}`);
}

function fail(name, detail = "") {
  results.push({ name, ok: false, detail });
  console.error(`FAIL  ${name}${detail ? ` — ${detail}` : ""}`);
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    channel: process.env.PW_CHANNEL || undefined
  }).catch(async (error) => {
    console.warn("default launch failed, trying chrome channel:", error.message);
    return chromium.launch({ headless: true, channel: "chrome" });
  });

  // 线上地址带 Basic Auth 时用 FOCUS_VERIFY_USER / FOCUS_VERIFY_PASS 提供凭据
  const contextOptions = {};
  if (process.env.FOCUS_VERIFY_USER && process.env.FOCUS_VERIFY_PASS) {
    contextOptions.httpCredentials = {
      username: process.env.FOCUS_VERIFY_USER,
      password: process.env.FOCUS_VERIFY_PASS
    };
  }
  const page = await browser.newPage(contextOptions);
  page.setDefaultTimeout(15000);

  try {
    await page.goto(BASE, { waitUntil: "networkidle" });
    const initialTitle = await page.title();
    if (initialTitle.includes("考研学习控制台")) {
      pass("page loads", `title=${initialTitle}`);
    } else {
      fail("page loads", `unexpected title=${initialTitle}`);
    }

    // dismiss optional banners if present
    for (const label of ["知道了", "稍后"]) {
      const btn = page.getByRole("button", { name: label });
      if (await btn.count()) {
        try { await btn.first().click({ timeout: 1000 }); } catch { /* ignore */ }
      }
    }

    const stickyBefore = await page.locator(".focus-sticky-bar").count();
    if (stickyBefore === 0) pass("sticky hidden when idle");
    else fail("sticky hidden when idle", `count=${stickyBefore}`);

    const startButtons = page.locator("button.minute-chip.focus-chip", { hasText: "开始" });
    const startCount = await startButtons.count();
    if (startCount < 1) {
      fail("start button exists", "no 开始 button found on today tasks");
      throw new Error("cannot continue without start button");
    }
    await startButtons.first().click();
    pass("start focus on first task");

    await page.waitForSelector(".focus-sticky-bar", { timeout: 5000 });
    pass("sticky bar appears after start");

    const stickyText = (await page.locator(".focus-sticky-bar").innerText()).replace(/\s+/g, " ");
    if (stickyText.includes("计时中") || stickyText.includes("已暂停")) {
      pass("sticky shows status", stickyText.slice(0, 80));
    } else {
      fail("sticky shows status", stickyText.slice(0, 120));
    }

    const titleRunning = await page.title();
    if (/\d{2}:\d{2}/.test(titleRunning) && titleRunning.includes("考研学习控制台")) {
      pass("document title while running", titleRunning);
    } else {
      fail("document title while running", titleRunning);
    }

    // wait ~2s for clock tick
    const title1 = await page.title();
    await page.waitForTimeout(2200);
    const title2 = await page.title();
    if (title1 !== title2 && /\d{2}:\d{2}/.test(title2)) {
      pass("document title ticks", `${title1} -> ${title2}`);
    } else {
      // clock may not change display if still same second boundary issues; check sticky clock changes
      const clock1 = await page.locator(".focus-sticky-clock").innerText();
      await page.waitForTimeout(1500);
      const clock2 = await page.locator(".focus-sticky-clock").innerText();
      if (clock1 !== clock2) pass("sticky clock ticks", `${clock1} -> ${clock2}`);
      else fail("title/clock tick", `title1=${title1}; title2=${title2}; clock1=${clock1}; clock2=${clock2}`);
    }

    // switch to plan tab via side rail / tabs
    const planTab = page.getByRole("button", { name: /计划/ }).first();
    await planTab.click();
    await page.waitForTimeout(300);
    const stickyOnPlan = await page.locator(".focus-sticky-bar").count();
    if (stickyOnPlan === 1) pass("sticky remains on plan page");
    else fail("sticky remains on plan page", `count=${stickyOnPlan}`);

    // pause from sticky bar
    const pauseBtn = page.locator(".focus-sticky-bar").getByRole("button", { name: /暂停/ });
    await pauseBtn.click();
    await page.waitForTimeout(200);
    const pausedTitle = await page.title();
    const stickyPaused = await page.locator(".focus-sticky-bar.paused").count();
    if (stickyPaused === 1) pass("sticky paused style");
    else fail("sticky paused style");
    if (pausedTitle.includes("⏸") || pausedTitle.includes("已暂停") || pausedTitle.includes("24:") || /\d{2}:\d{2}/.test(pausedTitle)) {
      pass("title after pause", pausedTitle);
    } else {
      fail("title after pause", pausedTitle);
    }
    if (pausedTitle.includes("⏸")) pass("title has pause marker");
    else fail("title has pause marker", pausedTitle);

    // resume
    await page.locator(".focus-sticky-bar").getByRole("button", { name: /继续/ }).click();
    await page.waitForTimeout(300);
    const resumeTitle = await page.title();
    if (!resumeTitle.includes("⏸")) pass("title resume clears pause mark", resumeTitle);
    else fail("title resume clears pause mark", resumeTitle);

    // finish and log (no confirm dialog)
    await page.locator(".focus-sticky-bar").getByRole("button", { name: /结束并记入/ }).click();
    await page.waitForTimeout(400);
    const stickyAfter = await page.locator(".focus-sticky-bar").count();
    const titleIdle = await page.title();
    if (stickyAfter === 0) pass("sticky hidden after finish");
    else fail("sticky hidden after finish", `count=${stickyAfter}`);
    if (titleIdle === "考研学习控制台" || (titleIdle.includes("考研学习控制台") && !/\d{2}:\d{2}/.test(titleIdle))) {
      pass("title restored after finish", titleIdle);
    } else {
      fail("title restored after finish", titleIdle);
    }

    // start again then discard
    await page.getByRole("button", { name: /今日/ }).first().click();
    await page.waitForTimeout(200);
    // after finish, active task shows "开始" again (or "已绑定" gone)
    const startAgain = page.locator("button.minute-chip.focus-chip").filter({ hasText: /开始|已绑定|计时中/ });
    if (await page.locator("button.minute-chip.focus-chip", { hasText: "开始" }).count()) {
      await page.locator("button.minute-chip.focus-chip", { hasText: "开始" }).first().click();
      await page.waitForSelector(".focus-sticky-bar");

      await Promise.all([
        page.waitForEvent("dialog").then((dialog) => dialog.accept()),
        page.locator(".focus-sticky-bar button", { hasText: "丢弃" }).click({ force: true })
      ]);
      await page.waitForTimeout(300);

      if ((await page.locator(".focus-sticky-bar").count()) === 0) pass("discard hides sticky");
      else fail("discard hides sticky");
      const titleDiscard = await page.title();
      if (titleDiscard === "考研学习控制台" || !/\d{2}:\d{2}/.test(titleDiscard)) {
        pass("title restored after discard", titleDiscard);
      } else {
        fail("title restored after discard", titleDiscard);
      }
    } else {
      fail("restart for discard", `start chips=${await startAgain.count()}`);
    }
  } finally {
    await browser.close();
  }

  const failed = results.filter((item) => !item.ok);
  console.log("\n=== SUMMARY ===");
  console.log(`passed=${results.filter((i) => i.ok).length} failed=${failed.length} total=${results.length}`);
  if (failed.length) {
    for (const item of failed) console.log(` - ${item.name}: ${item.detail}`);
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error("VERIFY CRASHED:", error);
  process.exit(1);
});
