export type SubjectName = "数学" | "英语" | "政治" | "专业课";

export type Subject = {
  id: string;
  name: SubjectName | string;
  color: string;
  weeklyTargetHours: number;
};

export type StudyTask = {
  id: string;
  subjectId: string;
  title: string;
  date: string;
  estimatedMinutes: number;
  actualMinutes: number;
  priority: "高" | "中" | "低";
  status: "todo" | "done";
};

export type DayReview = {
  date: string;
  text: string;
};

export type AppData = {
  version: 1;
  examDate: string;
  subjects: Subject[];
  tasks: StudyTask[];
  reviews: DayReview[];
};

export type DashboardStats = {
  plannedMinutes: number;
  actualMinutes: number;
  completionRate: number;
  laggingSubjectName: string;
};

export type DailyClosureItem = {
  id: "review" | "actual-time" | "tomorrow-plan";
  title: string;
  done: boolean;
  detail: string;
};

export type SubjectProgress = {
  subject: Subject;
  plannedMinutes: number;
  actualMinutes: number;
  completionRate: number;
};

export type SubjectWeeklyLoad = {
  subject: Subject;
  plannedMinutes: number;
  targetMinutes: number;
  loadRate: number;
  status: "empty" | "light" | "balanced" | "over";
};

export type WeeklyAdjustmentTip = {
  id: string;
  tone: "warn" | "balance" | "steady";
  title: string;
  detail: string;
};

export type WeekDayOverview = {
  date: string;
  plannedMinutes: number;
  actualMinutes: number;
  totalTasks: number;
  doneTasks: number;
  completionRate: number;
};

/** 热力图单日：实际学习为主，专注分钟为辅 */
export type HeatmapDay = {
  date: string;
  actualMinutes: number;
  plannedMinutes: number;
  focusMinutes: number;
  taskCount: number;
  doneTasks: number;
  hasReview: boolean;
  /** 0 空 / 1 少 / 2 中 / 3 多 / 4 很满 */
  level: 0 | 1 | 2 | 3 | 4;
};

export type StudyHeatmap = {
  days: HeatmapDay[];
  /** 按周分组，每周 7 天（周一→周日） */
  weeks: HeatmapDay[][];
  startDate: string;
  endDate: string;
  weekCount: number;
  totalActualMinutes: number;
  activeDays: number;
  /** 截止 endDate 的当前连续学习天数（actualMinutes > 0） */
  currentStreak: number;
  /** 窗口内最长连续学习天数 */
  bestStreak: number;
};

export type PlanScope = "week" | "all";

export type PlanTaskFilters = {
  scope: PlanScope;
  subjectId?: string;
  priority?: StudyTask["priority"] | "all";
  status?: StudyTask["status"] | "all";
  query?: string;
};

export type RolloverResult = {
  data: AppData;
  movedCount: number;
  targetDate: string;
};

export type TomorrowPlanResult = RolloverResult & {
  tomorrowTaskCount: number;
};

export type TaskShiftResult = {
  data: AppData;
  movedCount: number;
};

export type DayReliefResult = {
  data: AppData;
  movedCount: number;
  sourceDate?: string;
  targetDate?: string;
  taskId?: string;
  taskTitle?: string;
};

export type StudyBlockResult = {
  data: AppData;
  addedCount: number;
  subjectId?: string;
  subjectName?: string;
  date?: string;
  taskId?: string;
};

export type TaskUpdateResult = {
  data: AppData;
  updatedCount: number;
};

export type OverdueResolveResult = {
  data: AppData;
  movedCount: number;
  createdCount: number;
  targetDate: string;
};

export type WeekCopyResult = {
  data: AppData;
  copiedCount: number;
  sourceWeekStart: string;
  targetWeekStart: string;
};

export type DailyClosureResult = {
  data: AppData;
  reviewFilled: boolean;
  filledActualCount: number;
  movedCount: number;
  targetDate: string;
  tomorrowTaskCount: number;
  checklist: DailyClosureItem[];
};

export type WeeklyReport = {
  weekStart: string;
  weekEnd: string;
  totalTasks: number;
  doneTasks: number;
  completionRate: number;
  plannedMinutes: number;
  actualMinutes: number;
  executionRate: number;
  reviewDays: number;
  overdueCarryCount: number;
  strongestSubjectName: string;
  weakestSubjectName: string;
  subjectLines: string[];
  tipLines: string[];
  nextWeekFocus: string[];
  markdown: string;
};

export type DataOverview = {
  subjectCount: number;
  taskCount: number;
  doneTaskCount: number;
  reviewCount: number;
  latestTaskDate: string;
};

export type DataHealthItem = {
  id: "overdue-tasks" | "review-gap" | "future-plan-gap" | "steady";
  tone: "warn" | "balance" | "steady";
  title: string;
  detail: string;
  count: number;
};

const subjectSeeds: Array<Omit<Subject, "id">> = [
  { name: "数学", color: "#6f82ff", weeklyTargetHours: 14 },
  { name: "英语", color: "#39d6a3", weeklyTargetHours: 8 },
  { name: "政治", color: "#ffb547", weeklyTargetHours: 6 },
  { name: "专业课", color: "#b45cff", weeklyTargetHours: 12 }
];

const taskSeeds: Array<Omit<StudyTask, "id" | "subjectId" | "date" | "actualMinutes" | "status"> & { subject: SubjectName; offset: number }> = [
  { subject: "数学", title: "高数强化：极限与导数题组", estimatedMinutes: 120, priority: "高", offset: 0 },
  { subject: "英语", title: "阅读精读：长难句拆解", estimatedMinutes: 60, priority: "中", offset: 0 },
  { subject: "专业课", title: "专业课教材：核心章节梳理", estimatedMinutes: 90, priority: "高", offset: 0 },
  { subject: "政治", title: "政治选择题：基础概念回顾", estimatedMinutes: 45, priority: "低", offset: 0 },
  { subject: "数学", title: "线代题组：矩阵与秩", estimatedMinutes: 90, priority: "中", offset: 1 },
  { subject: "英语", title: "单词复习：高频词 + 真题例句", estimatedMinutes: 40, priority: "中", offset: 1 },
  { subject: "专业课", title: "专业课真题：一套小题训练", estimatedMinutes: 100, priority: "高", offset: 1 },
  { subject: "政治", title: "政治精讲：马原框架", estimatedMinutes: 50, priority: "中", offset: 2 },
  { subject: "数学", title: "概率论错题：条件概率与分布", estimatedMinutes: 75, priority: "中", offset: 2 },
  { subject: "专业课", title: "专业课错题复盘：薄弱点整理", estimatedMinutes: 80, priority: "高", offset: 2 }
];

