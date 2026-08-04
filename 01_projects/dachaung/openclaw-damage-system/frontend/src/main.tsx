import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  Archive,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Columns2,
  Download,
  FileDown,
  FileImage,
  GitBranch,
  History,
  Loader2,
  Microscope,
  Moon,
  RefreshCw,
  RotateCcw,
  Settings2,
  ShieldAlert,
  Sun,
  Trash2,
  Upload,
  Workflow,
  X
} from "lucide-react";
import "./styles.css";

type RiskLevel = "低" | "中" | "高";
const MAX_UPLOAD_BYTES = 8 * 1024 * 1024;
const MAX_BATCH_FILES = 12;

type WorkflowStep = {
  agent: string;
  label: string;
  status: string;
  duration_ms: number;
  summary: string;
};

type DamageKind = "crack" | "spalling" | "stain" | string;

type Detection = {
  kind: DamageKind;
  label: string;
  bbox: number[];
  confidence: number;
  area_ratio: number;
  length_estimate: number;
  explanation?: string;
};

const KIND_META: Record<string, { label: string; short: string; className: string }> = {
  crack: { label: "裂缝", short: "裂", className: "kind-crack" },
  spalling: { label: "剥落", short: "剥", className: "kind-spalling" },
  stain: { label: "渗水/色差", short: "渗", className: "kind-stain" }
};

function kindMeta(kind: string) {
  return KIND_META[kind] ?? { label: kind, short: "?", className: "kind-other" };
}

