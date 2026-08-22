"""服务端学习数据存取与校验。

校验规则逐条镜像 frontend/src/storage.ts 的 isValidAppData 白名单校验
（isPositiveNumber / isNonNegativeNumber / isPriority / isStatus / version === 1），
多出的字段一律忽略，与前端行为一致。
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

Priority = Literal["高", "中", "低"]
Status = Literal["todo", "done"]


class Subject(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    weeklyTargetHours: float = Field(gt=0, le=168)


class Task(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    subjectId: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    date: date
    estimatedMinutes: int = Field(gt=0, le=10080)
    actualMinutes: int = Field(ge=0, le=10080)
    priority: Priority
    status: Status


class Review(BaseModel):
    date: date
    text: str = Field(max_length=20_000)


class FocusStatEntry(BaseModel):
    date: date
    focusMinutes: int = Field(ge=0, le=1440)
    pomodoroCount: int = Field(ge=0, le=1000)
    sessionCount: int = Field(ge=0, le=10_000)


class AppDataModel(BaseModel):
    version: Literal[1] = 1
    examDate: date
    subjects: list[Subject] = Field(max_length=100)
    tasks: list[Task] = Field(max_length=20_000)
    reviews: list[Review] = Field(max_length=20_000)

    @model_validator(mode="after")
    def check_relationships(self) -> "AppDataModel":
        """引用关系与唯一性校验（P1-11）：重复 ID / 孤儿引用 / 重复复盘 → 422。"""
        subject_ids = [subject.id for subject in self.subjects]
        if len(set(subject_ids)) != len(subject_ids):
            raise ValueError("科目 ID 不能重复")
        task_ids = [task.id for task in self.tasks]
        if len(set(task_ids)) != len(task_ids):
            raise ValueError("任务 ID 不能重复")
        subject_set = set(subject_ids)
        for task in self.tasks:
            if task.subjectId not in subject_set:
                raise ValueError(f"任务引用了不存在的科目：{task.subjectId}")
        review_dates = [review.date.isoformat() for review in self.reviews]
        if len(set(review_dates)) != len(review_dates):
            raise ValueError("同一天复盘不能重复")
        return self


class FocusStatsModel(BaseModel):
    version: Literal[1] = 1
    byDate: dict[date, FocusStatEntry] = Field(max_length=2_000)

    @model_validator(mode="after")
    def check_key_date_match(self) -> "FocusStatsModel":
        for key, entry in self.byDate.items():
            if key.isoformat() != entry.date.isoformat():
                raise ValueError(f"专注统计日期键与条目不一致：{key} vs {entry.date}")
        return self


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_revision(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT value FROM meta WHERE key='revision'").fetchone()
    return int(row["value"]) if row else 0


def _bump_revision(conn: sqlite3.Connection, updated_at: str) -> int:
    revision = _read_revision(conn) + 1
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES ('revision', ?)",
        (str(revision),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES ('updated_at', ?)",
        (updated_at,),
    )
    return revision


def read_full_state(conn: sqlite3.Connection) -> dict[str, Any]:
    """组装前端 AppData 形状；空库返回 revision + data: null（前端负责播种）。"""
    meta = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM meta")}
    revision = int(meta.get("revision", "0"))
    updated_at = meta.get("updated_at")
    exam_date = meta.get("exam_date")

    if exam_date is None:
        return {
            "revision": revision,
            "updatedAt": updated_at,
            "data": None,
            "focusStats": {"version": 1, "byDate": {}},
        }

    subjects = [
        {
            "id": row["id"],
            "name": row["name"],
            "color": row["color"],
            "weeklyTargetHours": row["weekly_target_hours"],
        }
        for row in conn.execute("SELECT * FROM subjects ORDER BY sort_order")
    ]
    tasks = [
        {
            "id": row["id"],
            "subjectId": row["subject_id"],
            "title": row["title"],
            "date": row["date"],
            "estimatedMinutes": row["estimated_minutes"],
            "actualMinutes": row["actual_minutes"],
            "priority": row["priority"],
            "status": row["status"],
        }
        for row in conn.execute("SELECT * FROM tasks ORDER BY sort_order")
    ]
    reviews = [
        {"date": row["date"], "text": row["text"]}
        for row in conn.execute("SELECT * FROM reviews ORDER BY date")
    ]
    by_date = {
        row["date"]: {
            "date": row["date"],
            "focusMinutes": row["focus_minutes"],
            "pomodoroCount": row["pomodoro_count"],
            "sessionCount": row["session_count"],
        }
        for row in conn.execute("SELECT * FROM focus_stats ORDER BY date")
    }

    return {
        "revision": revision,
        "updatedAt": updated_at,
        "data": {
            "version": 1,
            "examDate": exam_date,
            "subjects": subjects,
            "tasks": tasks,
            "reviews": reviews,
        },
        "focusStats": {"version": 1, "byDate": by_date},
    }


def write_state(
    conn: sqlite3.Connection,
    data: AppDataModel,
    focus_stats: FocusStatsModel | None = None,
) -> int:
    """整快照写入（replace 语义）：单事务内先 DELETE 后批量 INSERT，返回新 revision。

    调用方负责事务边界与显式关闭连接，异常时整体回滚。
    focus_stats 语义（P1-9）：
    - 显式提供（含空 byDate）→ 整表替换（主动清空 = 传空 byDate）；
    - 未提供（旧备份导入等）→ 保留现有专注统计，绝不静默清空。
    """
    updated_at = _now_iso()
    conn.execute("DELETE FROM subjects")
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM reviews")
    if focus_stats is not None:
        conn.execute("DELETE FROM focus_stats")
        _write_focus_stats(conn, focus_stats)
    conn.executemany(
        "INSERT INTO subjects (id, name, color, weekly_target_hours, sort_order) VALUES (?, ?, ?, ?, ?)",
        [(s.id, s.name, s.color, s.weeklyTargetHours, i) for i, s in enumerate(data.subjects)],
    )
    conn.executemany(
        "INSERT INTO tasks (id, subject_id, title, date, estimated_minutes, actual_minutes, priority, status, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                t.id,
                t.subjectId,
                t.title,
                t.date,
                t.estimatedMinutes,
                t.actualMinutes,
                t.priority,
                t.status,
                i,
            )
            for i, t in enumerate(data.tasks)
        ],
    )
    conn.executemany(
        "INSERT INTO reviews (date, text) VALUES (?, ?)",
        [(r.date, r.text) for r in data.reviews],
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES ('exam_date', ?)",
        (data.examDate,),
    )
    return _bump_revision(conn, updated_at)


def _write_focus_stats(conn: sqlite3.Connection, focus_stats: FocusStatsModel | None) -> None:
    if focus_stats is None:
        return
    conn.executemany(
        "INSERT INTO focus_stats (date, focus_minutes, pomodoro_count, session_count) VALUES (?, ?, ?, ?)",
        [
            (date, entry.focusMinutes, entry.pomodoroCount, entry.sessionCount)
            for date, entry in sorted(focus_stats.byDate.items())
        ],
    )


def _existing_ids(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[0] for row in conn.execute(f"SELECT id FROM {table}")}


def _max_sort_order(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(sort_order), -1) AS m FROM {table}").fetchone()
    return int(row["m"])


def merge_state(
    conn: sqlite3.Connection,
    data: AppDataModel,
    focus_stats: FocusStatsModel | None = None,
) -> int:
    """幂等合并：subjects/tasks 按 id 覆盖、新 id 追加；reviews 按 date 覆盖；
    focusStats 按 date 逐项取 max。重复导入同一文件结果相同。"""
    updated_at = _now_iso()

    existing_subjects = _existing_ids(conn, "subjects")
    next_subject_order = _max_sort_order(conn, "subjects") + 1
    for i, subject in enumerate(data.subjects):
        if subject.id in existing_subjects:
            conn.execute(
                "UPDATE subjects SET name = ?, color = ?, weekly_target_hours = ? WHERE id = ?",
                (subject.name, subject.color, subject.weeklyTargetHours, subject.id),
            )
        else:
            conn.execute(
                "INSERT INTO subjects (id, name, color, weekly_target_hours, sort_order) VALUES (?, ?, ?, ?, ?)",
                (subject.id, subject.name, subject.color, subject.weeklyTargetHours, next_subject_order + i),
            )

    existing_tasks = _existing_ids(conn, "tasks")
    next_task_order = _max_sort_order(conn, "tasks") + 1
    for i, task in enumerate(data.tasks):
        if task.id in existing_tasks:
            conn.execute(
                "UPDATE tasks SET subject_id = ?, title = ?, date = ?, estimated_minutes = ?, actual_minutes = ?, priority = ?, status = ? WHERE id = ?",
                (
                    task.subjectId,
                    task.title,
                    task.date,
                    task.estimatedMinutes,
                    task.actualMinutes,
                    task.priority,
                    task.status,
                    task.id,
                ),
            )
        else:
            conn.execute(
                "INSERT INTO tasks (id, subject_id, title, date, estimated_minutes, actual_minutes, priority, status, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task.id,
                    task.subjectId,
                    task.title,
                    task.date,
                    task.estimatedMinutes,
                    task.actualMinutes,
                    task.priority,
                    task.status,
                    next_task_order + i,
                ),
            )

    conn.executemany(
        "INSERT INTO reviews (date, text) VALUES (?, ?) ON CONFLICT(date) DO UPDATE SET text = excluded.text",
        [(r.date, r.text) for r in data.reviews],
    )

    if focus_stats is not None:
        conn.executemany(
            "INSERT INTO focus_stats (date, focus_minutes, pomodoro_count, session_count) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(date) DO UPDATE SET "
            "focus_minutes = MAX(focus_minutes, excluded.focus_minutes), "
            "pomodoro_count = MAX(pomodoro_count, excluded.pomodoro_count), "
            "session_count = MAX(session_count, excluded.session_count)",
            [
                (date, entry.focusMinutes, entry.pomodoroCount, entry.sessionCount)
                for date, entry in focus_stats.byDate.items()
            ],
        )

    # 空库合并时补齐 exam_date，否则状态永远被当作空库
    if conn.execute("SELECT value FROM meta WHERE key='exam_date'").fetchone() is None:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('exam_date', ?)",
            (data.examDate,),
        )
    return _bump_revision(conn, updated_at)