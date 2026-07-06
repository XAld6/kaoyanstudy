import { describe, expect, it } from "vitest";
import { addLightSubjectStudyBlock, buildReviewTemplate, copyWeekTasks, createDefaultData, formatDate, generateRuleAdvice, generateWeeklyAdjustmentTips, getDailyClosureChecklist, getDataHealth, getDataOverview, getPlanTasks, getSubjectProgress, getSubjectWeeklyLoad, getTasksForWeek, getTodayStats, getWeekOverview, prepareTomorrowPlan, relieveHeaviestDay, resolveOverdueTasksToDate, resolveSubjectIdByKeywords, rolloverUnfinishedTasks, shiftTasksByIds, updateTasksByIds } from "./studyCore";

describe("studyCore", () => {
  it("creates a useful default考研 data set", () => {
    const data = createDefaultData();

    expect(data.subjects.map((subject) => subject.name)).toEqual(["数学", "英语", "政治", "专业课"]);
    expect(data.tasks.length).toBeGreaterThanOrEqual(8);
    expect(data.examDate).not.toBe("");
  });

  it("calculates today's plan, actual time, completion rate and weakest subject", () => {
    const data = createDefaultData();
    const today = data.tasks[0].date;
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    data.tasks = [
      { id: "m1", subjectId: math.id, title: "高数强化", date: today, estimatedMinutes: 120, actualMinutes: 100, priority: "高", status: "done" },
      { id: "e1", subjectId: english.id, title: "阅读精读", date: today, estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" }
    ];

    const stats = getTodayStats(data, today);

    expect(stats.plannedMinutes).toBe(180);
    expect(stats.actualMinutes).toBe(100);
    expect(stats.completionRate).toBe(50);
    expect(stats.laggingSubjectName).toBe("英语");
  });

  it("generates local fallback advice when progress is behind", () => {
    const data = createDefaultData();
    const today = data.tasks[0].date;
    data.tasks = data.tasks.map((task) => task.date === today ? { ...task, status: "todo", actualMinutes: 0 } : task);
    data.reviews = [{ date: today, text: "今天有点拖延，英语阅读没有做完。" }];

    const advice = generateRuleAdvice(data, today);

    expect(advice.length).toBeGreaterThanOrEqual(3);
    expect(advice.join("")).toContain("英语");
  });

  it("builds a review template from today's completion and next first task", () => {
    const data = createDefaultData();
    const today = "2026-06-10";
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    data.tasks = [
      { id: "math", subjectId: math.id, title: "高数强化", date: today, estimatedMinutes: 120, actualMinutes: 120, priority: "高", status: "done" },
      { id: "english", subjectId: english.id, title: "阅读精读", date: today, estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" }
    ];

    const template = buildReviewTemplate(data, today);

    expect(template).toContain("今日完成率：50%");
    expect(template).toContain("需补科目：英语");
    expect(template).toContain("明天第一件事：阅读精读");
  });

  it("checks whether review, actual time and tomorrow plan are ready for daily closure", () => {
    const data = createDefaultData();
    const today = "2026-06-10";
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "done", subjectId: math.id, title: "已完成", date: today, estimatedMinutes: 60, actualMinutes: 60, priority: "高", status: "done" },
      { id: "todo", subjectId: math.id, title: "未记录", date: today, estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" }
    ];

    const openChecklist = getDailyClosureChecklist(data, today);
    expect(openChecklist.find((item) => item.id === "review")?.done).toBe(false);
    expect(openChecklist.find((item) => item.id === "actual-time")?.done).toBe(false);
    expect(openChecklist.find((item) => item.id === "tomorrow-plan")?.done).toBe(false);

    data.reviews = [{ date: today, text: "今天数学完成不错，明天先做英语阅读。" }];
    data.tasks = data.tasks.map((task) => task.id === "todo" ? { ...task, actualMinutes: 30 } : task);
    data.tasks.push({ id: "tomorrow", subjectId: math.id, title: "明日任务", date: "2026-06-11", estimatedMinutes: 45, actualMinutes: 0, priority: "中", status: "todo" });

    const closedChecklist = getDailyClosureChecklist(data, today);
    expect(closedChecklist.every((item) => item.done)).toBe(true);
  });

  it("summarizes data overview for settings and backups", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.subjects = [math];
    data.tasks = [
      { id: "old", subjectId: math.id, title: "旧任务", date: "2026-06-08", estimatedMinutes: 60, actualMinutes: 60, priority: "中", status: "done" },
      { id: "new", subjectId: math.id, title: "新任务", date: "2026-06-12", estimatedMinutes: 90, actualMinutes: 0, priority: "高", status: "todo" }
    ];
    data.reviews = [
      { date: "2026-06-08", text: "完成不错" },
      { date: "2026-06-12", text: "继续推进" }
    ];

    const overview = getDataOverview(data);

    expect(overview).toEqual({
      subjectCount: 1,
      taskCount: 2,
      doneTaskCount: 1,
      reviewCount: 2,
      latestTaskDate: "2026-06-12"
    });
  });

  it("detects overdue unfinished tasks and missing future plan", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "old-todo", subjectId: math.id, title: "昨日遗留", date: "2026-06-09", estimatedMinutes: 60, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "today-done", subjectId: math.id, title: "今日完成", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 60, priority: "中", status: "done" }
    ];
    data.reviews = [{ date: "2026-06-10", text: "今天完成稳定，明天继续推进数学。" }];

    const health = getDataHealth(data, "2026-06-10");

    expect(health.map((item) => item.id)).toEqual(["overdue-tasks", "future-plan-gap"]);
    expect(health[0]).toMatchObject({ tone: "warn", count: 1 });
    expect(health[1]).toMatchObject({ tone: "balance", count: 0 });
  });

  it("moves overdue unfinished tasks to the selected date without losing partial records", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "not-started", subjectId: math.id, title: "未开始旧任务", date: "2026-06-08", estimatedMinutes: 90, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "partial", subjectId: math.id, title: "部分完成旧任务", date: "2026-06-09", estimatedMinutes: 120, actualMinutes: 45, priority: "中", status: "todo" },
      { id: "done", subjectId: math.id, title: "已完成旧任务", date: "2026-06-08", estimatedMinutes: 60, actualMinutes: 60, priority: "低", status: "done" },
      { id: "future", subjectId: math.id, title: "未来任务", date: "2026-06-11", estimatedMinutes: 60, actualMinutes: 0, priority: "低", status: "todo" }
    ];

    const result = resolveOverdueTasksToDate(data, "2026-06-10");

    expect(result.movedCount).toBe(2);
    expect(result.createdCount).toBe(1);
    expect(result.data.tasks.find((task) => task.id === "not-started")).toMatchObject({ date: "2026-06-10", actualMinutes: 0, status: "todo" });
    expect(result.data.tasks.find((task) => task.id === "partial")).toMatchObject({ date: "2026-06-09", actualMinutes: 45, status: "todo" });
    expect(result.data.tasks.find((task) => task.id === "partial-overdue-2026-06-10")).toMatchObject({
      title: "续做：部分完成旧任务",
      date: "2026-06-10",
      estimatedMinutes: 75,
      actualMinutes: 0,
      status: "todo"
    });
    expect(result.data.tasks.find((task) => task.id === "done")?.date).toBe("2026-06-08");
    expect(result.data.tasks.find((task) => task.id === "future")?.date).toBe("2026-06-11");
    expect(data.tasks.find((task) => task.id === "not-started")?.date).toBe("2026-06-08");
  });

  it("includes custom subjects in progress calculations", () => {
    const data = createDefaultData();
    data.subjects.push({ id: "subject-custom", name: "408", color: "#22c55e", weeklyTargetHours: 10 });
    data.tasks.push({
      id: "task-custom",
      subjectId: "subject-custom",
      title: "408 数据结构真题",
      date: formatDate(),
      estimatedMinutes: 90,
      actualMinutes: 45,
      priority: "高",
      status: "todo"
    });

    const custom = getSubjectProgress(data).find((item) => item.subject.name === "408");

    expect(custom?.plannedMinutes).toBe(90);
    expect(custom?.completionRate).toBe(50);
  });

  it("calculates progress relative to the selected end date", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "old", subjectId: math.id, title: "旧任务", date: "2026-06-01", estimatedMinutes: 120, actualMinutes: 120, priority: "中", status: "done" },
      { id: "current", subjectId: math.id, title: "当前窗口任务", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 30, priority: "中", status: "todo" }
    ];

    const mathProgress = getSubjectProgress(data, 7, "2026-06-10").find((item) => item.subject.id === math.id);

    expect(mathProgress?.plannedMinutes).toBe(60);
    expect(mathProgress?.completionRate).toBe(50);
  });

  it("resolves subject template keywords without matching unrelated custom subjects first", () => {
    const data = createDefaultData();
    data.subjects = [
      { id: "subject-data-structure", name: "数据结构", color: "#22c55e", weeklyTargetHours: 10 },
      { id: "subject-math", name: "数学", color: "#6f82ff", weeklyTargetHours: 14 }
    ];

    const subjectId = resolveSubjectIdByKeywords(data, ["数学", "高数"], 0);

    expect(subjectId).toBe("subject-math");
  });

  it("generates progress advice relative to the selected date", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    data.tasks = [
      { id: "math-selected", subjectId: math.id, title: "高数强化", date: "2026-06-10", estimatedMinutes: 100, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "english-today", subjectId: english.id, title: "阅读复盘", date: formatDate(), estimatedMinutes: 100, actualMinutes: 100, priority: "中", status: "done" }
    ];

    const advice = generateRuleAdvice(data, "2026-06-10");

    expect(advice.some((item) => item.startsWith("数学 最近 7 天实际/计划为 0%"))).toBe(true);
  });

  it("summarizes a Monday-to-Sunday week around the selected date", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    data.tasks = [
      { id: "mon-math", subjectId: math.id, title: "周一数学", date: "2026-06-08", estimatedMinutes: 90, actualMinutes: 90, priority: "高", status: "done" },
      { id: "wed-english", subjectId: english.id, title: "周三英语", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 30, priority: "中", status: "todo" },
      { id: "next-week", subjectId: math.id, title: "下周任务", date: "2026-06-15", estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" }
    ];

    const week = getWeekOverview(data, "2026-06-10");

    expect(week.map((day) => day.date)).toEqual([
      "2026-06-08",
      "2026-06-09",
      "2026-06-10",
      "2026-06-11",
      "2026-06-12",
      "2026-06-13",
      "2026-06-14"
    ]);
    expect(week[0]).toMatchObject({ plannedMinutes: 90, actualMinutes: 90, totalTasks: 1, doneTasks: 1, completionRate: 100 });
    expect(week[2]).toMatchObject({ plannedMinutes: 60, actualMinutes: 30, totalTasks: 1, doneTasks: 0, completionRate: 0 });
  });

  it("returns only tasks in the selected Monday-to-Sunday week sorted by date", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "next-week", subjectId: math.id, title: "下周任务", date: "2026-06-15", estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "wed", subjectId: math.id, title: "周三任务", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" },
      { id: "last-week", subjectId: math.id, title: "上周任务", date: "2026-06-07", estimatedMinutes: 45, actualMinutes: 0, priority: "低", status: "todo" },
      { id: "mon", subjectId: math.id, title: "周一任务", date: "2026-06-08", estimatedMinutes: 90, actualMinutes: 90, priority: "高", status: "done" }
    ];

    const tasks = getTasksForWeek(data, "2026-06-10");

    expect(tasks.map((task) => task.id)).toEqual(["mon", "wed"]);
  });

  it("copies source week tasks into a target week without duplicating existing target tasks", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "source-mon", subjectId: math.id, title: "周一数学", date: "2026-06-01", estimatedMinutes: 90, actualMinutes: 90, priority: "高", status: "done" },
      { id: "source-wed", subjectId: math.id, title: "周三数学", date: "2026-06-03", estimatedMinutes: 60, actualMinutes: 20, priority: "中", status: "todo" },
      { id: "target-existing", subjectId: math.id, title: "周一数学", date: "2026-06-08", estimatedMinutes: 90, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "outside", subjectId: math.id, title: "下周之外", date: "2026-06-15", estimatedMinutes: 45, actualMinutes: 0, priority: "低", status: "todo" }
    ];

    const result = copyWeekTasks(data, "2026-06-03", "2026-06-10");

    expect(result.copiedCount).toBe(1);
    expect(result.targetWeekStart).toBe("2026-06-08");
    expect(result.data.tasks.filter((task) => task.subjectId === math.id && task.title === "周一数学" && task.date === "2026-06-08")).toHaveLength(1);
    expect(result.data.tasks.find((task) => task.id !== "source-wed" && task.title === "周三数学" && task.date === "2026-06-10")).toMatchObject({
      estimatedMinutes: 60,
      actualMinutes: 0,
      priority: "中",
      status: "todo"
    });
    expect(data.tasks).toHaveLength(4);
  });

  it("filters plan tasks by scope, subject, priority and status", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    data.tasks = [
      { id: "math-high-todo", subjectId: math.id, title: "数学本周高优先级", date: "2026-06-10", estimatedMinutes: 90, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "math-high-done", subjectId: math.id, title: "数学本周已完成", date: "2026-06-11", estimatedMinutes: 90, actualMinutes: 90, priority: "高", status: "done" },
      { id: "english-high-todo", subjectId: english.id, title: "英语本周高优先级", date: "2026-06-12", estimatedMinutes: 60, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "math-mid-todo", subjectId: math.id, title: "数学本周中优先级", date: "2026-06-13", estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" },
      { id: "math-next-week", subjectId: math.id, title: "数学下周高优先级", date: "2026-06-15", estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" }
    ];

    const weekFiltered = getPlanTasks(data, "2026-06-10", {
      scope: "week",
      subjectId: math.id,
      priority: "高",
      status: "todo"
    });
    const allFiltered = getPlanTasks(data, "2026-06-10", {
      scope: "all",
      subjectId: math.id,
      priority: "高",
      status: "todo"
    });

    expect(weekFiltered.map((task) => task.id)).toEqual(["math-high-todo"]);
    expect(allFiltered.map((task) => task.id)).toEqual(["math-high-todo", "math-next-week"]);
  });

  it("searches plan tasks by title query together with the other filters", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    data.tasks = [
      { id: "math-real", subjectId: math.id, title: "数学真题套卷", date: "2026-06-10", estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "math-review", subjectId: math.id, title: "数学错题复盘", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "english-real", subjectId: english.id, title: "英语真题阅读", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" }
    ];

    const tasks = getPlanTasks(data, "2026-06-10", {
      scope: "week",
      subjectId: math.id,
      priority: "高",
      status: "todo",
      query: "真题"
    });

    expect(tasks.map((task) => task.id)).toEqual(["math-real"]);
  });

  it("rolls unfinished tasks to the next day without losing partial study records", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "not-started", subjectId: math.id, title: "未开始任务", date: "2026-06-10", estimatedMinutes: 90, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "partial", subjectId: math.id, title: "部分执行任务", date: "2026-06-10", estimatedMinutes: 120, actualMinutes: 45, priority: "中", status: "todo" },
      { id: "done", subjectId: math.id, title: "已完成任务", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 60, priority: "低", status: "done" }
    ];

    const result = rolloverUnfinishedTasks(data, "2026-06-10", "2026-06-11");

    expect(result.movedCount).toBe(2);
    expect(result.targetDate).toBe("2026-06-11");
    expect(result.data.tasks.find((task) => task.id === "not-started")).toMatchObject({ date: "2026-06-11", actualMinutes: 0, status: "todo" });
    expect(result.data.tasks.find((task) => task.id === "partial")).toMatchObject({ date: "2026-06-10", actualMinutes: 45, status: "todo" });
    expect(result.data.tasks.find((task) => task.id === "partial-carry-2026-06-11")).toMatchObject({
      title: "续做：部分执行任务",
      date: "2026-06-11",
      estimatedMinutes: 75,
      actualMinutes: 0,
      status: "todo"
    });
    expect(result.data.tasks.find((task) => task.id === "done")).toMatchObject({ date: "2026-06-10", status: "done" });
    expect(data.tasks.find((task) => task.id === "not-started")?.date).toBe("2026-06-10");
  });

  it("prepares tomorrow plan from unfinished tasks and reports tomorrow task count", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "not-started", subjectId: math.id, title: "未开始任务", date: "2026-06-10", estimatedMinutes: 90, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "partial", subjectId: math.id, title: "部分完成任务", date: "2026-06-10", estimatedMinutes: 120, actualMinutes: 45, priority: "中", status: "todo" },
      { id: "tomorrow-existing", subjectId: math.id, title: "明天已有任务", date: "2026-06-11", estimatedMinutes: 60, actualMinutes: 0, priority: "低", status: "todo" }
    ];

    const result = prepareTomorrowPlan(data, "2026-06-10");

    expect(result.movedCount).toBe(2);
    expect(result.targetDate).toBe("2026-06-11");
    expect(result.tomorrowTaskCount).toBe(3);
    expect(result.data.tasks.find((task) => task.id === "not-started")?.date).toBe("2026-06-11");
    expect(result.data.tasks.find((task) => task.id === "partial-carry-2026-06-11")).toMatchObject({
      title: "续做：部分完成任务",
      estimatedMinutes: 75,
      date: "2026-06-11"
    });
  });

  it("summarizes subject weekly load against weekly targets", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    const politics = data.subjects.find((subject) => subject.name === "政治")!;
    math.weeklyTargetHours = 2;
    english.weeklyTargetHours = 4;
    politics.weeklyTargetHours = 2;
    data.tasks = [
      { id: "math-mon", subjectId: math.id, title: "数学周一", date: "2026-06-08", estimatedMinutes: 60, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "math-wed", subjectId: math.id, title: "数学周三", date: "2026-06-10", estimatedMinutes: 75, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "math-next", subjectId: math.id, title: "数学下周", date: "2026-06-15", estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "english", subjectId: english.id, title: "英语", date: "2026-06-11", estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" },
      { id: "politics", subjectId: politics.id, title: "政治", date: "2026-06-12", estimatedMinutes: 90, actualMinutes: 0, priority: "中", status: "todo" }
    ];

    const load = getSubjectWeeklyLoad(data, "2026-06-10");

    expect(load.find((item) => item.subject.id === math.id)).toMatchObject({ plannedMinutes: 135, targetMinutes: 120, loadRate: 113, status: "over" });
    expect(load.find((item) => item.subject.id === english.id)).toMatchObject({ plannedMinutes: 60, targetMinutes: 240, loadRate: 25, status: "light" });
    expect(load.find((item) => item.subject.id === politics.id)).toMatchObject({ plannedMinutes: 90, targetMinutes: 120, loadRate: 75, status: "balanced" });
  });

  it("generates actionable weekly adjustment tips for overloaded subjects, light subjects and heavy days", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    const politics = data.subjects.find((subject) => subject.name === "政治")!;
    math.weeklyTargetHours = 2;
    english.weeklyTargetHours = 4;
    politics.weeklyTargetHours = 10;
    data.tasks = [
      { id: "math-mon", subjectId: math.id, title: "数学周一", date: "2026-06-08", estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "math-wed", subjectId: math.id, title: "数学周三", date: "2026-06-10", estimatedMinutes: 90, actualMinutes: 0, priority: "中", status: "todo" },
      { id: "english", subjectId: english.id, title: "英语阅读", date: "2026-06-11", estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" },
      { id: "politics-heavy", subjectId: politics.id, title: "政治大块", date: "2026-06-12", estimatedMinutes: 390, actualMinutes: 0, priority: "低", status: "todo" }
    ];

    const tips = generateWeeklyAdjustmentTips(data, "2026-06-10");

    expect(tips.some((tip) => tip.tone === "warn" && tip.title.includes("数学"))).toBe(true);
    expect(tips.some((tip) => tip.tone === "balance" && tip.detail.includes("英语"))).toBe(true);
    expect(tips.some((tip) => tip.tone === "warn" && tip.title.includes("2026-06-12"))).toBe(true);
  });

  it("returns a steady weekly adjustment tip when the selected week is balanced", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    data.subjects = [math, english];
    math.weeklyTargetHours = 2;
    english.weeklyTargetHours = 1;
    data.tasks = [
      { id: "math", subjectId: math.id, title: "数学", date: "2026-06-08", estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "english", subjectId: english.id, title: "英语", date: "2026-06-09", estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" }
    ];

    const tips = generateWeeklyAdjustmentTips(data, "2026-06-10");

    expect(tips).toHaveLength(1);
    expect(tips[0]).toMatchObject({ tone: "steady" });
    expect(tips[0].title).toContain("节奏稳定");
  });

  it("shifts only selected task dates by a day delta", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "first", subjectId: math.id, title: "第一项", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "second", subjectId: math.id, title: "第二项", date: "2026-06-08", estimatedMinutes: 90, actualMinutes: 0, priority: "中", status: "todo" },
      { id: "third", subjectId: math.id, title: "不移动", date: "2026-06-12", estimatedMinutes: 45, actualMinutes: 0, priority: "低", status: "todo" }
    ];

    const pushed = shiftTasksByIds(data, ["first", "second", "missing"], 1);
    const pulled = shiftTasksByIds(data, ["first"], -1);

    expect(pushed.movedCount).toBe(2);
    expect(pushed.data.tasks.find((task) => task.id === "first")?.date).toBe("2026-06-11");
    expect(pushed.data.tasks.find((task) => task.id === "second")?.date).toBe("2026-06-09");
    expect(pushed.data.tasks.find((task) => task.id === "third")?.date).toBe("2026-06-12");
    expect(pulled.data.tasks.find((task) => task.id === "first")?.date).toBe("2026-06-09");
    expect(data.tasks.find((task) => task.id === "first")?.date).toBe("2026-06-10");
  });

  it("relieves the heaviest day by moving a low-priority unfinished task to the next day", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "high", subjectId: math.id, title: "高优先级保留", date: "2026-06-10", estimatedMinutes: 150, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "low-small", subjectId: math.id, title: "低优先级小块", date: "2026-06-10", estimatedMinutes: 45, actualMinutes: 0, priority: "低", status: "todo" },
      { id: "low-large", subjectId: math.id, title: "低优先级大块", date: "2026-06-10", estimatedMinutes: 120, actualMinutes: 0, priority: "低", status: "todo" },
      { id: "done-low", subjectId: math.id, title: "已完成不移动", date: "2026-06-10", estimatedMinutes: 120, actualMinutes: 120, priority: "低", status: "done" },
      { id: "other-day", subjectId: math.id, title: "其他日期", date: "2026-06-11", estimatedMinutes: 60, actualMinutes: 0, priority: "低", status: "todo" }
    ];

    const result = relieveHeaviestDay(data, "2026-06-10", 360);

    expect(result.movedCount).toBe(1);
    expect(result.sourceDate).toBe("2026-06-10");
    expect(result.targetDate).toBe("2026-06-11");
    expect(result.taskId).toBe("low-large");
    expect(result.data.tasks.find((task) => task.id === "low-large")?.date).toBe("2026-06-11");
    expect(result.data.tasks.find((task) => task.id === "done-low")?.date).toBe("2026-06-10");
    expect(data.tasks.find((task) => task.id === "low-large")?.date).toBe("2026-06-10");
  });

  it("adds a study block for the lightest subject on the emptiest day of the selected week", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    const english = data.subjects.find((subject) => subject.name === "英语")!;
    data.subjects = [math, english];
    math.weeklyTargetHours = 2;
    english.weeklyTargetHours = 4;
    data.tasks = [
      { id: "math-mon", subjectId: math.id, title: "数学周一", date: "2026-06-08", estimatedMinutes: 120, actualMinutes: 0, priority: "高", status: "todo" },
      { id: "english-thu", subjectId: english.id, title: "英语阅读", date: "2026-06-11", estimatedMinutes: 60, actualMinutes: 0, priority: "中", status: "todo" }
    ];

    const result = addLightSubjectStudyBlock(data, "2026-06-10", 60);

    expect(result.addedCount).toBe(1);
    expect(result.subjectName).toBe("英语");
    expect(result.date).toBe("2026-06-09");
    expect(result.data.tasks.find((task) => task.id === result.taskId)).toMatchObject({
      subjectId: english.id,
      title: "英语基础巩固",
      date: "2026-06-09",
      estimatedMinutes: 60,
      actualMinutes: 0,
      priority: "中",
      status: "todo"
    });
    expect(data.tasks).toHaveLength(2);
  });

  it("updates selected tasks in bulk and fills actual time when marking done", () => {
    const data = createDefaultData();
    const math = data.subjects.find((subject) => subject.name === "数学")!;
    data.tasks = [
      { id: "first", subjectId: math.id, title: "第一项", date: "2026-06-10", estimatedMinutes: 60, actualMinutes: 0, priority: "低", status: "todo" },
      { id: "second", subjectId: math.id, title: "第二项", date: "2026-06-10", estimatedMinutes: 90, actualMinutes: 30, priority: "中", status: "todo" },
      { id: "third", subjectId: math.id, title: "不更新", date: "2026-06-10", estimatedMinutes: 45, actualMinutes: 0, priority: "低", status: "todo" }
    ];

    const result = updateTasksByIds(data, ["first", "second", "missing"], { priority: "高", status: "done" });

    expect(result.updatedCount).toBe(2);
    expect(result.data.tasks.find((task) => task.id === "first")).toMatchObject({ priority: "高", status: "done", actualMinutes: 60 });
    expect(result.data.tasks.find((task) => task.id === "second")).toMatchObject({ priority: "高", status: "done", actualMinutes: 30 });
    expect(result.data.tasks.find((task) => task.id === "third")).toMatchObject({ priority: "低", status: "todo", actualMinutes: 0 });
    expect(data.tasks.find((task) => task.id === "first")).toMatchObject({ priority: "低", status: "todo", actualMinutes: 0 });
  });
});