function pad(value: number) {
  return value.toString().padStart(2, "0");
}

function parseDate(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, (month || 1) - 1, day || 1);
}

export function formatDate(date = new Date()) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

export function uid(prefix: string) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function createDefaultData(): AppData {
  const today = new Date();
  const subjects = subjectSeeds.map((subject, index) => ({
    ...subject,
    id: `subject-${index + 1}`
  }));
  const subjectByName = new Map(subjects.map((subject) => [subject.name, subject.id]));

  return {
    version: 1,
    examDate: formatDate(addDays(today, 180)),
    subjects,
    tasks: taskSeeds.map((task, index) => ({
      id: `task-${index + 1}`,
      subjectId: subjectByName.get(task.subject)!,
      title: task.title,
      date: formatDate(addDays(today, task.offset)),
      estimatedMinutes: task.estimatedMinutes,
      actualMinutes: 0,
      priority: task.priority,
      status: "todo"
    })),
    reviews: []
  };
}

export function getTasksForDate(data: AppData, date: string) {
  return data.tasks.filter((task) => task.date === date);
}

export function getDataOverview(data: AppData): DataOverview {
  return {
    subjectCount: data.subjects.length,
    taskCount: data.tasks.length,
    doneTaskCount: data.tasks.filter((task) => task.status === "done").length,
    reviewCount: data.reviews.length,
    latestTaskDate: data.tasks.map((task) => task.date).sort((a, b) => b.localeCompare(a))[0] ?? "暂无"
  };
}

export function countOverdueTasks(data: AppData, date = formatDate()) {
  return data.tasks.filter((task) => task.date < date && task.status !== "done").length;
}

export function getDataHealth(data: AppData, date = formatDate()): DataHealthItem[] {
  const health: DataHealthItem[] = [];
  const overdueTasks = data.tasks.filter((task) => task.date < date && task.status !== "done");
  const futureTasks = data.tasks.filter((task) => task.date > date);
  const recentReviewDates = new Set(
    Array.from({ length: 3 }, (_, index) => formatDate(addDays(parseDate(date), -index)))
  );
  const recentReviewCount = data.reviews.filter((review) => recentReviewDates.has(review.date) && review.text.trim().length >= 8).length;

  if (overdueTasks.length) {
    health.push({
      id: "overdue-tasks",
      tone: "warn",
      title: "有逾期未完成任务",
      detail: `还有 ${overdueTasks.length} 个今天以前的任务未完成，建议先顺延或拆成更小的补救块。`,
      count: overdueTasks.length
    });
  }

  if (data.tasks.length > 0 && recentReviewCount === 0) {
    health.push({
      id: "review-gap",
      tone: "balance",
      title: "最近复盘偏少",
      detail: "最近 3 天还没有有效复盘，建议今晚补一句偏差原因和明天第一件事。",
      count: recentReviewCount
    });
  }

  if (futureTasks.length === 0) {
    health.push({
      id: "future-plan-gap",
      tone: "balance",
      title: "未来计划断档",
      detail: "今天之后还没有任务，建议至少排好明天的主科、英语和复盘块。",
      count: futureTasks.length
    });
  }

  if (!health.length) {
    health.push({
      id: "steady",
      tone: "steady",
      title: "数据状态稳定",
      detail: "没有发现明显逾期、复盘断档或未来计划缺口，可以继续按当前节奏推进。",
      count: 0
    });
  }

  return health;
}

function subjectName(data: AppData, subjectId: string) {
  return data.subjects.find((subject) => subject.id === subjectId)?.name ?? "未分组";
}

