from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def sample_appdata(**overrides):
    data = {
        "version": 1,
        "examDate": "2026-12-20",
        "subjects": [
            {"id": "s1", "name": "数学", "color": "#ff0000", "weeklyTargetHours": 10},
            {"id": "s2", "name": "英语", "color": "#00ff00", "weeklyTargetHours": 8},
        ],
        "tasks": [
            {
                "id": "t1",
                "subjectId": "s1",
                "title": "高数强化",
                "date": "2026-06-10",
                "estimatedMinutes": 120,
                "actualMinutes": 0,
                "priority": "高",
                "status": "todo",
            },
            {
                "id": "t2",
                "subjectId": "s2",
                "title": "阅读精读",
                "date": "2026-06-10",
                "estimatedMinutes": 60,
                "actualMinutes": 60,
                "priority": "中",
                "status": "done",
            },
        ],
        "reviews": [{"date": "2026-06-10", "text": "今日复盘"}],
    }
    data.update(overrides)
    return data


def sample_focus_stats(**overrides):
    stats = {
        "version": 1,
        "byDate": {
            "2026-06-10": {"date": "2026-06-10", "focusMinutes": 45, "pomodoroCount": 2, "sessionCount": 3}
        },
    }
    stats.update(overrides)
    return stats


def test_empty_db_returns_revision_zero_with_null_data():
    response = client.get("/api/state")

    assert response.status_code == 200
    body = response.json()
    assert body["revision"] == 0
    assert body["data"] is None
    assert body["focusStats"] == {"version": 1, "byDate": {}}


def test_put_then_get_returns_same_state():
    data = sample_appdata()
    stats = sample_focus_stats()

    put = client.put("/api/state", json={"baseRevision": 0, "data": data, "focusStats": stats})
    assert put.status_code == 200
    assert put.json()["revision"] == 1

    got = client.get("/api/state").json()
    assert got["revision"] == 1
    assert got["data"] == data
    assert got["focusStats"] == stats


def test_task_and_subject_order_is_preserved():
    data = sample_appdata()
    data["subjects"] = [
        {"id": "sB", "name": "政治", "color": "#0000ff", "weeklyTargetHours": 6},
        {"id": "sA", "name": "专业课", "color": "#ffff00", "weeklyTargetHours": 12},
    ]
    data["tasks"] = [
        {
            "id": "tB",
            "subjectId": "sB",
            "title": "后建任务",
            "date": "2026-06-10",
            "estimatedMinutes": 45,
            "actualMinutes": 0,
            "priority": "低",
            "status": "todo",
        },
        {
            "id": "tA",
            "subjectId": "sA",
            "title": "先建任务",
            "date": "2026-06-10",
            "estimatedMinutes": 90,
            "actualMinutes": 30,
            "priority": "高",
            "status": "done",
        },
    ]

    client.put("/api/state", json={"baseRevision": 0, "data": data, "focusStats": sample_focus_stats()})
    got = client.get("/api/state").json()

    assert [s["id"] for s in got["data"]["subjects"]] == ["sB", "sA"]
    assert [t["id"] for t in got["data"]["tasks"]] == ["tB", "tA"]


def test_put_with_stale_revision_returns_409_with_server_state():
    data = sample_appdata()
    stats = sample_focus_stats()
    first = client.put("/api/state", json={"baseRevision": 0, "data": data, "focusStats": stats})
    assert first.status_code == 200

    stale = client.put("/api/state", json={"baseRevision": 0, "data": data, "focusStats": stats})
    assert stale.status_code == 409
    body = stale.json()
    assert body["server"]["revision"] == 1
    assert body["server"]["data"] == data


def test_put_forward_revision_is_rejected_not_silently_accepted():
    """baseRevision 若解析失败会退化为 0 并直接覆盖（数据丢失）。
    空库 revision=0 时提交 baseRevision=7 必须 409，证明 camelCase 字段解析有效。"""
    response = client.put(
        "/api/state",
        json={"baseRevision": 7, "data": sample_appdata(), "focusStats": sample_focus_stats()},
    )
    assert response.status_code == 409


