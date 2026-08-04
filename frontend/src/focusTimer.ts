export type FocusMode = "stopwatch" | "pomodoro";
export type FocusPhase = "work" | "break";
export type FocusTimerStatus = "idle" | "running" | "paused";

export type FocusTimerState = {
  mode: FocusMode;
  phase: FocusPhase;
  status: FocusTimerStatus;
  taskId: string | null;
  taskTitle: string;
  /** 已完成片段累计毫秒（不含当前 running 段） */
  accumulatedMs: number;
  /** 当前 running 段开始时间戳；非 running 时为 null */
  segmentStartedAt: number | null;
  /** 番茄/休息目标分钟数；正计时 work 可忽略 */
  targetMinutes: number;
  /** 休息结束后可提示回到哪个任务 */
  lastWorkTaskId: string | null;
  lastWorkTaskTitle: string;
};

export type FocusTimerSnapshot = {
  elapsedMs: number;
  remainingMs: number | null;
  elapsedMinutes: number;
  display: string;
  progress: number;
  isComplete: boolean;
  status: FocusTimerStatus;
  mode: FocusMode;
  phase: FocusPhase;
  taskId: string | null;
  taskTitle: string;
  targetMinutes: number;
  lastWorkTaskId: string | null;
  lastWorkTaskTitle: string;
};

export type StopFocusTimerResult = {
  state: FocusTimerState;
  taskId: string | null;
  elapsedMinutes: number;
  elapsedMs: number;
  phase: FocusPhase;
  shouldStartBreak: boolean;
  lastWorkTaskId: string | null;
  lastWorkTaskTitle: string;
};

export const DEFAULT_POMODORO_MINUTES = 25;
export const DEFAULT_BREAK_MINUTES = 5;
export const POMODORO_DURATION_OPTIONS = [15, 25, 45] as const;
export type PomodoroDurationMinutes = (typeof POMODORO_DURATION_OPTIONS)[number];

export function normalizePomodoroMinutes(value: unknown, fallback = DEFAULT_POMODORO_MINUTES): number {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return fallback;
  const rounded = Math.round(n);
  if ((POMODORO_DURATION_OPTIONS as readonly number[]).includes(rounded)) return rounded;
  // 兼容会话里可能出现的自定义目标分钟
  return Math.max(1, rounded || fallback);
}

export function createIdleFocusTimer(
  mode: FocusMode = "stopwatch",
  targetMinutes = DEFAULT_POMODORO_MINUTES
): FocusTimerState {
  return {
    mode,
    phase: "work",
    status: "idle",
    taskId: null,
    taskTitle: "",
    accumulatedMs: 0,
    segmentStartedAt: null,
    targetMinutes: Math.max(1, Math.round(targetMinutes) || DEFAULT_POMODORO_MINUTES),
    lastWorkTaskId: null,
    lastWorkTaskTitle: ""
  };
}

function nextIdleAfterSession(
  state: FocusTimerState,
  preferredPomodoroMinutes = DEFAULT_POMODORO_MINUTES
): FocusTimerState {
  const wasPomodoro = state.mode === "pomodoro" || state.phase === "break";
  if (!wasPomodoro) {
    return createIdleFocusTimer("stopwatch", state.targetMinutes);
  }
  const minutes = state.phase === "work" && state.mode === "pomodoro"
    ? normalizePomodoroMinutes(state.targetMinutes, preferredPomodoroMinutes)
    : normalizePomodoroMinutes(preferredPomodoroMinutes);
  return createIdleFocusTimer("pomodoro", minutes);
}

export function getFocusElapsedMs(state: FocusTimerState, now = Date.now()): number {
  const live = state.status === "running" && state.segmentStartedAt != null
    ? Math.max(0, now - state.segmentStartedAt)
    : 0;
  return Math.max(0, state.accumulatedMs + live);
}

export function msToLoggedMinutes(ms: number): number {
  if (ms <= 0) return 0;
  return Math.max(1, Math.round(ms / 60000));
}

