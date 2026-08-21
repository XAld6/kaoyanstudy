"""服务端学习数据存取与校验。

校验规则逐条镜像 frontend/src/storage.ts 的 isValidAppData 白名单校验
（isPositiveNumber / isNonNegativeNumber / isPriority / isStatus / version === 1），
多出的字段一律忽略，与前端行为一致。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

Priority = Literal["高", "中", "低"]
Status = Literal["todo", "done"]


class Subject(BaseModel):
    id: str
    name: str
    color: str
    weeklyTargetHours: float = Field(gt=0)


class Task(BaseModel):
    id: str
    subjectId: str
    title: str
    date: str
    estimatedMinutes: int = Field(gt=0)
    actualMinutes: int = Field(ge=0)
    priority: Priority
    status: Status


class Review(BaseModel):
    date: str
    text: str


class FocusStatEntry(BaseModel):
    date: str
    focusMinutes: int = Field(ge=0)
    pomodoroCount: int = Field(ge=0)
    sessionCount: int = Field(ge=0)


class AppDataModel(BaseModel):
    version: Literal[1] = 1
    examDate: str
    subjects: list[Subject]
    tasks: list[Task]
    reviews: list[Review]


class FocusStatsModel(BaseModel):
    version: Literal[1] = 1
    byDate: dict[str, FocusStatEntry]


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

    调用方负责事务边界（with conn:），异常时整体回滚。
    """
    updated_at = _now_iso()
    conn.execute("DELETE FROM subjects")
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM reviews")
    conn.execute("DELETE FROM focus_stats")
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
    _write_focus_stats(conn, focus_stats)
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