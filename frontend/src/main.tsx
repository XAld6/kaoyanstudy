import React, { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Bot,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Copy,
  Download,
  Filter,
  Flame,
  Gauge,
  Import,
  LineChart,
  Pause,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Settings,
  Sparkles,
  Square,
  Timer,
  Trash2
} from "lucide-react";
import { ApiForm, Health, fetchConfig, requestAdvice, testConfig } from "./api";
import {
  AppData,
  PlanTaskFilters,
  Subject,
  StudyTask,
  WeeklyReport,
  addDays,
  addLightSubjectStudyBlock,
  appendWeeklyReportToReview,
  buildReviewTemplate,
  buildWeeklyReport,
  bumpTaskActualMinutes,
  copyWeekTasks,
  countOverdueTasks,
  createDefaultData,
  fillTaskActualMinutes,
  formatDate,
  StructuredAdvice,
  buildCoachAdvicePayload,
  generateStructuredRuleAdvice,
  generateWeeklyAdjustmentTips,
  parseStructuredAdvice,
  getDailyClosureChecklist,
  getDataHealth,
  getDataOverview,
  getPlanTasks,
  buildStudyHeatmap,
  getSubjectProgress,
  getSubjectWeeklyLoad,
  getTasksForDate,
  getTodayStats,
  getWeekOverview,
  patchTaskActualMinutes,
  prepareTomorrowPlan,
  relieveHeaviestDay,
  resolveOverdueTasksToDate,
  resolveSubjectIdByKeywords,
  rolloverUnfinishedTasks,
  runDailyClosure,
  shiftTasksByIds,
  updateTasksByIds,
  uid
} from "./studyCore";
import {
  BackupMeta,
  clearBackupMeta,
  createAppDataExport,
  formatBackupTimestamp,
  getBackupHealth,
  loadAppDataWithStatus,
  loadBackupMeta,
  loadFocusNotifyPrefs,
  loadFocusStatsStore,
  loadPomodoroMinutes,
  markBackupExported,
  parseImportedData,
  readLegacyFocusStats,
  readLegacyLocalData,
  restoreFocusTimerSession,
  saveAppData,
  saveFocusNotifyPrefs,
  saveFocusStatsStore,
  saveFocusTimerSession,
  savePomodoroMinutes
} from "./storage";
import {
  DEFAULT_BREAK_MINUTES,
  DEFAULT_DOCUMENT_TITLE,
  DEFAULT_POMODORO_MINUTES,
  FocusMode,
  FocusTimerState,
  POMODORO_DURATION_OPTIONS,
  buildFocusDocumentTitle,
  createIdleFocusTimer,
  discardFocusTimer,
  getFocusSnapshot,
  isFocusTimerActive,
  normalizePomodoroMinutes,
  pauseFocusTimer,
  resumeFocusTimer,
  setFocusMode,
  startBreakTimer,
  startFocusTimer,
  stopFocusTimer
} from "./focusTimer";
import {
  FocusNotifyPrefs,
  getNotificationPermissionState,
  notifyFocusComplete,
  playFocusCompleteSound,
  showFocusCompleteNotification
} from "./focusNotify";
import {
  FocusStatsStore,
  createEmptyFocusStatsStore,
  formatFocusStatsSummary,
  getDailyFocusStats,
  getFocusMinutesByDate,
  recordFocusSession as recordFocusSessionPure
} from "./focusStats";
import { daysLeft, minutesLabel } from "./format";
import { useSelectedDate } from "./hooks/useSelectedDate";
import { View, useView } from "./hooks/useView";
import { createStateSync, fetchState, importStateFile, pushState } from "./remoteStore";
import type { RemoteState, StateSync } from "./remoteStore";
import {
  ClosureChecklist,
  FocusStickyBar,
  HealthItem,
  Metric,
  OverviewItem,
  PlanTaskRow,
  StructuredAdviceBoard,
  StudyHeatmapBoard,
  TaskCreator,
  TaskRow,
  WeekPlanBoard,
  WeeklyAdjustmentPanel,
  WeeklyLoadStrip
} from "./uiComponents";
import "./styles.css";

const navItems: Array<{ view: View; label: string; icon: React.ReactNode }> = [
  { view: "today", label: "今日", icon: <CalendarDays size={18} /> },
  { view: "plan", label: "计划", icon: <ClipboardList size={18} /> },
  { view: "progress", label: "进度", icon: <LineChart size={18} /> },
  { view: "coach", label: "AI", icon: <Bot size={18} /> },
  { view: "settings", label: "设置", icon: <Settings size={18} /> }
];


type QuickTemplate = {
  key: string;
  label: string;
  title: string;
  estimatedMinutes: number;
  priority: StudyTask["priority"];
  subjectKeywords: string[];
  fallbackIndex: number;
};

const quickTemplates: QuickTemplate[] = [
  {
    key: "math-core",
    label: "数学·高数强化",
    title: "高数强化：极限与导数题组",
    estimatedMinutes: 90,
    priority: "高",
    subjectKeywords: ["数学", "高数", "数学一", "数学二", "数学三"],
    fallbackIndex: 0
  },
  {
    key: "english-read",
    label: "英语·阅读精读",
    title: "阅读精读：长难句拆解",
    estimatedMinutes: 60,
    priority: "中",
    subjectKeywords: ["英语", "英语一", "英语二", "阅读"],
    fallbackIndex: 1
  },
  {
    key: "politics-choice",
    label: "政治·选择题",
    title: "政治选择题：基础概念回顾",
    estimatedMinutes: 45,
    priority: "中",
    subjectKeywords: ["政治", "思政"],
    fallbackIndex: 2
  },
  {
    key: "major-review",
    label: "专业课·真题",
    title: "专业课真题：小题训练",
    estimatedMinutes: 100,
    priority: "高",
    subjectKeywords: ["专业课", "专业"],
    fallbackIndex: 3
  }
];


