import { describe, expect, it } from "vitest";
import {
  buildFocusDocumentTitle,
  createIdleFocusTimer,
  DEFAULT_BREAK_MINUTES,
  discardFocusTimer,
  formatFocusClock,
  getFocusSnapshot,
  msToLoggedMinutes,
  normalizePomodoroMinutes,
  parseFocusTimerState,
  pauseFocusTimer,
  reconcileFocusTimer,
  resumeFocusTimer,
  setFocusMode,
  startBreakTimer,
  startFocusTimer,
  stopFocusTimer
} from "./focusTimer";

describe("focusTimer", () => {
  it("formats clock as mm:ss and h:mm:ss", () => {
    expect(formatFocusClock(0)).toBe("00:00");
    expect(formatFocusClock(65_000)).toBe("01:05");
    expect(formatFocusClock(3_661_000)).toBe("1:01:01");
  });

  it("rounds logged minutes with a 1-minute minimum after any work", () => {
    expect(msToLoggedMinutes(0)).toBe(0);
    expect(msToLoggedMinutes(12_000)).toBe(1);
    expect(msToLoggedMinutes(90_000)).toBe(2);
  });

  it("runs stopwatch elapsed across pause and resume", () => {
    const t0 = 1_000_000;
    let state = startFocusTimer(createIdleFocusTimer("stopwatch"), "task-1", "高数", t0);
    state = pauseFocusTimer(state, t0 + 90_000);
    expect(getFocusSnapshot(state, t0 + 90_000).elapsedMs).toBe(90_000);

    state = resumeFocusTimer(state, t0 + 100_000);
    const snap = getFocusSnapshot(state, t0 + 130_000);
    expect(snap.elapsedMs).toBe(120_000);
    expect(snap.display).toBe("02:00");
    expect(snap.mode).toBe("stopwatch");
  });

  it("counts down pomodoro remaining time and marks complete", () => {
    const t0 = 2_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-2", "英语", t0);

    const mid = getFocusSnapshot(state, t0 + 5 * 60_000);
    expect(mid.remainingMs).toBe(20 * 60_000);
    expect(mid.display).toBe("20:00");
    expect(mid.isComplete).toBe(false);

    const done = getFocusSnapshot(state, t0 + 25 * 60_000);
    expect(done.remainingMs).toBe(0);
    expect(done.isComplete).toBe(true);
    expect(done.progress).toBe(1);
  });

  it("stops and returns minutes to log, then resets to idle", () => {
    const t0 = 3_000_000;
    const running = startFocusTimer(createIdleFocusTimer("stopwatch"), "task-3", "政治", t0);
    const result = stopFocusTimer(running, t0 + 12 * 60_000);

    expect(result.taskId).toBe("task-3");
    expect(result.elapsedMinutes).toBe(12);
    expect(result.state.status).toBe("idle");
    expect(result.state.taskId).toBeNull();
  });

  it("discards progress without logging", () => {
    const t0 = 4_000_000;
    const running = startFocusTimer(createIdleFocusTimer("stopwatch"), "task-4", "专业课", t0);
    const discarded = discardFocusTimer(running);
    expect(discarded.status).toBe("idle");
    expect(discarded.taskId).toBeNull();
    expect(getFocusSnapshot(discarded, t0 + 60_000).elapsedMs).toBe(0);
  });

  it("does not change mode while a session is active", () => {
    const t0 = 5_000_000;
    const running = startFocusTimer(createIdleFocusTimer("stopwatch"), "task-5", "高数", t0);
    const next = setFocusMode(running, "pomodoro", 25);
    expect(next.mode).toBe("stopwatch");
    expect(next.status).toBe("running");
  });

  it("builds browser tab titles for running and paused focus sessions", () => {
    const t0 = 6_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-6", "高数强化：极限与导数题组", t0);
    const runningSnap = getFocusSnapshot(state, t0 + 60_000);
    expect(buildFocusDocumentTitle(runningSnap)).toBe("24:00 · 高数强化：极限与导数题组 · 番茄 | 考研学习控制台");
    expect(buildFocusDocumentTitle({
      ...runningSnap,
      taskTitle: "这是一个特别特别特别长的任务标题需要被截断显示"
    })).toContain("…");

    state = pauseFocusTimer(state, t0 + 60_000);
    const pausedSnap = getFocusSnapshot(state, t0 + 90_000);
    expect(buildFocusDocumentTitle(pausedSnap)).toContain("⏸ ");
    expect(buildFocusDocumentTitle(pausedSnap)).toContain("24:00");
    expect(buildFocusDocumentTitle(pausedSnap)).toContain("番茄");

    expect(buildFocusDocumentTitle(getFocusSnapshot(createIdleFocusTimer(), t0))).toBe("考研学习控制台");
  });

  it("starts a 5-minute break after a finished pomodoro work session", () => {
    const t0 = 7_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-7", "英语阅读", t0);

    const result = stopFocusTimer(state, t0 + 25 * 60_000);
    expect(result.shouldStartBreak).toBe(true);
    expect(result.elapsedMinutes).toBe(25);
    expect(result.taskId).toBe("task-7");
    expect(result.phase).toBe("work");

    const breakState = startBreakTimer(
      result.state,
      t0 + 25 * 60_000,
      DEFAULT_BREAK_MINUTES,
      result.lastWorkTaskId,
      result.lastWorkTaskTitle
    );
    expect(breakState.phase).toBe("break");
    expect(breakState.status).toBe("running");
    expect(breakState.taskId).toBeNull();
    expect(breakState.taskTitle).toBe("休息");
    expect(breakState.targetMinutes).toBe(5);
    expect(breakState.lastWorkTaskTitle).toBe("英语阅读");

    const midBreak = getFocusSnapshot(breakState, t0 + 25 * 60_000 + 2 * 60_000);
    expect(midBreak.display).toBe("03:00");
    expect(midBreak.phase).toBe("break");
    expect(midBreak.isComplete).toBe(false);
    expect(buildFocusDocumentTitle(midBreak)).toBe("03:00 · 休息 | 考研学习控制台");

    const doneBreak = getFocusSnapshot(breakState, t0 + 25 * 60_000 + 5 * 60_000);
    expect(doneBreak.isComplete).toBe(true);
    expect(doneBreak.remainingMs).toBe(0);
  });

  it("does not start a break after stopwatch sessions", () => {
    const t0 = 8_000_000;
    const running = startFocusTimer(createIdleFocusTimer("stopwatch"), "task-8", "政治", t0);
    const result = stopFocusTimer(running, t0 + 10 * 60_000);
    expect(result.shouldStartBreak).toBe(false);
    expect(result.elapsedMinutes).toBe(10);
  });

  it("can start a new work session from break without logging break time", () => {
    const t0 = 9_000_000;
    const breakState = startBreakTimer(createIdleFocusTimer("pomodoro"), t0, 5, "task-9", "高数");
    const next = startFocusTimer(breakState, "task-9", "高数", t0 + 60_000);
    expect(next.phase).toBe("work");
    expect(next.status).toBe("running");
    expect(next.taskId).toBe("task-9");
    expect(next.mode).toBe("pomodoro");
    expect(getFocusSnapshot(next, t0 + 60_000).elapsedMs).toBe(0);
  });

  it("parses and rejects focus timer session payloads", () => {
    const t0 = 10_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-10", "英语", t0);
    expect(parseFocusTimerState(state)).toMatchObject({
      status: "running",
      mode: "pomodoro",
      taskId: "task-10"
    });
    expect(parseFocusTimerState(null)).toBeNull();
    expect(parseFocusTimerState({ mode: "pomodoro" })).toBeNull();
    expect(parseFocusTimerState({
      ...state,
      status: "running",
      segmentStartedAt: null
    })).toBeNull();
  });

  it("reconciles a still-running pomodoro after refresh using wall clock", () => {
    const t0 = 11_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-11", "高数", t0);

    const result = reconcileFocusTimer(state, t0 + 10 * 60_000);
    expect(result.restored).toBe(true);
    expect(result.logMinutes).toBe(0);
    expect(result.state.status).toBe("running");
    expect(getFocusSnapshot(result.state, t0 + 10 * 60_000).display).toBe("15:00");
    expect(result.message).toContain("高数");
  });

  it("logs finished pomodoro and starts remaining break after long absence", () => {
    const t0 = 12_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-12", "政治", t0);

    // 离开 27 分钟：番茄 25 + 休息已过 2 分钟
    const result = reconcileFocusTimer(state, t0 + 27 * 60_000, 5);
    expect(result.logTaskId).toBe("task-12");
    expect(result.logMinutes).toBe(25);
    expect(result.state.phase).toBe("break");
    expect(result.state.status).toBe("running");
    expect(getFocusSnapshot(result.state, t0 + 27 * 60_000).display).toBe("03:00");
    expect(result.notify?.title).toBe("政治");
    expect(result.message).toContain("记入 25 分钟");
  });

  it("finishes both pomodoro and break when absence is longer than work+break", () => {
    const t0 = 13_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 25);
    state = startFocusTimer(state, "task-13", "专业课", t0);

    const result = reconcileFocusTimer(state, t0 + 40 * 60_000, 5);
    expect(result.logTaskId).toBe("task-13");
    expect(result.logMinutes).toBe(25);
    expect(result.state.status).toBe("idle");
    expect(result.message).toContain("休息也已结束");
  });

  it("ends break that completed during absence without logging minutes", () => {
    const t0 = 14_000_000;
    const breakState = startBreakTimer(createIdleFocusTimer("pomodoro"), t0, 5, "task-14", "英语");
    const result = reconcileFocusTimer(breakState, t0 + 6 * 60_000);
    expect(result.logMinutes).toBe(0);
    expect(result.state.status).toBe("idle");
    expect(result.notify?.title).toBe("休息");
    expect(result.message).toContain("休息已在你离开期间结束");
  });

  it("restores paused stopwatch without advancing elapsed time", () => {
    const t0 = 15_000_000;
    let state = startFocusTimer(createIdleFocusTimer("stopwatch"), "task-15", "英语", t0);
    state = pauseFocusTimer(state, t0 + 3 * 60_000);
    const result = reconcileFocusTimer(state, t0 + 30 * 60_000);
    expect(result.restored).toBe(true);
    expect(result.state.status).toBe("paused");
    expect(getFocusSnapshot(result.state, t0 + 30 * 60_000).elapsedMs).toBe(3 * 60_000);
  });

  it("keeps preferred pomodoro duration after stop and discard", () => {
    expect(normalizePomodoroMinutes(45)).toBe(45);
    expect(normalizePomodoroMinutes(20)).toBe(20);
    expect(normalizePomodoroMinutes(99, 25)).toBe(99);

    const t0 = 16_000_000;
    let state = setFocusMode(createIdleFocusTimer(), "pomodoro", 45);
    state = startFocusTimer(state, "task-16", "数学", t0, 45);
    expect(state.targetMinutes).toBe(45);

    const stopped = stopFocusTimer(state, t0 + 5 * 60_000, 45);
    expect(stopped.state.mode).toBe("pomodoro");
    expect(stopped.state.targetMinutes).toBe(45);

    state = setFocusMode(createIdleFocusTimer(), "pomodoro", 15);
    state = startFocusTimer(state, "task-17", "英语", t0, 15);
    const discarded = discardFocusTimer(state, 15);
    expect(discarded.mode).toBe("pomodoro");
    expect(discarded.targetMinutes).toBe(15);
  });
});