export function getTodayStats(data: AppData, date: string): DashboardStats {
  const tasks = getTasksForDate(data, date);
  const plannedMinutes = tasks.reduce((sum, task) => sum + task.estimatedMinutes, 0);
  const actualMinutes = tasks.reduce((sum, task) => sum + task.actualMinutes, 0);
  const completionRate = tasks.length ? Math.round((tasks.filter((task) => task.status === "done").length / tasks.length) * 100) : 0;
  const laggingBySubject = new Map<string, number>();
  for (const task of tasks) {
    laggingBySubject.set(task.subjectId, (laggingBySubject.get(task.subjectId) ?? 0) + Math.max(task.estimatedMinutes - task.actualMinutes, 0));
  }
  const laggingSubjectId = [...laggingBySubject.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "";

  return {
    plannedMinutes,
    actualMinutes,
    completionRate,
    laggingSubjectName: laggingSubjectId ? subjectName(data, laggingSubjectId) : "暂无"
  };
}

export function buildReviewTemplate(data: AppData, date: string) {
  const stats = getTodayStats(data, date);
  const firstTask = getTasksForDate(data, date)
    .filter((task) => task.status !== "done")
    .sort((a, b) => priorityWeight[b.priority] - priorityWeight[a.priority] || b.estimatedMinutes - a.estimatedMinutes)[0];

  return [
    `今日完成率：${stats.completionRate}%`,
    `计划/执行：${minutesText(stats.plannedMinutes)} / ${minutesText(stats.actualMinutes)}`,
    `需补科目：${stats.laggingSubjectName}`,
    `明天第一件事：${firstTask?.title ?? "保持当前节奏，先做最重要的一块"}`,
    "一句复盘：今天偏差最大的原因是____，明天我先____。"
  ].join("\n");
}

export function getDailyClosureChecklist(data: AppData, date: string): DailyClosureItem[] {
  const tasks = getTasksForDate(data, date);
  const review = data.reviews.find((item) => item.date === date)?.text.trim() ?? "";
  const tomorrow = formatDate(addDays(parseDate(date), 1));
  const tomorrowTaskCount = getTasksForDate(data, tomorrow).length;
  const actualTimeReady = tasks.length > 0 && tasks.every((task) => task.status === "done" || task.actualMinutes > 0);

  return [
    {
      id: "review",
      title: "写完复盘",
      done: review.length >= 8,
      detail: review.length >= 8 ? "复盘已记录，可以留下今天的真实线索。" : "补一句偏差原因和明天第一件事。"
    },
    {
      id: "actual-time",
      title: "记录实际时长",
      done: actualTimeReady,
      detail: actualTimeReady ? "今日任务都有执行记录。" : "给做过的任务补上实际分钟数。"
    },
    {
      id: "tomorrow-plan",
      title: "准备明日任务",
      done: tomorrowTaskCount > 0,
      detail: tomorrowTaskCount > 0 ? `明天已有 ${tomorrowTaskCount} 个任务。` : "点击明日开局或手动加一个明天任务。"
    }
  ];
}

export function getSubjectProgress(data: AppData, days = 7, endDate = formatDate()): SubjectProgress[] {
  const start = parseDate(endDate);
  start.setDate(start.getDate() - (days - 1));
  const activeDates = new Set(Array.from({ length: days }, (_, index) => formatDate(addDays(start, index))));

  return data.subjects.map((subject) => {
    const tasks = data.tasks.filter((task) => task.subjectId === subject.id && activeDates.has(task.date));
    const plannedMinutes = tasks.reduce((sum, task) => sum + task.estimatedMinutes, 0);
    const actualMinutes = tasks.reduce((sum, task) => sum + task.actualMinutes, 0);
    return {
      subject,
      plannedMinutes,
      actualMinutes,
      completionRate: plannedMinutes ? Math.round((actualMinutes / plannedMinutes) * 100) : 0
    };
  });
}

export function resolveSubjectIdByKeywords(data: AppData, subjectKeywords: string[], fallbackIndex: number) {
  const keywords = subjectKeywords.map((keyword) => keyword.trim()).filter((keyword) => keyword.length >= 2);
  const exact = data.subjects.find((subject) => keywords.some((keyword) => subject.name === keyword));
  if (exact) return exact.id;

  const partial = data.subjects.find((subject) => keywords.some((keyword) => subject.name.includes(keyword) || keyword.includes(subject.name)));
  return partial?.id ?? data.subjects[fallbackIndex]?.id ?? data.subjects[0]?.id ?? "";
}

export function getWeekStart(date: string) {
  const current = parseDate(date);
  const day = current.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  return formatDate(addDays(current, mondayOffset));
}

export function getWeekOverview(data: AppData, selectedDate = formatDate()): WeekDayOverview[] {
  const start = parseDate(getWeekStart(selectedDate));
  return Array.from({ length: 7 }, (_, index) => {
    const date = formatDate(addDays(start, index));
    const tasks = getTasksForDate(data, date);
    const plannedMinutes = tasks.reduce((sum, task) => sum + task.estimatedMinutes, 0);
    const actualMinutes = tasks.reduce((sum, task) => sum + task.actualMinutes, 0);
    const doneTasks = tasks.filter((task) => task.status === "done").length;
    return {
      date,
      plannedMinutes,
      actualMinutes,
      totalTasks: tasks.length,
      doneTasks,
      completionRate: tasks.length ? Math.round((doneTasks / tasks.length) * 100) : 0
    };
  });
}

/** 按任务实际时长映射热力等级（约：1h / 2h / 4h 分档） */
export function getHeatmapLevel(actualMinutes: number): HeatmapDay["level"] {
  if (actualMinutes <= 0) return 0;
  if (actualMinutes < 60) return 1;
  if (actualMinutes < 120) return 2;
  if (actualMinutes < 240) return 3;
  return 4;
}

function countStreaks(days: HeatmapDay[], endDate: string) {
  let bestStreak = 0;
  let run = 0;
  for (const day of days) {
    if (day.actualMinutes > 0) {
      run += 1;
      bestStreak = Math.max(bestStreak, run);
    } else {
      run = 0;
    }
  }

  let currentStreak = 0;
  for (let index = days.length - 1; index >= 0; index -= 1) {
    const day = days[index];
    if (day.date > endDate) continue;
    if (day.actualMinutes > 0) currentStreak += 1;
    else break;
  }

  return { bestStreak, currentStreak };
}

/**
 * 学习热力日历：以 selectedDate 所在周为终点，向前 weekCount 周（周一至周日）。
 * focusMinutesByDate 可选，来自计时器专注统计。
 */
export function buildStudyHeatmap(
  data: AppData,
  endDate = formatDate(),
  weekCount = 12,
  focusMinutesByDate: Record<string, number> = {}
): StudyHeatmap {
  const weeks = Math.max(1, Math.min(26, Math.round(weekCount) || 12));
  const endWeekStart = getWeekStart(endDate);
  const startDate = formatDate(addDays(parseDate(endWeekStart), -(weeks - 1) * 7));
  const totalDays = weeks * 7;
  const reviewDates = new Set(
    data.reviews.filter((review) => review.text.trim().length >= 8).map((review) => review.date)
  );

  const days: HeatmapDay[] = Array.from({ length: totalDays }, (_, index) => {
    const date = formatDate(addDays(parseDate(startDate), index));
    const tasks = getTasksForDate(data, date);
    const plannedMinutes = tasks.reduce((sum, task) => sum + task.estimatedMinutes, 0);
    const actualMinutes = tasks.reduce((sum, task) => sum + task.actualMinutes, 0);
    const doneTasks = tasks.filter((task) => task.status === "done").length;
    const focusMinutes = Math.max(0, Math.round(focusMinutesByDate[date] ?? 0));
    return {
      date,
      actualMinutes,
      plannedMinutes,
      focusMinutes,
      taskCount: tasks.length,
      doneTasks,
      hasReview: reviewDates.has(date),
      level: getHeatmapLevel(actualMinutes)
    };
  });

  const weekColumns: HeatmapDay[][] = [];
  for (let week = 0; week < weeks; week += 1) {
    weekColumns.push(days.slice(week * 7, week * 7 + 7));
  }

  const totalActualMinutes = days.reduce((sum, day) => sum + day.actualMinutes, 0);
  const activeDays = days.filter((day) => day.actualMinutes > 0).length;
  const { bestStreak, currentStreak } = countStreaks(days, endDate);

  return {
    days,
    weeks: weekColumns,
    startDate,
    endDate: formatDate(addDays(parseDate(startDate), totalDays - 1)),
    weekCount: weeks,
    totalActualMinutes,
    activeDays,
    currentStreak,
    bestStreak
  };
}

export function getTasksForWeek(data: AppData, selectedDate = formatDate()) {
  const weekDates = new Set(getWeekOverview(data, selectedDate).map((day) => day.date));
  return [...data.tasks]
    .filter((task) => weekDates.has(task.date))
    .sort((a, b) => a.date.localeCompare(b.date));
}

function taskCopySignature(task: Pick<StudyTask, "subjectId" | "date" | "title">) {
  return `${task.subjectId}::${task.date}::${task.title.trim()}`;
}

function minutesText(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest} 分钟`;
  if (!rest) return `${hours} 小时`;
  return `${hours} 小时 ${rest} 分钟`;
}

const priorityWeight: Record<StudyTask["priority"], number> = {
  "低": 0,
  "中": 1,
  "高": 2
};

export function copyWeekTasks(data: AppData, sourceDate: string, targetDate: string): WeekCopyResult {
  const sourceWeekStart = getWeekStart(sourceDate);
  const targetWeekStart = getWeekStart(targetDate);
  const sourceStart = parseDate(sourceWeekStart);
  const targetStart = parseDate(targetWeekStart);
  const existingSignatures = new Set(data.tasks.map(taskCopySignature));
  const copiedTasks: StudyTask[] = [];

  for (const task of getTasksForWeek(data, sourceDate)) {
    const dayOffset = Math.round((parseDate(task.date).getTime() - sourceStart.getTime()) / 86400000);
    const targetTask = {
      ...task,
      id: uid("task"),
      date: formatDate(addDays(targetStart, dayOffset)),
      actualMinutes: 0,
      status: "todo" as const
    };
    const signature = taskCopySignature(targetTask);
    if (existingSignatures.has(signature)) continue;
    existingSignatures.add(signature);
    copiedTasks.push(targetTask);
  }

  return {
    data: { ...data, tasks: [...data.tasks, ...copiedTasks] },
    copiedCount: copiedTasks.length,
    sourceWeekStart,
    targetWeekStart
  };
}

export function getSubjectWeeklyLoad(data: AppData, selectedDate = formatDate()): SubjectWeeklyLoad[] {
  const weekTasks = getTasksForWeek(data, selectedDate);
  return data.subjects.map((subject) => {
    const plannedMinutes = weekTasks
      .filter((task) => task.subjectId === subject.id)
      .reduce((sum, task) => sum + task.estimatedMinutes, 0);
    const targetMinutes = subject.weeklyTargetHours * 60;
    const loadRate = targetMinutes ? Math.round((plannedMinutes / targetMinutes) * 100) : 0;
    const status: SubjectWeeklyLoad["status"] = plannedMinutes === 0 ? "empty" : loadRate > 110 ? "over" : loadRate < 70 ? "light" : "balanced";
    return { subject, plannedMinutes, targetMinutes, loadRate, status };
  });
}

export function generateWeeklyAdjustmentTips(data: AppData, selectedDate = formatDate()): WeeklyAdjustmentTip[] {
  const tips: WeeklyAdjustmentTip[] = [];
  const weeklyLoad = getSubjectWeeklyLoad(data, selectedDate);

  for (const item of weeklyLoad.filter((load) => load.status === "over").sort((a, b) => b.loadRate - a.loadRate).slice(0, 2)) {
    tips.push({
      id: `over-${item.subject.id}`,
      tone: "warn",
      title: `${item.subject.name} 本周排得偏满`,
      detail: `${item.subject.name} 已排 ${minutesText(item.plannedMinutes)}，目标 ${minutesText(item.targetMinutes)}。建议移走 1 个低优先级任务，或把 ${minutesText(Math.max(item.plannedMinutes - item.targetMinutes, 30))} 拆到下周。`
    });
  }

  for (const item of weeklyLoad.filter((load) => load.status === "empty" || load.status === "light").sort((a, b) => a.loadRate - b.loadRate).slice(0, 2)) {
    const suggestedBlock = Math.min(Math.max(item.targetMinutes - item.plannedMinutes, 45), 90);
    tips.push({
      id: `light-${item.subject.id}`,
      tone: "balance",
      title: `${item.subject.name} 还需要补一块`,
      detail: `${item.subject.name} 本周目标 ${minutesText(item.targetMinutes)}，当前只排了 ${minutesText(item.plannedMinutes)}。建议补一个 ${minutesText(suggestedBlock)} 的基础块或错题复盘块。`
    });
  }

  for (const day of getWeekOverview(data, selectedDate).filter((item) => item.plannedMinutes >= 360).slice(0, 2)) {
    tips.push({
      id: `heavy-day-${day.date}`,
      tone: "warn",
      title: `${day.date} 单日计划偏重`,
      detail: `当天已排 ${minutesText(day.plannedMinutes)}，建议把一个低优先级任务提前或推后一天，给复盘和缓冲留空间。`
    });
  }

  if (!tips.length) {
    tips.push({
      id: "steady-week",
      tone: "steady",
      title: "本周节奏稳定",
      detail: "各科计划量接近目标。保持当前排布，优先保证每天最后 10 分钟完成复盘。"
    });
  }

  return tips.slice(0, 5);
}

export function buildWeeklyReport(data: AppData, selectedDate = formatDate()): WeeklyReport {
  const weekStart = getWeekStart(selectedDate);
  const weekEnd = formatDate(addDays(parseDate(weekStart), 6));
  const weekDates = new Set(getWeekOverview(data, selectedDate).map((day) => day.date));
  const weekTasks = getTasksForWeek(data, selectedDate);
  const totalTasks = weekTasks.length;
  const doneTasks = weekTasks.filter((task) => task.status === "done").length;
  const plannedMinutes = weekTasks.reduce((sum, task) => sum + task.estimatedMinutes, 0);
  const actualMinutes = weekTasks.reduce((sum, task) => sum + task.actualMinutes, 0);
  const completionRate = totalTasks ? Math.round((doneTasks / totalTasks) * 100) : 0;
  const executionRate = plannedMinutes ? Math.round((actualMinutes / plannedMinutes) * 100) : 0;
  const reviewDays = data.reviews.filter((review) => weekDates.has(review.date) && review.text.trim().length >= 8).length;
  const overdueCarryCount = data.tasks.filter((task) => task.date < weekStart && task.status !== "done").length;

  const subjectStats = data.subjects.map((subject) => {
    const tasks = weekTasks.filter((task) => task.subjectId === subject.id);
    const planned = tasks.reduce((sum, task) => sum + task.estimatedMinutes, 0);
    const actual = tasks.reduce((sum, task) => sum + task.actualMinutes, 0);
    const done = tasks.filter((task) => task.status === "done").length;
    const rate = planned ? Math.round((actual / planned) * 100) : 0;
    return { subject, planned, actual, done, total: tasks.length, rate };
  });

  const ranked = [...subjectStats].filter((item) => item.planned > 0).sort((a, b) => b.rate - a.rate);
  const strongestSubjectName = ranked[0]?.subject.name ?? "暂无";
  const weakestSubjectName = ranked.length ? ranked[ranked.length - 1].subject.name : "暂无";

  const subjectLines = subjectStats.map((item) => {
    if (!item.total) {
      return `- ${item.subject.name}：本周未排任务（周目标 ${item.subject.weeklyTargetHours} 小时）`;
    }
    return `- ${item.subject.name}：完成 ${item.done}/${item.total}，实际/计划 ${minutesText(item.actual)} / ${minutesText(item.planned)}（${item.rate}%），周目标 ${item.subject.weeklyTargetHours} 小时`;
  });

  const tips = generateWeeklyAdjustmentTips(data, selectedDate);
  const tipLines = tips.map((tip) => `- ${tip.title}：${tip.detail}`);

  const nextWeekFocus: string[] = [];
  if (weakestSubjectName !== "暂无") {
    nextWeekFocus.push(`优先补强 ${weakestSubjectName}：安排 2 个 45-60 分钟固定块，不要只排大而无当的任务。`);
  }
  if (reviewDays < 3) {
    nextWeekFocus.push("下周把复盘做成固定动作：每晚 5 分钟，写清偏差原因和次日第一件事。");
  } else {
    nextWeekFocus.push("复盘节奏不错，下周继续保留；可把复盘里反复出现的薄弱点升级成专项任务。");
  }
  if (overdueCarryCount > 0) {
    nextWeekFocus.push(`先清空 ${overdueCarryCount} 个历史未完成任务，再加新计划，避免旧债滚雪球。`);
  } else if (executionRate < 70 && plannedMinutes > 0) {
    nextWeekFocus.push("本周执行率偏低，下周总计划量先砍 15%-20%，保证完成率回升。");
  } else {
    nextWeekFocus.push("保持本周主科强度，另加 1 个错题/真题复盘块巩固成果。");
  }

  const markdown = [
    `# 考研周报（${weekStart} ~ ${weekEnd}）`,
    "",
    "## 总览",
    `- 任务完成：${doneTasks}/${totalTasks}（${completionRate}%）`,
    `- 时长执行：${minutesText(actualMinutes)} / ${minutesText(plannedMinutes)}（${executionRate}%）`,
    `- 有效复盘：${reviewDays}/7 天`,
    `- 历史未完成遗留：${overdueCarryCount} 个`,
    `- 相对更稳的科目：${strongestSubjectName}`,
    `- 相对偏弱的科目：${weakestSubjectName}`,
    "",
    "## 分科",
    ...subjectLines,
    "",
    "## 本周调整提示",
    ...tipLines,
    "",
    "## 下周三条重点",
    ...nextWeekFocus.map((line, index) => `${index + 1}. ${line}`),
    ""
  ].join("\n");

  return {
    weekStart,
    weekEnd,
    totalTasks,
    doneTasks,
    completionRate,
    plannedMinutes,
    actualMinutes,
    executionRate,
    reviewDays,
    overdueCarryCount,
    strongestSubjectName,
    weakestSubjectName,
    subjectLines,
    tipLines,
    nextWeekFocus,
    markdown
  };
}