export function formatFocusClock(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const mm = minutes.toString().padStart(2, "0");
  const ss = seconds.toString().padStart(2, "0");
  if (hours > 0) {
    return `${hours}:${mm}:${ss}`;
  }
  return `${mm}:${ss}`;
}

function usesCountdown(state: FocusTimerState) {
  return state.phase === "break" || state.mode === "pomodoro";
}

export function getFocusSnapshot(state: FocusTimerState, now = Date.now()): FocusTimerSnapshot {
  const elapsedMs = getFocusElapsedMs(state, now);
  const targetMs = usesCountdown(state) ? state.targetMinutes * 60000 : null;
  const remainingMs = targetMs == null ? null : Math.max(0, targetMs - elapsedMs);
  const isComplete = targetMs != null && elapsedMs >= targetMs;
  const progress = targetMs == null ? 0 : Math.min(1, elapsedMs / targetMs);
  const displayMs = usesCountdown(state) ? (remainingMs ?? 0) : elapsedMs;

  return {
    elapsedMs,
    remainingMs,
    elapsedMinutes: msToLoggedMinutes(elapsedMs),
    display: formatFocusClock(displayMs),
    progress,
    isComplete,
    status: state.status,
    mode: state.mode,
    phase: state.phase,
    taskId: state.taskId,
    taskTitle: state.taskTitle,
    targetMinutes: state.targetMinutes,
    lastWorkTaskId: state.lastWorkTaskId,
    lastWorkTaskTitle: state.lastWorkTaskTitle
  };
}

export function setFocusMode(state: FocusTimerState, mode: FocusMode, targetMinutes = state.targetMinutes): FocusTimerState {
  if (state.status !== "idle") return state;
  const resolved = mode === "pomodoro"
    ? normalizePomodoroMinutes(targetMinutes)
    : Math.max(1, Math.round(targetMinutes) || DEFAULT_POMODORO_MINUTES);
  return {
    ...createIdleFocusTimer(mode, resolved),
    mode,
    targetMinutes: resolved
  };
}

export function startFocusTimer(
  state: FocusTimerState,
  taskId: string,
  taskTitle: string,
  now = Date.now(),
  preferredPomodoroMinutes = DEFAULT_POMODORO_MINUTES
): FocusTimerState {
  if (!taskId) return state;
  const pomodoroMinutes = normalizePomodoroMinutes(preferredPomodoroMinutes);

  // 休息中开始任务：直接进入新的工作番茄/正计时
  if (state.phase === "break") {
    const mode: FocusMode = state.mode === "stopwatch" ? "stopwatch" : "pomodoro";
    return {
      ...createIdleFocusTimer(mode, mode === "pomodoro" ? pomodoroMinutes : Math.max(state.targetMinutes, pomodoroMinutes)),
      mode,
      phase: "work",
      status: "running",
      taskId,
      taskTitle,
      segmentStartedAt: now,
      targetMinutes: mode === "pomodoro" ? pomodoroMinutes : Math.max(state.targetMinutes, pomodoroMinutes)
    };
  }

  if (state.status === "running" && state.taskId === taskId) return state;

  const workTarget = state.mode === "pomodoro"
    ? normalizePomodoroMinutes(state.targetMinutes || pomodoroMinutes, pomodoroMinutes)
    : Math.max(1, state.targetMinutes || pomodoroMinutes);

  if (state.status !== "idle" && state.taskId && state.taskId !== taskId) {
    return {
      ...createIdleFocusTimer(state.mode, workTarget),
      status: "running",
      taskId,
      taskTitle,
      segmentStartedAt: now
    };
  }

  if (state.status === "paused" && state.taskId === taskId) {
    return {
      ...state,
      status: "running",
      taskTitle,
      segmentStartedAt: now
    };
  }

  return {
    ...createIdleFocusTimer(state.mode, workTarget),
    status: "running",
    taskId,
    taskTitle,
    segmentStartedAt: now
  };
}

