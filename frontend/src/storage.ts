import { AppData, StudyTask, createDefaultData, formatDate } from "./studyCore";
import { DEFAULT_FOCUS_NOTIFY_PREFS, FocusNotifyPrefs } from "./focusNotify";
import {
  FocusStatsStore,
  createEmptyFocusStatsStore,
  parseFocusStatsStore,
  recordFocusSession as recordFocusSessionInStore,
  RecordFocusSessionInput
} from "./focusStats";
import {
  DEFAULT_BREAK_MINUTES,
  DEFAULT_POMODORO_MINUTES,
  FocusTimerState,
  POMODORO_DURATION_OPTIONS,
  ReconcileFocusTimerResult,
  createIdleFocusTimer,
  normalizePomodoroMinutes,
  parseFocusTimerState,
  reconcileFocusTimer
} from "./focusTimer";

const STORAGE_KEY = "kaoyan-study-console:v1";
const BACKUP_META_KEY = "kaoyan-study-console:backup-meta:v1";
const FOCUS_NOTIFY_PREFS_KEY = "kaoyan-study-console:focus-notify:v1";
const FOCUS_TIMER_SESSION_KEY = "kaoyan-study-console:focus-timer:v1";
const POMODORO_MINUTES_KEY = "kaoyan-study-console:pomodoro-minutes:v1";
const FOCUS_STATS_KEY = "kaoyan-study-console:focus-stats:v1";

/** 超过该天数未导出时提示建议备份 */
export const BACKUP_WARN_AFTER_DAYS = 7;
/** 超过该天数未导出时升级为强烈提醒 */
export const BACKUP_OVERDUE_AFTER_DAYS = 14;

export type LoadAppDataResult = {
  data: AppData;
  recovered: boolean;
};

export type AppDataExportKind = "manual" | "before-import";

export type AppDataExportPackage = {
  filename: string;
  content: string;
  mimeType: string;
};

export type BackupMeta = {
  lastExportAt: string | null;
  lastExportKind: AppDataExportKind | null;
};

export type BackupHealth = {
  id: "backup-never" | "backup-ok" | "backup-due" | "backup-overdue";
  tone: "warn" | "balance" | "steady";
  title: string;
  detail: string;
  daysSinceExport: number | null;
  lastExportLabel: string;
  needsAttention: boolean;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isPositiveNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function isNonNegativeNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

function isPriority(value: unknown): value is StudyTask["priority"] {
  return value === "高" || value === "中" || value === "低";
}

function isStatus(value: unknown): value is StudyTask["status"] {
  return value === "todo" || value === "done";
}

function isValidSubject(value: unknown) {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.name === "string"
    && typeof value.color === "string"
    && isPositiveNumber(value.weeklyTargetHours);
}

function isValidTask(value: unknown) {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.subjectId === "string"
    && typeof value.title === "string"
    && typeof value.date === "string"
    && isPositiveNumber(value.estimatedMinutes)
    && isNonNegativeNumber(value.actualMinutes)
    && isPriority(value.priority)
    && isStatus(value.status);
}

function isValidReview(value: unknown) {
  return isRecord(value) && typeof value.date === "string" && typeof value.text === "string";
}

function isValidAppData(value: unknown): value is AppData {
  return isRecord(value)
    && value.version === 1
    && typeof value.examDate === "string"
    && Array.isArray(value.subjects)
    && Array.isArray(value.tasks)
    && Array.isArray(value.reviews)
    && value.subjects.every(isValidSubject)
    && value.tasks.every(isValidTask)
    && value.reviews.every(isValidReview);
}

export function loadAppDataWithStatus(): LoadAppDataResult {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return { data: createDefaultData(), recovered: false };

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!isValidAppData(parsed)) {
      return { data: createDefaultData(), recovered: true };
    }
    return { data: parsed, recovered: false };
  } catch {
    return { data: createDefaultData(), recovered: true };
  }
}

export function loadAppData(): AppData {
  return loadAppDataWithStatus().data;
}

export function saveAppData(data: AppData) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function clearAppData() {
  localStorage.removeItem(STORAGE_KEY);
}

export function exportAppData(data: AppData) {
  return JSON.stringify(data, null, 2);
}

export function createAppDataExport(data: AppData, kind: AppDataExportKind = "manual", date = formatDate()): AppDataExportPackage {
  const name = kind === "before-import" ? `kaoyan-study-backup-before-import-${date}.json` : `kaoyan-study-${date}.json`;
  return {
    filename: name,
    content: exportAppData(data),
    mimeType: "application/json;charset=utf-8"
  };
}