export type AppendWeeklyReportResult = {
  data: AppData;
  report: WeeklyReport;
  date: string;
  appended: boolean;
  reason: "appended" | "already-present";
};

/** 把周报摘要写入指定日期的复盘（默认选中日），避免重复粘贴同一周 */
export function appendWeeklyReportToReview(
  data: AppData,
  selectedDate = formatDate(),
  report?: WeeklyReport
): AppendWeeklyReportResult {
  const weekly = report ?? buildWeeklyReport(data, selectedDate);
  const marker = `【周报 ${weekly.weekStart}`;
  const existing = data.reviews.find((review) => review.date === selectedDate)?.text.trim() ?? "";

  if (existing.includes(marker)) {
    return {
      data,
      report: weekly,
      date: selectedDate,
      appended: false,
      reason: "already-present"
    };
  }

  const block = [
    `${marker} ~ ${weekly.weekEnd}】`,
    `完成 ${weekly.doneTasks}/${weekly.totalTasks}（${weekly.completionRate}%）· 执行 ${minutesText(weekly.actualMinutes)} / ${minutesText(weekly.plannedMinutes)}（${weekly.executionRate}%）· 偏弱 ${weekly.weakestSubjectName}`,
    "下周三条重点：",
    ...weekly.nextWeekFocus.map((line, index) => `${index + 1}. ${line}`)
  ].join("\n");

  const text = existing ? `${existing}\n\n${block}` : block;
  return {
    data: {
      ...data,
      reviews: [
        ...data.reviews.filter((review) => review.date !== selectedDate),
        { date: selectedDate, text }
      ]
    },
    report: weekly,
    date: selectedDate,
    appended: true,
    reason: "appended"
  };
}

