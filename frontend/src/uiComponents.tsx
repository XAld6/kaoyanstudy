import React from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Gauge,
  Pause,
  Play,
  Plus,
  Sparkles,
  Square,
  Timer,
  Trash2
} from "lucide-react";
import {
  AppData,
  DailyClosureItem,
  DataHealthItem,
  HeatmapDay,
  StructuredAdvice,
  StudyHeatmap,
  StudyTask,
  SubjectWeeklyLoad,
  WeeklyAdjustmentTip,
  WeekDayOverview
} from "./studyCore";
import { FocusTimerSnapshot } from "./focusTimer";
import { minutesLabel } from "./format";

export const weekdayLabels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

export function Metric({ title, value, icon, tone }: { title: string; value: string; icon: React.ReactNode; tone?: "warn" }) {
  return (
    <section className={`metric ${tone ?? ""}`}>
      <span>{icon}{title}</span>
      <strong>{value}</strong>
    </section>
  );
}

export function FocusStickyBar({
  snapshot,
  onPauseResume,
  onFinish,
  onDiscard,
  onSkipBreak,
  onGoToday
}: {
  snapshot: FocusTimerSnapshot;
  onPauseResume: () => void;
  onFinish: () => void;
  onDiscard: () => void;
  onSkipBreak?: () => void;
  onGoToday?: () => void;
}) {
  const isBreak = snapshot.phase === "break";
  if (snapshot.status === "idle") return null;
  if (!isBreak && !snapshot.taskId) return null;

  const modeLabel = isBreak
    ? "休息剩余"
    : snapshot.mode === "pomodoro"
      ? "番茄剩余"
      : "已专注";
  const statusLabel = snapshot.status === "paused"
    ? (isBreak ? "休息已暂停" : "已暂停")
    : (isBreak ? "休息中" : "计时中");
  const taskLine = isBreak
    ? (snapshot.lastWorkTaskTitle ? `上一轮：${snapshot.lastWorkTaskTitle}` : "番茄休息")
    : (snapshot.taskTitle || "当前任务");
  const showCountdownBar = isBreak || snapshot.mode === "pomodoro";

  return (
    <div className={`focus-sticky-bar ${snapshot.status}${isBreak ? " break-phase" : ""}`} role="status" aria-live="polite">
      <div className="focus-sticky-main">
        <span className="focus-sticky-icon"><Timer size={16} /></span>
        <div className="focus-sticky-copy">
          <strong className="focus-sticky-clock">{snapshot.display}</strong>
          <span>
            {statusLabel} · {modeLabel}
            {showCountdownBar ? ` ${snapshot.targetMinutes}m` : ""}
            {" · "}
            {taskLine}
          </span>
        </div>
        {showCountdownBar && (
          <div className="focus-sticky-progress" aria-hidden="true">
            <i style={{ width: `${Math.round(snapshot.progress * 100)}%` }} />
          </div>
        )}
      </div>
      <div className="focus-sticky-actions">
        {onGoToday && (
          <button type="button" className="ghost mini" onClick={onGoToday}>今日</button>
        )}
        <button type="button" className="ghost compact-button" onClick={onPauseResume}>
          {snapshot.status === "running" ? <><Pause size={14} />暂停</> : <><Play size={14} />继续</>}
        </button>
        <button type="button" className="primary compact-button" onClick={onFinish}>
          <Square size={14} />{isBreak ? "结束休息" : "结束并记入"}
        </button>
        {isBreak && onSkipBreak ? (
          <button type="button" className="ghost mini" onClick={onSkipBreak}>跳过休息</button>
        ) : (
          <button type="button" className="ghost mini" onClick={onDiscard}>{isBreak ? "跳过休息" : "丢弃"}</button>
        )}
      </div>
    </div>
  );
}

export function OverviewItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="overview-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function HealthItem({ item, action }: { item: DataHealthItem; action?: { label: string; onClick: () => void } }) {
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