export function parseImportedData(text: string): AppData {
  const parsed = JSON.parse(text) as unknown;
  if (!isValidAppData(parsed)) {
    throw new Error("导入文件不是有效的考研学习数据。");
  }
  return parsed;
}

function isValidFocusNotifyPrefs(value: unknown): value is FocusNotifyPrefs {
  return isRecord(value)
    && typeof value.soundEnabled === "boolean"
    && typeof value.notificationEnabled === "boolean";
}

export function loadFocusNotifyPrefs(): FocusNotifyPrefs {
  const raw = localStorage.getItem(FOCUS_NOTIFY_PREFS_KEY);
  if (!raw) return { ...DEFAULT_FOCUS_NOTIFY_PREFS };

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!isValidFocusNotifyPrefs(parsed)) return { ...DEFAULT_FOCUS_NOTIFY_PREFS };
    return {
      soundEnabled: parsed.soundEnabled,
      notificationEnabled: parsed.notificationEnabled
    };
  } catch {
    return { ...DEFAULT_FOCUS_NOTIFY_PREFS };
  }
}

export function saveFocusNotifyPrefs(prefs: FocusNotifyPrefs): FocusNotifyPrefs {
  const next = {
    soundEnabled: Boolean(prefs.soundEnabled),
    notificationEnabled: Boolean(prefs.notificationEnabled)
  };
  localStorage.setItem(FOCUS_NOTIFY_PREFS_KEY, JSON.stringify(next));
  return next;
}

export function loadFocusTimerSession(): FocusTimerState | null {
  try {
    const raw = sessionStorage.getItem(FOCUS_TIMER_SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    return parseFocusTimerState(parsed);
  } catch {
    return null;
  }
}

/** 仅在有进行中的会话时写入；idle 则清除，避免刷新后误恢复 */
export function saveFocusTimerSession(state: FocusTimerState): void {
  try {
    if (state.status === "idle") {
      sessionStorage.removeItem(FOCUS_TIMER_SESSION_KEY);
      return;
    }
    sessionStorage.setItem(FOCUS_TIMER_SESSION_KEY, JSON.stringify(state));
  } catch {
    // sessionStorage may be unavailable (隐私模式等)
  }
}

export function clearFocusTimerSession(): void {
  try {
    sessionStorage.removeItem(FOCUS_TIMER_SESSION_KEY);
  } catch {
    // ignore
  }
}

/** 读取并按当前时间结算离开期间已完成的番茄/休息 */
export function restoreFocusTimerSession(
  now = Date.now(),
  breakMinutes = DEFAULT_BREAK_MINUTES,
  preferredPomodoroMinutes = loadPomodoroMinutes()
): ReconcileFocusTimerResult {
  const saved = loadFocusTimerSession();
  if (!saved) {
    const minutes = normalizePomodoroMinutes(preferredPomodoroMinutes);
    return {
      state: createIdleFocusTimer("stopwatch", minutes),
      logTaskId: null,
      logMinutes: 0,
      message: "",
      notify: null,
      restored: false
    };
  }
  return reconcileFocusTimer(saved, now, breakMinutes);
}

function clampPomodoroOption(minutes: number): number {
  const rounded = Math.round(minutes);
  if ((POMODORO_DURATION_OPTIONS as readonly number[]).includes(rounded)) return rounded;
  return DEFAULT_POMODORO_MINUTES;
}

export function loadPomodoroMinutes(): number {
  try {
    const raw = localStorage.getItem(POMODORO_MINUTES_KEY);
    if (!raw) return DEFAULT_POMODORO_MINUTES;
    return clampPomodoroOption(Number(raw));
  } catch {
    return DEFAULT_POMODORO_MINUTES;
  }
}

export function savePomodoroMinutes(minutes: number): number {
  const next = clampPomodoroOption(minutes);
  try {
    localStorage.setItem(POMODORO_MINUTES_KEY, String(next));
  } catch {
    // ignore
  }
  return next;
}

export function loadFocusStatsStore(): FocusStatsStore {
  try {
    const raw = localStorage.getItem(FOCUS_STATS_KEY);
    if (!raw) return createEmptyFocusStatsStore();
    const parsed = parseFocusStatsStore(JSON.parse(raw) as unknown);
    return parsed ?? createEmptyFocusStatsStore();
  } catch {
    return createEmptyFocusStatsStore();
  }
}

export function saveFocusStatsStore(store: FocusStatsStore): FocusStatsStore {
  try {
    localStorage.setItem(FOCUS_STATS_KEY, JSON.stringify(store));
  } catch {
    // ignore
  }
  return store;
}

export function recordFocusSession(input: RecordFocusSessionInput): FocusStatsStore {
  const next = recordFocusSessionInStore(loadFocusStatsStore(), input);
  return saveFocusStatsStore(next);
}

function isValidBackupMeta(value: unknown): value is BackupMeta {
  return isRecord(value)
    && (value.lastExportAt === null || typeof value.lastExportAt === "string")
    && (value.lastExportKind === null
      || value.lastExportKind === "manual"
      || value.lastExportKind === "before-import");
}

export function loadBackupMeta(): BackupMeta {
  const raw = localStorage.getItem(BACKUP_META_KEY);
  if (!raw) {
    return { lastExportAt: null, lastExportKind: null };
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!isValidBackupMeta(parsed)) {
      return { lastExportAt: null, lastExportKind: null };
    }
    return {
      lastExportAt: parsed.lastExportAt,
      lastExportKind: parsed.lastExportKind
    };
  } catch {
    return { lastExportAt: null, lastExportKind: null };
  }
}