function App() {
  const [initialLoad] = useState(() => loadAppDataWithStatus());
  const [pomodoroMinutes, setPomodoroMinutes] = useState(() => loadPomodoroMinutes());
  const [focusRestore] = useState(() => restoreFocusTimerSession(Date.now(), DEFAULT_BREAK_MINUTES, loadPomodoroMinutes()));
  // 数据源在服务器；本地缓存只用于首屏与离线兜底，水合完成后会被服务器状态替换
  const [data, setData] = useState<AppData>(() => initialLoad.data);
  const [view, setView] = useView();
  const [selectedDate, setSelectedDate] = useSelectedDate();
  const [newTask, setNewTask] = useState({ title: "", subjectId: "", estimatedMinutes: 60, priority: "中" as StudyTask["priority"] });
  const [newSubject, setNewSubject] = useState({ name: "", color: "#6f82ff", weeklyTargetHours: 8 });
  const [progressDays, setProgressDays] = useState(7);
  const [heatmapWeeks, setHeatmapWeeks] = useState(12);
  const [planScope, setPlanScope] = useState<"week" | "all">("week");
  const [planFilters, setPlanFilters] = useState<Omit<PlanTaskFilters, "scope">>({ subjectId: "all", priority: "all", status: "all", query: "" });
  const [todayActionStatus, setTodayActionStatus] = useState("");
  const [planActionStatus, setPlanActionStatus] = useState("");
  const [settingsActionStatus, setSettingsActionStatus] = useState("");
  const [backupMeta, setBackupMeta] = useState<BackupMeta>(() => loadBackupMeta());
  const [backupBannerDismissed, setBackupBannerDismissed] = useState(false);
  const [overdueBannerDismissed, setOverdueBannerDismissed] = useState(false);
  const [aiAdvice, setAiAdvice] = useState<StructuredAdvice | null>(null);
  const [aiStatus, setAiStatus] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [apiForm, setApiForm] = useState<ApiForm>({ api_key: "", base_url: "https://api.openai.com/v1", model: "gpt-4.1-mini" });
  const [apiTestStatus, setApiTestStatus] = useState("");
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [isApiTesting, setIsApiTesting] = useState(false);
  const [storageWarning, setStorageWarning] = useState(initialLoad.recovered ? "检测到本地缓存数据异常，已回退到示例数据。若你有备份，可在设置页导入 JSON。" : "");
  // 服务端同步状态：loading=水合中 / ready=正常 / saving=保存中 / offline=离线只读 / conflict=多端冲突
  const [syncStatus, setSyncStatus] = useState<"loading" | "ready" | "saving" | "offline" | "conflict">("loading");
  const [syncMessage, setSyncMessage] = useState("");
  const [conflictState, setConflictState] = useState<RemoteState | null>(null);
  const [revision, setRevision] = useState(0);
  const [focusTimer, setFocusTimer] = useState<FocusTimerState>(() => {
    if (focusRestore.restored) return focusRestore.state;
    // 无会话时保留上次选择的番茄时长（模式仍为正计时，切换番茄即可用）
    return createIdleFocusTimer("stopwatch", loadPomodoroMinutes());
  });
  const [focusNow, setFocusNow] = useState(() => Date.now());
  const [focusStatusMessage, setFocusStatusMessage] = useState(() => focusRestore.message);
  const [focusNotifyPrefs, setFocusNotifyPrefs] = useState<FocusNotifyPrefs>(() => loadFocusNotifyPrefs());
  const [focusNotifyStatus, setFocusNotifyStatus] = useState("");
  // 专注统计的真实来源在服务器；水合后会用服务器数据替换这里的本地缓存值
  const [focusStatsStore, setFocusStatsStore] = useState<FocusStatsStore>(() => loadFocusStatsStore());
  const focusStats = useMemo(() => getDailyFocusStats(focusStatsStore, formatDate()), [focusStatsStore]);
  const [weeklyReport, setWeeklyReport] = useState<WeeklyReport | null>(null);
  const [weeklyReportStatus, setWeeklyReportStatus] = useState("");
  const focusTimerRef = useRef(focusTimer);
  const focusNotifyPrefsRef = useRef(focusNotifyPrefs);
  const pomodoroMinutesRef = useRef(pomodoroMinutes);
  const focusRestoreNotifiedRef = useRef(false);
  // 服务端同步 refs（供去抖任务读取最新值，避免闭包过期）
  const dataRef = useRef<AppData>(data);
  const focusStatsStoreRef = useRef<FocusStatsStore>(focusStatsStore);
  const revisionRef = useRef(0);
  const syncStatusRef = useRef<"loading" | "ready" | "saving" | "offline" | "conflict">("loading");
  const suppressNextSyncRef = useRef(false);
  const hydratedRef = useRef(false);
  const focusRestoreAppliedRef = useRef(false);
  const stateSyncRef = useRef<StateSync | null>(null);
  if (!stateSyncRef.current) stateSyncRef.current = createStateSync();
  const stateSync = stateSyncRef.current;
  const focusActionRefs = useRef({
    pauseOrResume: () => {},
    finish: () => {},
    cancel: () => {},
    skipBreak: () => {}
  });
  focusTimerRef.current = focusTimer;
  focusNotifyPrefsRef.current = focusNotifyPrefs;
  pomodoroMinutesRef.current = pomodoroMinutes;

  // 本地只读缓存：数据变化立即写入（离线兜底用；服务器才是唯一数据源）
  useEffect(() => {
    saveAppData(data);
  }, [data]);

  // P0-1：专注统计缓存跟随内存最新值 —— 水合后不写缓存会导致新设备
  // 「服务器 1000 分钟 → 缓存空 → 本地 +25 → 整包覆盖」的数据丢失
  useEffect(() => {
    saveFocusStatsStore(focusStatsStore);
  }, [focusStatsStore]);

  // ref 镜像（必须声明在去抖调度 effect 之前，保证调度执行时读到最新值）
  useEffect(() => {
    dataRef.current = data;
  }, [data]);
  useEffect(() => {
    focusStatsStoreRef.current = focusStatsStore;
  }, [focusStatsStore]);
  useEffect(() => {
    revisionRef.current = revision;
  }, [revision]);

  // 水合：以服务器为唯一数据源；失败则用本地缓存只读兜底
  useEffect(() => {
    let cancelled = false;
    (async () => {
      let nextData: AppData;
      let nextStats: FocusStatsStore = createEmptyFocusStatsStore();
      let nextRevision = 0;
      let needPush = false;
      try {
        const remote = await fetchState();
        if (cancelled) return;
        if (remote === null) {
          // 空库：用默认数据播种并立即推送（baseRevision 0）
          nextData = createDefaultData();
          nextRevision = 0;
          needPush = true;
        } else {
          nextData = remote.data;
          nextStats = remote.focusStats;
          nextRevision = remote.revision;
        }
      } catch {
        if (cancelled) return;
        const cached = loadAppDataWithStatus();
        nextData = cached.data;
        nextStats = loadFocusStatsStore();
        syncStatusRef.current = "offline";
        setSyncStatus("offline");
        setSyncMessage("无法连接服务器，当前显示本地缓存（只读）。恢复连接后会自动重试。");
      }

      // 刷新恢复的番茄：把离开期间完成的时长补到最新数据上（一次性）
      if (focusRestore.logTaskId && focusRestore.logMinutes > 0 && !focusRestoreAppliedRef.current) {
        focusRestoreAppliedRef.current = true;
        nextData = bumpTaskActualMinutes(structuredClone(nextData), focusRestore.logTaskId, focusRestore.logMinutes);
        nextStats = recordFocusSessionPure(nextStats, { minutes: focusRestore.logMinutes, isPomodoro: true, date: formatDate() });
        needPush = true;
      }

      if (cancelled) return;
      dataRef.current = nextData;
      focusStatsStoreRef.current = nextStats;
      revisionRef.current = nextRevision;
      setData(nextData);
      setFocusStatsStore(nextStats);
      setRevision(nextRevision);
      if (syncStatusRef.current !== "offline") {
        syncStatusRef.current = "ready";
        setSyncStatus("ready");
      }
      hydratedRef.current = true;
      // 水合后的数据与服务器一致（或已在上面显式推送），首个调度直接跳过，避免每次刷新都 bump revision
      if (!needPush) suppressNextSyncRef.current = true;
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // 去抖推送到服务器：任何数据变化 800ms 合并一次 PUT（水合完成前不推）
  useEffect(() => {
    if (!hydratedRef.current) return;
    stateSync.schedule(async () => {
      if (suppressNextSyncRef.current) {
        suppressNextSyncRef.current = false;
        return;
      }
      // P1-8：返回 Promise —— 同步队列必须真实等待网络请求，flush() 才会等它完成
      await syncNow();
    });
  }, [data, focusStatsStore]);

  // 页面隐藏时强制 flush，避免关标签页丢最后一次改动
  useEffect(() => {
    function flushOnHide() {
      void stateSync.flush();
    }
    document.addEventListener("visibilitychange", flushOnHide);
    window.addEventListener("pagehide", flushOnHide);
    return () => {
      document.removeEventListener("visibilitychange", flushOnHide);
      window.removeEventListener("pagehide", flushOnHide);
    };
  }, []);

  // 断线重连：online 事件 + 每 30s 重试一次
  useEffect(() => {
    const tryReconnect = () => {
      if (syncStatusRef.current === "offline") retryConnection();
    };
    window.addEventListener("online", tryReconnect);
    const intervalId = window.setInterval(tryReconnect, 30000);
    return () => {
      window.removeEventListener("online", tryReconnect);
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    saveFocusTimerSession(focusTimer);
  }, [focusTimer]);

  // 刷新恢复时：离开期间已完成的番茄/休息补一次提醒（只触发一次）
  useEffect(() => {
    if (focusRestoreNotifiedRef.current) return;
    if (!focusRestore.notify) return;
    focusRestoreNotifiedRef.current = true;
    void notifyFocusComplete(
      focusNotifyPrefsRef.current,
      focusRestore.notify.title,
      focusRestore.notify.minutes
    );
  }, [focusRestore.notify]);

  useEffect(() => {
    fetchConfig()
      .then((config) => {
        setHealth(config);
        setApiForm((current) => ({ ...current, base_url: config.base_url, model: config.model }));
      })
      .catch(() => setHealth({ status: "offline", llm_configured: false, model: "未连接", base_url: "本地后端未启动" }));
  }, []);

  useEffect(() => {
    if (focusTimer.status !== "running") return;
    const id = window.setInterval(() => {
      const now = Date.now();
      setFocusNow(now);
      const current = focusTimerRef.current;
      if (current.status !== "running") return;
      if (!getFocusSnapshot(current, now).isComplete) return;
      const preferred = pomodoroMinutesRef.current;

      // 休息倒计时结束
      if (current.phase === "break") {
        const idle = discardFocusTimer(current, preferred);
        focusTimerRef.current = idle;
        setFocusTimer(idle);
        setFocusStatusMessage(
          current.lastWorkTaskTitle
            ? `休息结束。可以继续「${current.lastWorkTaskTitle}」，或换一个任务开始下一轮。`
            : "休息结束，可以开始下一轮专注。"
        );
        void notifyFocusComplete(focusNotifyPrefsRef.current, "休息", 0);
        return;
      }

      // 番茄工作结束 → 记入时长 → 自动进入 5 分钟休息
      if (current.mode !== "pomodoro" || current.phase !== "work") return;
      const result = stopFocusTimer(current, now, preferred);
      // P0-1/P1-10：基于内存最新统计叠加；离线/加载中/冲突时拒绝写入（只读约束）
      const canRecord = syncStatusRef.current === "ready" || syncStatusRef.current === "saving";
      if (result.taskId && result.elapsedMinutes > 0 && canRecord) {
        setData((dataCurrent) => bumpTaskActualMinutes(structuredClone(dataCurrent), result.taskId!, result.elapsedMinutes));
        focusStatsStoreRef.current = recordFocusSessionPure(
          focusStatsStoreRef.current,
          { minutes: result.elapsedMinutes, isPomodoro: true, date: formatDate() }
        );
        setFocusStatsStore(focusStatsStoreRef.current);
      } else if (result.taskId && result.elapsedMinutes > 0) {
        setFocusStatusMessage("当前离线或同步未就绪：本次番茄时长未记入（避免覆盖服务器数据）。");
      }
      void notifyFocusComplete(
        focusNotifyPrefsRef.current,
        current.taskTitle || "当前任务",
        result.elapsedMinutes
      );

      if (result.shouldStartBreak) {
        const breakState = startBreakTimer(
          result.state,
          now,
          DEFAULT_BREAK_MINUTES,
          result.lastWorkTaskId,
          result.lastWorkTaskTitle
        );
        focusTimerRef.current = breakState;
        setFocusTimer(breakState);
        setFocusStatusMessage(
          result.elapsedMinutes > 0
            ? canRecord
              ? `番茄完成：已记入 ${result.elapsedMinutes} 分钟。已开始 ${DEFAULT_BREAK_MINUTES} 分钟休息。`
              : `番茄时间到，已开始 ${DEFAULT_BREAK_MINUTES} 分钟休息。当前离线或同步未就绪，本次时长未记入。`
            : `番茄时间到。已开始 ${DEFAULT_BREAK_MINUTES} 分钟休息。`
        );
      } else {
        focusTimerRef.current = result.state;
        setFocusTimer(result.state);
        setFocusStatusMessage("番茄时间到。");
      }
    }, 1000);
    return () => window.clearInterval(id);
  }, [focusTimer.status, focusTimer.phase]);

  const todayTasks = useMemo(() => getTasksForDate(data, selectedDate), [data, selectedDate]);
  const stats = useMemo(() => getTodayStats(data, selectedDate), [data, selectedDate]);
  const ruleAdvice = useMemo(() => generateStructuredRuleAdvice(data, selectedDate), [data, selectedDate]);
  const displayedAdvice = aiAdvice ?? ruleAdvice;
  const dailyClosureChecklist = useMemo(() => getDailyClosureChecklist(data, selectedDate), [data, selectedDate]);
  const progress = useMemo(() => getSubjectProgress(data, progressDays, selectedDate), [data, progressDays, selectedDate]);
  const weekOverview = useMemo(() => getWeekOverview(data, selectedDate), [data, selectedDate]);
  const weeklyLoad = useMemo(() => getSubjectWeeklyLoad(data, selectedDate), [data, selectedDate]);
  const studyHeatmap = useMemo(
    () => buildStudyHeatmap(data, selectedDate, heatmapWeeks, getFocusMinutesByDate(focusStatsStore)),
    [data, selectedDate, heatmapWeeks, focusStatsStore]
  );
  const weeklyAdjustmentTips = useMemo(() => generateWeeklyAdjustmentTips(data, selectedDate), [data, selectedDate]);
  const hasHeavyDayTip = weeklyAdjustmentTips.some((tip) => tip.id.startsWith("heavy-day-"));
  const hasLightSubjectTip = weeklyAdjustmentTips.some((tip) => tip.id.startsWith("light-"));
  const visiblePlanTasks = useMemo(() => getPlanTasks(data, selectedDate, { scope: planScope, ...planFilters }), [data, planFilters, planScope, selectedDate]);
  const dataOverview = useMemo(() => getDataOverview(data), [data]);
  const dataHealth = useMemo(() => getDataHealth(data, selectedDate), [data, selectedDate]);
  const overdueCount = useMemo(() => countOverdueTasks(data, selectedDate), [data, selectedDate]);
  const backupHealth = useMemo(() => getBackupHealth(backupMeta), [backupMeta]);
  const focusSnapshot = useMemo(() => getFocusSnapshot(focusTimer, focusNow), [focusTimer, focusNow]);
  const focusActive = isFocusTimerActive(focusTimer);
  const notificationPermission = getNotificationPermissionState();
  const showBackupBanner = backupHealth.needsAttention && !backupBannerDismissed;
  const showOverdueBanner = overdueCount > 0 && !overdueBannerDismissed;
  const closureReadyCount = dailyClosureChecklist.filter((item) => item.done).length;
  const hasActivePlanFilters = planFilters.subjectId !== "all" || planFilters.priority !== "all" || planFilters.status !== "all" || Boolean(planFilters.query?.trim());
  const reviewText = data.reviews.find((review) => review.date === selectedDate)?.text ?? "";
  const focusTask = focusTimer.taskId ? data.tasks.find((task) => task.id === focusTimer.taskId) : undefined;

  useEffect(() => {
    document.title = buildFocusDocumentTitle(focusSnapshot, DEFAULT_DOCUMENT_TITLE);
    return () => {
      document.title = DEFAULT_DOCUMENT_TITLE;
    };
  }, [focusSnapshot]);

  /** 同步未就绪（加载中/离线/冲突未决）时锁定所有编辑入口 */
  const editsLocked = syncStatus === "loading" || syncStatus === "offline" || syncStatus === "conflict";

  function updateData(updater: (current: AppData) => AppData) {
    if (editsLocked) {
      setSyncMessage(
        syncStatus === "loading"
          ? "正在从服务器加载数据，暂时不能编辑。"
          : syncStatus === "conflict"
            ? "请先解决数据冲突后再编辑。"
            : "当前离线模式，编辑已暂停；恢复连接后自动重试同步。"
      );
      return;
    }
    setData((current) => updater(structuredClone(current)));
  }

  /** 把当前内存快照推送到服务器（去抖任务的真正执行体） */
  async function syncNow(forceBaseRevision?: number, options?: { allowConflict?: boolean }) {
    const current = dataRef.current;
    if (!current) return;
    // P0-3：常规调度在冲突状态下不推；「用本机版本覆盖」显式放行（allowConflict）
    if (syncStatusRef.current === "conflict" && !options?.allowConflict) return;
    syncStatusRef.current = "saving";
    setSyncStatus("saving");
    setSyncMessage("");
    try {
      const result = await pushState({
        baseRevision: forceBaseRevision ?? revisionRef.current,
        data: current,
        focusStats: focusStatsStoreRef.current
      });
      if (result.ok) {
        revisionRef.current = result.revision;
        setRevision(result.revision);
        syncStatusRef.current = "ready";
        setSyncStatus("ready");
      } else {
        // 冲突：先自动下载本机版本（不丢数据），再让用户选择
        downloadExportFile(createAppDataExport(current, "before-import", undefined, focusStatsStoreRef.current));
        setConflictState(result.conflict);
        syncStatusRef.current = "conflict";
        setSyncStatus("conflict");
        setSyncMessage("检测到其他设备已更新服务器数据。已自动下载本机版本备份，请选择保留哪一份。");
      }
    } catch (error) {
      syncStatusRef.current = "offline";
      setSyncStatus("offline");
      setSyncMessage(error instanceof Error ? `保存到服务器失败：${error.message}` : "保存到服务器失败，已暂停编辑。");
    }
  }

  function retryConnection() {
    if (syncStatusRef.current !== "offline") return;
    setSyncMessage("正在重试连接...");
    void syncNow();
  }

  function loadServerVersion() {
    if (!conflictState) return;
    suppressNextSyncRef.current = true; // 服务器版本无需再推回去
    dataRef.current = conflictState.data;
    focusStatsStoreRef.current = conflictState.focusStats;
    revisionRef.current = conflictState.revision;
    setData(conflictState.data);
    setFocusStatsStore(conflictState.focusStats);
    setRevision(conflictState.revision);
    setConflictState(null);
    syncStatusRef.current = "ready";
    setSyncStatus("ready");
    setSyncMessage("");
  }

  function overwriteWithLocalVersion() {
    if (!conflictState) return;
    const base = conflictState.revision;
    setConflictState(null);
    // P0-3：必须显式放行，否则 syncNow 会在 conflict 状态下直接返回（按钮失效）
    void syncNow(base, { allowConflict: true });
  }

  function toggleTask(taskId: string) {
    updateData((current) => {
      current.tasks = current.tasks.map((task) =>
        task.id === taskId
          ? { ...task, status: task.status === "done" ? "todo" : "done", actualMinutes: task.status === "done" ? 0 : task.actualMinutes || task.estimatedMinutes }
          : task
      );
      return current;
    });
  }

  function updateTaskMinutes(taskId: string, actualMinutes: number) {
    updateData((current) => patchTaskActualMinutes(current, taskId, actualMinutes));
  }

  function bumpMinutes(taskId: string, delta: number) {
    updateData((current) => bumpTaskActualMinutes(current, taskId, delta));
  }

  function fillMinutes(taskId: string) {
    updateData((current) => fillTaskActualMinutes(current, taskId));
  }

  /** 记录一次专注会话（P0-1 / P1-10 统一入口）：
   * - 基于内存最新统计（ref）叠加，而不是浏览器旧缓存 —— 新设备不会把服务器历史覆盖成 25 分钟；
   * - 离线/加载中/冲突（editsLocked）时拒绝写入，保持「只读」约束，避免本地与服务器分叉。
   * 返回是否已记入。
   */
  function applyFocusSessionLog(minutes: number, isPomodoro: boolean): boolean {
    if (minutes <= 0) return false;
    if (editsLocked) {
      setFocusStatusMessage("当前离线或同步未就绪：本次专注时长未记入（避免覆盖服务器数据）。");
      return false;
    }
    const next = recordFocusSessionPure(focusStatsStoreRef.current, { minutes, isPomodoro, date: formatDate() });
    focusStatsStoreRef.current = next;
    setFocusStatsStore(next);
    return true;
  }

  function changeFocusMode(mode: FocusMode) {
    if (isFocusTimerActive(focusTimer)) {
      setFocusStatusMessage("计时进行中，请先结束或丢弃后再切换模式。");
      return;
    }
    setFocusTimer(setFocusMode(focusTimer, mode, pomodoroMinutes));
    setFocusStatusMessage(mode === "pomodoro" ? `已切换为番茄倒计时（${pomodoroMinutes} 分钟）。` : "已切换为正计时。");
  }

  function changePomodoroMinutes(minutes: number) {
    if (isFocusTimerActive(focusTimer)) {
      setFocusStatusMessage("计时进行中，请先结束或丢弃后再改番茄时长。");
      return;
    }
    const next = savePomodoroMinutes(minutes);
    setPomodoroMinutes(next);
    pomodoroMinutesRef.current = next;
    if (focusTimer.mode === "pomodoro" || focusTimer.phase === "break") {
      setFocusTimer(setFocusMode(focusTimer, "pomodoro", next));
    }
    setFocusStatusMessage(`番茄时长已设为 ${next} 分钟。`);
  }

  function beginFocusOnTask(task: StudyTask) {
    if (isFocusTimerActive(focusTimer) && focusTimer.phase === "work" && focusTimer.taskId && focusTimer.taskId !== task.id) {
      if (!window.confirm(`当前正在计时「${focusTimer.taskTitle}」。切换到「${task.title}」将丢弃当前未结算时长，是否继续？`)) {
        return;
      }
    }
    if (isFocusTimerActive(focusTimer) && focusTimer.phase === "break") {
      if (!window.confirm("当前在休息中。开始新任务将结束休息，是否继续？")) return;
    }
    const now = Date.now();
    setFocusNow(now);
    const nextMode = focusTimer.phase === "break" ? "pomodoro" : focusTimer.mode;
    setFocusTimer(startFocusTimer(focusTimer, task.id, task.title, now, pomodoroMinutes));
    setFocusStatusMessage(`已开始${nextMode === "pomodoro" || focusTimer.mode === "pomodoro" ? "番茄" : "正计时"}：${task.title}`);
  }

  function pauseOrResumeFocus() {
    const now = Date.now();
    setFocusNow(now);
    if (focusTimer.status === "running") {
      setFocusTimer(pauseFocusTimer(focusTimer, now));
      setFocusStatusMessage(focusTimer.phase === "break" ? "已暂停休息。" : "已暂停计时。");
      return;
    }
    if (focusTimer.status === "paused") {
      setFocusTimer(resumeFocusTimer(focusTimer, now));
      setFocusStatusMessage(focusTimer.phase === "break" ? "已继续休息。" : "已继续计时。");
    }
  }

  function finishFocusAndLog() {
    if (!isFocusTimerActive(focusTimer)) return;
    const now = Date.now();
    setFocusNow(now);

    if (focusTimer.phase === "break") {
      const idle = discardFocusTimer(focusTimer, pomodoroMinutes);
      setFocusTimer(idle);
      setFocusStatusMessage("已结束休息。");
      return;
    }

    const wasPomodoro = focusTimer.mode === "pomodoro";
    const result = stopFocusTimer(focusTimer, now, pomodoroMinutes);
    // P1-10：applyFocusSessionLog 返回是否真正记入（离线/同步未就绪时会被拒绝），
    // 后续消息必须尊重该结果，不得再显示「已记入」
    let logged = false;
    if (result.taskId && result.elapsedMinutes > 0) {
      updateData((current) => bumpTaskActualMinutes(current, result.taskId!, result.elapsedMinutes));
      logged = applyFocusSessionLog(result.elapsedMinutes, wasPomodoro);
    }

    if (result.shouldStartBreak && result.elapsedMinutes > 0) {
      const breakState = startBreakTimer(
        result.state,
        now,
        DEFAULT_BREAK_MINUTES,
        result.lastWorkTaskId,
        result.lastWorkTaskTitle
      );
      setFocusTimer(breakState);
      setFocusStatusMessage(
        logged
          ? `已记入 ${result.elapsedMinutes} 分钟，并开始 ${DEFAULT_BREAK_MINUTES} 分钟休息。`
          : `已开始 ${DEFAULT_BREAK_MINUTES} 分钟休息。当前离线或同步未就绪，本次时长未记入。`
      );
      return;
    }

    setFocusTimer(result.state);
    if (result.taskId && result.elapsedMinutes > 0 && logged) {
      setFocusStatusMessage(`已结束计时：给「${focusTimer.taskTitle || "当前任务"}」记入 ${result.elapsedMinutes} 分钟。`);
    } else {
      setFocusStatusMessage("计时已结束，本次不足 1 分钟，未记入时长。");
    }
  }

  function cancelFocusSession() {
    if (!isFocusTimerActive(focusTimer)) return;
    const message = focusTimer.phase === "break"
      ? "确定跳过休息吗？"
      : "确定丢弃当前计时进度吗？不会写入实际时长。";
    if (!window.confirm(message)) return;
    setFocusTimer(discardFocusTimer(focusTimer, pomodoroMinutes));
    setFocusStatusMessage(focusTimer.phase === "break" ? "已跳过休息。" : "已丢弃本次计时。");
  }

  function skipBreakSession() {
    if (focusTimer.phase !== "break") return;
    setFocusTimer(discardFocusTimer(focusTimer, pomodoroMinutes));
    setFocusStatusMessage("已跳过休息。");
  }

  focusActionRefs.current = {
    pauseOrResume: pauseOrResumeFocus,
    finish: finishFocusAndLog,
    cancel: cancelFocusSession,
    skipBreak: skipBreakSession
  };

  useEffect(() => {
    function isTypingTarget(target: EventTarget | null) {
      if (!(target instanceof HTMLElement)) return false;
      const tag = target.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
      if (target.isContentEditable) return true;
      return Boolean(target.closest("input, textarea, select, [contenteditable='true']"));
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return;
      if (isTypingTarget(event.target)) return;
      if (!isFocusTimerActive(focusTimerRef.current)) return;

      const key = event.key;
      if (key === " " || key === "Spacebar") {
        event.preventDefault();
        focusActionRefs.current.pauseOrResume();
        return;
      }
      if (key === "Enter") {
        event.preventDefault();
        focusActionRefs.current.finish();
        return;
      }
      if (key === "Escape") {
        event.preventDefault();
        if (focusTimerRef.current.phase === "break") {
          focusActionRefs.current.skipBreak();
        } else {
          focusActionRefs.current.cancel();
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function updateFocusNotifyPrefs(patch: Partial<FocusNotifyPrefs>) {
    const next = saveFocusNotifyPrefs({ ...focusNotifyPrefs, ...patch });
    setFocusNotifyPrefs(next);
    focusNotifyPrefsRef.current = next;
    setFocusNotifyStatus("专注提醒设置已保存到本机浏览器。");
  }

  async function requestNotificationPermissionFromSettings() {
    if (typeof Notification === "undefined") {
      setFocusNotifyStatus("当前浏览器不支持系统通知。");
      return;
    }
    try {
      const permission = await Notification.requestPermission();
      if (permission === "granted") {
        updateFocusNotifyPrefs({ notificationEnabled: true });
        setFocusNotifyStatus("已获得通知权限，番茄到点会弹出系统通知。");
      } else if (permission === "denied") {
        setFocusNotifyStatus("通知权限被拒绝。可在浏览器站点设置里重新允许。");
      } else {
        setFocusNotifyStatus("尚未授权通知，下次到点时仍可再请求。");
      }
    } catch {
      setFocusNotifyStatus("请求通知权限失败。");
    }
  }

  async function testFocusNotify() {
    const parts: string[] = [];
    if (focusNotifyPrefs.soundEnabled) {
      const played = await playFocusCompleteSound();
      parts.push(played ? "提示音已播放" : "提示音播放失败");
    } else {
      parts.push("提示音已关闭");
    }

    if (focusNotifyPrefs.notificationEnabled) {
      const result = await showFocusCompleteNotification("测试任务", 25, { enabled: true });
      if (result.shown) parts.push("系统通知已弹出");
      else if (result.reason === "denied") parts.push("通知权限被拒绝");
      else if (result.reason === "unsupported") parts.push("浏览器不支持通知");
      else if (result.reason === "default") parts.push("尚未授权通知");
      else parts.push("通知未弹出");
    } else {
      parts.push("系统通知已关闭");
    }
    setFocusNotifyStatus(parts.join(" · "));
  }

  function generateWeeklyReportForSelectedDate() {
    const report = buildWeeklyReport(data, selectedDate);
    setWeeklyReport(report);
    setWeeklyReportStatus(`已生成 ${report.weekStart} ~ ${report.weekEnd} 周报。`);
  }

  async function copyWeeklyReport() {
    if (!weeklyReport) {
      generateWeeklyReportForSelectedDate();
    }
    const report = weeklyReport ?? buildWeeklyReport(data, selectedDate);
    setWeeklyReport(report);
    try {
      await navigator.clipboard.writeText(report.markdown);
      setWeeklyReportStatus("周报已复制到剪贴板。");
    } catch {
      setWeeklyReportStatus("复制失败，请手动全选下方文本复制。");
    }
  }

  function downloadWeeklyReport() {
    const report = weeklyReport ?? buildWeeklyReport(data, selectedDate);
    setWeeklyReport(report);
    const blob = new Blob([report.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `kaoyan-weekly-report-${report.weekStart}.md`;
    link.click();
    URL.revokeObjectURL(url);
    setWeeklyReportStatus(`已下载周报：kaoyan-weekly-report-${report.weekStart}.md`);
  }

  function appendWeeklyReportToSelectedReview() {
    const result = appendWeeklyReportToReview(data, selectedDate, weeklyReport ?? undefined);
    setWeeklyReport(result.report);
    if (result.appended) {
      setData(result.data);
      setWeeklyReportStatus(`已把 ${result.report.weekStart} ~ ${result.report.weekEnd} 周报摘要写入 ${result.date} 的复盘。`);
    } else {
      setWeeklyReportStatus(`${result.date} 的复盘里已有该周周报摘要，未重复写入。`);
    }
  }

  function addTask() {
    if (!newTask.title.trim()) return;
    const subjectId = newTask.subjectId || data.subjects[0]?.id;
    if (!subjectId) return;
    updateData((current) => {
      current.tasks.unshift({
        id: uid("task"),
        subjectId,
        title: newTask.title.trim(),
        date: selectedDate,
        estimatedMinutes: Number(newTask.estimatedMinutes) || 60,
        actualMinutes: 0,
        priority: newTask.priority,
        status: "todo"
      });
      return current;
    });
    setNewTask({ title: "", subjectId, estimatedMinutes: 60, priority: "中" });
  }

  function addQuickTask(template: QuickTemplate) {
    const subjectId = resolveSubjectIdByKeywords(data, template.subjectKeywords, template.fallbackIndex);
    if (!subjectId) return;
    updateData((current) => {
      current.tasks.unshift({
        id: uid("task"),
        subjectId,
        title: template.title,
        date: selectedDate,
        estimatedMinutes: template.estimatedMinutes,
        actualMinutes: 0,
        priority: template.priority,
        status: "todo"
      });
      return current;
    });
    setView("today");
  }

  function deleteTask(taskId: string) {
    updateData((current) => {
      current.tasks = current.tasks.filter((task) => task.id !== taskId);
      return current;
    });
  }

  function updateTask(taskId: string, patch: Partial<StudyTask>) {
    updateData((current) => {
      current.tasks = current.tasks.map((task) => task.id === taskId ? { ...task, ...patch } : task);
      return current;
    });
  }

  function resetPlanFilters() {
    setPlanFilters({ subjectId: "all", priority: "all", status: "all", query: "" });
  }

  function rolloverSelectedDateTasks() {
    let message = "";
    updateData((current) => {
      const result = rolloverUnfinishedTasks(current, selectedDate);
      message = result.movedCount
        ? `已将 ${result.movedCount} 个未完成任务顺延到 ${result.targetDate}。`
        : `${selectedDate} 没有需要顺延的未完成任务。`;
      return result.data;
    });
    setPlanActionStatus(message);
  }

  function prepareSelectedTomorrowPlan() {
    if (!window.confirm("确定根据今天的未完成任务整理明日开局吗？未开始任务会顺延到明天，部分完成任务会生成续做任务。")) return;

    let movedCount = 0;
    let targetDate = "";
    let tomorrowTaskCount = 0;
    updateData((current) => {
      const result = prepareTomorrowPlan(current, selectedDate);
      movedCount = result.movedCount;
      targetDate = result.targetDate;
      tomorrowTaskCount = result.tomorrowTaskCount;
      return result.data;
    });
    setTodayActionStatus(
      movedCount
        ? `已整理 ${movedCount} 个未完成任务到 ${targetDate}，明天现在共有 ${tomorrowTaskCount} 个任务。`
        : `${selectedDate} 没有需要整理到明天的未完成任务。`
    );
  }

  function runSelectedDailyClosure() {
    if (!window.confirm("确定执行一键收尾吗？将补复盘草稿、补已完成任务的实际时长，并把未完成任务整理到明天。")) return;

    let reviewFilled = false;
    let filledActualCount = 0;
    let movedCount = 0;
    let targetDate = "";
    let tomorrowTaskCount = 0;
    let readyCount = 0;
    updateData((current) => {
      const result = runDailyClosure(current, selectedDate);
      reviewFilled = result.reviewFilled;
      filledActualCount = result.filledActualCount;
      movedCount = result.movedCount;
      targetDate = result.targetDate;
      tomorrowTaskCount = result.tomorrowTaskCount;
      readyCount = result.checklist.filter((item) => item.done).length;
      return result.data;
    });

    const parts = [
      reviewFilled ? "已写入复盘草稿" : "复盘已有内容",
      filledActualCount ? `补了 ${filledActualCount} 个完成任务时长` : "完成任务时长已齐",
      movedCount ? `顺延 ${movedCount} 项到 ${targetDate}` : "无需顺延",
      `明天 ${tomorrowTaskCount} 项`,
      `收尾 ${readyCount}/3`
    ];
    setTodayActionStatus(parts.join(" · "));
  }

  function shiftVisiblePlanTasks(dayDelta: number) {
    if (!visiblePlanTasks.length) {
      setPlanActionStatus("当前没有可批量调整的任务。");
      return;
    }
    const direction = dayDelta > 0 ? "推后一天" : "提前一天";
    if (!window.confirm(`确定将当前筛选可见的 ${visiblePlanTasks.length} 个任务${direction}吗？`)) return;

    let movedCount = 0;
    const taskIds = visiblePlanTasks.map((task) => task.id);
    updateData((current) => {
      const result = shiftTasksByIds(current, taskIds, dayDelta);
      movedCount = result.movedCount;
      return result.data;
    });
    setPlanActionStatus(`已将 ${movedCount} 个可见任务${direction}。`);
  }

  function patchVisiblePlanTasks(patch: Partial<StudyTask>, actionLabel: string) {
    if (!visiblePlanTasks.length) {
      setPlanActionStatus("当前没有可批量调整的任务。");
      return;
    }
    if (!window.confirm(`确定将当前筛选可见的 ${visiblePlanTasks.length} 个任务${actionLabel}吗？`)) return;

    let updatedCount = 0;
    const taskIds = visiblePlanTasks.map((task) => task.id);
    updateData((current) => {
      const result = updateTasksByIds(current, taskIds, patch);
      updatedCount = result.updatedCount;
      return result.data;
    });
    setPlanActionStatus(`已将 ${updatedCount} 个可见任务${actionLabel}。`);
  }

  function resolveOverdueTasks(source: "today" | "settings" = "settings") {
    let movedCount = 0;
    let createdCount = 0;
    updateData((current) => {
      const result = resolveOverdueTasksToDate(current, selectedDate);
      movedCount = result.movedCount;
      createdCount = result.createdCount;
      return result.data;
    });
    const message = movedCount
      ? `已整理 ${movedCount} 个逾期任务到 ${selectedDate}${createdCount ? `，其中 ${createdCount} 个生成了续做任务` : ""}。`
      : "当前没有需要整理的逾期任务。";
    if (source === "today") {
      setTodayActionStatus(message);
      setOverdueBannerDismissed(false);
    } else {
      setSettingsActionStatus(message);
    }
  }

  function copyPreviousWeekTasks() {
    const sourceDate = formatDate(addDays(new Date(selectedDate), -7));
    if (!window.confirm(`确定把 ${sourceDate} 所在周的计划复制到当前周吗？已存在的同名同科目同日期任务会自动跳过。`)) return;

    let copiedCount = 0;
    let sourceWeekStart = "";
    let targetWeekStart = "";
    updateData((current) => {
      const result = copyWeekTasks(current, sourceDate, selectedDate);
      copiedCount = result.copiedCount;
      sourceWeekStart = result.sourceWeekStart;
      targetWeekStart = result.targetWeekStart;
      return result.data;
    });
    setPlanScope("week");
    setPlanActionStatus(
      copiedCount
        ? `已从 ${sourceWeekStart} 所在周复制 ${copiedCount} 个任务到 ${targetWeekStart} 所在周。`
        : `${sourceWeekStart} 所在周没有可复制的新任务，或当前周已经有相同任务。`
    );
  }

  function relieveSelectedWeekHeavyDay() {
    if (!window.confirm("确定自动减轻本周最重的一天吗？系统会优先把未完成的低优先级大块任务推后一天。")) return;

    let movedCount = 0;
    let taskTitle = "";
    let sourceDate = "";
    let targetDate = "";
    updateData((current) => {
      const result = relieveHeaviestDay(current, selectedDate);
      movedCount = result.movedCount;
      taskTitle = result.taskTitle ?? "";
      sourceDate = result.sourceDate ?? "";
      targetDate = result.targetDate ?? "";
      return result.data;
    });
    setPlanScope("week");
    setPlanActionStatus(
      movedCount
        ? `已把「${taskTitle}」从 ${sourceDate} 推后到 ${targetDate}，给当天留出缓冲。`
        : sourceDate
          ? `${sourceDate} 已经偏重，但没有可移动的未完成任务。`
          : "当前周没有超过 6 小时的单日计划。"
    );
  }

  function addSuggestedStudyBlock() {
    if (!window.confirm("确定给本周偏少的科目补一个 60 分钟基础块吗？系统会放到本周当前最空的一天。")) return;

    let addedCount = 0;
    let subjectName = "";
    let date = "";
    updateData((current) => {
      const result = addLightSubjectStudyBlock(current, selectedDate, 60);
      addedCount = result.addedCount;
      subjectName = result.subjectName ?? "";
      date = result.date ?? "";
      return result.data;
    });
    setPlanScope("week");
    setPlanActionStatus(
      addedCount
        ? `已给 ${subjectName} 在 ${date} 补了一个 60 分钟基础巩固块。`
        : "当前周没有明显偏少的科目，不需要自动补块。"
    );
  }

  function addSubject() {
    const name = newSubject.name.trim();
    if (!name) return;
    updateData((current) => {
      current.subjects.push({
        id: uid("subject"),
        name,
        color: newSubject.color,
        weeklyTargetHours: Number(newSubject.weeklyTargetHours) || 8
      });
      return current;
    });
    setNewSubject({ name: "", color: "#6f82ff", weeklyTargetHours: 8 });
  }

  function updateSubject(subjectId: string, patch: Partial<Subject>) {
    updateData((current) => {
      current.subjects = current.subjects.map((subject) => subject.id === subjectId ? { ...subject, ...patch } : subject);
      return current;
    });
  }

  function deleteSubject(subjectId: string) {
    updateData((current) => {
      if (current.subjects.length <= 1) return current;
      const fallbackId = current.subjects.find((subject) => subject.id !== subjectId)?.id;
      current.subjects = current.subjects.filter((subject) => subject.id !== subjectId);
      current.tasks = current.tasks.map((task) => task.subjectId === subjectId && fallbackId ? { ...task, subjectId: fallbackId } : task);
      return current;
    });
  }

  function saveReview(text: string) {
    updateData((current) => {
      const trimmed = text.trim();
      current.reviews = current.reviews.filter((review) => review.date !== selectedDate);
      if (trimmed) {
        current.reviews.push({ date: selectedDate, text });
      }
      return current;
    });
  }

  function insertReviewTemplate() {
    const template = buildReviewTemplate(data, selectedDate);
    const nextText = reviewText.trim() ? `${reviewText.trim()}\n\n${template}` : template;
    saveReview(nextText);
  }

  async function askAiCoach() {
    if (isAiLoading) return;
    setIsAiLoading(true);
    setAiStatus("正在请求 AI 教练...");
    setAiAdvice(null);
    try {
      const body = await requestAdvice({
        date: selectedDate,
        payload: buildCoachAdvicePayload(data, selectedDate)
      });
      const structured = parseStructuredAdvice(body.advice ?? []);
      setAiAdvice(structured);
      setAiStatus("AI 结构化建议已生成（补哪科 / 砍哪块 / 明日三件事）");
    } catch (error) {
      setAiAdvice(ruleAdvice);
      setAiStatus(error instanceof Error ? `已切换本地结构化建议：${error.message}` : "已切换本地结构化建议");
    } finally {
      setIsAiLoading(false);
    }
  }

  async function testApiConfig() {
    if (isApiTesting) return;
    setIsApiTesting(true);
    setApiTestStatus("正在测试 API 连接...");
    try {
      const body = await testConfig(apiForm);
      setApiTestStatus(`${body.message} 当前模型：${body.model}`);
    } catch (error) {
      setApiTestStatus(error instanceof Error ? error.message : "API 测试失败。");
    } finally {
      setIsApiTesting(false);
    }
  }

  function downloadExportFile(file: { content: string; filename: string; mimeType: string }) {
    const blob = new Blob([file.content], { type: file.mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = file.filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  function downloadData(kind: "manual" | "before-import" = "manual") {
    downloadExportFile(createAppDataExport(data, kind, undefined, focusStatsStore));
    const nextMeta = markBackupExported(kind);
    setBackupMeta(nextMeta);
    setBackupBannerDismissed(false);
    if (kind === "manual") {
      setSettingsActionStatus(`已下载备份：${formatBackupTimestamp(nextMeta.lastExportAt)}。建议把文件放到安全位置。`);
      setTodayActionStatus(`已下载学习数据备份（${formatBackupTimestamp(nextMeta.lastExportAt)}）。`);
    }
  }

  /** 导入 JSON 文件到服务器（replace 语义，等价「恢复备份」） */
  function importData(event: ChangeEvent<HTMLInputElement>) {
    if (editsLocked) return;
    const file = event.target.files?.[0];
    if (!file) return;
    downloadData("before-import");
    file.text().then(async (text) => {
      // 先走前端现有校验（错误信息与旧版一致），再发到服务器
      parseImportedData(text);
      const remote = await importStateFile(text, "replace");
      suppressNextSyncRef.current = true; // 服务器已是这份数据，无需再推
      dataRef.current = remote.data;
      focusStatsStoreRef.current = remote.focusStats;
      revisionRef.current = remote.revision;
      setData(remote.data);
      setFocusStatsStore(remote.focusStats);
      setRevision(remote.revision);
      syncStatusRef.current = "ready";
      setSyncStatus("ready");
      setSyncMessage("");
      setStorageWarning("导入前已自动下载当前数据备份；服务器数据已更新。");
      setSettingsActionStatus(`导入成功（revision ${remote.revision}）。导入前已自动备份当前数据。`);
      event.target.value = "";
    }).catch((error) => {
      alert(error instanceof Error ? error.message : "导入失败");
      event.target.value = "";
    });
  }

  /** 从本机旧版 localStorage 一键迁移到服务器（replace；老键全程只读，迁移后仍保留） */
  async function migrateLegacyData() {
    if (editsLocked) return;
    const legacy = readLegacyLocalData();
    if (!legacy) {
      setSettingsActionStatus("本机浏览器没有找到旧版本地数据，无需迁移。");
      return;
    }
    setSettingsActionStatus("正在把本机旧数据导入服务器...");
    try {
      const legacyStats = readLegacyFocusStats();
      const remote = await importStateFile(JSON.stringify({ ...legacy, focusStats: legacyStats ?? undefined }), "replace");
      suppressNextSyncRef.current = true;
      dataRef.current = remote.data;
      focusStatsStoreRef.current = remote.focusStats;
      revisionRef.current = remote.revision;
      setData(remote.data);
      setFocusStatsStore(remote.focusStats);
      setRevision(remote.revision);
      syncStatusRef.current = "ready";
      setSyncStatus("ready");
      setSyncMessage("");
      setSettingsActionStatus(`已把本机旧数据迁移到服务器（revision ${remote.revision}）。旧数据仍保留在本机浏览器里。`);
    } catch (error) {
      setSettingsActionStatus(`迁移失败：${error instanceof Error ? error.message : "未知错误"}。`);
    }
  }

  /** 从服务器下载当前数据备份（可离线读回的 JSON） */
  async function downloadServerBackup() {
    try {
      const response = await fetch("/api/state/export");
      const text = await response.text();
      if (!response.ok) {
        let detail = "下载服务器备份失败。";
        try {
          detail = String(JSON.parse(text).detail ?? detail);
        } catch {
          // keep default
        }
        throw new Error(detail);
      }
      downloadExportFile({ content: text, filename: `kaoyan-study-server-${formatDate()}.json`, mimeType: "application/json;charset=utf-8" });
      setSettingsActionStatus("已从服务器下载当前数据备份。");
    } catch (error) {
      setSettingsActionStatus(error instanceof Error ? error.message : "下载服务器备份失败。");
    }
  }

  function resetData() {
    if (editsLocked) return;
    if (!window.confirm("确定要重置为示例数据吗？服务器上的学习记录会被替换成示例数据。")) return;
    clearBackupMeta();
    setBackupMeta(loadBackupMeta());
    setBackupBannerDismissed(false);
    const fresh = createDefaultData();
    dataRef.current = fresh;
    focusStatsStoreRef.current = createEmptyFocusStatsStore();
    setData(fresh);
    setFocusStatsStore(createEmptyFocusStatsStore()); // 数据变化 effect 会自动调度推送
    setSettingsActionStatus("已重置为示例数据并同步到服务器。备份记录已清空，请尽快重新导出。");
  }

  return (
    <main className={`app-shell ${focusActive ? "focus-active" : ""}`}>
      {focusActive && (
        <FocusStickyBar
          snapshot={focusSnapshot}
          onPauseResume={pauseOrResumeFocus}
          onFinish={finishFocusAndLog}
          onDiscard={cancelFocusSession}
          onSkipBreak={focusTimer.phase === "break" ? skipBreakSession : undefined}
          onGoToday={() => setView("today")}
        />
      )}
      <aside className="rail">
        <div className="logo-mark">K</div>
        {navItems.map((item) => (
          <button key={item.view} className={view === item.view ? "active" : ""} onClick={() => setView(item.view)} title={item.label}>
            {item.icon}
          </button>
        ))}
      </aside>

      <section className="workspace">
        <header className="hero-band">
          <div className="hero-copy">
            <p className="eyebrow">KAOYAN STUDY CONSOLE</p>
            <h1>今日学习控制台</h1>
            <p className="subline">距离目标日还有 <b>{daysLeft(data.examDate)}</b> 天。先把今天的主线任务压住，再把复盘收好。</p>
            <div className="brief-strip">
              <div>
                <span>计划</span>
                <strong>{minutesLabel(stats.plannedMinutes)}</strong>
              </div>
              <div>
                <span>执行</span>
                <strong>{minutesLabel(stats.actualMinutes)}</strong>
              </div>
              <div>
                <span>完成率</span>
                <strong>{stats.completionRate}%</strong>
              </div>
            </div>
          </div>
          <div className="date-card hero-date-card">
            <span>当前日期</span>
            <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
            <div className="date-meta">
              <span>目标日</span>
              <strong>{data.examDate || "未设置"}</strong>
            </div>
          </div>
        </header>

        <nav className="tabs">
          {navItems.map((item) => (
            <button key={item.view} className={view === item.view ? "active" : ""} onClick={() => setView(item.view)}>
              {item.icon}{item.label}
            </button>
          ))}
        </nav>

        {storageWarning && <div className="notice storage-warning">{storageWarning}<button className="ghost mini" onClick={() => setStorageWarning("")}>知道了</button></div>}

        {syncStatus === "loading" && <div className="notice sync-notice">正在从服务器加载数据…</div>}
        {syncStatus === "saving" && <div className="notice sync-notice sync-saving">正在保存到服务器…</div>}
        {syncStatus === "offline" && (
          <div className="notice sync-notice sync-offline">
            <strong>离线只读</strong>
            <span>{syncMessage}</span>
            <button className="ghost mini" onClick={retryConnection}>重试连接</button>
          </div>
        )}
        {syncStatus === "conflict" && conflictState && (
          <div className="notice sync-notice sync-conflict">
            <strong>数据冲突</strong>
            <span>{syncMessage}</span>
            <button className="primary compact-button" onClick={loadServerVersion}>加载服务器版本</button>
            <button className="ghost compact-button" onClick={overwriteWithLocalVersion}>用本机版本覆盖</button>
          </div>
        )}

        {showBackupBanner && (
          <div className={`notice backup-banner tone-${backupHealth.tone}`}>
            <div className="backup-banner-copy">
              <strong>{backupHealth.title}</strong>
              <span>{backupHealth.detail}</span>
            </div>
            <div className="backup-banner-actions">
              <button className="primary compact-button" onClick={() => downloadData("manual")}><Download size={16} />立即备份</button>
              <button className="ghost mini" onClick={() => setBackupBannerDismissed(true)}>稍后</button>
            </div>
          </div>
        )}

        {showOverdueBanner && (
          <div className="notice backup-banner tone-warn overdue-banner">
            <div className="backup-banner-copy">
              <strong>有 {overdueCount} 个逾期未完成任务</strong>
              <span>建议先整理到当前日期，再开始今天的主线，避免旧任务一直挂着。</span>
            </div>
            <div className="backup-banner-actions">
              <button className="primary compact-button" onClick={() => resolveOverdueTasks("today")}><RotateCcw size={16} />一键整理到今天</button>
              <button className="ghost mini" onClick={() => setOverdueBannerDismissed(true)}>稍后</button>
            </div>
          </div>
        )}

        {view === "today" && (
          <section className="panel-grid today-grid">
            <Metric title="计划时长" value={minutesLabel(stats.plannedMinutes)} icon={<Timer size={20} />} />
            <Metric title="实际执行" value={minutesLabel(stats.actualMinutes)} icon={<CheckCircle2 size={20} />} />
            <Metric title="完成率" value={`${stats.completionRate}%`} icon={<Flame size={20} />} />
            <Metric title="需补科目" value={stats.laggingSubjectName} icon={<AlertTriangle size={20} />} tone="warn" />
            <Metric title="今日专注" value={minutesLabel(focusStats.focusMinutes)} icon={<Timer size={20} />} />
            <Metric title="今日番茄" value={`${focusStats.pomodoroCount} 个`} icon={<Flame size={20} />} />

            <section className="panel backup-strip">
              <div className="backup-strip-copy">
                <span className="eyebrow">本地数据</span>
                <strong>{backupHealth.title}</strong>
                <p>最近导出：{backupHealth.lastExportLabel} · 任务 {dataOverview.taskCount} · 复盘 {dataOverview.reviewCount} 天{overdueCount ? ` · 逾期 ${overdueCount}` : ""}</p>
              </div>
              <div className="backup-strip-actions">
                {overdueCount > 0 && (
                  <button className="ghost compact-button" onClick={() => resolveOverdueTasks("today")}><RotateCcw size={16} />整理逾期</button>
                )}
                <button className="primary compact-button" onClick={() => downloadData("manual")}><Download size={16} />导出备份</button>
              </div>
            </section>

            <section className={`panel focus-panel ${isFocusTimerActive(focusTimer) ? "active" : ""} ${focusTimer.phase === "break" ? "break-phase" : ""}`}>
              <div className="panel-head">
                <h2>专注计时</h2>
                <div className="panel-actions">
                  <div className="segmented">
                    <button className={focusTimer.mode === "stopwatch" && focusTimer.phase === "work" ? "active" : ""} onClick={() => changeFocusMode("stopwatch")} disabled={isFocusTimerActive(focusTimer)}>正计时</button>
                    <button className={focusTimer.mode === "pomodoro" || focusTimer.phase === "break" ? "active" : ""} onClick={() => changeFocusMode("pomodoro")} disabled={isFocusTimerActive(focusTimer)}>番茄 {pomodoroMinutes}m</button>
                  </div>
                </div>
              </div>
              <div className="pomodoro-duration-row" aria-label="番茄时长">
                <span className="hint">番茄时长</span>
                <div className="segmented compact">
                  {POMODORO_DURATION_OPTIONS.map((minutes) => (
                    <button
                      key={minutes}
                      type="button"
                      className={pomodoroMinutes === minutes ? "active" : ""}
                      disabled={isFocusTimerActive(focusTimer)}
                      onClick={() => changePomodoroMinutes(minutes)}
                    >
                      {minutes}m
                    </button>
                  ))}
                </div>
                <span className="pill focus-stats-pill" title={formatFocusStatsSummary(focusStats)}>
                  今日 {focusStats.pomodoroCount} 番茄 · {minutesLabel(focusStats.focusMinutes)}
                </span>
              </div>
              <div className="focus-board">
                <div className="focus-clock-block">
                  <span className="focus-mode-label">
                    {focusTimer.phase === "break"
                      ? "休息剩余"
                      : focusTimer.mode === "pomodoro" ? "番茄剩余" : "已专注"}
                  </span>
                  <strong className="focus-clock">{focusSnapshot.display}</strong>
                  <span className="focus-task-label">
                    {focusTimer.phase === "break"
                      ? `${focusTimer.status === "paused" ? "休息已暂停" : "休息中"}${focusTimer.lastWorkTaskTitle ? ` · 上一轮：${focusTimer.lastWorkTaskTitle}` : ""}`
                      : focusTimer.taskId
                        ? `${focusTimer.status === "paused" ? "已暂停 · " : "进行中 · "}${focusTimer.taskTitle}`
                        : "点任务上的「开始」绑定一个今日任务"}
                  </span>
                  {(focusTimer.mode === "pomodoro" || focusTimer.phase === "break") && isFocusTimerActive(focusTimer) && (
                    <div className="focus-progress" aria-hidden="true">
                      <i style={{ width: `${Math.round(focusSnapshot.progress * 100)}%` }} />
                    </div>
                  )}
                </div>
                <div className="focus-controls">
                  <button className="ghost compact-button" onClick={pauseOrResumeFocus} disabled={!isFocusTimerActive(focusTimer)}>
                    {focusTimer.status === "running" ? <><Pause size={16} />暂停</> : <><Play size={16} />继续</>}
                  </button>
                  <button className="primary compact-button" onClick={finishFocusAndLog} disabled={!isFocusTimerActive(focusTimer)}>
                    <Square size={16} />{focusTimer.phase === "break" ? "结束休息" : "结束并记入"}
                  </button>
                  <button className="ghost compact-button" onClick={cancelFocusSession} disabled={!isFocusTimerActive(focusTimer)}>
                    {focusTimer.phase === "break" ? "跳过休息" : "丢弃"}
                  </button>
                </div>
              </div>
              {focusTask && focusTimer.phase === "work" && (
                <p className="hint focus-hint">
                  当前任务实际时长 {minutesLabel(focusTask.actualMinutes)}
                  {focusSnapshot.elapsedMinutes > 0 ? ` · 本段约 ${focusSnapshot.elapsedMinutes} 分钟（结束时累加）` : ""}
                </p>
              )}
              <p className="hint focus-shortcut-hint">快捷键：空格 暂停/继续 · Enter 结束并记入 · Esc 跳过休息/丢弃（输入框内不触发）</p>
              {(focusStatusMessage || isFocusTimerActive(focusTimer)) && (
                <div className="notice inline-notice">
                  {focusStatusMessage || (focusTimer.phase === "break"
                    ? `休息 ${DEFAULT_BREAK_MINUTES} 分钟，到点会提醒。可跳过或直接点任务开始下一轮。`
                    : focusTimer.mode === "pomodoro"
                      ? `番茄 ${focusTimer.targetMinutes || pomodoroMinutes} 分钟，到点自动记入并进入 ${DEFAULT_BREAK_MINUTES} 分钟休息。`
                      : "正计时运行中，点「结束并记入」把本段时间加到任务实际时长。")}
                </div>
              )}
            </section>

            <section className="panel task-panel">
              <div className="panel-head">
                <h2>今日任务</h2>
                <div className="panel-actions">
                  <span className="pill">可直接用模板补任务</span>
                  <button className="ghost compact-button" onClick={() => downloadData("manual")}><Download size={16} />备份</button>
                  <button className="ghost compact-button" onClick={prepareSelectedTomorrowPlan}><ArrowRight size={16} />明日开局</button>
                  <button className="icon-button" onClick={addTask} title="添加任务"><Plus size={18} /></button>
                </div>
              </div>
              <div className="quick-templates">
                {quickTemplates.map((template) => (
                  <button key={template.key} className="quick-template" onClick={() => addQuickTask(template)}>
                    <strong>{template.label}</strong>
                    <span>{minutesLabel(template.estimatedMinutes)} · {template.priority}优先级</span>
                  </button>
                ))}
              </div>
              <TaskCreator data={data} newTask={newTask} setNewTask={setNewTask} addTask={addTask} />
              {todayActionStatus && <div className="notice inline-notice">{todayActionStatus}</div>}
              <div className="task-list">
                {todayTasks.map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    data={data}
                    toggleTask={toggleTask}
                    updateTaskMinutes={updateTaskMinutes}
                    bumpMinutes={bumpMinutes}
                    fillMinutes={fillMinutes}
                    deleteTask={deleteTask}
                    onStartFocus={beginFocusOnTask}
                    isFocusTarget={focusTimer.taskId === task.id && isFocusTimerActive(focusTimer)}
                    focusRunning={focusTimer.taskId === task.id && focusTimer.status === "running"}
                  />
                ))}
                {!todayTasks.length && <p className="empty">今天还没有任务，先加一个 45 分钟的小任务。</p>}
              </div>
            </section>

            <section className="panel">
              <div className="panel-head">
                <h2>今日复盘</h2>
                <div className="panel-actions">
                  <span className="pill">收尾 {closureReadyCount}/3</span>
                  <button className="ghost compact-button" onClick={insertReviewTemplate}><ClipboardList size={16} />复盘模板</button>
                  <button className="primary compact-button" onClick={runSelectedDailyClosure}><CheckCircle2 size={16} />一键收尾</button>
                </div>
              </div>
              <textarea value={reviewText} onChange={(event) => saveReview(event.target.value)} placeholder="写一句：今天偏差最大的是哪科？明天第一件事是什么？" />
              <ClosureChecklist items={dailyClosureChecklist} />
              <p className="hint closure-hint">一键收尾会：补复盘草稿（若为空）→ 给已完成但未记时长的任务填计划分钟 → 把未完成任务整理到明天。</p>
              <StructuredAdviceBoard advice={ruleAdvice} sourceLabel="本地规则" />
            </section>
          </section>
        )}

        {view === "plan" && (
          <section className="panel">
            <div className="panel-head">
              <h2>计划排布</h2>
              <span className="pill">可直接调整日期、科目和时长</span>
            </div>
            <div className="plan-quick-actions" aria-label="计划快捷操作">
              <button className="ghost compact-button" onClick={copyPreviousWeekTasks}><Copy size={16} />复制上周</button>
              <button className="ghost compact-button" onClick={rolloverSelectedDateTasks}><ArrowRight size={16} />顺延未完成</button>
              <button className="ghost compact-button" onClick={() => resolveOverdueTasks("today")} disabled={overdueCount === 0}><RotateCcw size={16} />整理逾期{overdueCount ? ` ${overdueCount}` : ""}</button>
              <button className="ghost compact-button" onClick={relieveSelectedWeekHeavyDay} disabled={!hasHeavyDayTip}><ArrowRight size={16} />一键减负</button>
              <button className="ghost compact-button" onClick={addSuggestedStudyBlock} disabled={!hasLightSubjectTip}><Plus size={16} />一键补块</button>
              <button className="primary compact-button" onClick={() => { setView("progress"); generateWeeklyReportForSelectedDate(); }}><ClipboardList size={16} />生成周报</button>
            </div>
            <WeekPlanBoard weekOverview={weekOverview} selectedDate={selectedDate} setSelectedDate={setSelectedDate} />
            <WeeklyLoadStrip weeklyLoad={weeklyLoad} />
            <WeeklyAdjustmentPanel
              tips={weeklyAdjustmentTips}
              canAddStudyBlock={hasLightSubjectTip}
              canRelieveHeavyDay={hasHeavyDayTip}
              onAddStudyBlock={addSuggestedStudyBlock}
              onRelieveHeavyDay={relieveSelectedWeekHeavyDay}
            />
            <div className="plan-toolbar">
              <div>
                <strong>{planScope === "week" ? "本周任务" : "全部任务"}</strong>
                <span>{visiblePlanTasks.length} 项 · 选中日期 {selectedDate}{hasActivePlanFilters ? " · 已筛选" : ""}</span>
              </div>
              <div className="plan-toolbar-actions">
                <div className="segmented">
                  <button className={planScope === "week" ? "active" : ""} onClick={() => setPlanScope("week")}>本周</button>
                  <button className={planScope === "all" ? "active" : ""} onClick={() => setPlanScope("all")}>全部</button>
                </div>
                <button className="ghost compact-button" onClick={() => shiftVisiblePlanTasks(-1)}><ArrowLeft size={16} />提前一天</button>
                <button className="ghost compact-button" onClick={() => shiftVisiblePlanTasks(1)}><ArrowRight size={16} />推后一天</button>
                <button className="ghost compact-button" onClick={rolloverSelectedDateTasks}><ArrowRight size={16} />顺延未完成</button>
              </div>
            </div>
            {planActionStatus && <div className="notice inline-notice">{planActionStatus}</div>}
            <div className="plan-filter-bar">
              <div className="filter-title"><Filter size={16} /><span>筛选</span></div>
              <label>
                <span>搜索</span>
                <input value={planFilters.query ?? ""} onChange={(event) => setPlanFilters((current) => ({ ...current, query: event.target.value }))} placeholder="按任务标题搜索" />
              </label>
              <label>
                <span>科目</span>
                <select value={planFilters.subjectId} onChange={(event) => setPlanFilters((current) => ({ ...current, subjectId: event.target.value }))}>
                  <option value="all">全部科目</option>
                  {data.subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
                </select>
              </label>
              <label>
                <span>优先级</span>
                <select value={planFilters.priority} onChange={(event) => setPlanFilters((current) => ({ ...current, priority: event.target.value as PlanTaskFilters["priority"] }))}>
                  <option value="all">全部优先级</option>
                  <option value="高">高优先级</option>
                  <option value="中">中优先级</option>
                  <option value="低">低优先级</option>
                </select>
              </label>
              <label>
                <span>状态</span>
                <select value={planFilters.status} onChange={(event) => setPlanFilters((current) => ({ ...current, status: event.target.value as PlanTaskFilters["status"] }))}>
                  <option value="all">全部状态</option>
                  <option value="todo">待完成</option>
                  <option value="done">已完成</option>
                </select>
              </label>
              <button className="ghost compact-button" onClick={resetPlanFilters} disabled={!hasActivePlanFilters}><RotateCcw size={16} />重置</button>
            </div>
            <div className="bulk-action-bar">
              <div className="bulk-action-copy">
                <strong>批量调整</strong>
                <span>作用于当前筛选可见的 {visiblePlanTasks.length} 个任务</span>
              </div>
              <label>
                <span>优先级</span>
                <select value="" onChange={(event) => {
                  const priority = event.target.value as StudyTask["priority"] | "";
                  if (priority) patchVisiblePlanTasks({ priority }, `设为${priority}优先级`);
                }}>
                  <option value="">选择优先级...</option>
                  <option value="高">高优先级</option>
                  <option value="中">中优先级</option>
                  <option value="低">低优先级</option>
                </select>
              </label>
              <label>
                <span>状态</span>
                <select value="" onChange={(event) => {
                  const status = event.target.value as StudyTask["status"] | "";
                  if (status) patchVisiblePlanTasks({ status }, status === "done" ? "标记为已完成" : "标记为待完成");
                }}>
                  <option value="">选择状态...</option>
                  <option value="todo">待完成</option>
                  <option value="done">已完成</option>
                </select>
              </label>
            </div>
            <div className="plan-list">
              {visiblePlanTasks.map((task) => (
                <PlanTaskRow
                  key={task.id}
                  task={task}
                  data={data}
                  updateTask={updateTask}
                  deleteTask={deleteTask}
                />
              ))}
              {!visiblePlanTasks.length && <p className="empty">{hasActivePlanFilters ? "当前筛选下没有任务，可以重置筛选或调整任务条件。" : planScope === "week" ? "本周还没有任务，可以回到「今日」添加模板任务，或把已有任务日期调整到本周。" : "还没有计划任务。"}</p>}
            </div>
          </section>
        )}

        {view === "progress" && (
          <section className="panel-grid progress-grid">
            <section className="panel heatmap-panel">
              <div className="panel-head">
                <h2>学习热力</h2>
                <div className="panel-actions">
                  <div className="segmented compact">
                    {[8, 12, 16].map((weeks) => (
                      <button key={weeks} className={heatmapWeeks === weeks ? "active" : ""} onClick={() => setHeatmapWeeks(weeks)}>
                        {weeks} 周
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <p className="subline">
                以当前日期所在周为终点，向前看最近 {heatmapWeeks} 周。格子颜色按任务「实际学习」时长分档；悬停可看计划、专注与复盘。
              </p>
              <StudyHeatmapBoard
                heatmap={studyHeatmap}
                selectedDate={selectedDate}
                onSelectDate={setSelectedDate}
              />
            </section>

            <section className="panel progress-main">
              <div className="panel-head">
                <h2>进度对比</h2>
                <div className="segmented">
                  {[7, 14, 30].map((days) => (
                    <button key={days} className={progressDays === days ? "active" : ""} onClick={() => setProgressDays(days)}>
                      {days} 天
                    </button>
                  ))}
                </div>
              </div>
              <div className="progress-list">
                {progress.map((item) => (
                  <div className="progress-row" key={item.subject.id}>
                    <div>
                      <strong style={{ color: item.subject.color }}>{item.subject.name}</strong>
                      <span>实际 {minutesLabel(item.actualMinutes)} / 计划 {minutesLabel(item.plannedMinutes)} / 周目标 {item.subject.weeklyTargetHours} 小时</span>
                    </div>
                    <div className="bar"><i style={{ width: `${Math.min(item.completionRate, 100)}%`, background: item.subject.color }} /></div>
                    <b>{item.completionRate}%</b>
                    <input type="number" min="1" value={item.subject.weeklyTargetHours} onChange={(event) => updateSubject(item.subject.id, { weeklyTargetHours: Number(event.target.value) || 1 })} title="每周目标小时" />
                  </div>
                ))}
              </div>
            </section>

            <section className="panel weekly-report-panel">
              <div className="panel-head">
                <h2>本周周报</h2>
                <div className="panel-actions">
                  <button className="primary compact-button" onClick={generateWeeklyReportForSelectedDate}><ClipboardList size={16} />生成周报</button>
                  <button className="ghost compact-button" onClick={appendWeeklyReportToSelectedReview}><ClipboardList size={16} />写入复盘</button>
                  <button className="ghost compact-button" onClick={copyWeeklyReport} disabled={!weeklyReport}><Copy size={16} />复制</button>
                  <button className="ghost compact-button" onClick={downloadWeeklyReport} disabled={!weeklyReport}><Download size={16} />下载 MD</button>
                </div>
              </div>
              <p className="subline">按顶部当前日期所在周统计（周一至周日）。「写入复盘」会把摘要追加到当前日期的复盘，同一周不会重复写入。</p>
              {weeklyReportStatus && <div className="notice inline-notice">{weeklyReportStatus}</div>}
              {weeklyReport ? (
                <>
                  <div className="data-overview weekly-report-overview" aria-label="周报概览">
                    <OverviewItem label="完成率" value={`${weeklyReport.completionRate}%`} />
                    <OverviewItem label="执行率" value={`${weeklyReport.executionRate}%`} />
                    <OverviewItem label="复盘" value={`${weeklyReport.reviewDays}/7`} />
                    <OverviewItem label="偏弱科" value={weeklyReport.weakestSubjectName} />
                    <OverviewItem label="周期" value={`${weeklyReport.weekStart.slice(5)}~${weeklyReport.weekEnd.slice(5)}`} />
                  </div>
                  <div className="weekly-focus-list">
                    {weeklyReport.nextWeekFocus.map((line, index) => (
                      <div className="advice" key={`${index}-${line.slice(0, 12)}`}>{index + 1}. {line}</div>
                    ))}
                  </div>
                  <textarea className="weekly-report-text" readOnly value={weeklyReport.markdown} />
                </>
              ) : (
                <p className="empty">还没有生成周报。点「生成周报」可得到完成率、分科执行、调整提示和下周三条重点。</p>
              )}
            </section>
          </section>
        )}

        {view === "coach" && (
          <section className="panel coach-panel">
            <div className="panel-head">
              <h2>AI 教练</h2>
              <button className="primary" onClick={askAiCoach} disabled={isAiLoading}><Sparkles size={18} />{isAiLoading ? "生成中..." : "生成结构化建议"}</button>
            </div>
            <p className="subline">
              固定输出：补哪科 / 砍哪块 / 明日三件事。
              模型状态：{health?.llm_configured ? `已配置 ${health.model}` : "未配置，失败时使用本地规则建议"}
            </p>
            {aiStatus && <div className="notice">{aiStatus}</div>}
            <StructuredAdviceBoard
              advice={displayedAdvice}
              sourceLabel={aiAdvice ? "AI / 回退结果" : "本地规则预览"}
              large
            />
          </section>
        )}

        {view === "settings" && (
          <section className="panel settings-panel">
            <div className="panel-head">
              <h2>设置与数据</h2>
              <span className="pill">服务端 v{data.version} · rev {revision}</span>
            </div>
            <div className="data-overview" aria-label="数据概览">
              <OverviewItem label="科目数" value={`${dataOverview.subjectCount}`} />
              <OverviewItem label="任务数" value={`${dataOverview.taskCount}`} />
              <OverviewItem label="已完成" value={`${dataOverview.doneTaskCount}`} />
              <OverviewItem label="复盘天数" value={`${dataOverview.reviewCount}`} />
              <OverviewItem label="最近任务" value={dataOverview.latestTaskDate} />
            </div>
            <section className={`backup-card tone-${backupHealth.tone}`} aria-label="备份状态">
              <div className="backup-card-copy">
                <div className="panel-head compact-head">
                  <h2>数据备份</h2>
                  <span className={`pill ${backupHealth.needsAttention ? "" : "ok"}`}>{backupHealth.needsAttention ? "需关注" : "正常"}</span>
                </div>
                <p className="backup-card-title">{backupHealth.title}</p>
                <p className="hint">{backupHealth.detail}</p>
                <div className="backup-meta-grid">
                  <OverviewItem label="最近导出" value={backupHealth.lastExportLabel} />
                  <OverviewItem label="距今" value={backupHealth.daysSinceExport === null ? "—" : `${backupHealth.daysSinceExport} 天`} />
                  <OverviewItem label="存储位置" value="服务器 SQLite（本地只读缓存）" />
                </div>
              </div>
              <div className="backup-card-actions">
                <button className="primary" onClick={() => downloadData("manual")}><Download size={18} />导出 JSON 备份</button>
                <label className="ghost file-button"><Import size={18} />导入 JSON<input type="file" accept="application/json" onChange={importData} /></label>
              </div>
            </section>

            <section className="panel focus-notify-panel" aria-label="专注提醒设置">
              <div className="panel-head compact-head">
                <h2>专注提醒</h2>
                <span className="pill">番茄到点</span>
              </div>
              <p className="hint">番茄倒计时结束时，可播放提示音并弹出系统通知（需浏览器授权）。标签页在后台时尤其有用。</p>
              <div className="focus-notify-options">
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={focusNotifyPrefs.soundEnabled}
                    onChange={(event) => updateFocusNotifyPrefs({ soundEnabled: event.target.checked })}
                  />
                  <span>到点播放提示音</span>
                </label>
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={focusNotifyPrefs.notificationEnabled}
                    onChange={(event) => updateFocusNotifyPrefs({ notificationEnabled: event.target.checked })}
                  />
                  <span>到点系统通知</span>
                </label>
              </div>
              <div className="backup-meta-grid focus-notify-meta">
                <OverviewItem
                  label="通知权限"
                  value={
                    notificationPermission === "granted" ? "已允许"
                      : notificationPermission === "denied" ? "已拒绝"
                        : notificationPermission === "unsupported" ? "不支持"
                          : "未授权"
                  }
                />
                <OverviewItem label="提示音" value={focusNotifyPrefs.soundEnabled ? "开" : "关"} />
                <OverviewItem label="系统通知" value={focusNotifyPrefs.notificationEnabled ? "开" : "关"} />
              </div>
              <div className="button-row focus-notify-actions">
                <button className="primary compact-button" onClick={() => void testFocusNotify()}><Sparkles size={16} />试听/测试通知</button>
                <button className="ghost compact-button" onClick={() => void requestNotificationPermissionFromSettings()}>请求通知权限</button>
              </div>
              {focusNotifyStatus && <div className="notice inline-notice">{focusNotifyStatus}</div>}
            </section>

            <section className="health-panel" aria-label="数据健康诊断">
              {dataHealth.map((item) => (
                <HealthItem
                  item={item}
                  key={item.id}
                  action={item.id === "overdue-tasks" ? { label: "整理到当前日期", onClick: () => resolveOverdueTasks("settings") } : undefined}
                />
              ))}
            </section>
            {settingsActionStatus && <div className="notice inline-notice">{settingsActionStatus}</div>}
            <section className="api-box">
              <div className="panel-head compact-head">
                <h2>API 配置</h2>
                <span className={`pill ${health?.llm_configured ? "ok" : ""}`}>{health?.llm_configured ? "已配置" : "未配置"}</span>
              </div>
              <label className="field">
                <span>API Key</span>
                <input type="password" readOnly value={apiForm.api_key} placeholder="服务器上由 /etc/kaoyan-console.env 配置（网页只读）" autoComplete="off" />
              </label>
              <label className="field">
                <span>Base URL</span>
                <input value={apiForm.base_url} onChange={(event) => setApiForm((current) => ({ ...current, base_url: event.target.value }))} placeholder="https://api.openai.com/v1" />
              </label>
              <label className="field">
                <span>Model</span>
                <input value={apiForm.model} onChange={(event) => setApiForm((current) => ({ ...current, model: event.target.value }))} placeholder="gpt-4.1-mini" />
              </label>
              <div className="button-row">
                <button className="ghost" onClick={testApiConfig} disabled={isApiTesting}><CheckCircle2 size={18} />{isApiTesting ? "测试中..." : "测试连接"}</button>
              </div>
              {apiTestStatus && <div className="notice inline-notice">{apiTestStatus}</div>}
              <p className="hint">服务器上 API Key 只能通过 /etc/kaoyan-console.env 配置，网页不可修改；「测试连接」只测试服务器当前生效的配置（Key 不会发送到其他地址）。</p>
              <pre className="example-box">{`示例：
API Key: sk-xxxxxxxx
Base URL: https://api.openai.com/v1
Model: gpt-4.1-mini

OpenAI 兼容服务也可以这样填：
Base URL: https://你的服务地址/v1
Model: 该服务支持的模型名`}</pre>
            </section>
            <label className="field">
              <span>目标日期</span>
              <input type="date" value={data.examDate} onChange={(event) => updateData((current) => ({ ...current, examDate: event.target.value }))} />
            </label>
            <section className="subject-manager">
              <div className="panel-head compact-head">
                <h2>科目管理</h2>
                <span className="pill">{data.subjects.length} 个科目</span>
              </div>
              <div className="subject-creator">
                <input value={newSubject.name} onChange={(event) => setNewSubject((current) => ({ ...current, name: event.target.value }))} onKeyDown={(event) => event.key === "Enter" && addSubject()} placeholder="新增科目，例如：管综、408、教育学" />
                <input type="color" value={newSubject.color} onChange={(event) => setNewSubject((current) => ({ ...current, color: event.target.value }))} title="科目颜色" />
                <input type="number" min="1" value={newSubject.weeklyTargetHours} onChange={(event) => setNewSubject((current) => ({ ...current, weeklyTargetHours: Number(event.target.value) || 1 }))} title="每周目标小时" />
                <button className="primary" onClick={addSubject}><Plus size={18} />添加科目</button>
              </div>
            </section>
            <div className="subject-editor">
              {data.subjects.map((subject) => (
                <div className="subject-row" key={subject.id}>
                  <input value={subject.name} onChange={(event) => updateSubject(subject.id, { name: event.target.value })} />
                  <input type="color" value={subject.color} onChange={(event) => updateSubject(subject.id, { color: event.target.value })} title="科目颜色" />
                  <input type="number" min="1" value={subject.weeklyTargetHours} onChange={(event) => updateSubject(subject.id, { weeklyTargetHours: Number(event.target.value) || 1 })} title="每周目标小时" />
                  <button className="icon-button subtle" onClick={() => deleteSubject(subject.id)} title="删除科目"><Trash2 size={16} /></button>
                </div>
              ))}
            </div>
            <div className="settings-actions">
              <button className="primary" onClick={() => downloadData("manual")}><Download size={18} />导出 JSON 备份</button>
              <label className="ghost file-button"><Import size={18} />导入 JSON 到服务器<input type="file" accept="application/json" onChange={importData} /></label>
              <button className="ghost" onClick={() => void downloadServerBackup()}><Download size={18} />从服务器下载备份</button>
              <button className="ghost" onClick={() => void migrateLegacyData()}><Import size={18} />从本机旧数据一键迁移</button>
              <button className="danger" onClick={resetData}><RefreshCw size={18} />重置示例数据</button>
            </div>
            <p className="hint">学习数据保存在服务器 SQLite（本地浏览器保留只读缓存供离线查看）。服务器会自动每日备份；建议仍定期用「导出 JSON 备份」留一份文件。</p>
          </section>
        )}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

