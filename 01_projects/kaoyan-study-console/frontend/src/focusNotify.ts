export type FocusNotifyPrefs = {
  soundEnabled: boolean;
  notificationEnabled: boolean;
};

export type NotificationPermissionState = "unsupported" | "default" | "granted" | "denied";

export const DEFAULT_FOCUS_NOTIFY_PREFS: FocusNotifyPrefs = {
  soundEnabled: true,
  notificationEnabled: true
};

export function getNotificationPermissionState(
  notificationApi: { permission?: string } | undefined = typeof Notification !== "undefined" ? Notification : undefined
): NotificationPermissionState {
  if (!notificationApi || typeof notificationApi.permission !== "string") return "unsupported";
  if (notificationApi.permission === "granted") return "granted";
  if (notificationApi.permission === "denied") return "denied";
  return "default";
}

export function buildPomodoroCompleteMessage(taskTitle: string, elapsedMinutes: number) {
  const title = taskTitle.trim() || "当前任务";
  const body = elapsedMinutes > 0
    ? `「${title}」番茄结束，已记入约 ${elapsedMinutes} 分钟。`
    : `「${title}」番茄时间到。`;
  return {
    title: "番茄完成",
    body
  };
}

type MinimalAudioContext = {
  state: string;
  currentTime: number;
  resume: () => Promise<void> | void;
  close: () => Promise<void> | void;
  createOscillator: () => {
    type: string;
    frequency: { value: number };
    connect: (node: unknown) => void;
    start: (when?: number) => void;
    stop: (when?: number) => void;
  };
  createGain: () => {
    gain: {
      setValueAtTime: (value: number, when: number) => void;
      linearRampToValueAtTime?: (value: number, when: number) => void;
      exponentialRampToValueAtTime?: (value: number, when: number) => void;
    };
    connect: (node: unknown) => void;
  };
  destination: unknown;
};

/** 用 Web Audio 播两声短提示，无外部音频文件 */
export async function playFocusCompleteSound(
  audioContextFactory?: () => MinimalAudioContext
): Promise<boolean> {
  try {
    const factory = audioContextFactory ?? (() => {
      const Ctor = (globalThis as unknown as {
        AudioContext?: new () => MinimalAudioContext;
        webkitAudioContext?: new () => MinimalAudioContext;
      }).AudioContext
        ?? (globalThis as unknown as { webkitAudioContext?: new () => MinimalAudioContext }).webkitAudioContext;
      if (!Ctor) throw new Error("AudioContext unsupported");
      return new Ctor();
    });

    const ctx = factory();
    if (ctx.state === "suspended" && typeof ctx.resume === "function") {
      await ctx.resume();
    }

    const playBeep = (when: number, frequency: number, duration = 0.12) => {
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = "sine";
      oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0.001, when);
      if (typeof gain.gain.linearRampToValueAtTime === "function") {
        gain.gain.linearRampToValueAtTime(0.12, when + 0.015);
        gain.gain.linearRampToValueAtTime(0.001, when + duration);
      } else if (typeof gain.gain.exponentialRampToValueAtTime === "function") {
        gain.gain.exponentialRampToValueAtTime(0.12, when + 0.015);
        gain.gain.exponentialRampToValueAtTime(0.001, when + duration);
      }
      oscillator.connect(gain);
      gain.connect(ctx.destination);
      oscillator.start(when);
      oscillator.stop(when + duration + 0.02);
    };

    const now = Number(ctx.currentTime) || 0;
    playBeep(now, 880);
    playBeep(now + 0.16, 1175);

    if (typeof globalThis.setTimeout === "function") {
      globalThis.setTimeout(() => {
        void Promise.resolve(ctx.close()).catch(() => undefined);
      }, 500);
    }
    return true;
  } catch {
    return false;
  }
}

export type ShowNotificationResult = {
  shown: boolean;
  reason: "shown" | "disabled" | "unsupported" | "denied" | "default" | "error";
};

export async function showFocusCompleteNotification(
  taskTitle: string,
  elapsedMinutes: number,
  options?: {
    enabled?: boolean;
    notificationCtor?: typeof Notification;
    requestPermission?: () => Promise<NotificationPermission>;
  }
): Promise<ShowNotificationResult> {
  if (options?.enabled === false) {
    return { shown: false, reason: "disabled" };
  }

  const NotificationCtor = options?.notificationCtor
    ?? (typeof Notification !== "undefined" ? Notification : undefined);
  if (!NotificationCtor) {
    return { shown: false, reason: "unsupported" };
  }

  let permission = NotificationCtor.permission as NotificationPermission;
  if (permission === "default") {
    const request = options?.requestPermission
      ?? (() => NotificationCtor.requestPermission());
    try {
      permission = await request();
    } catch {
      return { shown: false, reason: "error" };
    }
  }

  if (permission === "denied") return { shown: false, reason: "denied" };
  if (permission !== "granted") return { shown: false, reason: "default" };

  const message = buildPomodoroCompleteMessage(taskTitle, elapsedMinutes);
  try {
    const notification = new NotificationCtor(message.title, {
      body: message.body,
      tag: "kaoyan-focus-pomodoro-complete",
      silent: false
    });
    if (typeof notification.close === "function" && typeof window !== "undefined" && typeof window.setTimeout === "function") {
      window.setTimeout(() => {
        try {
          notification.close();
        } catch {
          // ignore close failures
        }
      }, 8000);
    }
    return { shown: true, reason: "shown" };
  } catch {
    return { shown: false, reason: "error" };
  }
}

export async function notifyFocusComplete(
  prefs: FocusNotifyPrefs,
  taskTitle: string,
  elapsedMinutes: number
): Promise<{ sound: boolean; notification: ShowNotificationResult }> {
  const sound = prefs.soundEnabled ? await playFocusCompleteSound() : false;
  const notification = await showFocusCompleteNotification(taskTitle, elapsedMinutes, {
    enabled: prefs.notificationEnabled
  });
  return { sound, notification };
}
