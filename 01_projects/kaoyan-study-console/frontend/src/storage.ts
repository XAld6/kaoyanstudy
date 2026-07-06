import { AppData, StudyTask, createDefaultData, formatDate } from "./studyCore";

const STORAGE_KEY = "kaoyan-study-console:v1";

export type LoadAppDataResult = {
  data: AppData;
  recovered: boolean;
};

export type AppDataExportKind = "manual" | "before-import";

export type AppDataExportPackage = {
  filename: string;
  content: string;
  mimeType: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isPositiveNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function isNonNegativeNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

function isPriority(value: unknown): value is StudyTask["priority"] {
  return value === "高" || value === "中" || value === "低";
}

function isStatus(value: unknown): value is StudyTask["status"] {
  return value === "todo" || value === "done";
}

function isValidSubject(value: unknown) {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.name === "string"
    && typeof value.color === "string"
    && isPositiveNumber(value.weeklyTargetHours);
}

function isValidTask(value: unknown) {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.subjectId === "string"
    && typeof value.title === "string"
    && typeof value.date === "string"
    && isPositiveNumber(value.estimatedMinutes)
    && isNonNegativeNumber(value.actualMinutes)
    && isPriority(value.priority)
    && isStatus(value.status);
}

function isValidReview(value: unknown) {
  return isRecord(value) && typeof value.date === "string" && typeof value.text === "string";
}

function isValidAppData(value: unknown): value is AppData {
  return isRecord(value)
    && value.version === 1
    && typeof value.examDate === "string"
    && Array.isArray(value.subjects)
    && Array.isArray(value.tasks)
    && Array.isArray(value.reviews)
    && value.subjects.every(isValidSubject)
    && value.tasks.every(isValidTask)
    && value.reviews.every(isValidReview);
}

export function loadAppDataWithStatus(): LoadAppDataResult {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return { data: createDefaultData(), recovered: false };

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!isValidAppData(parsed)) {
      return { data: createDefaultData(), recovered: true };
    }
    return { data: parsed, recovered: false };
  } catch {
    return { data: createDefaultData(), recovered: true };
  }
}

export function loadAppData(): AppData {
  return loadAppDataWithStatus().data;
}

export function saveAppData(data: AppData) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function clearAppData() {
  localStorage.removeItem(STORAGE_KEY);
}

export function exportAppData(data: AppData) {
  return JSON.stringify(data, null, 2);
}

export function createAppDataExport(data: AppData, kind: AppDataExportKind = "manual", date = formatDate()): AppDataExportPackage {
  const name = kind === "before-import" ? `kaoyan-study-backup-before-import-${date}.json` : `kaoyan-study-${date}.json`;
  return {
    filename: name,
    content: exportAppData(data),
    mimeType: "application/json;charset=utf-8"
  };
}

export function parseImportedData(text: string): AppData {
  const parsed = JSON.parse(text) as unknown;
  if (!isValidAppData(parsed)) {
    throw new Error("导入文件不是有效的考研学习数据。");
  }
  return parsed;
}