export function getPlanTasks(data: AppData, selectedDate = formatDate(), filters: PlanTaskFilters = { scope: "week" }) {
  const baseTasks = filters.scope === "week" ? getTasksForWeek(data, selectedDate) : [...data.tasks].sort((a, b) => a.date.localeCompare(b.date));
  const query = filters.query?.trim().toLowerCase() ?? "";
  return baseTasks.filter((task) => {
    const matchesSubject = !filters.subjectId || filters.subjectId === "all" || task.subjectId === filters.subjectId;
    const matchesPriority = !filters.priority || filters.priority === "all" || task.priority === filters.priority;
    const matchesStatus = !filters.status || filters.status === "all" || task.status === filters.status;
    const matchesQuery = !query || task.title.toLowerCase().includes(query);
    return matchesSubject && matchesPriority && matchesStatus && matchesQuery;
  });
}

export function rolloverUnfinishedTasks(data: AppData, sourceDate: string, targetDate = formatDate(addDays(parseDate(sourceDate), 1))): RolloverResult {
  const existingIds = new Set(data.tasks.map((task) => task.id));
  const carryTasks: StudyTask[] = [];
  let movedCount = 0;

  const tasks = data.tasks.map((task) => {
    if (task.date !== sourceDate || task.status === "done") return task;

    if (task.actualMinutes > 0) {
      const carryId = `${task.id}-carry-${targetDate}`;
      if (!existingIds.has(carryId)) {
        carryTasks.push({
          ...task,
          id: carryId,
          title: `续做：${task.title}`,
          date: targetDate,
          estimatedMinutes: Math.max(task.estimatedMinutes - task.actualMinutes, 10),
          actualMinutes: 0,
          status: "todo"
        });
        movedCount += 1;
      }
      return task;
    }

    movedCount += 1;
    return { ...task, date: targetDate, actualMinutes: 0 };
  });

  return {
    data: { ...data, tasks: [...tasks, ...carryTasks] },
    movedCount,
    targetDate
  };
}

