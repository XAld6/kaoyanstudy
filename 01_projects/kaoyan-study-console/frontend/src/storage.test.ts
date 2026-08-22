import { beforeEach, describe, expect, it } from "vitest";
import { createDefaultData } from "./studyCore";
import {
  BACKUP_OVERDUE_AFTER_DAYS,
  BACKUP_WARN_AFTER_DAYS,
  clearBackupMeta,
  clearFocusTimerSession,
  createAppDataExport,
  getBackupHealth,
  loadAppData,
  loadAppDataWithStatus,
  loadBackupMeta,
  loadFocusNotifyPrefs,
  loadFocusStatsStore,
  loadFocusTimerSession,
  loadPomodoroMinutes,
  markBackupExported,
  parseImportedData,
  readLegacyFocusStats,
  readLegacyLocalData,
  recordFocusSession,
  restoreFocusTimerSession,
  saveAppData,
  saveFocusNotifyPrefs,
  saveFocusTimerSession,
  savePomodoroMinutes
} from "./storage";
import { createIdleFocusTimer, setFocusMode, startFocusTimer } from "./focusTimer";

const CACHE_KEY = "kaoyan-study-console:cache:v1";
const LEGACY_KEY = "kaoyan-study-console:v1";
const LEGACY_FOCUS_STATS_KEY = "kaoyan-study-console:focus-stats:v1";
const BACKUP_META_KEY = "kaoyan-study-console:backup-meta:v1";
const FOCUS_NOTIFY_PREFS_KEY = "kaoyan-study-console:focus-notify:v1";
const FOCUS_TIMER_SESSION_KEY = "kaoyan-study-console:focus-timer:v1";
const POMODORO_MINUTES_KEY = "kaoyan-study-console:pomodoro-minutes:v1";
const FOCUS_STATS_CACHE_KEY = "kaoyan-study-console:focus-stats-cache:v1";
const localStorageMock = new Map<string, string>();
const sessionStorageMock = new Map<string, string>();

Object.defineProperty(globalThis, "localStorage", {
  value: {
    getItem: (key: string) => localStorageMock.get(key) ?? null,
    setItem: (key: string, value: string) => localStorageMock.set(key, value),
    removeItem: (key: string) => localStorageMock.delete(key),
    clear: () => localStorageMock.clear()
  },
  configurable: true
});

Object.defineProperty(globalThis, "sessionStorage", {
  value: {
    getItem: (key: string) => sessionStorageMock.get(key) ?? null,
    setItem: (key: string, value: string) => sessionStorageMock.set(key, value),
    removeItem: (key: string) => sessionStorageMock.delete(key),
    clear: () => sessionStorageMock.clear()
  },
  configurable: true
});

