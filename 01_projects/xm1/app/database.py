from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from utils.config import load_settings, project_path


settings = load_settings()
database_url = settings["paths"]["database_url"]
if database_url.startswith("sqlite:///"):
    database_path = project_path(database_url.replace("sqlite:///", "", 1))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite:///{database_path.as_posix()}"

engine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class InspectionRecord(Base):
    __tablename__ = "inspection_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    image_path: Mapped[str] = mapped_column(String(500))
    result_path: Mapped[str] = mapped_column(String(500))
    detections_json: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32), index=True)
    engine: Mapped[str] = mapped_column(String(64), default="rule-demo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)


class InspectionTask(Base):
    __tablename__ = "inspection_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_name: Mapped[str] = mapped_column(String(255), index=True)
    building_name: Mapped[str] = mapped_column(String(255), index=True)
    area: Mapped[str] = mapped_column(String(255), default="校园公共区域")
    inspector: Mapped[str] = mapped_column(String(100), default="后勤巡检员")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)


class RepairOrder(Base):
    __tablename__ = "repair_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("inspection_records.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    defect_type: Mapped[str] = mapped_column(String(64), index=True)
    risk_level: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    handler: Mapped[str] = mapped_column(String(100), default="维修班组")
    deadline: Mapped[str] = mapped_column(String(64), default="48小时内处理")
    before_image_path: Mapped[str] = mapped_column(String(500))
    after_image_path: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed_demo_tasks() -> None:
    with get_session() as session:
        if session.query(InspectionTask).count() > 0:
            return
        session.add_all(
            [
                InspectionTask(
                    task_name="教学楼外墙月度巡检",
                    building_name="第一教学楼",
                    area="主入口与东西立面",
                    inspector="后勤巡检员A",
                    status="in_progress",
                ),
                InspectionTask(
                    task_name="宿舍区雨季专项巡检",
                    building_name="学生宿舍3号楼",
                    area="南立面与连廊区域",
                    inspector="后勤巡检员B",
                    status="pending",
                ),
                InspectionTask(
                    task_name="图书馆高空外墙复查",
                    building_name="图书馆",
                    area="北侧高空墙面",
                    inspector="物业巡检组",
                    status="completed",
                ),
            ]
        )


@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def to_web_path(path: str | Path) -> str:
    absolute = Path(path)
    if not absolute.is_absolute():
        absolute = project_path(absolute)
    relative = absolute.relative_to(project_path("."))
    posix_path = relative.as_posix()
    mappings = {
        "data/uploads/": "/uploads/",
        "data/results/": "/results/",
        "data/samples/": "/samples/",
    }
    for prefix, web_prefix in mappings.items():
        if posix_path.startswith(prefix):
            return web_prefix + posix_path.removeprefix(prefix)
    return "/" + posix_path