export function prepareTomorrowPlan(data: AppData, sourceDate: string): TomorrowPlanResult {
  const result = rolloverUnfinishedTasks(data, sourceDate);
  return {
    ...result,
    tomorrowTaskCount: getTasksForDate(result.data, result.targetDate).length
  };
}

export function patchTaskActualMinutes(data: AppData, taskId: string, actualMinutes: number): AppData {
  const minutes = Math.max(0, Math.round(Number.isFinite(actualMinutes) ? actualMinutes : 0));
  return {
    ...data,
    tasks: data.tasks.map((task) =>
      task.id === taskId
        ? { ...task, actualMinutes: minutes, status: minutes > 0 ? task.status : "todo" }
        : task
    )
  };
}

export function bumpTaskActualMinutes(data: AppData, taskId: string, delta: number): AppData {
  const task = data.tasks.find((item) => item.id === taskId);
  if (!task) return data;
  return patchTaskActualMinutes(data, taskId, task.actualMinutes + delta);
}

export function fillTaskActualMinutes(data: AppData, taskId: string): AppData {
  const task = data.tasks.find((item) => item.id === taskId);
  if (!task) return data;
  return patchTaskActualMinutes(data, taskId, task.estimatedMinutes);
}

export function fillMissingDoneActualMinutes(data: AppData, date: string): { data: AppData; filledCount: number } {
  let filledCount = 0;
  const tasks = data.tasks.map((task) => {
    if (task.date !== date || task.status !== "done" || task.actualMinutes > 0) return task;
    filledCount += 1;
    return { ...task, actualMinutes: task.estimatedMinutes };
  });
  return { data: { ...data, tasks }, filledCount };
}

export function ensureReviewTemplate(data: AppData, date: string): { data: AppData; filled: boolean } {
  const existing = data.reviews.find((review) => review.date === date)?.text.trim() ?? "";
  if (existing.length >= 8) {
    return { data, filled: false };
  }

  const template = buildReviewTemplate(data, date);
  const text = existing ? `${existing}\n\n${template}` : template;
  return {
    data: {
      ...data,
      reviews: [...data.reviews.filter((review) => review.date !== date), { date, text }]
    },
    filled: true
  };
}

export function runDailyClosure(data: AppData, date: string): DailyClosureResult {
  const reviewResult = ensureReviewTemplate(data, date);
  const actualResult = fillMissingDoneActualMinutes(reviewResult.data, date);
  const tomorrow = prepareTomorrowPlan(actualResult.data, date);

  return {
    data: tomorrow.data,
    reviewFilled: reviewResult.filled,
    filledActualCount: actualResult.filledCount,
    movedCount: tomorrow.movedCount,
    targetDate: tomorrow.targetDate,
    tomorrowTaskCount: tomorrow.tomorrowTaskCount,
    checklist: getDailyClosureChecklist(tomorrow.data, date)
  };
}

export function resolveOverdueTasksToDate(data: AppData, targetDate = formatDate()): OverdueResolveResult {
  const existingIds = new Set(data.tasks.map((task) => task.id));
  const createdTasks: StudyTask[] = [];
  let movedCount = 0;

  const tasks = data.tasks.map((task) => {
    if (task.date >= targetDate || task.status === "done") return task;

    movedCount += 1;
    if (task.actualMinutes > 0) {
      const carryId = `${task.id}-overdue-${targetDate}`;
      if (!existingIds.has(carryId)) {
        existingIds.add(carryId);
        createdTasks.push({
          ...task,
          id: carryId,
          title: `续做：${task.title}`,
          date: targetDate,
          estimatedMinutes: Math.max(task.estimatedMinutes - task.actualMinutes, 10),
          actualMinutes: 0,
          status: "todo"
        });
      }
      return task;
    }

    return { ...task, date: targetDate, actualMinutes: 0 };
  });

  return {
    data: { ...data, tasks: [...tasks, ...createdTasks] },
    movedCount,
    createdCount: createdTasks.length,
    targetDate
  };
}

export function shiftTasksByIds(data: AppData, taskIds: string[], dayDelta: number): TaskShiftResult {
  const ids = new Set(taskIds);
  let movedCount = 0;
  const tasks = data.tasks.map((task) => {
    if (!ids.has(task.id) || dayDelta === 0) return task;
    movedCount += 1;
    return { ...task, date: formatDate(addDays(parseDate(task.date), dayDelta)) };
  });

  return {
    data: { ...data, tasks },
    movedCount
  };
}

