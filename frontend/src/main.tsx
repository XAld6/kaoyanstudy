import React, { ChangeEvent, useEffect, useMemo, useState } from "react";
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
  Plus,
  RefreshCw,
  RotateCcw,
  Settings,
  Sparkles,
  Timer,
  Trash2
} from "lucide-react";
import { ApiForm, Health, fetchConfig, requestAdvice, saveConfig, testConfig } from "./api";
import {
  AppData,
  DailyClosureItem,
  DataHealthItem,
  PlanTaskFilters,
  Subject,
  SubjectWeeklyLoad,
  StudyTask,
  WeeklyAdjustmentTip,
  WeekDayOverview,
  addDays,
  addLightSubjectStudyBlock,
  buildReviewTemplate,
  copyWeekTasks,
  formatDate,
  generateRuleAdvice,
  generateWeeklyAdjustmentTips,
  getDailyClosureChecklist,
  getDataHealth,
  getDataOverview,
  getPlanTasks,
  getSubjectProgress,
  getSubjectWeeklyLoad,
  getTasksForDate,
  getTodayStats,
  getWeekOverview,
  prepareTomorrowPlan,
  relieveHeaviestDay,
  resolveOverdueTasksToDate,
  resolveSubjectIdByKeywords,
  rolloverUnfinishedTasks,
  shiftTasksByIds,
  updateTasksByIds,
  uid
} from "./studyCore";
import { clearAppData, createAppDataExport, loadAppData, loadAppDataWithStatus, parseImportedData, saveAppData } from "./storage";
import "./styles.css";

type View = "today" | "plan" | "progress" | "coach" | "settings";

const navItems: Array<{ view: View; label: string; icon: React.ReactNode }> = [
  { view: "today", label: "今日", icon: <CalendarDays size={18} /> },
  { view: "plan", label: "计划", icon: <ClipboardList size={18} /> },
  { view: "progress", label: "进度", icon: <LineChart size={18} /> },
  { view: "coach", label: "AI", icon: <Bot size={18} /> },
  { view: "settings", label: "设置", icon: <Settings size={18} /> }
];

const weekdayLabels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

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

