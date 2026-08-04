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
  recordFocusSession,
  restoreFocusTimerSession,
  saveAppData,
  saveFocusNotifyPrefs,
  saveFocusTimerSession,
  savePomodoroMinutes
} from "./storage";
import { createIdleFocusTimer, setFocusMode, startFocusTimer } from "./focusTimer";

const STORAGE_KEY = "kaoyan-study-console:v1";
const BACKUP_META_KEY = "kaoyan-study-console:backup-meta:v1";
const FOCUS_NOTIFY_PREFS_KEY = "kaoyan-study-console:focus-notify:v1";
const FOCUS_TIMER_SESSION_KEY = "kaoyan-study-console:focus-timer:v1";
const POMODORO_MINUTES_KEY = "kaoyan-study-console:pomodoro-minutes:v1";
const FOCUS_STATS_KEY = "kaoyan-study-console:focus-stats:v1";
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

  it("loads saved app data from localStorage", () => {
    const data = createDefaultData();
    data.examDate = "2026-12-20";

    saveAppData(data);

    expect(loadAppData().examDate).toBe("2026-12-20");
  });

  it("falls back to default data when localStorage data is incomplete", () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, subjects: [], tasks: [] }));

    const data = loadAppData();

    expect(data.examDate).not.toBe("");
    expect(data.reviews).toEqual([]);
  });

  it("reports when saved data had to be recovered", () => {
    localStorage.setItem(STORAGE_KEY, "not json");

    const result = loadAppDataWithStatus();

    expect(result.recovered).toBe(true);
    expect(result.data.examDate).not.toBe("");
  });

  it("rejects imported data with invalid task fields", () => {
    const data = createDefaultData();
    const invalid = { ...data, tasks: [{ ...data.tasks[0], actualMinutes: "30" }] };

    expect(() => parseImportedData(JSON.stringify(invalid))).toThrow("导入文件不是有效的考研学习数据。");
  });

  it("creates named export packages for manual export and before-import backup", () => {
    const data = createDefaultData();

    const manual = createAppDataExport(data, "manual", "2026-06-10");
    const backup = createAppDataExport(data, "before-import", "2026-06-10");

    expect(manual.filename).toBe("kaoyan-study-2026-06-10.json");
    expect(backup.filename).toBe("kaoyan-study-backup-before-import-2026-06-10.json");
    expect(JSON.parse(manual.content).version).toBe(1);
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

  it("persists preferred pomodoro minutes and focus stats", () => {
    expect(loadPomodoroMinutes()).toBe(25);
    expect(savePomodoroMinutes(45)).toBe(45);
    expect(loadPomodoroMinutes()).toBe(45);
    expect(localStorage.getItem(POMODORO_MINUTES_KEY)).toBe("45");
    expect(savePomodoroMinutes(12)).toBe(25);

    const store = recordFocusSession({ minutes: 25, isPomodoro: true, date: "2026-07-12" });
    expect(store.byDate["2026-07-12"].pomodoroCount).toBe(1);
    expect(loadFocusStatsStore().byDate["2026-07-12"].focusMinutes).toBe(25);
    expect(localStorage.getItem(FOCUS_STATS_KEY)).toContain("pomodoroCount");
  });
});
