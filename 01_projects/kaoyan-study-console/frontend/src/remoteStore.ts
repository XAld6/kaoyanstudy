import { AppData, createDefaultData } from "./studyCore";
import { FocusStatsStore, createEmptyFocusStatsStore, parseFocusStatsStore } from "./focusStats";
import { readApiBody } from "./api";

export type RemoteState = {
  revision: number;
  updatedAt: string | null;
  data: AppData;
  focusStats: FocusStatsStore;
};

export type PushResult =
  | { ok: true; revision: number; updatedAt: string | null }
  | { ok: false; conflict: RemoteState };

function errorDetail(body: unknown, fallback: string): string {
  if (typeof body === "object" && body !== null) {
    const detail = (body as Record<string, unknown>).detail;
    if (typeof detail === "string" && detail) return detail;
  }
  return fallback;
}

function parseRemoteState(record: Record<string, unknown>): RemoteState {
  return {
    revision: Number(record.revision ?? 0),
    updatedAt: typeof record.updatedAt === "string" ? record.updatedAt : null,
    data: (record.data ?? createDefaultData()) as AppData,
    focusStats: parseFocusStatsStore(record.focusStats) ?? createEmptyFocusStatsStore()
  };
}

/** 拉取服务器状态；空库返回 null（调用方用 createDefaultData() 播种） */
export async function fetchState(): Promise<RemoteState | null> {
  const response = await fetch("/api/state");
  const body = await readApiBody(response);
  if (!response.ok) {
    throw new Error(errorDetail(body, "读取服务器数据失败"));
  }
  const record = body as Record<string, unknown>;
  if (record.data == null) return null;
  return parseRemoteState(record);
}

/** 整快照推送；baseRevision 不匹配时返回 conflict（含服务器当前状态） */
export async function pushState(input: {
  baseRevision: number;
  data: AppData;
  focusStats: FocusStatsStore;
}): Promise<PushResult> {
  const response = await fetch("/api/state", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      baseRevision: input.baseRevision,
      data: input.data,
      focusStats: input.focusStats
    })
  });
  const body = await readApiBody(response);

  if (response.status === 409) {
    const record = body as Record<string, unknown>;
    const server = record.server as Record<string, unknown> | undefined;
    if (!server) {
      throw new Error(errorDetail(body, "服务器数据冲突，但无法读取服务器当前状态"));
    }
    return {
      ok: false,
      conflict: parseRemoteState(server)
    };
  }

  if (!response.ok) {
    throw new Error(errorDetail(body, "保存到服务器失败"));
  }
  return {
    ok: true,
    revision: Number((body as Record<string, unknown>).revision ?? 0),
    updatedAt:
      typeof (body as Record<string, unknown>).updatedAt === "string"
        ? ((body as Record<string, unknown>).updatedAt as string)
        : null
  };
}

/**
 * 把导入文本发送到服务器。
 * 兼容两种输入：裸 AppData（老备份 JSON）与带 focusStats 的新导出格式。
 * mode：replace=整体替换（恢复备份语义，幂等）；merge=按 id/date 幂等合并。
 */
export async function importStateFile(text: string, mode: "replace" | "merge"): Promise<RemoteState> {
  const raw = JSON.parse(text) as Record<string, unknown>;
  const dataRaw = raw.data && typeof raw.data === "object" ? raw.data : raw;
  const focusStatsRaw =
    raw.focusStats ??
    (typeof dataRaw === "object" && dataRaw !== null
      ? (dataRaw as Record<string, unknown>).focusStats
      : undefined) ??
    undefined;

  const response = await fetch("/api/state/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data: dataRaw, focusStats: focusStatsRaw, mode })
  });
  const body = await readApiBody(response);
  if (!response.ok) {
    throw new Error(errorDetail(body, "导入到服务器失败"));
  }
  return parseRemoteState(body as Record<string, unknown>);
}

export type StateSync = {
  /** 去抖调度：delayMs 内多次调用合并为一次；任务串行执行，绝不并发 PUT */
  schedule(task: () => void | Promise<void>): void;
  /** 立即执行挂起的任务并等待全部在途任务完成（供 pagehide/visibilitychange 调用） */
  flush(): Promise<void>;
};

/** 去抖同步器：800ms 合并 + 串行队列（每次真正执行时读取最新状态） */
export function createStateSync(opts: { delayMs?: number } = {}): StateSync {
  const delayMs = opts.delayMs ?? 800;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let pendingTask: (() => void | Promise<void>) | null = null;
  let queue: Promise<void> = Promise.resolve();

  function runTask(task: () => void | Promise<void>): void {
    queue = queue.then(task).catch(() => {
      // 单次任务失败不阻塞队列后续任务；错误由 task 内部自行处理
    });
  }

  return {
    schedule(task) {
      pendingTask = task;
      if (timer) return;
      timer = setTimeout(() => {
        timer = null;
        const current = pendingTask;
        pendingTask = null;
        if (current) runTask(current);
      }, delayMs);
    },
    async flush() {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      const current = pendingTask;
      pendingTask = null;
      if (current) runTask(current);
      await queue;
    }
  };
}