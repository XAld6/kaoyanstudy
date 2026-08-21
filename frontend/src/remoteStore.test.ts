import { afterEach, describe, expect, it, vi } from "vitest";
import { createDefaultData } from "./studyCore";
import { createStateSync, fetchState, importStateFile, pushState } from "./remoteStore";

function mockFetchResponse(body: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    text: async () => JSON.stringify(body)
  } as Response;
}

const sampleData = () => {
  const data = createDefaultData();
  data.examDate = "2026-12-20";
  data.tasks = data.tasks.slice(0, 1);
  return data;
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("remoteStore", () => {
  it("fetchState parses server state", async () => {
    const data = sampleData();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse({
      revision: 3,
      updatedAt: "2026-08-21T12:00:00+00:00",
      data,
      focusStats: { version: 1, byDate: { "2026-08-21": { date: "2026-08-21", focusMinutes: 25, pomodoroCount: 1, sessionCount: 1 } } }
    })));

    const state = await fetchState();

    expect(state).not.toBeNull();
    expect(state!.revision).toBe(3);
    expect(state!.data.examDate).toBe("2026-12-20");
    expect(state!.focusStats.byDate["2026-08-21"].focusMinutes).toBe(25);
  });

  it("fetchState returns null for empty store", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse({ revision: 0, updatedAt: null, data: null, focusStats: {} })));
    expect(await fetchState()).toBeNull();
  });

  it("fetchState throws with server detail on failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse({ detail: "服务器内部错误" }, false, 500)));
    await expect(fetchState()).rejects.toThrow("服务器内部错误");
  });

  it("pushState returns ok with new revision", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse({
      revision: 5,
      updatedAt: "2026-08-21T12:00:00+00:00",
      data: sampleData(),
      focusStats: { version: 1, byDate: {} }
    })));

    const result = await pushState({ baseRevision: 4, data: sampleData(), focusStats: { version: 1, byDate: {} } });

    expect(result.ok).toBe(true);
    if (result.ok) expect(result.revision).toBe(5);
  });

  it("pushState maps 409 conflict with server state", async () => {
    const serverData = sampleData();
    serverData.examDate = "2026-12-25";
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse({
      detail: "冲突",
      server: { revision: 9, updatedAt: null, data: serverData, focusStats: { version: 1, byDate: {} } }
    }, false, 409)));

    const result = await pushState({ baseRevision: 4, data: sampleData(), focusStats: { version: 1, byDate: {} } });

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.conflict.revision).toBe(9);
      expect(result.conflict.data.examDate).toBe("2026-12-25");
    }
  });

  it("pushState throws on unexpected failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse({ detail: "网关错误" }, false, 502)));
    await expect(pushState({ baseRevision: 0, data: sampleData(), focusStats: { version: 1, byDate: {} } })).rejects.toThrow("网关错误");
  });

  it("importStateFile wraps bare old-format AppData with replace mode", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockFetchResponse({
      revision: 1,
      updatedAt: null,
      data: sampleData(),
      focusStats: { version: 1, byDate: {} }
    }));
    vi.stubGlobal("fetch", fetchMock);

    const remote = await importStateFile(JSON.stringify(sampleData()), "replace");
    expect(remote.revision).toBe(1);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/state/import");
    const sent = JSON.parse(String(init.body)) as Record<string, unknown>;
    expect(sent.mode).toBe("replace");
    expect((sent.data as Record<string, unknown>).examDate).toBe("2026-12-20");
  });

  it("importStateFile forwards focusStats inside export-style files", async () => {
    const stats = { version: 1, byDate: { "2026-08-21": { date: "2026-08-21", focusMinutes: 25, pomodoroCount: 1, sessionCount: 1 } } };
    const fetchMock = vi.fn().mockResolvedValue(mockFetchResponse({
      revision: 2,
      updatedAt: null,
      data: sampleData(),
      focusStats: stats
    }));
    vi.stubGlobal("fetch", fetchMock);

    await importStateFile(JSON.stringify({ ...sampleData(), focusStats: stats }), "merge");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/state/import");
    const sent = JSON.parse(String(init.body)) as Record<string, unknown>;
    expect(sent.mode).toBe("merge");
    expect((sent.focusStats as Record<string, unknown>).byDate).toBeDefined();
  });
});

describe("createStateSync", () => {
  it("coalesces multiple schedules within the delay window", async () => {
    vi.useFakeTimers();
    try {
      const calls: string[] = [];
      const sync = createStateSync({ delayMs: 50 });
      sync.schedule(() => void calls.push("a"));
      sync.schedule(() => void calls.push("b"));
      sync.schedule(() => void calls.push("c"));
      expect(calls).toEqual([]);

      await vi.advanceTimersByTimeAsync(100);
      // 800ms 窗口内合并为一次任务（任务执行时读最新状态，旧调度被覆盖）
      expect(calls).toEqual(["c"]);
    } finally {
      vi.useRealTimers();
    }
  });

  it("flush executes pending task immediately and awaits completion", async () => {
    vi.useFakeTimers();
    try {
      const calls: string[] = [];
      const sync = createStateSync({ delayMs: 500 });
      sync.schedule(() => {
        calls.push("pushed");
      });
      await sync.flush();
      expect(calls).toEqual(["pushed"]);
    } finally {
      vi.useRealTimers();
    }
  });

  it("runs queued tasks serially, never concurrently", async () => {
    const order: string[] = [];
    let inFlight = 0;
    let maxInFlight = 0;
    const sync = createStateSync({ delayMs: 10 });

    sync.schedule(() => new Promise<void>((resolve) => {
      inFlight += 1;
      maxInFlight = Math.max(maxInFlight, inFlight);
      setTimeout(() => {
        order.push("first");
        inFlight -= 1;
        resolve();
      }, 40);
    }));
    await sync.flush(); // 执行第一个任务（慢）

    sync.schedule(() => new Promise<void>((resolve) => {
      inFlight += 1;
      maxInFlight = Math.max(maxInFlight, inFlight);
      setTimeout(() => {
        order.push("second");
        inFlight -= 1;
        resolve();
      }, 10);
    }));
    await sync.flush(); // 排队等第一个完成后才执行

    expect(order).toEqual(["first", "second"]);
    expect(maxInFlight).toBe(1);
  });

  it("isolates a failing task without blocking later queued tasks", async () => {
    const order: string[] = [];
    const sync = createStateSync({ delayMs: 10 });

    sync.schedule(() => {
      throw new Error("boom");
    });
    sync.schedule(() => {
      order.push("after-failure");
    });

    await new Promise<void>((resolve) => setTimeout(resolve, 80));
    expect(order).toEqual(["after-failure"]);
  });
});