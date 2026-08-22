"""部署脚本回归测试：直接断言脚本内容的关键行为，防止再次引入执行错误。"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def read_script(name: str) -> str:
    return (REPO_ROOT / "deploy" / name).read_text(encoding="utf-8")


def test_update_script_rsyncs_from_frontend_absolutely():
    """P1-5：rsync 必须使用绝对路径（在 cd frontend 之后再写 frontend/dist 会失效）。"""
    src = read_script("update.sh")
    assert 'rsync -a --delete dist/ "$BASE/web/"' in src


def test_update_script_supports_target_revision_for_rollback():
    """P1-7：回滚必须可用——脚本接受目标版本参数，而不是无条件切回 origin/main。"""
    src = read_script("update.sh")
    assert 'TARGET_REVISION="${1:-origin/main}"' in src
    assert 'git reset --hard "$TARGET_REVISION"' in src


def test_update_script_cds_out_of_caller_cwd():
    """dab0137：脚本开头必须 cd 到固定 BASE，避免被调用者 CWD 影响。"""
    src = read_script("update.sh")
    assert 'cd "$BASE"' in src or 'cd "$BASE/repo"' in src


def test_backup_script_cleans_pre_import_backups():
    """P2-14：预导入备份必须纳入 30 天清理，否则目录持续增长。"""
    src = read_script("backup.sh")
    assert "pre-import-*.db" in src


def test_backup_script_keeps_wal_safe_backup():
    src = read_script("backup.sh")
    assert ".backup" in src
    # 非注释的命令行里不允许直接 cp 数据库
    commands = [line.strip() for line in src.splitlines() if line.strip() and not line.strip().startswith("#")]
    assert not any(line.startswith("cp ") or " cp " in line for line in commands)


def test_systemd_unit_binds_loopback_only():
    """安全要件：后端 unit 的 ExecStart 必须绑 127.0.0.1，绑 0.0.0.0 会绕过 Basic Auth。"""
    unit = (REPO_ROOT / "deploy" / "kaoyan-api.service").read_text(encoding="utf-8")
    exec_start = next(line for line in unit.splitlines() if line.startswith("ExecStart="))
    assert "--host 127.0.0.1" in exec_start
    assert "0.0.0.0" not in exec_start


def test_backup_service_sets_beijing_timezone():
    svc = (REPO_ROOT / "deploy" / "kaoyan-backup.service").read_text(encoding="utf-8")
    assert "TZ=Asia/Shanghai" in svc