export function startBreakTimer(
  state: FocusTimerState,
  now = Date.now(),
  breakMinutes = DEFAULT_BREAK_MINUTES,
  lastWorkTaskId = state.taskId ?? state.lastWorkTaskId,
  lastWorkTaskTitle = state.taskTitle || state.lastWorkTaskTitle
): FocusTimerState {
  return {
    mode: "pomodoro",
    phase: "break",
    status: "running",
    taskId: null,
    taskTitle: "休息",
    accumulatedMs: 0,
    segmentStartedAt: now,
    targetMinutes: Math.max(1, Math.round(breakMinutes) || DEFAULT_BREAK_MINUTES),
    lastWorkTaskId,
    lastWorkTaskTitle: lastWorkTaskTitle || ""
  };
}

export function pauseFocusTimer(state: FocusTimerState, now = Date.now()): FocusTimerState {
  if (state.status !== "running" || state.segmentStartedAt == null) return state;
  return {
    ...state,
    status: "paused",
    accumulatedMs: getFocusElapsedMs(state, now),
    segmentStartedAt: null
  };
}

export function resumeFocusTimer(state: FocusTimerState, now = Date.now()): FocusTimerState {
  if (state.status !== "paused") return state;
  if (state.phase === "work" && !state.taskId) return state;
  return {
    ...state,
    status: "running",
    segmentStartedAt: now
  };
}

export function stopFocusTimer(
  state: FocusTimerState,
  now = Date.now(),
  preferredPomodoroMinutes = DEFAULT_POMODORO_MINUTES
): StopFocusTimerResult {
  const elapsedMs = getFocusElapsedMs(state, now);
  const taskId = state.taskId;
  const phase = state.phase;
  const shouldStartBreak = phase === "work" && state.mode === "pomodoro" && elapsedMs > 0;
  return {
    state: nextIdleAfterSession(state, preferredPomodoroMinutes),
    taskId,
    elapsedMinutes: phase === "work" ? msToLoggedMinutes(elapsedMs) : 0,
    elapsedMs,
    phase,
    shouldStartBreak,
    lastWorkTaskId: taskId ?? state.lastWorkTaskId,
    lastWorkTaskTitle: state.taskTitle || state.lastWorkTaskTitle
  };
}

export function discardFocusTimer(
  state: FocusTimerState,
  preferredPomodoroMinutes = DEFAULT_POMODORO_MINUTES
): FocusTimerState {
  return nextIdleAfterSession(state, preferredPomodoroMinutes);
}

export function isFocusTimerActive(state: FocusTimerState): boolean {
  return state.status === "running" || state.status === "paused";
}

export const DEFAULT_DOCUMENT_TITLE = "考研学习控制台";

/** 浏览器标签标题：倒计时/正计时/休息 + 任务名 */
export function buildFocusDocumentTitle(
  snapshot: Pick<FocusTimerSnapshot, "status" | "mode" | "phase" | "display" | "taskId" | "taskTitle" | "lastWorkTaskTitle">,
  baseTitle = DEFAULT_DOCUMENT_TITLE,
  maxTaskChars = 16
): string {
  if (snapshot.status === "idle") return baseTitle;

  const paused = snapshot.status === "paused" ? "⏸ " : "";

  if (snapshot.phase === "break") {
    return `${paused}${snapshot.display} · 休息 | ${baseTitle}`;
  }

  if (!snapshot.taskId) return baseTitle;

  const rawTitle = snapshot.taskTitle.trim() || "当前任务";
  const shortTask = rawTitle.length > maxTaskChars ? `${rawTitle.slice(0, maxTaskChars)}…` : rawTitle;
  const modeTag = snapshot.mode === "pomodoro" ? "番茄" : "专注";
  return `${paused}${snapshot.display} · ${shortTask} · ${modeTag} | ${baseTitle}`;
}

export type FocusRestoreNotify = {
  title: string;
  minutes: number;
};

