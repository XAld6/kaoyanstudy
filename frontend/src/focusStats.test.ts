import { describe, expect, it } from "vitest";
import {
  createEmptyFocusStatsStore,
  formatFocusStatsSummary,
  getDailyFocusStats,
  getFocusMinutesByDate,
  parseFocusStatsStore,
  recordFocusSession
} from "./focusStats";

describe("focusStats", () => {
  it("records focus minutes and pomodoro counts by date", () => {
    let store = createEmptyFocusStatsStore();
    store = recordFocusSession(store, { minutes: 25, isPomodoro: true, date: "2026-07-12" });
    store = recordFocusSession(store, { minutes: 15, isPomodoro: false, date: "2026-07-12" });
    store = recordFocusSession(store, { minutes: 25, isPomodoro: true, date: "2026-07-11" });

    const today = getDailyFocusStats(store, "2026-07-12");
    expect(today.focusMinutes).toBe(40);
    expect(today.pomodoroCount).toBe(1);
    expect(today.sessionCount).toBe(2);

    const yesterday = getDailyFocusStats(store, "2026-07-11");
    expect(yesterday.pomodoroCount).toBe(1);
    expect(yesterday.focusMinutes).toBe(25);
  });

  it("ignores zero-minute sessions", () => {
    const store = recordFocusSession(createEmptyFocusStatsStore(), {
      minutes: 0,
      isPomodoro: true,
      date: "2026-07-12"
    });
    expect(getDailyFocusStats(store, "2026-07-12").sessionCount).toBe(0);
  });

  it("parses stored payloads and formats summary text", () => {
    const parsed = parseFocusStatsStore({
      version: 1,
      byDate: {
        "2026-07-12": { focusMinutes: 50, pomodoroCount: 2, sessionCount: 3 }
      }
    });
    expect(parsed).not.toBeNull();
    const stats = getDailyFocusStats(parsed!, "2026-07-12");
    expect(formatFocusStatsSummary(stats)).toContain("50 分钟");
    expect(formatFocusStatsSummary(stats)).toContain("2 个番茄");
    expect(parseFocusStatsStore({ version: 2, byDate: {} })).toBeNull();
  });

  it("exports focus minutes by date for heatmap", () => {
    let store = createEmptyFocusStatsStore();
    store = recordFocusSession(store, { minutes: 30, isPomodoro: true, date: "2026-07-12" });
    store = recordFocusSession(store, { minutes: 0, isPomodoro: false, date: "2026-07-13" });
    expect(getFocusMinutesByDate(store)).toEqual({ "2026-07-12": 30 });
  });
});