export function relieveHeaviestDay(data: AppData, selectedDate = formatDate(), dailyLimitMinutes = 360): DayReliefResult {
  const heavyDay = getWeekOverview(data, selectedDate)
    .filter((day) => day.plannedMinutes >= dailyLimitMinutes)
    .sort((a, b) => b.plannedMinutes - a.plannedMinutes)[0];
  if (!heavyDay) return { data, movedCount: 0 };

  const candidate = data.tasks
    .filter((task) => task.date === heavyDay.date && task.status === "todo")
    .sort((a, b) => priorityWeight[a.priority] - priorityWeight[b.priority] || b.estimatedMinutes - a.estimatedMinutes)[0];
  if (!candidate) return { data, movedCount: 0, sourceDate: heavyDay.date };

  const targetDate = formatDate(addDays(parseDate(candidate.date), 1));
  const tasks = data.tasks.map((task) => task.id === candidate.id ? { ...task, date: targetDate } : task);
  return {
    data: { ...data, tasks },
    movedCount: 1,
    sourceDate: candidate.date,
    targetDate,
    taskId: candidate.id,
    taskTitle: candidate.title
  };
}

export function addLightSubjectStudyBlock(data: AppData, selectedDate = formatDate(), minutes = 60): StudyBlockResult {
  const lightSubject = getSubjectWeeklyLoad(data, selectedDate)
    .filter((item) => item.status === "empty" || item.status === "light")
    .sort((a, b) => a.loadRate - b.loadRate || (b.targetMinutes - b.plannedMinutes) - (a.targetMinutes - a.plannedMinutes))[0];
  if (!lightSubject) return { data, addedCount: 0 };

  const lightDay = getWeekOverview(data, selectedDate)
    .sort((a, b) => a.plannedMinutes - b.plannedMinutes || a.date.localeCompare(b.date))[0];
  if (!lightDay) return { data, addedCount: 0 };

  const task: StudyTask = {
    id: uid("task"),
    subjectId: lightSubject.subject.id,
    title: `${lightSubject.subject.name}基础巩固`,
    date: lightDay.date,
    estimatedMinutes: Math.max(minutes, 10),
    actualMinutes: 0,
    priority: "中",
    status: "todo"
  };

  return {
    data: { ...data, tasks: [...data.tasks, task] },
    addedCount: 1,
    subjectId: lightSubject.subject.id,
    subjectName: lightSubject.subject.name,
    date: lightDay.date,
    taskId: task.id
  };
}

export function updateTasksByIds(data: AppData, taskIds: string[], patch: Partial<StudyTask>): TaskUpdateResult {
  const ids = new Set(taskIds);
  let updatedCount = 0;
  const tasks = data.tasks.map((task) => {
    if (!ids.has(task.id)) return task;
    updatedCount += 1;
    const nextTask = { ...task, ...patch };
    if (patch.status === "done" && nextTask.actualMinutes <= 0) {
      nextTask.actualMinutes = nextTask.estimatedMinutes;
    }
    if (patch.status === "todo" && patch.actualMinutes === undefined) {
      nextTask.actualMinutes = task.actualMinutes;
    }
    return nextTask;
  });

  return {
    data: { ...data, tasks },
    updatedCount
  };
}

export type AdviceSectionId = "boost" | "cut" | "tomorrow";

export type AdviceSection = {
  id: AdviceSectionId;
  title: string;
  items: string[];
};

export type StructuredAdvice = {
  sections: AdviceSection[];
  flat: string[];
};

const ADVICE_SECTION_META: Array<{ id: AdviceSectionId; title: string; aliases: string[] }> = [
  { id: "boost", title: "补哪科", aliases: ["补哪科", "补强", "需补", "薄弱"] },
  { id: "cut", title: "砍哪块", aliases: ["砍哪块", "减负", "砍掉", "降载"] },
  { id: "tomorrow", title: "明日三件事", aliases: ["明日三件事", "明天三件事", "明日重点", "明天重点", "明日"] }
];

function emptyAdviceSections(): AdviceSection[] {
  return ADVICE_SECTION_META.map((meta) => ({ id: meta.id, title: meta.title, items: [] }));
}

export function flattenStructuredAdvice(advice: StructuredAdvice): string[] {
  if (advice.flat.length) return advice.flat;
  return advice.sections.flatMap((section) => section.items.map((item) => `【${section.title}】${item}`));
}

export function buildStructuredAdvice(sections: AdviceSection[]): StructuredAdvice {
  const normalized = emptyAdviceSections().map((empty) => {
    const found = sections.find((section) => section.id === empty.id);
    return {
      ...empty,
      items: (found?.items ?? []).map((item) => item.trim()).filter(Boolean).slice(0, 3)
    };
  });
  return {
    sections: normalized,
    flat: normalized.flatMap((section) => section.items.map((item) => `【${section.title}】${item}`))
  };
}

