import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  VALID_VIEWS,
  VIEW_STORAGE_KEY,
  loadSavedView,
  saveViewToStorage
} from "./useView";

const sessionStorageMock = new Map<string, string>();

Object.defineProperty(globalThis, "sessionStorage", {
  value: {
    getItem: (key: string) => sessionStorageMock.get(key) ?? null,
    setItem: (key: string, value: string) => sessionStorageMock.set(key, value),
    removeItem: (key: string) => sessionStorageMock.delete(key),
    clear: () => sessionStorageMock.clear()
  },
  configurable: true
});

describe("useView helpers", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it("exposes the storage key and the canonical view list", () => {
    expect(VIEW_STORAGE_KEY).toBe("kaoyan-study-console:view:v1");
    expect(VALID_VIEWS).toEqual(["today", "plan", "progress", "coach", "settings"]);
  });

  it("loadSavedView returns today when nothing is stored", () => {
    expect(loadSavedView()).toBe("today");
  });

  it("saveViewToStorage persists view and loadSavedView reads it back", () => {
    saveViewToStorage("progress");
    expect(sessionStorage.getItem(VIEW_STORAGE_KEY)).toBe("progress");
    expect(loadSavedView()).toBe("progress");
  });

  it("loadSavedView rejects unknown stored values and falls back to today", () => {
    sessionStorage.setItem(VIEW_STORAGE_KEY, "nonsense");
    expect(loadSavedView()).toBe("today");
  });
});
