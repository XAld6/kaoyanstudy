import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  Archive,
  CheckCircle2,
  ChevronRight,
  Download,
  FileImage,
  GitBranch,
  History,
  Loader2,
  Microscope,
  RefreshCw,
  ShieldAlert,
  Upload,
  Workflow
} from "lucide-react";
import "./styles.css";

type RiskLevel = "低" | "中" | "高";
const MAX_UPLOAD_BYTES = 8 * 1024 * 1024;

type WorkflowStep = {
  agent: string;
  label: string;
  status: string;
  duration_ms: number;
  summary: string;
};

type Detection = {
  kind: string;
  label: string;
  bbox: number[];
  confidence: number;
  area_ratio: number;
  length_estimate: number;
};

type RecordSummary = {
  id: number;
  filename: string;
  created_at: string;
  risk_level: RiskLevel;
  review_status: string;
  confidence: number;
  detection_count: number;
  original_url: string;
  annotated_url: string;
};

type RecordDetail = RecordSummary & {
  quality: Record<string, string | number | boolean>;
  detections: Detection[];
  workflow: WorkflowStep[];
  metrics: Record<string, number>;
  risk_reason: string;
  review_note: string;
};

const riskRank: Record<RiskLevel, number> = { 低: 1, 中: 2, 高: 3 };
const riskOptions: RiskLevel[] = ["低", "中", "高"];

const agentRoles = [
  "图像质量Agent",
  "病害识别Agent",
  "量化分析Agent",
  "风险评估Agent",
  "复核路由Agent",
  "报告归档Agent"
];

function assetUrl(path: string) {
  return path;
}

async function apiErrorMessage(res: Response, fallback: string) {
  const text = await res.text();
  if (!text) return fallback;
  try {
    const body = JSON.parse(text) as { detail?: unknown };
    return typeof body.detail === "string" && body.detail.trim() ? body.detail : fallback;
  } catch {
    return fallback;
  }
}

function getSixAgentWorkflow(workflow: WorkflowStep[]) {
  if (workflow.length <= 6) return workflow;
  const archive = workflow.find((step) => step.agent === "ArchiveAgent");
  const report = workflow.find((step) => step.agent === "ReportAgent");
  if (!archive || !report) return workflow.slice(0, 6);
  const merged: WorkflowStep = {
    agent: "ReportArchiveAgent",
    label: "报告归档输出",
    status: report.status,
    duration_ms: archive.duration_ms + report.duration_ms,
    summary: "原图、标注图、结构化结果、工作流日志和PDF报告素材已归档"
  };
  return [...workflow.filter((step) => step.agent !== "ArchiveAgent" && step.agent !== "ReportAgent"), merged].slice(0, 6);
}