export type ReconcileFocusTimerResult = {
  state: FocusTimerState;
  /** 离开期间番茄已完成时需记入的任务 */
  logTaskId: string | null;
  logMinutes: number;
  message: string;
  notify: FocusRestoreNotify | null;
  restored: boolean;
};

function startBreakWithElapsed(
  lastWorkTaskId: string | null,
  lastWorkTaskTitle: string,
  breakElapsedMs: number,
  now: number,
  breakMinutes = DEFAULT_BREAK_MINUTES
): FocusTimerState {
  const targetMs = Math.max(1, breakMinutes) * 60000;
  const clamped = Math.max(0, Math.min(breakElapsedMs, targetMs));
  return {
    mode: "pomodoro",
    phase: "break",
    status: "running",
    taskId: null,
    taskTitle: "休息",
    accumulatedMs: clamped,
    segmentStartedAt: now,
    targetMinutes: Math.max(1, Math.round(breakMinutes) || DEFAULT_BREAK_MINUTES),
    lastWorkTaskId,
    lastWorkTaskTitle: lastWorkTaskTitle || ""
  };
}

/**
 * 刷新/重开标签后恢复计时：用真实时间戳续算。
 * 若番茄/休息在离开期间已到期，则在此结算（番茄只记目标分钟，避免离开过久多记）。
 */
export function reconcileFocusTimer(
  state: FocusTimerState,
  now = Date.now(),
  breakMinutes = DEFAULT_BREAK_MINUTES
): ReconcileFocusTimerResult {
  if (state.status === "idle") {
    return {
      state: createIdleFocusTimer(state.mode, state.targetMinutes),
      logTaskId: null,
      logMinutes: 0,
      message: "",
      notify: null,
      restored: false
    };
  }

  if (state.phase === "break") {
    const snap = getFocusSnapshot(state, now);
    if (snap.isComplete) {
      const idle = discardFocusTimer(state);
      return {
        state: idle,
        logTaskId: null,
        logMinutes: 0,
        message: state.lastWorkTaskTitle
          ? `休息已在你离开期间结束。可以继续「${state.lastWorkTaskTitle}」，或换一个任务开始下一轮。`
          : "休息已在你离开期间结束，可以开始下一轮专注。",
        notify: { title: "休息", minutes: 0 },
        restored: true
      };
    }

    return {
      state,
      logTaskId: null,
      logMinutes: 0,
      message: state.status === "paused" ? "已恢复暂停中的休息。" : "已恢复休息倒计时。",
      notify: null,
      restored: true
    };
  }

  // work
  if (state.mode === "pomodoro") {
    const targetMs = state.targetMinutes * 60000;
    const elapsedMs = getFocusElapsedMs(state, now);
    if (elapsedMs >= targetMs) {
      const logMinutes = state.targetMinutes;
      const logTaskId = state.taskId;
      const lastWorkTaskId = state.taskId ?? state.lastWorkTaskId;
      const lastWorkTaskTitle = state.taskTitle || state.lastWorkTaskTitle;
      const overshootMs = elapsedMs - targetMs;
      const breakTargetMs = Math.max(1, breakMinutes) * 60000;

      if (overshootMs >= breakTargetMs) {
        return {
          state: createIdleFocusTimer("pomodoro", normalizePomodoroMinutes(state.targetMinutes)),
          logTaskId,
          logMinutes,
          message: logTaskId && logMinutes > 0
            ? `番茄已在离开期间完成：已记入 ${logMinutes} 分钟。休息也已结束。`
            : "番茄与休息均已在离开期间结束。",
          notify: { title: lastWorkTaskTitle || "当前任务", minutes: logMinutes },
          restored: true
        };
      }

      const breakState = startBreakWithElapsed(
        lastWorkTaskId,
        lastWorkTaskTitle,
        overshootMs,
        now,
        breakMinutes
      );
      const remainingBreakMin = Math.max(1, Math.ceil((breakTargetMs - overshootMs) / 60000));
      return {
        state: breakState,
        logTaskId,
        logMinutes,
        message: logTaskId && logMinutes > 0
          ? `番茄已在离开期间完成：已记入 ${logMinutes} 分钟。已进入休息（约剩 ${remainingBreakMin} 分钟）。`
          : `番茄已在离开期间完成，已进入休息（约剩 ${remainingBreakMin} 分钟）。`,
        notify: { title: lastWorkTaskTitle || "当前任务", minutes: logMinutes },
        restored: true
      };
    }
  }

  const modeLabel = state.mode === "pomodoro" ? "番茄" : "正计时";
  const statusHint = state.status === "paused" ? "暂停中的" : "";
  return {
    state,
    logTaskId: null,
    logMinutes: 0,
    message: state.taskTitle
      ? `已恢复${statusHint}${modeLabel}：「${state.taskTitle}」。`
      : `已恢复${statusHint}${modeLabel}。`,
    notify: null,
    restored: true
  };
}