function metricNumber(metrics: Record<string, number>, key: string, fallback = 0) {
  const value = metrics[key];
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

type RecordSummary = {
  id: number;
  filename: string;
  created_at: string;
  risk_level: RiskLevel;
  review_status: string;
  confidence: number;
  detection_count: number;
  original_url: string;
  annotated_url: string;
  crack_count?: number;
  spalling_count?: number;
  stain_count?: number;
};

type RecordDetail = RecordSummary & {
  quality: Record<string, string | number | boolean>;
  detections: Detection[];
  workflow: WorkflowStep[];
  metrics: Record<string, number>;
  risk_reason: string;
  review_note: string;
};

type ServerStats = {
  total: number;
  pending_review: number;
  auto_pass: number;
  reviewed: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  avg_confidence: number;
  total_detections: number;
  by_risk: Record<string, number>;
  by_kind?: { crack: number; spalling: number; stain: number };
  by_review?: Record<string, number>;
  timeline?: { day: string; count: number }[];
  confidence_buckets?: Record<string, number>;
};

type SettingSchemaItem = {
  key: string;
  label: string;
  min: number;
  max: number;
  step: number;
  type: "float" | "int" | string;
};

type RuntimeSettings = Record<string, number>;

type CompareResult = {
  left: {
    id: number;
    filename: string;
    risk_level: RiskLevel;
    confidence: number;
    detection_count: number;
    original_url: string;
    annotated_url: string;
    metrics: Record<string, number>;
    risk_reason?: string;
  };
  right: {
    id: number;
    filename: string;
    risk_level: RiskLevel;
    confidence: number;
    detection_count: number;
    original_url: string;
    annotated_url: string;
    metrics: Record<string, number>;
    risk_reason?: string;
  };
  delta: {
    risk_delta: number;
    confidence_delta: number;
    area_ratio_delta: number;
    count_delta: { crack: number; spalling: number; stain: number; total: number };
  };
  notes: string[];
  verdict?: string;
};

const riskRank: Record<RiskLevel, number> = { 低: 1, 中: 2, 高: 3 };
const riskOptions: RiskLevel[] = ["低", "中", "高"];
const reviewFilterOptions = ["全部", "待复核", "自动通过", "已复核"] as const;

const agentRoles = [
  "图像质量Agent",
  "病害识别Agent",
  "量化分析Agent",
  "风险评估Agent",
  "复核路由Agent",
  "报告归档Agent"
];

function assetUrl(path: string) {
  return path;
}

async function apiErrorMessage(res: Response, fallback: string) {
  const text = await res.text();
  if (!text) return fallback;
  try {
    const body = JSON.parse(text) as { detail?: unknown };
    return typeof body.detail === "string" && body.detail.trim() ? body.detail : fallback;
  } catch {
    return fallback;
  }
}

function getSixAgentWorkflow(workflow: WorkflowStep[]) {
  if (workflow.length <= 6) return workflow;
  const archive = workflow.find((step) => step.agent === "ArchiveAgent");
  const report = workflow.find((step) => step.agent === "ReportAgent");
  if (!archive || !report) return workflow.slice(0, 6);
  const merged: WorkflowStep = {
    agent: "ReportArchiveAgent",
    label: "报告归档输出",
    status: report.status,
    duration_ms: archive.duration_ms + report.duration_ms,
    summary: "原图、标注图、结构化结果、工作流日志和PDF报告素材已归档"
  };
  return [...workflow.filter((step) => step.agent !== "ArchiveAgent" && step.agent !== "ReportAgent"), merged].slice(0, 6);
}

function App() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [records, setRecords] = useState<RecordSummary[]>([]);
  const [active, setActive] = useState<RecordDetail | null>(null);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setDragging] = useState(false);
  const [backendOnline, setBackendOnline] = useState<"unknown" | "online" | "offline">("unknown");
  const [detectorLabel, setDetectorLabel] = useState("检测后端检测中");
  const [appVersion, setAppVersion] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [reviewRisk, setReviewRisk] = useState<RiskLevel>("低");
  const [filterRisk, setFilterRisk] = useState<"全部" | RiskLevel>("全部");
  const [filterReview, setFilterReview] = useState<(typeof reviewFilterOptions)[number]>("全部");
  const [filterQuery, setFilterQuery] = useState("");
  const [serverStats, setServerStats] = useState<ServerStats | null>(null);
  const [compareLeftId, setCompareLeftId] = useState<number | null>(null);
  const [compareRightId, setCompareRightId] = useState<number | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [comparing, setComparing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<RuntimeSettings>({});
  const [settingsSchema, setSettingsSchema] = useState<SettingSchemaItem[]>([]);
  const [settingsDirty, setSettingsDirty] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [redetecting, setRedetecting] = useState(false);
  const [lightbox, setLightbox] = useState<{ src: string; title: string } | null>(null);
  const [darkMode, setDarkMode] = useState(() => {
    try {
      return localStorage.getItem("openclaw-theme") === "dark";
    } catch {
      return false;
    }
  });
  const [autoNextOnReview, setAutoNextOnReview] = useState(() => {
    try {
      return localStorage.getItem("openclaw-auto-next") !== "0";
    } catch {
      return true;
    }
  });
  const [showStatsPanel, setShowStatsPanel] = useState(false);
  const [sortBy, setSortBy] = useState<"id" | "confidence" | "detection_count" | "filename">("id");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(30);
  const [pageMeta, setPageMeta] = useState({ total: 0, pages: 1, has_next: false, has_prev: false });
  const [batchRedetecting, setBatchRedetecting] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);
  const canUpload = !uploading && backendOnline !== "offline";
  const dropZoneClass = ["drop-zone", canUpload ? "" : "disabled", canUpload && isDragging ? "dragging" : ""].filter(Boolean).join(" ");
  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const allVisibleSelected = records.length > 0 && records.every((r) => selectedSet.has(r.id));

  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? "dark" : "light";
    try {
      localStorage.setItem("openclaw-theme", darkMode ? "dark" : "light");
    } catch {
      /* ignore */
    }
  }, [darkMode]);

  useEffect(() => {
    try {
      localStorage.setItem("openclaw-auto-next", autoNextOnReview ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [autoNextOnReview]);

  function buildFilterQuery(extraIds?: number[]) {
    const params = new URLSearchParams();
    if (filterRisk !== "全部") params.set("risk_level", filterRisk);
    if (filterReview !== "全部") params.set("review_status", filterReview);
    if (filterQuery.trim()) params.set("q", filterQuery.trim());
    if (extraIds && extraIds.length) params.set("ids", extraIds.join(","));
    return params.toString();
  }

  function toggleSelect(id: number) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function toggleSelectAllVisible() {
    if (allVisibleSelected) {
      const visible = new Set(records.map((r) => r.id));
      setSelectedIds((prev) => prev.filter((id) => !visible.has(id)));
    } else {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...records.map((r) => r.id)])));
    }
  }

  const stats = useMemo(() => {
    if (serverStats) {
      return {
        total: serverStats.total,
        pending: serverStats.pending_review,
        high: serverStats.high_risk,
        avg: serverStats.avg_confidence
      };
    }
    const total = records.length;
    const pending = records.filter((r) => r.review_status === "待复核").length;
    const high = records.filter((r) => r.risk_level === "高").length;
    const avg = total ? records.reduce((sum, r) => sum + r.confidence, 0) / total : 0;
    return { total, pending, high, avg };
  }, [records, serverStats]);

  async function loadStats() {
    const res = await fetch("/api/stats");
    if (!res.ok) return;
    const data = (await res.json()) as ServerStats;
    setServerStats(data);
  }

  async function loadRecords(selectFirst = false) {
    const params = new URLSearchParams();
    if (filterRisk !== "全部") params.set("risk_level", filterRisk);
    if (filterReview !== "全部") params.set("review_status", filterReview);
    if (filterQuery.trim()) params.set("q", filterQuery.trim());
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    params.set("sort", sortBy);
    params.set("order", sortOrder);
    const res = await fetch(`/api/records/page?${params.toString()}`);
    if (!res.ok) {
      // fallback to flat list for older backends
      const query = buildFilterQuery();
      const legacy = await fetch(query ? `/api/records?${query}` : "/api/records");
      if (!legacy.ok) throw new Error(await apiErrorMessage(legacy, "历史记录加载失败"));
      const data: RecordSummary[] = await legacy.json();
      setRecords(data);
      setPageMeta({ total: data.length, pages: 1, has_next: false, has_prev: false });
      if (selectFirst && data[0]) await openRecord(data[0].id);
      else if (active && !data.some((item) => item.id === active.id)) setActive(null);
      return;
    }
    const body = (await res.json()) as {
      items: RecordSummary[];
      total: number;
      pages: number;
      has_next: boolean;
      has_prev: boolean;
      page: number;
    };
    setRecords(body.items || []);
    setPageMeta({
      total: body.total || 0,
      pages: body.pages || 1,
      has_next: Boolean(body.has_next),
      has_prev: Boolean(body.has_prev)
    });
    if (selectFirst && body.items?.[0]) {
      await openRecord(body.items[0].id);
    } else if (active && !(body.items || []).some((item) => item.id === active.id)) {
      setActive(null);
    }
  }

  async function loadSettings() {
    const res = await fetch("/api/settings");
    if (!res.ok) return;
    const body = (await res.json()) as { settings: RuntimeSettings; schema: SettingSchemaItem[] };
    setSettings(body.settings || {});
    setSettingsSchema(body.schema || []);
    setSettingsDirty(false);
  }

  async function saveSettings() {
    setSavingSettings(true);
    try {
      const res = await fetch("/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res, "参数保存失败"));
      const body = (await res.json()) as { settings: RuntimeSettings; schema: SettingSchemaItem[] };
      setSettings(body.settings || {});
      setSettingsSchema(body.schema || []);
      setSettingsDirty(false);
      setInfo("运行参数已更新，后续检测将使用新阈值");
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "参数保存失败");
    } finally {
      setSavingSettings(false);
    }
  }

  async function resetSettings() {
    setSavingSettings(true);
    try {
      const res = await fetch("/api/settings/reset", { method: "POST" });
      if (!res.ok) throw new Error(await apiErrorMessage(res, "参数重置失败"));
      const body = (await res.json()) as { settings: RuntimeSettings; schema: SettingSchemaItem[] };
      setSettings(body.settings || {});
      setSettingsSchema(body.schema || []);
      setSettingsDirty(false);
      setInfo("已恢复默认运行参数");
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "参数重置失败");
    } finally {
      setSavingSettings(false);
    }
  }

  function exportWithCurrentFilter(kind: "csv" | "pdf-zip", onlySelected = false) {
    const query = onlySelected && selectedIds.length
      ? buildFilterQuery(selectedIds)
      : buildFilterQuery();
    const url = kind === "csv"
      ? `/api/export/csv${query ? `?${query}` : ""}`
      : `/api/export/pdf-zip${query ? `?${query}` : ""}`;
    window.open(url, "_blank", "noopener,noreferrer");
    if (onlySelected && selectedIds.length) {
      setInfo(kind === "csv" ? `已导出选中 ${selectedIds.length} 条 CSV` : `已打包选中 ${selectedIds.length} 份 PDF`);
    } else {
      setInfo(kind === "csv" ? "已开始下载 CSV 导出" : "已开始下载批量 PDF 压缩包");
    }
  }

  async function batchDeleteSelected() {
    if (!selectedIds.length) {
      setError("请先勾选要删除的记录");
      return;
    }
    if (!window.confirm(`确认删除选中的 ${selectedIds.length} 条记录？`)) return;
    try {
      const res = await fetch("/api/records/batch-delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: selectedIds })
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res, "批量删除失败"));
      const body = (await res.json()) as { deleted_count: number };
      if (active && selectedIds.includes(active.id)) setActive(null);
      setSelectedIds([]);
      setInfo(`已删除 ${body.deleted_count} 条记录`);
      setError("");
      await refreshAll(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量删除失败");
    }
  }

  async function batchReviewSelected(status: "已复核" | "自动通过" = "已复核") {
    if (!selectedIds.length) {
      setError("请先勾选要复核的记录");
      return;
    }
    if (!window.confirm(`确认将选中的 ${selectedIds.length} 条标记为「${status}」？（保留原风险等级）`)) return;
    try {
      const res = await fetch("/api/records/batch-review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ids: selectedIds,
          status,
          review_note: status === "已复核" ? "批量复核通过" : "批量标记自动通过",
          keep_risk: true
        })
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res, "批量复核失败"));
      const body = (await res.json()) as { updated_count: number };
      setInfo(`已批量复核 ${body.updated_count} 条`);
      setError("");
      if (active && selectedIds.includes(active.id)) {
        await openRecord(active.id);
      }
      await refreshAll(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量复核失败");
    }
  }

  function navigateRecord(delta: number) {
    if (!records.length) return;
    const currentIdx = active ? records.findIndex((r) => r.id === active.id) : -1;
    let nextIdx: number;
    if (currentIdx < 0) {
      nextIdx = delta > 0 ? 0 : records.length - 1;
    } else {
      nextIdx = currentIdx + delta;
      if (nextIdx < 0 || nextIdx >= records.length) return;
    }
    const next = records[nextIdx];
    if (next) void selectRecord(next.id);
  }

  const activeIndex = active ? records.findIndex((r) => r.id === active.id) : -1;
  const canPrev = activeIndex > 0;
  const canNext = activeIndex >= 0 && activeIndex < records.length - 1;

  async function redetectActive() {
    if (!active) return;
    setRedetecting(true);
    setError("");
    try {
      const res = await fetch(`/api/records/${active.id}/redetect`, { method: "POST" });
      if (!res.ok) throw new Error(await apiErrorMessage(res, "重新检测失败"));
      const data: RecordDetail = await res.json();
      setActive(data);
      setReviewNote(data.review_note || "");
      setReviewRisk(data.risk_level);
      setInfo(`已用当前参数重新检测 #${data.id}`);
      await refreshAll(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新检测失败");
    } finally {
      setRedetecting(false);
    }
  }

  async function runCompare() {
    if (compareLeftId == null || compareRightId == null) {
      setError("请先选择左右两条记录进行对比");
      return;
    }
    if (compareLeftId === compareRightId) {
      setError("对比需要两条不同的记录");
      return;
    }
    setComparing(true);
    setError("");
    try {
      const res = await fetch(`/api/compare?left_id=${compareLeftId}&right_id=${compareRightId}`);
      if (!res.ok) throw new Error(await apiErrorMessage(res, "对比失败"));
      const data = (await res.json()) as CompareResult;
      setCompareResult(data);
      setInfo(`已对比 #${compareLeftId} 与 #${compareRightId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "对比失败");
    } finally {
      setComparing(false);
    }
  }

  function pickForCompare(id: number, side: "left" | "right" | "auto" = "auto") {
    if (side === "left") {
      setCompareLeftId(id);
      return;
    }
    if (side === "right") {
      setCompareRightId(id);
      return;
    }
    if (compareLeftId == null || compareLeftId === id) {
      setCompareLeftId(id);
    } else if (compareRightId == null || compareRightId === id) {
      setCompareRightId(id);
    } else {
      setCompareLeftId(compareRightId);
      setCompareRightId(id);
    }
  }

  async function openRecord(id: number) {
    const res = await fetch(`/api/records/${id}`);
    if (!res.ok) throw new Error(await apiErrorMessage(res, "记录详情加载失败"));
    const data: RecordDetail = await res.json();
    setActive(data);
    setReviewNote(data.review_note || "");
    setReviewRisk(data.risk_level);
  }

  async function refreshAll(selectFirst = false) {
    try {
      await Promise.all([loadRecords(selectFirst), loadStats()]);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "历史记录加载失败");
    }
  }

  async function selectRecord(id: number) {
    try {
      await openRecord(id);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "记录详情加载失败");
    }
  }

  function openFilePicker() {
    if (!canUpload) return;
    inputRef.current?.click();
  }

  async function onFiles(fileList: FileList | File[] | null) {
    const files = fileList ? Array.from(fileList as ArrayLike<File>) : [];
    if (!files.length) {
      setDragging(false);
      return;
    }
    if (files.length > MAX_BATCH_FILES) {
      setDragging(false);
      setError(`单次最多上传 ${MAX_BATCH_FILES} 张图片，请分批处理。`);
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    const oversized = files.find((file) => file.size > MAX_UPLOAD_BYTES);
    if (oversized) {
      setDragging(false);
      setError(`文件 ${oversized.name} 超过 8MB，请压缩后再试。`);
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    setUploading(true);
    setError("");
    setInfo("");
    try {
      if (files.length === 1) {
        const single = files[0]!;
        const form = new FormData();
        form.append("file", single);
        const res = await fetch("/api/detect", { method: "POST", body: form });
        if (!res.ok) throw new Error(await apiErrorMessage(res, "检测失败"));
        const data: RecordDetail = await res.json();
        setActive(data);
        setReviewNote(data.review_note || "");
        setReviewRisk(data.risk_level);
        setInfo(`已完成：${data.filename}`);
      } else {
        const form = new FormData();
        files.forEach((file) => form.append("files", file));
        const res = await fetch("/api/detect/batch", { method: "POST", body: form });
        if (!res.ok) throw new Error(await apiErrorMessage(res, "批量检测失败"));
        const body = (await res.json()) as {
          ok_count: number;
          error_count: number;
          records: RecordDetail[];
          errors: { filename: string; error: string }[];
        };
        if (body.records[0]) {
          setActive(body.records[0]);
          setReviewNote(body.records[0].review_note || "");
          setReviewRisk(body.records[0].risk_level);
        }
        const errHint = body.error_count
          ? `，失败 ${body.error_count} 张：${body.errors.map((e) => e.filename).join("、")}`
          : "";
        setInfo(`批量完成：成功 ${body.ok_count} 张${errHint}`);
        if (body.ok_count === 0 && body.error_count > 0) {
          setError(body.errors[0]?.error || "批量检测全部失败");
        }
      }
      await refreshAll(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "检测失败");
    } finally {
      setDragging(false);
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function onDropZoneDragOver(event: React.DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    if (!canUpload) return;
    event.dataTransfer.dropEffect = "copy";
    setDragging(true);
  }

  function onDropZoneDragLeave(event: React.DragEvent<HTMLButtonElement>) {
    const nextTarget = event.relatedTarget;
    if (!(nextTarget instanceof Node) || !event.currentTarget.contains(nextTarget)) {
      setDragging(false);
    }
  }

  function onDropZoneDrop(event: React.DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setDragging(false);
    if (!canUpload) return;
    void onFiles(event.dataTransfer.files);
  }

  async function saveReview() {
    if (!active) return;
    const currentId = active.id;
    try {
      const res = await fetch(`/api/records/${active.id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "已复核", risk_level: reviewRisk, review_note: reviewNote })
      });
      if (!res.ok) {
        setError(await apiErrorMessage(res, "复核保存失败"));
        return;
      }
      const data: RecordDetail = await res.json();
      setActive(data);
      setError("");
      setInfo("复核已保存");
      await refreshAll(false);
      if (autoNextOnReview) {
        const idx = records.findIndex((r) => r.id === currentId);
        const next = idx >= 0 ? records[idx + 1] : undefined;
        if (next) {
          await selectRecord(next.id);
          setInfo(`复核已保存，已跳转下一条 #${next.id}`);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "复核保存失败");
    }
  }

  async function batchRedetectSelected() {
    if (!selectedIds.length) {
      setError("请先勾选要重检的记录");
      return;
    }
    if (!window.confirm(`确认用当前参数批量重检 ${selectedIds.length} 条？`)) return;
    setBatchRedetecting(true);
    try {
      const res = await fetch("/api/records/batch-redetect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: selectedIds })
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res, "批量重检失败"));
      const body = (await res.json()) as { ok_count: number; error_count: number };
      setInfo(`批量重检完成：成功 ${body.ok_count}，失败 ${body.error_count}`);
      setError("");
      if (active && selectedIds.includes(active.id)) await openRecord(active.id);
      await refreshAll(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量重检失败");
    } finally {
      setBatchRedetecting(false);
    }
  }

  function quickFilterPending() {
    setFilterReview("待复核");
    setFilterRisk("全部");
    setPage(1);
    setInfo("已切换到待复核队列");
  }

  function quickFilterHigh() {
    setFilterRisk("高");
    setFilterReview("全部");
    setPage(1);
    setInfo("已筛选高风险记录");
  }

  async function deleteActive() {
    if (!active) return;
    if (!window.confirm(`确认删除记录 #${active.id}（${active.filename}）？`)) return;
    try {
      const res = await fetch(`/api/records/${active.id}`, { method: "DELETE" });
      if (!res.ok) {
        setError(await apiErrorMessage(res, "删除失败"));
        return;
      }
      setActive(null);
      setInfo("已删除记录");
      await refreshAll(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  async function checkBackend() {
    try {
      const res = await fetch("/api/health");
      if (!res.ok) {
        setBackendOnline("offline");
        return;
      }
      setBackendOnline("online");
      const body = (await res.json()) as {
        version?: string;
        detector?: { label?: string; active?: string; note?: string };
      };
      if (body.version) setAppVersion(body.version);
      if (body.detector?.label) {
        setDetectorLabel(body.detector.label);
      } else if (body.detector?.active === "yolo") {
        setDetectorLabel("YOLO 深度模型");
      } else {
        setDetectorLabel("OpenCV 规则初筛");
      }
    } catch {
      setBackendOnline("offline");
    }
  }

  useEffect(() => {
    refreshAll(true).catch(() => setError("历史记录加载失败"));
    checkBackend();
    loadSettings().catch(() => undefined);
    const timer = window.setInterval(() => {
      void checkBackend();
    }, 15000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    loadRecords(false).catch(() => setError("筛选记录失败"));
  }, [filterRisk, filterReview, filterQuery, page, sortBy, sortOrder]);

  useEffect(() => {
    setPage(1);
  }, [filterRisk, filterReview, filterQuery, sortBy, sortOrder]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select" || target?.isContentEditable) return;

      if (event.key === "Escape") {
        if (lightbox) {
          setLightbox(null);
          return;
        }
        if (showSettings) {
          setShowSettings(false);
          return;
        }
      }
      if ((event.key === "u" || event.key === "U") && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        openFilePicker();
      }
      if ((event.key === "r" || event.key === "R") && !event.ctrlKey && !event.metaKey && active && !redetecting) {
        event.preventDefault();
        void redetectActive();
      }
      if ((event.key === "s" || event.key === "S") && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        setShowSettings((v) => !v);
      }
      if (event.key === "ArrowDown" || event.key === "j" || event.key === "J") {
        event.preventDefault();
        navigateRecord(1);
      }
      if (event.key === "ArrowUp" || event.key === "k" || event.key === "K") {
        event.preventDefault();
        navigateRecord(-1);
      }
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && records.length) {
        event.preventDefault();
        navigateRecord(event.key === "ArrowRight" ? 1 : -1);
      }
      if ((event.key === "Enter" || event.key === "e" || event.key === "E") && active && !event.ctrlKey) {
        // quick save review with current form values
        if (event.key === "e" || event.key === "E") {
          event.preventDefault();
          void saveReview();
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [active, lightbox, showSettings, redetecting, canUpload, records, reviewRisk, reviewNote]);

  return (
    <main className={`app ${darkMode ? "theme-dark" : ""}`}>
      <aside className="side-rail" aria-label="主导航">
        <div className="mark">Z</div>
        <button
          aria-label="上传检测"
          title="上传检测 (U)"
          onClick={openFilePicker}
          disabled={!canUpload}
        >
          <Upload size={20} />
        </button>
        <button aria-label="待复核队列" title="待复核队列" onClick={quickFilterPending}>
          <History size={20} />
        </button>
        <button aria-label="统计面板" title="统计面板" onClick={() => setShowStatsPanel((v) => !v)}>
          <Activity size={20} />
        </button>
        <button
          aria-label={darkMode ? "浅色模式" : "暗色模式"}
          title={darkMode ? "浅色模式" : "暗色模式"}
          onClick={() => setDarkMode((v) => !v)}
        >
          {darkMode ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <div className="rail-spacer" />
        <button aria-label="参数" title="参数 (S)" onClick={() => setShowSettings((v) => !v)}>
          <Settings2 size={20} />
        </button>
      </aside>

      <section className="console-shell">
        <header className="console-top">
          <div className="brand-block">
            <p className="eyebrow">OpenClaw-compatible inspection workflow</p>
            <h1>智爪识损</h1>
            <span>基础设施病害 AI 辅助筛查控制台</span>
          </div>
          <div className="system-strip" aria-label="系统状态">
            <span className={`status-pill ${backendOnline === "online" ? "online" : backendOnline === "offline" ? "offline" : ""}`}>
              {backendOnline === "online" ? <CheckCircle2 size={15} /> : <Activity size={15} />}
              {backendOnline === "online" ? "后端在线" : backendOnline === "offline" ? "后端离线" : "后端检测中"}
            </span>
            <span className="status-pill"><Workflow size={15} />6-Agent协同</span>
            <span className="status-pill"><Archive size={15} />v2 工作台</span>
            <span className="status-pill" title={detectorLabel}>
              <Microscope size={15} />
              {detectorLabel.length > 16 ? `${detectorLabel.slice(0, 16)}…` : detectorLabel}
            </span>
            {appVersion && <span className="status-pill">v{appVersion}</span>}
          </div>
          <div className="top-actions">
            <button className="ghost" onClick={() => refreshAll(false)}>
              <RefreshCw size={17} />刷新
            </button>
            <button className="ghost" onClick={quickFilterPending} title="一键待复核">
              <ShieldAlert size={17} />待复核
            </button>
            <button className="ghost" onClick={quickFilterHigh} title="一键高风险">
              <AlertTriangle size={17} />高风险
            </button>
            <button className="ghost" onClick={() => setShowStatsPanel((v) => !v)} title="统计">
              <Activity size={17} />统计
            </button>
            <button className="ghost" onClick={() => setShowSettings((v) => !v)} title="运行参数">
              <Settings2 size={17} />参数
            </button>
            <button className="ghost" onClick={() => setDarkMode((v) => !v)} title="主题切换">
              {darkMode ? <Sun size={17} /> : <Moon size={17} />}
            </button>
            <button className="primary" onClick={openFilePicker} disabled={!canUpload}>
              {uploading ? <Loader2 className="spin" size={18} /> : <Upload size={18} />}
              上传/批量
            </button>
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              multiple
              disabled={!canUpload}
              onChange={(event) => onFiles(event.target.files)}
            />
          </div>
        </header>

        {error && <div className="notice">{error}</div>}
        {info && !error && <div className="notice info">{info}</div>}

        {showStatsPanel && serverStats && (
          <section className="stats-panel" aria-label="统计面板">
            <div className="section-title">
              <Activity size={18} />
              <h2>运行统计</h2>
              <span className="section-meta">风险 / 复核 / 类型 / 时间线</span>
              <button type="button" className="linkish" onClick={() => setShowStatsPanel(false)}>收起</button>
            </div>
            <div className="stats-bars">
              <div className="stat-block">
                <strong>风险分布</strong>
                <BarRow label="高" value={serverStats.high_risk} max={Math.max(1, serverStats.total)} tone="red" />
                <BarRow label="中" value={serverStats.medium_risk} max={Math.max(1, serverStats.total)} tone="amber" />
                <BarRow label="低" value={serverStats.low_risk} max={Math.max(1, serverStats.total)} tone="teal" />
              </div>
              <div className="stat-block">
                <strong>复核状态</strong>
                <BarRow label="待复核" value={serverStats.pending_review} max={Math.max(1, serverStats.total)} tone="amber" />
                <BarRow label="已复核" value={serverStats.reviewed} max={Math.max(1, serverStats.total)} tone="blue" />
                <BarRow label="自动通过" value={serverStats.auto_pass} max={Math.max(1, serverStats.total)} tone="teal" />
              </div>
              <div className="stat-block">
                <strong>病害类型累计</strong>
                <BarRow label="裂缝" value={serverStats.by_kind?.crack || 0} max={Math.max(1, serverStats.total_detections || 1)} tone="red" />
                <BarRow label="剥落" value={serverStats.by_kind?.spalling || 0} max={Math.max(1, serverStats.total_detections || 1)} tone="amber" />
                <BarRow label="渗水" value={serverStats.by_kind?.stain || 0} max={Math.max(1, serverStats.total_detections || 1)} tone="blue" />
              </div>
              <div className="stat-block">
                <strong>近 14 日检测量</strong>
                <div className="timeline-bars">
                  {(serverStats.timeline || []).map((item) => {
                    const maxC = Math.max(1, ...(serverStats.timeline || []).map((t) => t.count));
                    return (
                      <div key={item.day} className="tl-col" title={`${item.day}: ${item.count}`}>
                        <i style={{ height: `${Math.max(8, Math.round((item.count / maxC) * 64))}px` }} />
                        <em>{item.day.slice(5)}</em>
                      </div>
                    );
                  })}
                  {!(serverStats.timeline || []).length && <small className="muted">暂无时间线数据</small>}
                </div>
              </div>
            </div>
          </section>
        )}

        {showSettings && (
          <section className="settings-panel" aria-label="运行参数">
            <div className="section-title">
              <Settings2 size={18} />
              <h2>运行参数</h2>
              <span className="section-meta">保存后落盘 · 重检/新上传立即生效 · 快捷键 S</span>
            </div>
            <div className="settings-grid">
              {settingsSchema.map((item) => (
                <label key={item.key} className="setting-item">
                  <span>{item.label}</span>
                  <div className="setting-controls">
                    <input
                      type="range"
                      min={item.min}
                      max={item.max}
                      step={item.step}
                      value={settings[item.key] ?? item.min}
                      onChange={(e) => {
                        const raw = Number(e.target.value);
                        const next = item.type === "int" ? Math.round(raw) : raw;
                        setSettings((prev) => ({ ...prev, [item.key]: next }));
                        setSettingsDirty(true);
                      }}
                    />
                    <input
                      type="number"
                      min={item.min}
                      max={item.max}
                      step={item.step}
                      value={settings[item.key] ?? ""}
                      onChange={(e) => {
                        const raw = Number(e.target.value);
                        if (!Number.isFinite(raw)) return;
                        const next = item.type === "int" ? Math.round(raw) : raw;
                        setSettings((prev) => ({ ...prev, [item.key]: next }));
                        setSettingsDirty(true);
                      }}
                    />
                  </div>
                </label>
              ))}
            </div>
            <div className="settings-actions">
              <button className="primary" onClick={() => void saveSettings()} disabled={savingSettings || !settingsDirty}>
                {savingSettings ? <Loader2 className="spin" size={16} /> : <CheckCircle2 size={16} />}
                保存参数
              </button>
              <button className="ghost" onClick={() => void resetSettings()} disabled={savingSettings}>
                恢复默认
              </button>
              <label className="toggle-inline">
                <input
                  type="checkbox"
                  checked={autoNextOnReview}
                  onChange={(e) => setAutoNextOnReview(e.target.checked)}
                />
                复核后自动下一条
              </label>
              <button className="ghost" onClick={() => setShowSettings(false)}>收起</button>
            </div>
          </section>
        )}

        <section className="overview-grid">
          <button className="upload-banner" onClick={openFilePicker} disabled={!canUpload}>
            <span>
              <strong>{uploading ? "正在执行AI诊断" : "上传巡检图片开始诊断"}</strong>
              <small>
                {backendOnline === "offline"
                  ? "后端当前离线，请先启动服务再上传巡检图片"
                  : uploading
                    ? "支持单张或批量（最多12张），6个Agent依次完成质检、识别、量化、评估、复核路由和报告归档"
                    : "支持单张/批量上传，筛选导出 CSV/PDF，双记录对比，可调识别阈值"}
              </small>
            </span>
            <i>{uploading ? <Loader2 className="spin" size={22} /> : <Upload size={22} />}</i>
          </button>
          <Metric icon={<Archive size={20} />} label="检测记录" value={stats.total.toString()} />
          <Metric icon={<ShieldAlert size={20} />} label="待复核" value={stats.pending.toString()} tone="amber" />
          <Metric icon={<Activity size={20} />} label="高风险" value={stats.high.toString()} tone="red" />
          <Metric icon={<Microscope size={20} />} label="平均置信度" value={`${Math.round(stats.avg * 100)}%`} />
        </section>

        <section className="workbench">
          <aside className="task-panel">
            <div className="section-title">
              <History size={18} />
              <h2>巡检任务队列</h2>
            </div>
            <div className="filter-bar">
              <label>
                <span>风险</span>
                <select value={filterRisk} onChange={(e) => setFilterRisk(e.target.value as "全部" | RiskLevel)}>
                  <option value="全部">全部</option>
                  {riskOptions.map((risk) => (
                    <option key={risk} value={risk}>{risk}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>复核</span>
                <select value={filterReview} onChange={(e) => setFilterReview(e.target.value as (typeof reviewFilterOptions)[number])}>
                  {reviewFilterOptions.map((status) => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </label>
              <label className="filter-query">
                <span>文件名</span>
                <input
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  placeholder="关键词筛选"
                />
              </label>
              <label>
                <span>排序</span>
                <select
                  value={`${sortBy}:${sortOrder}`}
                  onChange={(e) => {
                    const [s, o] = e.target.value.split(":") as [typeof sortBy, typeof sortOrder];
                    setSortBy(s);
                    setSortOrder(o);
                  }}
                >
                  <option value="id:desc">最新优先</option>
                  <option value="id:asc">最旧优先</option>
                  <option value="confidence:desc">置信度高→低</option>
                  <option value="confidence:asc">置信度低→高</option>
                  <option value="detection_count:desc">候选多→少</option>
                  <option value="filename:asc">文件名 A→Z</option>
                </select>
              </label>
            </div>
            <div className="export-bar">
              <button className="ghost compact" onClick={() => exportWithCurrentFilter("csv", selectedIds.length > 0)} title={selectedIds.length ? "导出选中 CSV" : "按当前筛选导出 CSV"}>
                <FileDown size={15} />CSV{selectedIds.length ? `(${selectedIds.length})` : ""}
              </button>
              <button className="ghost compact" onClick={() => exportWithCurrentFilter("pdf-zip", selectedIds.length > 0)} title={selectedIds.length ? "打包选中 PDF" : "按当前筛选打包 PDF"}>
                <Download size={15} />PDF{selectedIds.length ? `(${selectedIds.length})` : ""}
              </button>
              <button
                className="ghost compact"
                onClick={() => void runCompare()}
                disabled={comparing || compareLeftId == null || compareRightId == null}
                title="对比已选左右记录"
              >
                {comparing ? <Loader2 className="spin" size={15} /> : <Columns2 size={15} />}
                对比
              </button>
              <button className="ghost compact" onClick={() => void batchReviewSelected("已复核")} disabled={!selectedIds.length} title="批量标记已复核">
                <CheckCircle2 size={15} />复核
              </button>
              <button className="ghost compact" onClick={() => void batchRedetectSelected()} disabled={!selectedIds.length || batchRedetecting} title="批量重检">
                {batchRedetecting ? <Loader2 className="spin" size={15} /> : <RotateCcw size={15} />}
                重检
              </button>
              <button className="ghost compact danger" onClick={() => void batchDeleteSelected()} disabled={!selectedIds.length} title="批量删除选中">
                <Trash2 size={15} />删
              </button>
            </div>
            {records.length > 0 && (
              <div className="thumb-strip" aria-label="记录缩略图">
                {records.slice(0, 24).map((record) => (
                  <button
                    key={`thumb-${record.id}`}
                    type="button"
                    className={`thumb-item ${active?.id === record.id ? "active" : ""} risk-border-${record.risk_level}`}
                    onClick={() => selectRecord(record.id)}
                    title={`#${record.id} ${record.filename}`}
                  >
                    <img src={assetUrl(record.annotated_url)} alt="" loading="lazy" />
                    <span>{record.risk_level}</span>
                  </button>
                ))}
              </div>
            )}
            <div className="compare-pick">
              <label className="select-all">
                <input type="checkbox" checked={allVisibleSelected} onChange={toggleSelectAllVisible} />
                全选
              </label>
              <span>已选 {selectedIds.length}</span>
              <span>左 #{compareLeftId ?? "—"}</span>
              <span>右 #{compareRightId ?? "—"}</span>
              <button
                type="button"
                className="linkish"
                onClick={() => {
                  setCompareLeftId(null);
                  setCompareRightId(null);
                  setCompareResult(null);
                  setSelectedIds([]);
                }}
              >
                清空
              </button>
            </div>
            <div className="record-list" ref={listRef}>
              {records.map((record) => (
                <div
                  key={record.id}
                  className={`record-row ${active?.id === record.id ? "active" : ""} ${compareLeftId === record.id ? "cmp-left" : ""} ${compareRightId === record.id ? "cmp-right" : ""} ${selectedSet.has(record.id) ? "selected" : ""}`}
                >
                  <label className="record-check" title="多选">
                    <input
                      type="checkbox"
                      checked={selectedSet.has(record.id)}
                      onChange={() => toggleSelect(record.id)}
                    />
                  </label>
                  <button type="button" className="record-main" onClick={() => selectRecord(record.id)}>
                    <span className={`risk-chip risk-${record.risk_level}`}>{record.risk_level}</span>
                    <span className="record-copy">
                      <strong>{record.filename}</strong>
                      <small>{record.created_at}</small>
                    </span>
                    <span className="record-meta">
                      <em>{record.detection_count} 候选</em>
                      <em>裂{record.crack_count ?? 0}/剥{record.spalling_count ?? 0}/渗{record.stain_count ?? 0}</em>
                      <em>{Math.round(record.confidence * 100)}%</em>
                      <em>{record.review_status}</em>
                    </span>
                  </button>
                  <div className="record-pick">
                    <button type="button" className={compareLeftId === record.id ? "picked" : ""} onClick={() => pickForCompare(record.id, "left")} title="设为对比左侧">
                      L
                    </button>
                    <button type="button" className={compareRightId === record.id ? "picked" : ""} onClick={() => pickForCompare(record.id, "right")} title="设为对比右侧">
                      R
                    </button>
                  </div>
                </div>
              ))}
              {!records.length && <div className="empty compact">暂无匹配记录</div>}
            </div>
            <div className="pager">
              <button type="button" className="ghost compact" disabled={!pageMeta.has_prev || page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
                上一页
              </button>
              <span>
                {page} / {pageMeta.pages} · 共 {pageMeta.total}
              </span>
              <button type="button" className="ghost compact" disabled={!pageMeta.has_next} onClick={() => setPage((p) => p + 1)}>
                下一页
              </button>
            </div>
            {compareResult && (
              <ComparePanel
                result={compareResult}
                onClose={() => setCompareResult(null)}
              />
            )}
          </aside>

          <section className="diagnosis-panel">
            {!active ? (
              <button
                type="button"
                className={dropZoneClass}
                onClick={openFilePicker}
                onDragOver={onDropZoneDragOver}
                onDragLeave={onDropZoneDragLeave}
                onDrop={onDropZoneDrop}
                disabled={!canUpload}
              >
                <FileImage size={42} />
                <h2>上传巡检图片（支持批量）</h2>
                <p>系统将自动完成图像质量检查、病害候选识别、风险判断、人工复核入口和报告生成。可一次拖入多张图片。</p>
              </button>
            ) : (
              <ResultView
                active={active}
                reviewRisk={reviewRisk}
                setReviewRisk={setReviewRisk}
                reviewNote={reviewNote}
                setReviewNote={setReviewNote}
                saveReview={saveReview}
                deleteRecord={deleteActive}
                redetect={redetectActive}
                redetecting={redetecting}
                openLightbox={(src, title) => setLightbox({ src, title })}
                onPrev={() => navigateRecord(-1)}
                onNext={() => navigateRecord(1)}
                canPrev={canPrev}
                canNext={canNext}
                positionLabel={activeIndex >= 0 ? `${activeIndex + 1} / ${records.length}` : ""}
              />
            )}
          </section>
        </section>
      </section>
      {lightbox && (
        <div className="lightbox" role="dialog" aria-modal="true" onClick={() => setLightbox(null)}>
          <button type="button" className="lightbox-close" aria-label="关闭" onClick={() => setLightbox(null)}>
            <X size={20} />
          </button>
          <figure onClick={(e) => e.stopPropagation()}>
            <figcaption>{lightbox.title}</figcaption>
            <img src={lightbox.src} alt={lightbox.title} />
          </figure>
        </div>
      )}
    </main>
  );
}

function Metric({ icon, label, value, tone = "blue" }: { icon: React.ReactNode; label: string; value: string; tone?: "blue" | "amber" | "red" }) {
  return (
    <div className={`metric metric-${tone}`}>
      <div>{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function BarRow({
  label,
  value,
  max,
  tone = "blue"
}: {
  label: string;
  value: number;
  max: number;
  tone?: "blue" | "amber" | "red" | "teal";
}) {
  const pct = Math.min(100, Math.round((value / Math.max(1, max)) * 100));
  return (
    <div className={`bar-row tone-${tone}`}>
      <span>{label}</span>
      <div className="bar-track" aria-hidden>
        <i style={{ width: `${pct}%` }} />
      </div>
      <em>{value}</em>
    </div>
  );
}

function ResultView({
  active,
  reviewRisk,
  setReviewRisk,
  reviewNote,
  setReviewNote,
  saveReview,
  deleteRecord,
  redetect,
  redetecting,
  openLightbox,
  onPrev,
  onNext,
  canPrev,
  canNext,
  positionLabel
}: {
  active: RecordDetail;
  reviewRisk: RiskLevel;
  setReviewRisk: (value: RiskLevel) => void;
  reviewNote: string;
  setReviewNote: (value: string) => void;
  saveReview: () => void;
  deleteRecord: () => void;
  redetect: () => void;
  redetecting: boolean;
  openLightbox: (src: string, title: string) => void;
  onPrev: () => void;
  onNext: () => void;
  canPrev: boolean;
  canNext: boolean;
  positionLabel: string;
}) {
  const strongest = active.detections.reduce((max, d) => Math.max(max, d.confidence), 0);
  const areaRatio = metricNumber(active.metrics, "total_area_ratio");
  const crackCount = metricNumber(active.metrics, "crack_count");
  const spallingCount = metricNumber(active.metrics, "spalling_count");
  const stainCount = metricNumber(active.metrics, "stain_count");
  const avgConf = metricNumber(active.metrics, "avg_confidence", active.confidence);
  const readable = Boolean(active.quality.readable);
  const qualityMessage =
    typeof active.quality.message === "string" && active.quality.message
      ? active.quality.message
      : readable
        ? "图像满足基础识别条件"
        : "图像质量偏低，建议补拍或人工复核";
  const qualityGrade = typeof active.quality.quality_grade === "string" ? active.quality.quality_grade : "";
  const qualityScore =
    typeof active.quality.quality_score === "number" ? active.quality.quality_score : null;
  const detectorUsed =
    typeof active.quality.detector_label === "string" && active.quality.detector_label
      ? active.quality.detector_label
      : typeof active.quality.detector === "string"
        ? String(active.quality.detector)
        : "OpenCV 规则初筛";
  const displayWorkflow = getSixAgentWorkflow(active.workflow);
  const totalWorkflowMs = displayWorkflow.reduce((sum, step) => sum + step.duration_ms, 0);
  const typeCount = [crackCount, spallingCount, stainCount].filter((n) => n > 0).length;

  const sortedDetections = useMemo(
    () => [...active.detections].sort((a, b) => b.confidence - a.confidence),
    [active.detections]
  );

  return (
    <>
      <div className="nav-bar">
        <button type="button" className="ghost compact" onClick={onPrev} disabled={!canPrev} title="上一条（↑ / K）">
          <ChevronLeft size={16} />上一条
        </button>
        <span className="nav-pos">{positionLabel || `记录 #${active.id}`}</span>
        <button type="button" className="ghost compact" onClick={onNext} disabled={!canNext} title="下一条（↓ / J）">
          下一条<ChevronRight size={16} />
        </button>
      </div>
      <header className="result-hero">
        <div>
          <p className="eyebrow">Record #{active.id} · OpenClaw 本地工作流 · 快捷键 ↑↓/JK 切换 · E 保存复核</p>
          <h2>{active.filename}</h2>
          <p>{active.risk_reason}</p>
          <div className="hero-tags">
            <span className={`status-tag review-${active.review_status === "自动通过" ? "pass" : active.review_status === "已复核" ? "done" : "pending"}`}>
              {active.review_status}
            </span>
            <span className="status-tag muted">{active.created_at}</span>
            <span className="status-tag muted">工作流 {totalWorkflowMs}ms</span>
            <span className="status-tag muted" title={detectorUsed}>{detectorUsed}</span>
            {typeCount > 1 && <span className="status-tag multi">多类型病害</span>}
          </div>
        </div>
        <div className={`risk-score risk-${active.risk_level}`}>
          <span>{active.risk_level}</span>
          <small>风险等级</small>
        </div>
      </header>

      <section className="summary-bar">
        <SummaryItem label="候选区域" value={`${active.detection_count} 处`} />
        <SummaryItem label="最高置信度" value={`${Math.round(strongest * 100)}%`} />
        <SummaryItem label="平均置信度" value={`${Math.round(avgConf * 100)}%`} />
        <SummaryItem label="病害面积占比" value={`${(areaRatio * 100).toFixed(2)}%`} />
        <SummaryItem
          label="图像质量"
          value={
            qualityGrade
              ? `${qualityGrade}${qualityScore != null ? ` · ${qualityScore}` : ""}`
              : readable
                ? "可识别"
                : "需补拍"
          }
          hint={qualityMessage}
        />
      </section>

      <section className="damage-metrics" aria-label="病害类型统计">
        <DamageMetric kind="crack" count={crackCount} total={active.detection_count} />
        <DamageMetric kind="spalling" count={spallingCount} total={active.detection_count} />
        <DamageMetric kind="stain" count={stainCount} total={active.detection_count} />
        <div className="damage-metric damage-legend">
          <span className="damage-metric-label">标注图例</span>
          <div className="legend-row">
            <i className="kind-swatch kind-crack" />裂缝
            <i className="kind-swatch kind-spalling" />剥落
            <i className="kind-swatch kind-stain" />渗水/色差
          </div>
          <small>与标注图分色一致，便于答辩讲解</small>
        </div>
      </section>

      <section className="image-stage">
        <figure>
          <figcaption><FileImage size={16} />原始巡检图 · 点击放大</figcaption>
          <button
            type="button"
            className="img-zoom"
            onClick={() => openLightbox(assetUrl(active.original_url), `原图 · ${active.filename}`)}
          >
            <img src={assetUrl(active.original_url)} alt="原始巡检图" />
          </button>
        </figure>
        <figure>
          <figcaption>
            <AlertTriangle size={16} />AI标注结果 · 点击放大
            <span className="fig-legend">
              <i className="kind-swatch kind-crack" />裂
              <i className="kind-swatch kind-spalling" />剥
              <i className="kind-swatch kind-stain" />渗
            </span>
          </figcaption>
          <button
            type="button"
            className="img-zoom"
            onClick={() => openLightbox(assetUrl(active.annotated_url), `标注 · ${active.filename}`)}
          >
            <img src={assetUrl(active.annotated_url)} alt="AI标注结果" />
          </button>
        </figure>
      </section>

      <section className="agent-lane">
        <div className="section-title">
          <Workflow size={18} />
          <h3>6个OpenClaw Agent协同工作流</h3>
          <span className="section-meta">总耗时 {totalWorkflowMs}ms · {displayWorkflow.length} 步</span>
        </div>
        <div className="agent-role-strip">
          {agentRoles.map((role) => <span key={role}>{role}</span>)}
        </div>
        <div className="workflow-track">
          {displayWorkflow.map((step, index) => (
            <article className={`workflow-node status-${step.status}`} key={`${step.agent}-${index}`}>
              <div className="workflow-node-head">
                <span>{index + 1}</span>
                <em className={step.status === "completed" ? "ok" : ""}>{step.status === "completed" ? "完成" : step.status}</em>
              </div>
              <strong>{step.label}</strong>
              <small>{step.agent}</small>
              <small className="duration">{step.duration_ms} ms</small>
              <p>{step.summary}</p>
              {index < displayWorkflow.length - 1 && <ChevronRight className="node-arrow" size={17} />}
            </article>
          ))}
        </div>
      </section>

      <section className="detail-grid">
        <div className="table-panel">
          <div className="section-title">
            <GitBranch size={18} />
            <h3>病害候选明细</h3>
            <span className="section-meta">按置信度排序 · 共 {sortedDetections.length} 项</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>类型</th>
                <th>置信度</th>
                <th>面积占比</th>
                <th>长度(px)</th>
                <th>解释 / 坐标</th>
              </tr>
            </thead>
            <tbody>
              {sortedDetections.map((item, index) => {
                const meta = kindMeta(item.kind);
                return (
                  <tr key={`${item.kind}-${index}`} className={`det-row ${meta.className}`}>
                    <td>
                      <span className={`kind-badge ${meta.className}`}>
                        <i className={`kind-swatch ${meta.className}`} />
                        {item.label || meta.label}
                      </span>
                    </td>
                    <td>
                      <div className="conf-cell">
                        <strong>{Math.round(item.confidence * 100)}%</strong>
                        <span className="conf-bar" aria-hidden>
                          <span style={{ width: `${Math.min(100, Math.round(item.confidence * 100))}%` }} />
                        </span>
                      </div>
                    </td>
                    <td>{(item.area_ratio * 100).toFixed(2)}%</td>
                    <td>{Math.round(item.length_estimate)}</td>
                    <td>
                      <div className="explain-cell">
                        {item.explanation && <span>{item.explanation}</span>}
                        <code className="mono">{item.bbox.join(", ")}</code>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {!sortedDetections.length && (
                <tr>
                  <td colSpan={5}>未发现明显病害候选区域，可纳入常规巡检记录</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="review-panel">
          <div className="section-title">
            <CheckCircle2 size={18} />
            <h3>人工复核与报告</h3>
          </div>
          <div className="review-snapshot">
            <div>
              <span>系统建议风险</span>
              <strong className={`text-risk-${active.risk_level}`}>{active.risk_level}</strong>
            </div>
            <div>
              <span>当前复核状态</span>
              <strong>{active.review_status}</strong>
            </div>
            <div>
              <span>类型构成</span>
              <strong>
                裂{crackCount} · 剥{spallingCount} · 渗{stainCount}
              </strong>
            </div>
          </div>
          <div className="review-grid">
            <label>
              <span>复核风险</span>
              <select value={reviewRisk} onChange={(event) => setReviewRisk(event.target.value as RiskLevel)}>
                {riskOptions
                  .slice()
                  .sort((a, b) => riskRank[a] - riskRank[b])
                  .map((risk) => <option key={risk}>{risk}</option>)}
              </select>
            </label>
            <label className="note-field">
              <span>复核意见</span>
              <textarea value={reviewNote} onChange={(event) => setReviewNote(event.target.value)} placeholder="填写现场复核意见、处理建议或持续观察说明" />
            </label>
            <div className="review-actions">
              <button className="primary" onClick={saveReview}>
                <CheckCircle2 size={18} />保存复核
              </button>
              <button className="ghost" onClick={redetect} disabled={redetecting} title="用当前参数重新检测（快捷键 R）">
                {redetecting ? <Loader2 className="spin" size={18} /> : <RotateCcw size={18} />}
                重新检测
              </button>
              <a className="download" href={`/api/records/${active.id}/report`} target="_blank" rel="noreferrer">
                <Download size={18} />下载PDF报告
              </a>
              <button className="ghost danger" onClick={deleteRecord}>
                <Trash2 size={18} />删除记录
              </button>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

function DamageMetric({ kind, count, total }: { kind: "crack" | "spalling" | "stain"; count: number; total: number }) {
  const meta = kindMeta(kind);
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className={`damage-metric ${meta.className}`}>
      <div className="damage-metric-top">
        <i className={`kind-swatch ${meta.className}`} />
        <span className="damage-metric-label">{meta.label}</span>
      </div>
      <strong>{count}</strong>
      <small>{total > 0 ? `占候选 ${pct}%` : "无候选"}</small>
    </div>
  );
}

function SummaryItem({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="summary-item" title={hint}>
      <span>{label}</span>
      <strong>{value}</strong>
      {hint && <small className="summary-hint">{hint}</small>}
    </div>
  );
}

function ComparePanel({ result, onClose }: { result: CompareResult & { verdict?: string }; onClose: () => void }) {
  const leftArea = Number(result.left.metrics?.total_area_ratio || 0);
  const rightArea = Number(result.right.metrics?.total_area_ratio || 0);
  return (
    <div className="compare-panel">
      <div className="section-title">
        <Columns2 size={16} />
        <h3>记录对比</h3>
        <button type="button" className="linkish" onClick={onClose}>关闭</button>
      </div>
      {result.verdict && <p className="compare-verdict">{result.verdict}</p>}
      <div className="compare-cols">
        <article>
          <strong>#{result.left.id} {result.left.filename}</strong>
          <span className={`risk-chip risk-${result.left.risk_level}`}>{result.left.risk_level}</span>
          <small>候选 {result.left.detection_count} · 置信 {Math.round(result.left.confidence * 100)}% · 面积 {(leftArea * 100).toFixed(2)}%</small>
          <img src={assetUrl(result.left.annotated_url)} alt="左侧标注" />
        </article>
        <article>
          <strong>#{result.right.id} {result.right.filename}</strong>
          <span className={`risk-chip risk-${result.right.risk_level}`}>{result.right.risk_level}</span>
          <small>候选 {result.right.detection_count} · 置信 {Math.round(result.right.confidence * 100)}% · 面积 {(rightArea * 100).toFixed(2)}%</small>
          <img src={assetUrl(result.right.annotated_url)} alt="右侧标注" />
        </article>
      </div>
      <ul className="compare-notes">
        {result.notes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
      <div className="compare-delta">
        <span>置信Δ {(result.delta.confidence_delta * 100).toFixed(1)}%</span>
        <span>面积Δ {(result.delta.area_ratio_delta * 100).toFixed(2)}%</span>
        <span>候选Δ {result.delta.count_delta.total >= 0 ? "+" : ""}{result.delta.count_delta.total}</span>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