function App() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [records, setRecords] = useState<RecordSummary[]>([]);
  const [active, setActive] = useState<RecordDetail | null>(null);
  const [uploading, setUploading] = useState(false);
  const [backendOnline, setBackendOnline] = useState<"unknown" | "online" | "offline">("unknown");
  const [error, setError] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [reviewRisk, setReviewRisk] = useState<RiskLevel>("低");

  const stats = useMemo(() => {
    const total = records.length;
    const pending = records.filter((r) => r.review_status === "待复核").length;
    const high = records.filter((r) => r.risk_level === "高").length;
    const avg = total ? records.reduce((sum, r) => sum + r.confidence, 0) / total : 0;
    return { total, pending, high, avg };
  }, [records]);

  async function loadRecords(selectFirst = false) {
    const res = await fetch("/api/records");
    if (!res.ok) throw new Error(await apiErrorMessage(res, "历史记录加载失败"));
    const data: RecordSummary[] = await res.json();
    setRecords(data);
    if (selectFirst && data[0]) {
      await openRecord(data[0].id);
    }
  }

  async function openRecord(id: number) {
    const res = await fetch(`/api/records/${id}`);
    if (!res.ok) throw new Error(await apiErrorMessage(res, "记录详情加载失败"));
    const data: RecordDetail = await res.json();
    setActive(data);
    setReviewNote(data.review_note || "");
    setReviewRisk(data.risk_level);
  }

  async function refreshRecords() {
    try {
      await loadRecords(true);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "历史记录加载失败");
    }
  }

  async function selectRecord(id: number) {
    try {
      await openRecord(id);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "记录详情加载失败");
    }
  }

  async function onFile(file: File | null) {
    if (!file) return;
    if (file.size > MAX_UPLOAD_BYTES) {
      setError("上传图片不能超过 8MB，请压缩后再试。");
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    setUploading(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/detect", { method: "POST", body: form });
      if (!res.ok) {
        throw new Error(await apiErrorMessage(res, "检测失败"));
      }
      const data: RecordDetail = await res.json();
      setActive(data);
      setReviewNote(data.review_note || "");
      setReviewRisk(data.risk_level);
      await loadRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "检测失败");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function saveReview() {
    if (!active) return;
    try {
      const res = await fetch(`/api/records/${active.id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "已复核", risk_level: reviewRisk, review_note: reviewNote })
      });
      if (!res.ok) {
        setError(await apiErrorMessage(res, "复核保存失败"));
        return;
      }
      const data: RecordDetail = await res.json();
      setActive(data);
      setError("");
      await loadRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "复核保存失败");
    }
  }

  async function checkBackend() {
    try {
      const res = await fetch("/api/health");
      setBackendOnline(res.ok ? "online" : "offline");
    } catch {
      setBackendOnline("offline");
    }
  }

  useEffect(() => {
    loadRecords(true).catch(() => setError("历史记录加载失败"));
    checkBackend();
    const timer = window.setInterval(() => {
      void checkBackend();
    }, 15000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <main className="app">
      <aside className="side-rail" aria-label="主导航">
        <div className="mark">Z</div>
        <button
          aria-label="上传检测"
          title="上传检测"
          onClick={() => inputRef.current?.click()}
          disabled={uploading || backendOnline === "offline"}
        >
          <Upload size={20} />
        </button>
        <button aria-label="历史记录" title="历史记录"><History size={20} /></button>
        <button aria-label="Agent工作流" title="Agent工作流"><Workflow size={20} /></button>
        <div className="rail-spacer" />
        <button aria-label="运行状态" title="运行状态"><Activity size={20} /></button>
      </aside>

      <section className="console-shell">
        <header className="console-top">
          <div className="brand-block">
            <p className="eyebrow">OpenClaw-compatible inspection workflow</p>
            <h1>智爪识损</h1>
            <span>基础设施病害 AI 辅助筛查控制台</span>
          </div>
          <div className="system-strip" aria-label="系统状态">
            <span className={`status-pill ${backendOnline === "online" ? "online" : backendOnline === "offline" ? "offline" : ""}`}>
              {backendOnline === "online" ? <CheckCircle2 size={15} /> : <Activity size={15} />}
              {backendOnline === "online" ? "后端在线" : backendOnline === "offline" ? "后端离线" : "后端检测中"}
            </span>
            <span className="status-pill"><Workflow size={15} />6-Agent协同</span>
            <span className="status-pill"><Archive size={15} />SQLite归档</span>
            <span className="status-pill"><Microscope size={15} />OpenCV识别</span>
          </div>
          <div className="top-actions">
            <button className="ghost" onClick={refreshRecords}>
              <RefreshCw size={17} />刷新
            </button>
            <button className="primary" onClick={() => inputRef.current?.click()} disabled={uploading || backendOnline === "offline"}>
              {uploading ? <Loader2 className="spin" size={18} /> : <Upload size={18} />}
              上传巡检图
            </button>
            <input ref={inputRef} type="file" accept="image/*" onChange={(event) => onFile(event.target.files?.[0] ?? null)} />
          </div>
        </header>

        {error && <div className="notice">{error}</div>}

        <section className="overview-grid">
          <button className="upload-banner" onClick={() => inputRef.current?.click()} disabled={uploading || backendOnline === "offline"}>
            <span>
              <strong>{uploading ? "正在执行AI诊断" : "上传巡检图片开始诊断"}</strong>
              <small>{backendOnline === "offline" ? "后端当前离线，请先启动服务再上传巡检图片" : uploading ? "6个OpenClaw兼容Agent正在依次完成质检、识别、量化、评估、复核路由和报告归档" : "支持桥梁、道路、隧道、构件表面巡检图，生成标注图与PDF报告"}</small>
            </span>
            <i>{uploading ? <Loader2 className="spin" size={22} /> : <Upload size={22} />}</i>
          </button>
          <Metric icon={<Archive size={20} />} label="检测记录" value={stats.total.toString()} />
          <Metric icon={<ShieldAlert size={20} />} label="待复核" value={stats.pending.toString()} tone="amber" />
          <Metric icon={<Activity size={20} />} label="高风险" value={stats.high.toString()} tone="red" />
          <Metric icon={<Microscope size={20} />} label="平均置信度" value={`${Math.round(stats.avg * 100)}%`} />
        </section>

        <section className="workbench">
          <aside className="task-panel">
            <div className="section-title">
              <History size={18} />
              <h2>巡检任务队列</h2>
            </div>
            <div className="record-list">
              {records.map((record) => (
                <button key={record.id} className={`record-row ${active?.id === record.id ? "active" : ""}`} onClick={() => selectRecord(record.id)}>
                  <span className={`risk-chip risk-${record.risk_level}`}>{record.risk_level}</span>
                  <span className="record-copy">
                    <strong>{record.filename}</strong>
                    <small>{record.created_at}</small>
                  </span>
                  <span className="record-meta">
                    <em>{record.detection_count} 个候选</em>
                    <em>{record.review_status}</em>
                  </span>
                </button>
              ))}
              {!records.length && <div className="empty">暂无检测记录</div>}
            </div>
          </aside>

          <section className="diagnosis-panel">
            {!active ? (
              <div className="drop-zone" onClick={() => inputRef.current?.click()}>
                <FileImage size={42} />
                <h2>上传一张巡检图片</h2>
                <p>系统将自动完成图像质量检查、病害候选识别、风险判断、人工复核入口和报告生成。</p>
              </div>
            ) : (
              <ResultView
                active={active}
                reviewRisk={reviewRisk}
                setReviewRisk={setReviewRisk}
                reviewNote={reviewNote}
                setReviewNote={setReviewNote}
                saveReview={saveReview}
              />
            )}
          </section>
        </section>
      </section>
    </main>
  );
}

function Metric({ icon, label, value, tone = "blue" }: { icon: React.ReactNode; label: string; value: string; tone?: "blue" | "amber" | "red" }) {
  return (
    <div className={`metric metric-${tone}`}>
      <div>{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ResultView({
  active,
  reviewRisk,
  setReviewRisk,
  reviewNote,
  setReviewNote,
  saveReview
}: {
  active: RecordDetail;
  reviewRisk: RiskLevel;
  setReviewRisk: (value: RiskLevel) => void;
  reviewNote: string;
  setReviewNote: (value: string) => void;
  saveReview: () => void;
}) {
  const strongest = active.detections.reduce((max, d) => Math.max(max, d.confidence), 0);
  const areaRatio = Number(active.metrics.total_area_ratio || 0);
  const readable = active.quality.readable ? "可识别" : "需补拍";
  const displayWorkflow = getSixAgentWorkflow(active.workflow);

  return (
    <>
      <header className="result-hero">
        <div>
          <p className="eyebrow">Record #{active.id}</p>
          <h2>{active.filename}</h2>
          <p>{active.risk_reason}</p>
        </div>
        <div className={`risk-score risk-${active.risk_level}`}>
          <span>{active.risk_level}</span>
          <small>风险等级</small>
        </div>
      </header>

      <section className="summary-bar">
        <SummaryItem label="候选区域" value={`${active.detection_count} 处`} />
        <SummaryItem label="最高置信度" value={`${Math.round(strongest * 100)}%`} />
        <SummaryItem label="病害面积占比" value={`${(areaRatio * 100).toFixed(2)}%`} />
        <SummaryItem label="图像质量" value={readable} />
        <SummaryItem label="复核状态" value={active.review_status} />
      </section>

      <section className="image-stage">
        <figure>
          <figcaption><FileImage size={16} />原始巡检图</figcaption>
          <img src={assetUrl(active.original_url)} alt="原始巡检图" />
        </figure>
        <figure>
          <figcaption><AlertTriangle size={16} />AI标注结果</figcaption>
          <img src={assetUrl(active.annotated_url)} alt="AI标注结果" />
        </figure>
      </section>

      <section className="agent-lane">
        <div className="section-title">
          <Workflow size={18} />
          <h3>6个OpenClaw Agent协同工作流</h3>
        </div>
        <div className="agent-role-strip">
          {agentRoles.map((role) => <span key={role}>{role}</span>)}
        </div>
        <div className="workflow-track">
          {displayWorkflow.map((step, index) => (
            <article className="workflow-node" key={step.agent}>
              <span>{index + 1}</span>
              <strong>{step.label}</strong>
              <small>{step.agent} · {step.duration_ms}ms</small>
              <p>{step.summary}</p>
              {index < displayWorkflow.length - 1 && <ChevronRight className="node-arrow" size={17} />}
            </article>
          ))}
        </div>
      </section>

      <section className="detail-grid">
        <div className="table-panel">
          <div className="section-title">
            <GitBranch size={18} />
            <h3>病害候选明细</h3>
          </div>
          <table>
            <thead>
              <tr>
                <th>类型</th>
                <th>置信度</th>
                <th>面积占比</th>
                <th>长度估计(px)</th>
                <th>坐标</th>
              </tr>
            </thead>
            <tbody>
              {active.detections.map((item, index) => (
                <tr key={`${item.kind}-${index}`}>
                  <td>{item.label}</td>
                  <td>{Math.round(item.confidence * 100)}%</td>
                  <td>{(item.area_ratio * 100).toFixed(2)}%</td>
                  <td>{item.length_estimate}</td>
                  <td>{item.bbox.join(", ")}</td>
                </tr>
              ))}
              {!active.detections.length && (
                <tr>
                  <td colSpan={5}>未发现明显病害候选区域</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="review-panel">
          <div className="section-title">
            <CheckCircle2 size={18} />
            <h3>人工复核与报告</h3>
          </div>
          <div className="review-grid">
            <label>
              <span>复核风险</span>
              <select value={reviewRisk} onChange={(event) => setReviewRisk(event.target.value as RiskLevel)}>
                {riskOptions
                  .slice()
                  .sort((a, b) => riskRank[a] - riskRank[b])
                  .map((risk) => <option key={risk}>{risk}</option>)}
              </select>
            </label>
            <label className="note-field">
              <span>复核意见</span>
              <textarea value={reviewNote} onChange={(event) => setReviewNote(event.target.value)} placeholder="填写现场复核意见、处理建议或持续观察说明" />
            </label>
            <div className="review-actions">
              <button className="primary" onClick={saveReview}>
                <CheckCircle2 size={18} />保存复核
              </button>
              <a className="download" href={`/api/records/${active.id}/report`} target="_blank" rel="noreferrer">
                <Download size={18} />下载PDF报告
              </a>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