function minutesLabel(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest} 分钟`;
  if (!rest) return `${hours} 小时`;
  return `${hours} 小时 ${rest} 分钟`;
}

function daysLeft(examDate: string) {
  if (!examDate) return 0;
  const today = new Date(formatDate());
  const exam = new Date(examDate);
  return Math.max(0, Math.ceil((exam.getTime() - today.getTime()) / 86400000));
}

function App() {
  const [initialLoad] = useState(() => loadAppDataWithStatus());
  const [data, setData] = useState<AppData>(() => initialLoad.data);
  const [view, setView] = useState<View>("today");
  const [selectedDate, setSelectedDate] = useState(formatDate());
  const [newTask, setNewTask] = useState({ title: "", subjectId: "", estimatedMinutes: 60, priority: "中" as StudyTask["priority"] });
  const [newSubject, setNewSubject] = useState({ name: "", color: "#6f82ff", weeklyTargetHours: 8 });
  const [progressDays, setProgressDays] = useState(7);
  const [planScope, setPlanScope] = useState<"week" | "all">("week");
  const [planFilters, setPlanFilters] = useState<Omit<PlanTaskFilters, "scope">>({ subjectId: "all", priority: "all", status: "all", query: "" });
  const [todayActionStatus, setTodayActionStatus] = useState("");
  const [planActionStatus, setPlanActionStatus] = useState("");
  const [settingsActionStatus, setSettingsActionStatus] = useState("");
  const [aiAdvice, setAiAdvice] = useState<string[]>([]);
  const [aiStatus, setAiStatus] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [apiForm, setApiForm] = useState<ApiForm>({ api_key: "", base_url: "https://api.openai.com/v1", model: "gpt-4.1-mini" });
  const [apiSaveStatus, setApiSaveStatus] = useState("");
  const [apiTestStatus, setApiTestStatus] = useState("");
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [isApiSaving, setIsApiSaving] = useState(false);
  const [isApiTesting, setIsApiTesting] = useState(false);
  const [storageWarning, setStorageWarning] = useState(initialLoad.recovered ? "检测到浏览器里的学习数据异常，已回退到示例数据。若你有备份，请在设置页导入 JSON。" : "");

  useEffect(() => {
    saveAppData(data);
  }, [data]);

  useEffect(() => {
    fetchConfig()
      .then((config) => {
        setHealth(config);
        setApiForm((current) => ({ ...current, base_url: config.base_url, model: config.model }));
      })
      .catch(() => setHealth({ status: "offline", llm_configured: false, model: "未连接", base_url: "本地后端未启动" }));
  }, []);

  const todayTasks = useMemo(() => getTasksForDate(data, selectedDate), [data, selectedDate]);
  const stats = useMemo(() => getTodayStats(data, selectedDate), [data, selectedDate]);
  const ruleAdvice = useMemo(() => generateRuleAdvice(data, selectedDate), [data, selectedDate]);
  const dailyClosureChecklist = useMemo(() => getDailyClosureChecklist(data, selectedDate), [data, selectedDate]);
  const progress = useMemo(() => getSubjectProgress(data, progressDays, selectedDate), [data, progressDays, selectedDate]);
  const weekOverview = useMemo(() => getWeekOverview(data, selectedDate), [data, selectedDate]);
  const weeklyLoad = useMemo(() => getSubjectWeeklyLoad(data, selectedDate), [data, selectedDate]);
  const weeklyAdjustmentTips = useMemo(() => generateWeeklyAdjustmentTips(data, selectedDate), [data, selectedDate]);
  const hasHeavyDayTip = weeklyAdjustmentTips.some((tip) => tip.id.startsWith("heavy-day-"));
  const hasLightSubjectTip = weeklyAdjustmentTips.some((tip) => tip.id.startsWith("light-"));
  const visiblePlanTasks = useMemo(() => getPlanTasks(data, selectedDate, { scope: planScope, ...planFilters }), [data, planFilters, planScope, selectedDate]);
  const dataOverview = useMemo(() => getDataOverview(data), [data]);
  const dataHealth = useMemo(() => getDataHealth(data, selectedDate), [data, selectedDate]);
  const hasActivePlanFilters = planFilters.subjectId !== "all" || planFilters.priority !== "all" || planFilters.status !== "all" || Boolean(planFilters.query?.trim());
  const reviewText = data.reviews.find((review) => review.date === selectedDate)?.text ?? "";

  function updateData(updater: (current: AppData) => AppData) {
    setData((current) => updater(structuredClone(current)));
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
    updateData((current) => {
      current.tasks = current.tasks.map((task) => task.id === taskId ? { ...task, actualMinutes, status: actualMinutes > 0 ? task.status : "todo" } : task);
      return current;
    });
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

  function resolveOverdueTasks() {
    let movedCount = 0;
    let createdCount = 0;
    updateData((current) => {
      const result = resolveOverdueTasksToDate(current, selectedDate);
      movedCount = result.movedCount;
      createdCount = result.createdCount;
      return result.data;
    });
    setSettingsActionStatus(
      movedCount
        ? `已整理 ${movedCount} 个逾期任务到 ${selectedDate}${createdCount ? `，其中 ${createdCount} 个生成了续做任务` : ""}。`
        : "当前没有需要整理的逾期任务。"
    );
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
    setAiAdvice([]);
    try {
      const recentDates = Array.from({ length: 7 }, (_, index) => formatDate(addDays(new Date(selectedDate), index - 6)));
      const body = await requestAdvice({
        date: selectedDate,
        payload: {
          subjects: data.subjects,
          tasks: data.tasks.filter((task) => recentDates.includes(task.date)),
          review: reviewText,
          local_advice: ruleAdvice
        }
      });
      setAiAdvice(body.advice);
      setAiStatus("AI 建议已生成");
    } catch (error) {
      setAiAdvice(ruleAdvice);
      setAiStatus(error instanceof Error ? `已切换本地建议：${error.message}` : "已切换本地建议");
    } finally {
      setIsAiLoading(false);
    }
  }

  async function saveApiConfig() {
    if (isApiSaving) return;
    setIsApiSaving(true);
    setApiSaveStatus("正在保存 API 配置...");
    try {
      const config = await saveConfig(apiForm);
      setHealth(config);
      setApiForm((current) => ({ ...current, api_key: "" }));
      setApiSaveStatus("API 配置已保存到本地后端。");
    } catch (error) {
      setApiSaveStatus(error instanceof Error ? error.message : "API 配置保存失败。");
    } finally {
      setIsApiSaving(false);
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

  function downloadData() {
    downloadExportFile(createAppDataExport(data, "manual"));
  }

  function importData(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    downloadExportFile(createAppDataExport(data, "before-import"));
    file.text().then((text) => {
      setData(parseImportedData(text));
      setStorageWarning("导入前已自动下载当前数据备份；新数据已导入。");
      event.target.value = "";
    }).catch((error) => {
      alert(error instanceof Error ? error.message : "导入失败");
      event.target.value = "";
    });
  }

  function resetData() {
    if (!window.confirm("确定要重置为示例数据吗？当前浏览器里的学习记录会被清空。")) return;
    clearAppData();
    setData(loadAppData());
  }

  return (
    <main className="app-shell">
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

        {view === "today" && (
          <section className="panel-grid today-grid">
            <Metric title="计划时长" value={minutesLabel(stats.plannedMinutes)} icon={<Timer size={20} />} />
            <Metric title="实际执行" value={minutesLabel(stats.actualMinutes)} icon={<CheckCircle2 size={20} />} />
            <Metric title="完成率" value={`${stats.completionRate}%`} icon={<Flame size={20} />} />
            <Metric title="需补科目" value={stats.laggingSubjectName} icon={<AlertTriangle size={20} />} tone="warn" />

            <section className="panel task-panel">
              <div className="panel-head">
                <h2>今日任务</h2>
                <div className="panel-actions">
                  <span className="pill">可直接用模板补任务</span>
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
                {todayTasks.map((task) => <TaskRow key={task.id} task={task} data={data} toggleTask={toggleTask} updateTaskMinutes={updateTaskMinutes} deleteTask={deleteTask} />)}
                {!todayTasks.length && <p className="empty">今天还没有任务，先加一个 45 分钟的小任务。</p>}
              </div>
            </section>

            <section className="panel">
              <div className="panel-head">
                <h2>今日复盘</h2>
                <div className="panel-actions">
                  <span className="pill">自动保存</span>
                  <button className="ghost compact-button" onClick={insertReviewTemplate}><ClipboardList size={16} />复盘模板</button>
                </div>
              </div>
              <textarea value={reviewText} onChange={(event) => saveReview(event.target.value)} placeholder="写一句：今天偏差最大的是哪科？明天第一件事是什么？" />
              <ClosureChecklist items={dailyClosureChecklist} />
              <div className="advice-stack">
                {ruleAdvice.map((item) => <div className="advice" key={item}>{item}</div>)}
              </div>
            </section>
          </section>
        )}

        {view === "plan" && (
          <section className="panel">
            <div className="panel-head">
              <h2>计划排布</h2>
              <span className="pill">可直接调整日期、科目和时长</span>
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
                <button className="ghost compact-button" onClick={copyPreviousWeekTasks}><Copy size={16} />复制上周</button>
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
          <section className="panel">
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
        )}

        {view === "coach" && (
          <section className="panel coach-panel">
            <div className="panel-head">
              <h2>AI 教练</h2>
              <button className="primary" onClick={askAiCoach} disabled={isAiLoading}><Sparkles size={18} />{isAiLoading ? "生成中..." : "生成明日建议"}</button>
            </div>
            <p className="subline">模型状态：{health?.llm_configured ? `已配置 ${health.model}` : "未配置，失败时使用本地规则建议"}</p>
            {aiStatus && <div className="notice">{aiStatus}</div>}
            <div className="advice-stack large">
              {(aiAdvice.length ? aiAdvice : ruleAdvice).map((item) => <div className="advice" key={item}>{item}</div>)}
            </div>
          </section>
        )}

        {view === "settings" && (
          <section className="panel settings-panel">
            <div className="panel-head">
              <h2>设置与数据</h2>
              <span className="pill">localStorage v{data.version}</span>
            </div>
            <div className="data-overview" aria-label="数据概览">
              <OverviewItem label="科目数" value={`${dataOverview.subjectCount}`} />
              <OverviewItem label="任务数" value={`${dataOverview.taskCount}`} />
              <OverviewItem label="已完成" value={`${dataOverview.doneTaskCount}`} />
              <OverviewItem label="复盘天数" value={`${dataOverview.reviewCount}`} />
              <OverviewItem label="最近任务" value={dataOverview.latestTaskDate} />
            </div>
            <section className="health-panel" aria-label="数据健康诊断">
              {dataHealth.map((item) => (
                <HealthItem
                  item={item}
                  key={item.id}
                  action={item.id === "overdue-tasks" ? { label: "整理到当前日期", onClick: resolveOverdueTasks } : undefined}
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
                <input type="password" value={apiForm.api_key} onChange={(event) => setApiForm((current) => ({ ...current, api_key: event.target.value }))} placeholder={health?.llm_configured ? "已保存，留空不会显示旧 Key" : "sk-..."} autoComplete="off" />
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
                <button className="primary" onClick={saveApiConfig} disabled={isApiSaving}><Sparkles size={18} />{isApiSaving ? "保存中..." : "保存 API 配置"}</button>
                <button className="ghost" onClick={testApiConfig} disabled={isApiTesting}><CheckCircle2 size={18} />{isApiTesting ? "测试中..." : "测试连接"}</button>
              </div>
              {apiSaveStatus && <div className="notice inline-notice">{apiSaveStatus}</div>}
              {apiTestStatus && <div className="notice inline-notice">{apiTestStatus}</div>}
              <p className="hint">API Key 会发送到本地后端保存，不写入浏览器 localStorage，也不会回显。</p>
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
              <button className="ghost" onClick={downloadData}><Download size={18} />导出 JSON</button>
              <label className="ghost file-button"><Import size={18} />导入 JSON<input type="file" accept="application/json" onChange={importData} /></label>
              <button className="danger" onClick={resetData}><RefreshCw size={18} />重置示例数据</button>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

function Metric({ title, value, icon, tone }: { title: string; value: string; icon: React.ReactNode; tone?: "warn" }) {
  return (
    <section className={`metric ${tone ?? ""}`}>
      <span>{icon}{title}</span>
      <strong>{value}</strong>
    </section>
  );
}

function OverviewItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="overview-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function HealthItem({ item, action }: { item: DataHealthItem; action?: { label: string; onClick: () => void } }) {
  return (
    <article className={`health-item ${item.tone}`}>
      <span>{item.tone === "warn" ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}</span>
      <div>
        <strong>{item.title}</strong>
        <em>{item.detail}</em>
        {action && <button className="mini-action" onClick={action.onClick}>{action.label}</button>}
      </div>
    </article>
  );
}

function ClosureChecklist({ items }: { items: DailyClosureItem[] }) {
  return (
    <section className="closure-checklist" aria-label="每日收尾检查">
      {items.map((item) => (
        <article className={`closure-item ${item.done ? "done" : ""}`} key={item.id}>
          <span>{item.done ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}</span>
          <div>
            <strong>{item.title}</strong>
            <em>{item.detail}</em>
          </div>
        </article>
      ))}
    </section>
  );
}

function WeekPlanBoard({ weekOverview, selectedDate, setSelectedDate }: {
  weekOverview: WeekDayOverview[];
  selectedDate: string;
  setSelectedDate: React.Dispatch<React.SetStateAction<string>>;
}) {
  return (
    <section className="week-board" aria-label="本周计划">
      {weekOverview.map((day, index) => (
        <button
          key={day.date}
          className={`week-day ${day.date === selectedDate ? "active" : ""}`}
          onClick={() => setSelectedDate(day.date)}
          title="切换当前日期"
        >
          <span>{weekdayLabels[index]}</span>
          <strong>{day.date.slice(5)}</strong>
          <i>{minutesLabel(day.plannedMinutes)} / {minutesLabel(day.actualMinutes)}</i>
          <em>{day.doneTasks}/{day.totalTasks} 完成 · {day.completionRate}%</em>
        </button>
      ))}
    </section>
  );
}

const weeklyLoadLabels: Record<SubjectWeeklyLoad["status"], string> = {
  empty: "未排",
  light: "偏少",
  balanced: "合适",
  over: "超载"
};

function WeeklyLoadStrip({ weeklyLoad }: { weeklyLoad: SubjectWeeklyLoad[] }) {
  return (
    <section className="weekly-load-strip" aria-label="本周容量">
      <div className="load-strip-head"><Gauge size={16} /><strong>本周容量</strong></div>
      {weeklyLoad.map((item) => (
        <article className={`load-chip ${item.status}`} key={item.subject.id}>
          <div>
            <span style={{ color: item.subject.color }}>{item.subject.name}</span>
            <strong>{minutesLabel(item.plannedMinutes)} / {minutesLabel(item.targetMinutes)}</strong>
          </div>
          <div className="load-bar"><i style={{ width: `${Math.min(item.loadRate, 100)}%`, background: item.subject.color }} /></div>
          <em>{item.loadRate}% · {weeklyLoadLabels[item.status]}</em>
        </article>
      ))}
    </section>
  );
}

function WeeklyAdjustmentPanel({ tips, canAddStudyBlock, canRelieveHeavyDay, onAddStudyBlock, onRelieveHeavyDay }: {
  tips: WeeklyAdjustmentTip[];
  canAddStudyBlock: boolean;
  canRelieveHeavyDay: boolean;
  onAddStudyBlock: () => void;
  onRelieveHeavyDay: () => void;
}) {
  return (
    <section className="weekly-adjustments" aria-label="本周调整建议">
      <div className="adjustment-head">
        <Sparkles size={16} />
        <strong>本周调整建议</strong>
        <div className="adjustment-actions">
          <button className="mini-action" onClick={onAddStudyBlock} disabled={!canAddStudyBlock} title="给偏少科目补一个 60 分钟基础块">
            <Plus size={14} />一键补块
          </button>
          <button className="mini-action" onClick={onRelieveHeavyDay} disabled={!canRelieveHeavyDay} title="自动推后一个低优先级未完成任务">
            <ArrowRight size={14} />一键减负
          </button>
        </div>
      </div>
      <div className="adjustment-grid">
        {tips.map((tip) => (
          <article className={`adjustment-tip ${tip.tone}`} key={tip.id}>
            <strong>{tip.title}</strong>
            <span>{tip.detail}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

function TaskCreator({ data, newTask, setNewTask, addTask }: {
  data: AppData;
  newTask: { title: string; subjectId: string; estimatedMinutes: number; priority: StudyTask["priority"] };
  setNewTask: React.Dispatch<React.SetStateAction<{ title: string; subjectId: string; estimatedMinutes: number; priority: StudyTask["priority"] }>>;
  addTask: () => void;
}) {
  return (
    <div className="task-creator">
      <input value={newTask.title} onChange={(event) => setNewTask((current) => ({ ...current, title: event.target.value }))} onKeyDown={(event) => event.key === "Enter" && addTask()} placeholder="新增任务，例如：英语阅读 Text 1 精读" />
      <select value={newTask.subjectId} onChange={(event) => setNewTask((current) => ({ ...current, subjectId: event.target.value }))}>
        <option value="">默认科目</option>
        {data.subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
      </select>
      <input type="number" min="10" step="5" value={newTask.estimatedMinutes} onChange={(event) => setNewTask((current) => ({ ...current, estimatedMinutes: Number(event.target.value) }))} />
      <select value={newTask.priority} onChange={(event) => setNewTask((current) => ({ ...current, priority: event.target.value as StudyTask["priority"] }))} title="优先级">
        <option value="高">高优先级</option>
        <option value="中">中优先级</option>
        <option value="低">低优先级</option>
      </select>
    </div>
  );
}

function PlanTaskRow({ task, data, updateTask, deleteTask }: {
  task: StudyTask;
  data: AppData;
  updateTask: (taskId: string, patch: Partial<StudyTask>) => void;
  deleteTask: (taskId: string) => void;
}) {
  const subject = data.subjects.find((item) => item.id === task.subjectId);
  return (
    <article className="plan-edit-row">
      <span className="subject-dot" style={{ background: subject?.color }} />
      <input value={task.title} onChange={(event) => updateTask(task.id, { title: event.target.value })} title="任务标题" />
      <input type="date" value={task.date} onChange={(event) => updateTask(task.id, { date: event.target.value })} title="计划日期" />
      <select value={task.subjectId} onChange={(event) => updateTask(task.id, { subjectId: event.target.value })} title="科目">
        {data.subjects.map((subjectItem) => <option key={subjectItem.id} value={subjectItem.id}>{subjectItem.name}</option>)}
      </select>
      <input type="number" min="10" step="5" value={task.estimatedMinutes} onChange={(event) => updateTask(task.id, { estimatedMinutes: Number(event.target.value) || 10 })} title="预计分钟" />
      <select value={task.priority} onChange={(event) => updateTask(task.id, { priority: event.target.value as StudyTask["priority"] })} title="优先级">
        <option value="高">高</option>
        <option value="中">中</option>
        <option value="低">低</option>
      </select>
      <select value={task.status} onChange={(event) => {
        const status = event.target.value as StudyTask["status"];
        updateTask(task.id, { status, actualMinutes: status === "done" ? task.actualMinutes || task.estimatedMinutes : task.actualMinutes });
      }} title="状态">
        <option value="todo">待完成</option>
        <option value="done">已完成</option>
      </select>
      <button className="icon-button subtle" onClick={() => deleteTask(task.id)} title="删除任务"><Trash2 size={16} /></button>
    </article>
  );
}

function TaskRow({ task, data, toggleTask, updateTaskMinutes, deleteTask, compact }: {
  task: StudyTask;
  data: AppData;
  toggleTask: (taskId: string) => void;
  updateTaskMinutes: (taskId: string, actualMinutes: number) => void;
  deleteTask: (taskId: string) => void;
  compact?: boolean;
}) {
  const subject = data.subjects.find((item) => item.id === task.subjectId);
  return (
    <article className={`task-row ${task.status === "done" ? "done" : ""}`}>
      <button className="check" onClick={() => toggleTask(task.id)} title="切换完成状态">{task.status === "done" ? <CheckCircle2 size={18} /> : null}</button>
      <div className="task-main">
        <strong>{task.title}</strong>
        <span><i style={{ background: subject?.color }} />{subject?.name ?? "未分组"} · {task.date} · 预计 {minutesLabel(task.estimatedMinutes)} · {task.priority}优先级</span>
      </div>
      {!compact && <input type="number" min="0" step="5" value={task.actualMinutes} onChange={(event) => updateTaskMinutes(task.id, Number(event.target.value))} title="实际分钟" />}
      <button className="icon-button subtle" onClick={() => deleteTask(task.id)} title="删除任务"><Trash2 size={16} /></button>
    </article>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