/** 校验并规范化从存储读出的计时状态；无效则返回 null */
export function parseFocusTimerState(value: unknown): FocusTimerState | null {
  if (typeof value !== "object" || value === null) return null;
  const raw = value as Record<string, unknown>;
  const mode = raw.mode;
  const phase = raw.phase;
  const status = raw.status;
  if (mode !== "stopwatch" && mode !== "pomodoro") return null;
  if (phase !== "work" && phase !== "break") return null;
  if (status !== "idle" && status !== "running" && status !== "paused") return null;

  const taskId = raw.taskId === null ? null : typeof raw.taskId === "string" ? raw.taskId : null;
  if (raw.taskId !== null && raw.taskId !== undefined && typeof raw.taskId !== "string") return null;

  const taskTitle = typeof raw.taskTitle === "string" ? raw.taskTitle : "";
  const accumulatedMs = typeof raw.accumulatedMs === "number" && Number.isFinite(raw.accumulatedMs)
    ? Math.max(0, raw.accumulatedMs)
    : null;
  if (accumulatedMs == null) return null;

  let segmentStartedAt: number | null = null;
  if (raw.segmentStartedAt === null || raw.segmentStartedAt === undefined) {
    segmentStartedAt = null;
  } else if (typeof raw.segmentStartedAt === "number" && Number.isFinite(raw.segmentStartedAt)) {
    segmentStartedAt = raw.segmentStartedAt;
  } else {
    return null;
  }

  const targetMinutes = typeof raw.targetMinutes === "number" && Number.isFinite(raw.targetMinutes)
    ? Math.max(1, Math.round(raw.targetMinutes))
    : null;
  if (targetMinutes == null) return null;

  const lastWorkTaskId = raw.lastWorkTaskId === null || raw.lastWorkTaskId === undefined
    ? null
    : typeof raw.lastWorkTaskId === "string"
      ? raw.lastWorkTaskId
      : null;
  if (raw.lastWorkTaskId !== null && raw.lastWorkTaskId !== undefined && typeof raw.lastWorkTaskId !== "string") {
    return null;
  }
  const lastWorkTaskTitle = typeof raw.lastWorkTaskTitle === "string" ? raw.lastWorkTaskTitle : "";

  if (status === "idle") {
    return createIdleFocusTimer(mode, mode === "pomodoro" ? DEFAULT_POMODORO_MINUTES : targetMinutes);
  }
  if (status === "running" && segmentStartedAt == null) return null;
  if (status === "paused" && segmentStartedAt != null) return null;
  if (phase === "work" && !taskId) return null;

  return {
    mode: phase === "break" ? "pomodoro" : mode,
    phase,
    status,
    taskId: phase === "break" ? null : taskId,
    taskTitle: phase === "break" ? (taskTitle || "休息") : taskTitle,
    accumulatedMs,
    segmentStartedAt: status === "running" ? segmentStartedAt : null,
    targetMinutes,
    lastWorkTaskId,
    lastWorkTaskTitle
  };
}