describe("storage", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it("loads saved app data from cache", () => {
    const data = createDefaultData();
    data.examDate = "2026-12-20";

    saveAppData(data);

    expect(loadAppData().examDate).toBe("2026-12-20");
    expect(localStorage.getItem(CACHE_KEY)).toContain("2026-12-20");
  });

  it("falls back to default data when cache is incomplete", () => {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ version: 1, subjects: [], tasks: [] }));

    const data = loadAppData();

    expect(data.examDate).not.toBe("");
    expect(data.reviews).toEqual([]);
  });

  it("reports when cached data had to be recovered", () => {
    localStorage.setItem(CACHE_KEY, "not json");

    const result = loadAppDataWithStatus();

    expect(result.recovered).toBe(true);
    expect(result.data.examDate).not.toBe("");
  });

  it("never writes to the legacy key and can read legacy data for migration", () => {
    const data = createDefaultData();
    data.examDate = "2026-12-20";

    saveAppData(data);
    // 新写入只落在缓存键，老键保持不存在
    expect(localStorage.getItem(LEGACY_KEY)).toBeNull();
    // 无老数据时返回 null
    expect(readLegacyLocalData()).toBeNull();
  });

  it("reads legacy local data (old key) without removing it", () => {
    const legacy = createDefaultData();
    legacy.examDate = "2025-11-30";
    localStorage.setItem(LEGACY_KEY, JSON.stringify(legacy));

    const read = readLegacyLocalData();

    expect(read?.examDate).toBe("2025-11-30");
    // 老键保留，全程只读
    expect(localStorage.getItem(LEGACY_KEY)).toContain("2025-11-30");
  });

  it("returns null for invalid legacy data", () => {
    localStorage.setItem(LEGACY_KEY, "not json");
    expect(readLegacyLocalData()).toBeNull();

    localStorage.setItem(LEGACY_KEY, JSON.stringify({ version: 1, subjects: [], tasks: [] }));
    expect(readLegacyLocalData()).toBeNull();
  });

  it("reads legacy focus stats alongside legacy data", () => {
    expect(readLegacyFocusStats()).toBeNull();

    const stats = { version: 1, byDate: { "2026-07-12": { date: "2026-07-12", focusMinutes: 45, pomodoroCount: 2, sessionCount: 3 } } };
    localStorage.setItem(LEGACY_FOCUS_STATS_KEY, JSON.stringify(stats));
    expect(readLegacyFocusStats()?.byDate["2026-07-12"].focusMinutes).toBe(45);
  });

  it("rejects imported data with invalid task fields", () => {
    const data = createDefaultData();
    const invalid = { ...data, tasks: [{ ...data.tasks[0], actualMinutes: "30" }] };

    expect(() => parseImportedData(JSON.stringify(invalid))).toThrow("导入文件不是有效的考研学习数据。");
  });

  it("creates named export packages, optionally embedding focus stats", () => {
    const data = createDefaultData();

    const manual = createAppDataExport(data, "manual", "2026-06-10");
    const backup = createAppDataExport(data, "before-import", "2026-06-10");
    const withStats = createAppDataExport(data, "manual", "2026-06-10", {
      version: 1,
      byDate: { "2026-06-10": { date: "2026-06-10", focusMinutes: 25, pomodoroCount: 1, sessionCount: 1 } }
    });

    expect(manual.filename).toBe("kaoyan-study-2026-06-10.json");
    expect(backup.filename).toBe("kaoyan-study-backup-before-import-2026-06-10.json");
    expect(JSON.parse(manual.content).version).toBe(1);
    expect(JSON.parse(manual.content).focusStats).toBeUndefined();
    // 带 focusStats 的导出：老导入器会忽略多余字段，双向兼容
    expect(JSON.parse(withStats.content).focusStats.byDate["2026-06-10"].focusMinutes).toBe(25);
    expect(backup.mimeType).toBe("application/json;charset=utf-8");
  });

  it("records and loads backup export metadata", () => {
    const exportedAt = new Date("2026-06-10T08:30:00");
    const meta = markBackupExported("manual", exportedAt);

    expect(meta.lastExportKind).toBe("manual");
    expect(meta.lastExportAt).toBe(exportedAt.toISOString());
    expect(loadBackupMeta()).toEqual(meta);
    expect(localStorage.getItem(BACKUP_META_KEY)).toContain("manual");
  });

  it("reports never-exported backup health", () => {
    const health = getBackupHealth(loadBackupMeta(), new Date("2026-06-10T12:00:00"));

    expect(health.id).toBe("backup-never");
    expect(health.needsAttention).toBe(true);
    expect(health.tone).toBe("warn");
  });

  it("escalates backup health from ok to due to overdue", () => {
    const now = new Date("2026-06-20T12:00:00");
    markBackupExported("manual", new Date("2026-06-18T09:00:00"));
    expect(getBackupHealth(loadBackupMeta(), now).id).toBe("backup-ok");

    clearBackupMeta();
    markBackupExported("manual", new Date("2026-06-12T09:00:00"));
    const due = getBackupHealth(loadBackupMeta(), now);
    expect(due.id).toBe("backup-due");
    expect(due.daysSinceExport).toBeGreaterThanOrEqual(BACKUP_WARN_AFTER_DAYS);
    expect(due.needsAttention).toBe(true);

    clearBackupMeta();
    markBackupExported("before-import", new Date("2026-06-01T09:00:00"));
    const overdue = getBackupHealth(loadBackupMeta(), now);
    expect(overdue.id).toBe("backup-overdue");
    expect(overdue.daysSinceExport).toBeGreaterThanOrEqual(BACKUP_OVERDUE_AFTER_DAYS);
    expect(overdue.needsAttention).toBe(true);
  });

  it("persists focus notify preferences", () => {
    expect(loadFocusNotifyPrefs()).toEqual({ soundEnabled: true, notificationEnabled: true });

    const saved = saveFocusNotifyPrefs({ soundEnabled: false, notificationEnabled: true });
    expect(saved.soundEnabled).toBe(false);
    expect(loadFocusNotifyPrefs()).toEqual({ soundEnabled: false, notificationEnabled: true });
    expect(localStorage.getItem(FOCUS_NOTIFY_PREFS_KEY)).toContain("soundEnabled");
  });

  it("persists active focus timer in sessionStorage and clears on idle", () => {
    const t0 = 1_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-s1", "高数", t0);

    saveFocusTimerSession(state);
    expect(sessionStorage.getItem(FOCUS_TIMER_SESSION_KEY)).toContain("task-s1");
    expect(loadFocusTimerSession()?.taskId).toBe("task-s1");

    saveFocusTimerSession(createIdleFocusTimer("pomodoro"));
    expect(sessionStorage.getItem(FOCUS_TIMER_SESSION_KEY)).toBeNull();
    expect(loadFocusTimerSession()).toBeNull();
  });

  it("restores focus timer session and settles completed pomodoro", () => {
    const t0 = 2_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-s2", "英语", t0);
    saveFocusTimerSession(state);

    const restored = restoreFocusTimerSession(t0 + 26 * 60_000, 5);
    expect(restored.restored).toBe(true);
    expect(restored.logTaskId).toBe("task-s2");
    expect(restored.logMinutes).toBe(25);
    expect(restored.state.phase).toBe("break");

    clearFocusTimerSession();
    expect(restoreFocusTimerSession(t0 + 30 * 60_000).restored).toBe(false);
  });

  it("persists preferred pomodoro minutes and focus stats cache", () => {
    expect(loadPomodoroMinutes()).toBe(25);
    expect(savePomodoroMinutes(45)).toBe(45);
    expect(loadPomodoroMinutes()).toBe(45);
    expect(localStorage.getItem(POMODORO_MINUTES_KEY)).toBe("45");
    expect(savePomodoroMinutes(12)).toBe(25);

    const store = recordFocusSession({ minutes: 25, isPomodoro: true, date: "2026-07-12" });
    expect(store.byDate["2026-07-12"].pomodoroCount).toBe(1);
    expect(loadFocusStatsStore().byDate["2026-07-12"].focusMinutes).toBe(25);
    expect(localStorage.getItem(FOCUS_STATS_CACHE_KEY)).toContain("pomodoroCount");
  });
});