export function StructuredAdviceBoard({
  advice,
  sourceLabel,
  large
}: {
  advice: StructuredAdvice;
  sourceLabel: string;
  large?: boolean;
}) {
  return (
    <div className={`structured-advice ${large ? "large" : ""}`}>
      <div className="structured-advice-head">
        <span className="pill">{sourceLabel}</span>
        <span className="hint">补哪科 · 砍哪块 · 明日三件事</span>
      </div>
      <div className="structured-advice-grid">
        {advice.sections.map((section) => (
          <article className={`advice-section tone-${section.id}`} key={section.id}>
            <strong>{section.title}</strong>
            <div className="advice-stack">
              {section.items.length
                ? section.items.map((item) => <div className="advice" key={`${section.id}-${item}`}>{item}</div>)
                : <div className="advice empty-advice">暂无</div>}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export function ClosureChecklist({ items }: { items: DailyClosureItem[] }) {
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

export function WeekPlanBoard({ weekOverview, selectedDate, setSelectedDate }: {
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

export function WeeklyLoadStrip({ weeklyLoad }: { weeklyLoad: SubjectWeeklyLoad[] }) {
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

function heatmapDayTitle(day: HeatmapDay) {
  const parts = [
    day.date,
    `实际 ${minutesLabel(day.actualMinutes)}`,
    `计划 ${minutesLabel(day.plannedMinutes)}`
  ];
  if (day.focusMinutes > 0) parts.push(`专注 ${minutesLabel(day.focusMinutes)}`);
  if (day.taskCount > 0) parts.push(`任务 ${day.doneTasks}/${day.taskCount}`);
  if (day.hasReview) parts.push("有复盘");
  return parts.join(" · ");
}

export function StudyHeatmapBoard({
  heatmap,
  selectedDate,
  onSelectDate
}: {
  heatmap: StudyHeatmap;
  selectedDate: string;
  onSelectDate: (date: string) => void;
}) {
  return (
    <section className="study-heatmap" aria-label="学习热力日历">
      <div className="heatmap-meta">
        <div className="heatmap-stat">
          <span>窗口合计</span>
          <strong>{minutesLabel(heatmap.totalActualMinutes)}</strong>
        </div>
        <div className="heatmap-stat">
          <span>有学习天数</span>
          <strong>{heatmap.activeDays} 天</strong>
        </div>
        <div className="heatmap-stat">
          <span>当前连续</span>
          <strong>{heatmap.currentStreak} 天</strong>
        </div>
        <div className="heatmap-stat">
          <span>最长连续</span>
          <strong>{heatmap.bestStreak} 天</strong>
        </div>
      </div>

      <div className="heatmap-body">
        <div className="heatmap-weekday-labels" aria-hidden="true">
          {weekdayLabels.map((label) => <span key={label}>{label}</span>)}
        </div>
        <div className="heatmap-weeks" role="grid" aria-label={`${heatmap.weekCount} 周学习热力`}>
          {heatmap.weeks.map((week, weekIndex) => (
            <div className="heatmap-week" role="row" key={`${week[0]?.date ?? weekIndex}`}>
              {week.map((day) => (
                <button
                  type="button"
                  key={day.date}
                  role="gridcell"
                  className={`heatmap-cell level-${day.level}${day.date === selectedDate ? " selected" : ""}${day.hasReview ? " has-review" : ""}`}
                  title={heatmapDayTitle(day)}
                  aria-label={heatmapDayTitle(day)}
                  aria-pressed={day.date === selectedDate}
                  onClick={() => onSelectDate(day.date)}
                />
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="heatmap-footer">
        <span className="hint">点击格子切换顶部当前日期 · 颜色越深实际学习越多</span>
        <div className="heatmap-legend" aria-hidden="true">
          <span>少</span>
          {[0, 1, 2, 3, 4].map((level) => <i key={level} className={`heatmap-cell level-${level}`} />)}
          <span>多</span>
        </div>
      </div>
    </section>
  );
}

export function WeeklyAdjustmentPanel({ tips, canAddStudyBlock, canRelieveHeavyDay, onAddStudyBlock, onRelieveHeavyDay }: {
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

export function TaskCreator({ data, newTask, setNewTask, addTask }: {
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

export function PlanTaskRow({ task, data, updateTask, deleteTask }: {
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

export function TaskRow({
  task,
  data,
  toggleTask,
  updateTaskMinutes,
  bumpMinutes,
  fillMinutes,
  deleteTask,
  onStartFocus,
  isFocusTarget,
  focusRunning,
  compact
}: {
  task: StudyTask;
  data: AppData;
  toggleTask: (taskId: string) => void;
  updateTaskMinutes: (taskId: string, actualMinutes: number) => void;
  bumpMinutes: (taskId: string, delta: number) => void;
  fillMinutes: (taskId: string) => void;
  deleteTask: (taskId: string) => void;
  onStartFocus?: (task: StudyTask) => void;
  isFocusTarget?: boolean;
  focusRunning?: boolean;
  compact?: boolean;
}) {
  const subject = data.subjects.find((item) => item.id === task.subjectId);
  return (
    <article className={`task-row ${task.status === "done" ? "done" : ""} ${isFocusTarget ? "focus-target" : ""}`}>
      <button className="check" onClick={() => toggleTask(task.id)} title="切换完成状态">{task.status === "done" ? <CheckCircle2 size={18} /> : null}</button>
      <div className="task-main">
        <strong>{task.title}</strong>
        <span><i style={{ background: subject?.color }} />{subject?.name ?? "未分组"} · {task.date} · 预计 {minutesLabel(task.estimatedMinutes)} · {task.priority}优先级</span>
        {!compact && (
          <div className="minute-chips" aria-label="实际时长快捷">
            {onStartFocus && (
              <button
                type="button"
                className={`minute-chip focus-chip ${isFocusTarget ? "active" : ""}`}
                onClick={() => onStartFocus(task)}
                title={isFocusTarget ? "当前计时任务" : "开始专注计时"}
              >
                {focusRunning ? "计时中" : isFocusTarget ? "已绑定" : "开始"}
              </button>
            )}
            <button type="button" className="minute-chip" onClick={() => bumpMinutes(task.id, 15)} title="实际时长 +15 分钟">+15</button>
            <button type="button" className="minute-chip" onClick={() => bumpMinutes(task.id, 30)} title="实际时长 +30 分钟">+30</button>
            <button type="button" className="minute-chip" onClick={() => fillMinutes(task.id)} title="填满计划时长">填满</button>
          </div>
        )}
      </div>
      {!compact && (
        <div className="minute-field">
          <input type="number" min="0" step="5" value={task.actualMinutes} onChange={(event) => updateTaskMinutes(task.id, Number(event.target.value))} title="实际分钟" />
          <span>分钟</span>
        </div>
      )}
      <button className="icon-button subtle" onClick={() => deleteTask(task.id)} title="删除任务"><Trash2 size={16} /></button>
    </article>
  );
}
