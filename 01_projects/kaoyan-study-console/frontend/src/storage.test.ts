import { beforeEach, describe, expect, it } from "vitest";
import { createDefaultData } from "./studyCore";
import { createAppDataExport, loadAppData, loadAppDataWithStatus, parseImportedData, saveAppData } from "./storage";

const STORAGE_KEY = "kaoyan-study-console:v1";
const localStorageMock = new Map<string, string>();

Object.defineProperty(globalThis, "localStorage", {
  value: {
    getItem: (key: string) => localStorageMock.get(key) ?? null,
    setItem: (key: string, value: string) => localStorageMock.set(key, value),
    removeItem: (key: string) => localStorageMock.delete(key),
    clear: () => localStorageMock.clear()
  },
  configurable: true
});

describe("storage", () => {
  beforeEach(() => {
    localStorage.clear();
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
});
