import { formatDate } from "./studyCore";

export type DailyFocusStats = {
  date: string;
  /** 计时器记入的专注分钟（番茄 + 正计时） */
  focusMinutes: number;
  /** 完成的番茄个数（含到点自动完成与手动结束的番茄） */
  pomodoroCount: number;
  /** 记入过时长的会话次数（正计时/番茄均算） */
  sessionCount: number;
};

export type FocusStatsStore = {
  version: 1;
  byDate: Record<string, DailyFocusStats>;
};

export const EMPTY_DAILY_FOCUS_STATS = (date = formatDate()): DailyFocusStats => ({
  date,
  focusMinutes: 0,
  pomodoroCount: 0,
  sessionCount: 0
});

export function createEmptyFocusStatsStore(): FocusStatsStore {
  return { version: 1, byDate: {} };
}

export function getDailyFocusStats(store: FocusStatsStore, date = formatDate()): DailyFocusStats {
  const existing = store.byDate[date];
  if (!existing) return EMPTY_DAILY_FOCUS_STATS(date);
  return {
    date,
    focusMinutes: Math.max(0, existing.focusMinutes || 0),
    pomodoroCount: Math.max(0, existing.pomodoroCount || 0),
    sessionCount: Math.max(0, existing.sessionCount || 0)
  };
}

/** 供热力图等按日汇总：date -> focusMinutes */
export function getFocusMinutesByDate(store: FocusStatsStore): Record<string, number> {
  const map: Record<string, number> = {};
  for (const [date, entry] of Object.entries(store.byDate)) {
    const minutes = Math.max(0, Math.round(entry?.focusMinutes || 0));
    if (minutes > 0) map[date] = minutes;
  }
  return map;
}

export type RecordFocusSessionInput = {
  minutes: number;
  isPomodoro: boolean;
  date?: string;
};

/** 记入一次专注会话；不足 1 分钟不计入 */
export function recordFocusSession(
  store: FocusStatsStore,
  input: RecordFocusSessionInput
): FocusStatsStore {
  const minutes = Math.max(0, Math.round(input.minutes) || 0);
  if (minutes <= 0) return store;

  const date = input.date ?? formatDate();
  const current = getDailyFocusStats(store, date);
  const next: DailyFocusStats = {
    date,
    focusMinutes: current.focusMinutes + minutes,
    pomodoroCount: current.pomodoroCount + (input.isPomodoro ? 1 : 0),
    sessionCount: current.sessionCount + 1
  };

  return {
    version: 1,
    byDate: {
      ...store.byDate,
      [date]: next
    }
  };
}

export function parseFocusStatsStore(value: unknown): FocusStatsStore | null {
  if (typeof value !== "object" || value === null) return null;
  const raw = value as Record<string, unknown>;
  if (raw.version !== 1 || typeof raw.byDate !== "object" || raw.byDate === null) return null;

  const byDate: Record<string, DailyFocusStats> = {};
  for (const [date, entry] of Object.entries(raw.byDate as Record<string, unknown>)) {
    if (typeof entry !== "object" || entry === null) continue;
    const item = entry as Record<string, unknown>;
    const focusMinutes = typeof item.focusMinutes === "number" && Number.isFinite(item.focusMinutes)
      ? Math.max(0, Math.round(item.focusMinutes))
      : 0;
    const pomodoroCount = typeof item.pomodoroCount === "number" && Number.isFinite(item.pomodoroCount)
      ? Math.max(0, Math.round(item.pomodoroCount))
      : 0;
    const sessionCount = typeof item.sessionCount === "number" && Number.isFinite(item.sessionCount)
      ? Math.max(0, Math.round(item.sessionCount))
      : 0;
    byDate[date] = { date, focusMinutes, pomodoroCount, sessionCount };
  }
  return { version: 1, byDate };
}

export function formatFocusStatsSummary(stats: DailyFocusStats): string {
  if (stats.focusMinutes <= 0 && stats.pomodoroCount <= 0) {
    return "今日尚未用计时器记录专注";
  }
  const parts = [`专注 ${stats.focusMinutes} 分钟`];
  if (stats.pomodoroCount > 0) parts.push(`${stats.pomodoroCount} 个番茄`);
  if (stats.sessionCount > 0) parts.push(`${stats.sessionCount} 次会话`);
  return parts.join(" · ");
}