def test_import_same_file_twice_replace_is_idempotent():
    data = sample_appdata()
    stats = sample_focus_stats()
    body = {"data": data, "focusStats": stats, "mode": "replace"}

    first = client.post("/api/state/import", json=body)
    second = client.post("/api/state/import", json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == second.json()["data"]
    assert first.json()["focusStats"] == second.json()["focusStats"]
    # 幂等=数据一致；revision 每次导入仍递增（文件版本号语义）
    assert second.json()["revision"] > first.json()["revision"]


def test_import_merge_twice_is_idempotent_and_reviews_do_not_duplicate():
    data = sample_appdata()
    stats = sample_focus_stats()
    body = {"data": data, "focusStats": stats, "mode": "merge"}

    first = client.post("/api/state/import", json=body)
    second = client.post("/api/state/import", json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == second.json()["data"]
    assert first.json()["focusStats"] == second.json()["focusStats"]
    # reviews 按 date 覆盖，重复导入不会让复盘文本翻倍
    assert len(second.json()["data"]["reviews"]) == 1


def test_import_merge_keeps_existing_and_appends_new():
    existing = sample_appdata()
    client.post("/api/state/import", json={"data": existing, "mode": "replace"})

    incoming = sample_appdata()
    incoming["subjects"].append({"id": "s3", "name": "政治", "color": "#0000ff", "weeklyTargetHours": 6})
    incoming["tasks"].append(
        {
            "id": "t3",
            "subjectId": "s1",
            "title": "新任务",
            "date": "2026-06-11",
            "estimatedMinutes": 30,
            "actualMinutes": 0,
            "priority": "低",
            "status": "todo",
        }
    )
    incoming["reviews"].append({"date": "2026-06-11", "text": "次日复盘"})

    merged = client.post("/api/state/import", json={"data": incoming, "mode": "merge"})
    assert merged.status_code == 200
    got = merged.json()["data"]
    assert {s["id"] for s in got["subjects"]} == {"s1", "s2", "s3"}
    assert {t["id"] for t in got["tasks"]} == {"t1", "t2", "t3"}
    # 原有复盘仍保留，新复盘追加
    assert len(got["reviews"]) == 2


def test_import_invalid_data_returns_422():
    bad = sample_appdata()
    bad["tasks"][0]["priority"] = "极高"

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422
    assert "学习数据格式不合法" in response.json()["detail"]


def test_put_invalid_data_returns_422():
    bad = sample_appdata()
    bad["tasks"][0]["estimatedMinutes"] = -10

    response = client.put("/api/state", json={"baseRevision": 0, "data": bad})

    assert response.status_code == 422


def test_export_returns_full_backup_package():
    data = sample_appdata()
    stats = sample_focus_stats()
    client.put("/api/state", json={"baseRevision": 0, "data": data, "focusStats": stats})

    response = client.get("/api/state/export")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    body = response.json()
    assert body["examDate"] == data["examDate"]
    assert body["tasks"] == data["tasks"]
    assert body["focusStats"] == stats


def test_export_on_empty_db_returns_404():
    response = client.get("/api/state/export")
    assert response.status_code == 404


# ---- 审查修复回归测试（P0-2 / P1-9 / P1-11 / P2-15） ----


def test_concurrent_put_same_base_only_one_succeeds():
    """P0-2：两个设备基于同一 revision 并发提交，只能有一个成功（另一个 409）。"""
    data = sample_appdata()
    payload = {"baseRevision": 0, "data": data, "focusStats": sample_focus_stats()}

    def put_once(_index: int) -> int:
        own = TestClient(app)
        return own.put("/api/state", json=payload).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = sorted(pool.map(put_once, range(2)))

    assert codes == [200, 409], f"并发同版本提交应该恰好一个成功，实际 {codes}"


def test_put_without_focus_stats_is_rejected():
    """P1-9：普通快照 PUT 的 focusStats 必须显式提供，缺失直接拒绝（不再被当成清空）。"""
    data = sample_appdata()

    response = client.put("/api/state", json={"baseRevision": 0, "data": data})

    assert response.status_code == 422


def test_import_replace_without_focus_stats_preserves_existing_stats():
    """P1-9：导入旧备份（没有 focusStats）时，已有专注统计必须保留，不能被清空。"""
    first = client.put(
        "/api/state",
        json={"baseRevision": 0, "data": sample_appdata(), "focusStats": sample_focus_stats()},
    )
    assert first.status_code == 200

    # 裸旧备份文件：只有 AppData，无 focusStats
    second = client.post("/api/state/import", json={"data": sample_appdata()})
    assert second.status_code == 200

    got = second.json()
    assert got["focusStats"]["byDate"] == sample_focus_stats()["byDate"], "导入旧备份不应清空专注统计"


def test_import_replace_with_explicit_empty_stats_clears():
    """P1-9：显式提供空 byDate 才表示主动清空统计。"""
    first = client.put(
        "/api/state",
        json={"baseRevision": 0, "data": sample_appdata(), "focusStats": sample_focus_stats()},
    )
    assert first.status_code == 200

    explicit = client.post(
        "/api/state/import",
        json={"data": sample_appdata(), "focusStats": {"version": 1, "byDate": {}}},
    )
    assert explicit.status_code == 200
    assert explicit.json()["focusStats"]["byDate"] == {}


def test_import_rejects_non_date_exam_date():
    """P1-11：examDate 必须是合法日期字符串。"""
    bad = sample_appdata()
    bad["examDate"] = "not-a-date"

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422


def test_import_rejects_non_date_task_date():
    bad = sample_appdata()
    bad["tasks"][0]["date"] = "2026/06/10"

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422


def test_import_rejects_orphan_subject_reference():
    """P1-11：任务引用的科目必须存在。"""
    bad = sample_appdata()
    bad["tasks"][0]["subjectId"] = "missing-subject"

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422


def test_import_rejects_duplicate_subject_ids():
    bad = sample_appdata()
    bad["subjects"].append(dict(bad["subjects"][0]))

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422


def test_import_rejects_duplicate_task_ids():
    """重复任务 ID 现在必须返回清晰的 422，而不是 SQLite 主键异常 500。"""
    bad = sample_appdata()
    bad["tasks"].append(dict(bad["tasks"][0]))

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422


def test_import_rejects_focus_key_date_mismatch():
    """P1-11：focusStats 的 byDate key 必须与条目里的 date 一致。"""
    stats = sample_focus_stats()
    stats["byDate"]["2026-06-10"] = {
        "date": "1999-01-01",
        "focusMinutes": 45,
        "pomodoroCount": 2,
        "sessionCount": 3,
    }

    response = client.post("/api/state/import", json={"data": sample_appdata(), "focusStats": stats})

    assert response.status_code == 422


def test_import_rejects_overlong_title():
    bad = sample_appdata()
    bad["tasks"][0]["title"] = "长" * 300

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422


def test_import_rejects_overlong_review():
    bad = sample_appdata()
    bad["reviews"] = [{"date": "2026-06-10", "text": "x" * 25_000}]

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422


def test_import_rejects_invalid_subject_color():
    bad = sample_appdata()
    bad["subjects"][0]["color"] = "red"  # 不是 #rrggbb

    response = client.post("/api/state/import", json={"data": bad})

    assert response.status_code == 422


def test_oversized_payload_rejected_with_413():
    """P2-15：超大请求体（>20MB）应返回 413 而不是耗尽内存。"""
    big = sample_appdata()
    big["reviews"] = [{"date": "2026-06-10", "text": "x" * (21 * 1024 * 1024)}]

    response = client.post("/api/state/import", json={"data": big})

    assert response.status_code == 413