export function markBackupExported(kind: AppDataExportKind = "manual", at = new Date()): BackupMeta {
  const meta: BackupMeta = {
    lastExportAt: at.toISOString(),
    lastExportKind: kind
  };
  localStorage.setItem(BACKUP_META_KEY, JSON.stringify(meta));
  return meta;
}

export function clearBackupMeta() {
  localStorage.removeItem(BACKUP_META_KEY);
}

function startOfLocalDay(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

export function getDaysSinceLastBackup(meta: BackupMeta, now = new Date()): number | null {
  if (!meta.lastExportAt) return null;
  const exportedAt = new Date(meta.lastExportAt);
  if (Number.isNaN(exportedAt.getTime())) return null;
  const diffMs = startOfLocalDay(now) - startOfLocalDay(exportedAt);
  return Math.max(0, Math.floor(diffMs / 86400000));
}

export function formatBackupTimestamp(iso: string | null): string {
  if (!iso) return "从未导出";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "从未导出";
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function pad(value: number) {
  return value.toString().padStart(2, "0");
}

export function getBackupHealth(
  meta: BackupMeta,
  now = new Date(),
  warnAfterDays = BACKUP_WARN_AFTER_DAYS,
  overdueAfterDays = BACKUP_OVERDUE_AFTER_DAYS
): BackupHealth {
  const daysSinceExport = getDaysSinceLastBackup(meta, now);
  const lastExportLabel = formatBackupTimestamp(meta.lastExportAt);

  if (daysSinceExport === null) {
    return {
      id: "backup-never",
      tone: "warn",
      title: "尚未导出备份",
      detail: "学习数据只保存在本机浏览器。建议立刻导出一份 JSON，换浏览器或清缓存后还能恢复。",
      daysSinceExport: null,
      lastExportLabel,
      needsAttention: true
    };
  }

  if (daysSinceExport >= overdueAfterDays) {
    return {
      id: "backup-overdue",
      tone: "warn",
      title: "备份已过期",
      detail: `最近一次导出在 ${daysSinceExport} 天前（${lastExportLabel}）。请尽快下载备份，避免数据意外丢失。`,
      daysSinceExport,
      lastExportLabel,
      needsAttention: true
    };
  }

  if (daysSinceExport >= warnAfterDays) {
    return {
      id: "backup-due",
      tone: "balance",
      title: "建议更新备份",
      detail: `最近一次导出在 ${daysSinceExport} 天前（${lastExportLabel}）。超过 ${warnAfterDays} 天未备份，建议再导出一次。`,
      daysSinceExport,
      lastExportLabel,
      needsAttention: true
    };
  }

  const freshness = daysSinceExport === 0 ? "今天刚导出过" : `${daysSinceExport} 天前导出过`;
  return {
    id: "backup-ok",
    tone: "steady",
    title: "备份状态正常",
    detail: `${freshness}（${lastExportLabel}）。学习数据仍建议定期导出，尤其是大量改计划之后。`,
    daysSinceExport,
    lastExportLabel,
    needsAttention: false
  };
}