function matchAdviceSectionTitle(line: string): AdviceSectionId | null {
  const cleaned = line
    .replace(/^[#*\-\d.、\s]+/, "")
    .replace(/[【\[]/g, "")
    .replace(/[】\]]/g, "")
    .replace(/[:：\-]+$/g, "")
    .trim();
  for (const meta of ADVICE_SECTION_META) {
    if (meta.aliases.some((alias) => cleaned === alias || cleaned.startsWith(alias))) {
      return meta.id;
    }
  }
  return null;
}

function stripAdviceSectionPrefix(line: string): string {
  return line
    .replace(/^[#*\-\d.、\s]+/, "")
    .replace(/^[【\[]?\s*(补哪科|补强|需补|薄弱|砍哪块|减负|砍掉|降载|明日三件事|明天三件事|明日重点|明天重点|明日)\s*[】\]]?\s*[:：\-]?\s*/, "")
    .replace(/^\d+[.、)\s]+/, "")
    .trim();
}

export function parseStructuredAdvice(lines: string[]): StructuredAdvice {
  const buckets: Record<AdviceSectionId, string[]> = { boost: [], cut: [], tomorrow: [] };
  let current: AdviceSectionId | null = null;

  for (const raw of lines) {
    const line = raw.trim().replace(/^[-*•]\s*/, "");
    if (!line) continue;

    const tagged = line.match(/^【\s*(补哪科|砍哪块|明日三件事)\s*】\s*(.*)$/);
    if (tagged) {
      const id = matchAdviceSectionTitle(tagged[1]);
      if (id) {
        current = id;
        const rest = tagged[2].trim();
        if (rest) buckets[id].push(rest);
      }
      continue;
    }

    const sectionId = matchAdviceSectionTitle(line);
    if (sectionId) {
      current = sectionId;
      const rest = stripAdviceSectionPrefix(line);
      if (rest && !matchAdviceSectionTitle(rest)) {
        buckets[sectionId].push(rest);
      }
      continue;
    }

    const content = line.replace(/^\d+[.、)\s]+/, "").trim();
    if (!content) continue;
    if (current) {
      buckets[current].push(content);
    } else {
      buckets.tomorrow.push(content);
    }
  }

  const structured = buildStructuredAdvice([
    { id: "boost", title: "补哪科", items: buckets.boost },
    { id: "cut", title: "砍哪块", items: buckets.cut },
    { id: "tomorrow", title: "明日三件事", items: buckets.tomorrow }
  ]);

  // 若模型只回了扁平建议，至少保证明日区有内容
  if (!structured.sections.some((section) => section.items.length)) {
    return buildStructuredAdvice([
      { id: "tomorrow", title: "明日三件事", items: lines.map((line) => line.trim()).filter(Boolean).slice(0, 5) }
    ]);
  }
  return structured;
}

export function generateStructuredRuleAdvice(data: AppData, date: string): StructuredAdvice {
  const stats = getTodayStats(data, date);
  const todayTasks = getTasksForDate(data, date);
  const review = data.reviews.find((item) => item.date === date)?.text ?? "";
  const unfinished = todayTasks
    .filter((task) => task.status !== "done")
    .sort((a, b) => priorityWeight[b.priority] - priorityWeight[a.priority] || b.estimatedMinutes - a.estimatedMinutes);
  const subjectProgress = getSubjectProgress(data, 7, date);
  const weakest = subjectProgress.filter((item) => item.plannedMinutes > 0).sort((a, b) => a.completionRate - b.completionRate)[0];
  const lowPriorityOpen = unfinished.filter((task) => task.priority === "低");
  const boost: string[] = [];
  const cut: string[] = [];
  const tomorrow: string[] = [];

  const mentionedSubject = data.subjects.find((subject) => review.includes(subject.name));
  if (mentionedSubject) {
    boost.push(`复盘提到了 ${mentionedSubject.name}，明天把它放进黄金时间段。`);
  }
  if (weakest) {
    boost.push(`${weakest.subject.name} 近 7 天执行率 ${weakest.completionRate}%，明天给它留一个不被打断的 45-60 分钟固定块。`);
  }
  if (stats.laggingSubjectName && stats.laggingSubjectName !== "暂无" && stats.laggingSubjectName !== weakest?.subject.name && stats.laggingSubjectName !== mentionedSubject?.name) {
    boost.push(`今天缺口最大的是 ${stats.laggingSubjectName}，明天优先补这块，不要先做零碎杂事。`);
  } else if (stats.laggingSubjectName && stats.laggingSubjectName !== "暂无" && !boost.some((item) => item.includes(stats.laggingSubjectName))) {
    boost.push(`今天缺口最大的是 ${stats.laggingSubjectName}，明天优先补这块，不要先做零碎杂事。`);
  }
  if (!boost.length) {
    boost.push("各科暂时没有明显短板，明天保持主科强度，并加 20 分钟错题复盘。");
  }

  if (lowPriorityOpen.length) {
    cut.push(`先拿掉或推后低优先级「${lowPriorityOpen[0].title}」，给主科和补弱留位置。`);
  }
  if (stats.completionRate < 60 && unfinished.length >= 2) {
    cut.push(`今日完成率仅 ${stats.completionRate}%，明天总任务数压到 3 个以内，去掉可延后的大块。`);
  }
  if (/拖延|没做完|焦虑|很乱|效率低/.test(review)) {
    cut.push("复盘有拖延/低效信号：明天只保留 1 个高压任务，其余改成 30-45 分钟保底块。");
  }
  if (!cut.length) {
    cut.push("当前没有必须硬砍的块；若明天计划超过 6 小时，优先砍掉最低优先级的一项。");
  }

  if (!todayTasks.length) {
    tomorrow.push("先排 3 个最小任务：主科、英语、复盘各一个。");
  } else if (unfinished[0]) {
    tomorrow.push(`第一件事：完成或续做 ${subjectName(data, unfinished[0].subjectId)}「${unfinished[0].title}」。`);
  } else {
    tomorrow.push("第一件事：沿用今天节奏，先做最高优先级主科块。");
  }
  if (weakest) {
    tomorrow.push(`第二件事：${weakest.subject.name} 专项 45-60 分钟（可拆成两段）。`);
  } else {
    tomorrow.push("第二件事：主科错题/真题复盘 30-45 分钟。");
  }
  tomorrow.push("第三件事：晚上 5 分钟复盘——写清偏差科目和后天第一件事。");

  return buildStructuredAdvice([
    { id: "boost", title: "补哪科", items: boost.slice(0, 2) },
    { id: "cut", title: "砍哪块", items: cut.slice(0, 2) },
    { id: "tomorrow", title: "明日三件事", items: tomorrow.slice(0, 3) }
  ]);
}

export function generateRuleAdvice(data: AppData, date: string): string[] {
  return flattenStructuredAdvice(generateStructuredRuleAdvice(data, date));
}

export function buildCoachAdvicePayload(data: AppData, date: string) {
  const stats = getTodayStats(data, date);
  const todayTasks = getTasksForDate(data, date);
  const recentDates = Array.from({ length: 7 }, (_, index) => formatDate(addDays(parseDate(date), index - 6)));
  const recentTasks = data.tasks.filter((task) => recentDates.includes(task.date));
  const structured = generateStructuredRuleAdvice(data, date);

  return {
    date,
    today_stats: stats,
    today_tasks: todayTasks.map((task) => ({
      title: task.title,
      subject: subjectName(data, task.subjectId),
      estimatedMinutes: task.estimatedMinutes,
      actualMinutes: task.actualMinutes,
      priority: task.priority,
      status: task.status
    })),
    recent_subject_progress: getSubjectProgress(data, 7, date).map((item) => ({
      subject: item.subject.name,
      plannedMinutes: item.plannedMinutes,
      actualMinutes: item.actualMinutes,
      completionRate: item.completionRate
    })),
    review: data.reviews.find((item) => item.date === date)?.text ?? "",
    local_structured_advice: structured.sections,
    recent_task_count: recentTasks.length,
    output_format: [
      "请严格按下面三个小节输出，每节 1-3 条短句：",
      "【补哪科】",
      "【砍哪块】",
      "【明日三件事】"
    ].join("\n")
  };
}
