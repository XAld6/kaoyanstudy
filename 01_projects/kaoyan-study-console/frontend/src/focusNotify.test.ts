import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  buildPomodoroCompleteMessage,
  getNotificationPermissionState,
  playFocusCompleteSound,
  showFocusCompleteNotification
} from "./focusNotify";

describe("focusNotify", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("builds a clear pomodoro complete message", () => {
    expect(buildPomodoroCompleteMessage("高数强化", 25)).toEqual({
      title: "番茄完成",
      body: "「高数强化」番茄结束，已记入约 25 分钟。"
    });
  });

  it("maps notification permission states", () => {
    expect(getNotificationPermissionState(undefined)).toBe("unsupported");
    expect(getNotificationPermissionState({ permission: "granted" })).toBe("granted");
    expect(getNotificationPermissionState({ permission: "denied" })).toBe("denied");
    expect(getNotificationPermissionState({ permission: "default" })).toBe("default");
  });

  it("plays a short complete sound through AudioContext", async () => {
    const oscillator = {
      type: "sine",
      frequency: { value: 0 },
      connect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn()
    };
    const gain = {
      gain: {
        setValueAtTime: vi.fn(),
        linearRampToValueAtTime: vi.fn()
      },
      connect: vi.fn()
    };
    const ctx = {
      state: "running",
      currentTime: 10,
      resume: vi.fn(async () => undefined),
      close: vi.fn(async () => undefined),
      createOscillator: vi.fn(() => oscillator),
      createGain: vi.fn(() => gain),
      destination: {}
    };

    const played = await playFocusCompleteSound(() => ctx);
    expect(played).toBe(true);
    expect(ctx.createOscillator).toHaveBeenCalledTimes(2);
    expect(oscillator.start).toHaveBeenCalled();
    expect(oscillator.stop).toHaveBeenCalled();
    expect(gain.gain.linearRampToValueAtTime).toHaveBeenCalled();
  });

  it("shows notification when permission is granted", async () => {
    const instances: Array<{ close: ReturnType<typeof vi.fn>; title: string; options?: NotificationOptions }> = [];
    function FakeNotification(this: { close: ReturnType<typeof vi.fn>; title: string; options?: NotificationOptions }, title: string, options?: NotificationOptions) {
      this.close = vi.fn();
      this.title = title;
      this.options = options;
      instances.push(this);
    }
    (FakeNotification as unknown as { permission: NotificationPermission }).permission = "granted";
    (FakeNotification as unknown as { requestPermission: () => Promise<NotificationPermission> }).requestPermission = async () => "granted";

    const result = await showFocusCompleteNotification("英语阅读", 25, {
      enabled: true,
      notificationCtor: FakeNotification as unknown as typeof Notification
    });

    expect(result).toEqual({ shown: true, reason: "shown" });
    expect(instances[0]?.title).toBe("番茄完成");
    expect(String(instances[0]?.options?.body ?? "")).toContain("英语阅读");
  });

  it("does not show notification when disabled or denied", async () => {
    class DeniedNotification {
      static permission: NotificationPermission = "denied";
      static requestPermission = vi.fn(async () => "denied" as NotificationPermission);
      constructor() {
        throw new Error("should not construct");
      }
    }

    await expect(showFocusCompleteNotification("任务", 25, {
      enabled: false,
      notificationCtor: DeniedNotification as unknown as typeof Notification
    })).resolves.toEqual({ shown: false, reason: "disabled" });

    await expect(showFocusCompleteNotification("任务", 25, {
      enabled: true,
      notificationCtor: DeniedNotification as unknown as typeof Notification
    })).resolves.toEqual({ shown: false, reason: "denied" });
  });
});
