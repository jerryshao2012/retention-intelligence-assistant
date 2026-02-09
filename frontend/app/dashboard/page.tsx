"use client";

import { useEffect, useMemo, useState } from "react";
import Nav from "../../components/Nav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface MetricRow {
  id: string;
  window_start: string;
  window_end: string;
  compliance: number;
  completeness: number;
  guardrail_blocks: number;
  total_messages: number;
  created_at: string;
}

interface MetricsResponse {
  metrics: MetricRow[];
  sla: {
    compliance: number;
    completeness: number;
  };
}

interface JudgeRun {
  id: string;
  conversation_id: string;
  scoring_id: string;
  scoring_version: string;
  scoring_revision: string;
  model: string;
  parsed: Record<string, unknown>;
  created_at: string;
}

function TrendChart({ values, stroke, sla }: { values: number[]; stroke: string; sla: number }) {
  if (values.length === 0) return null;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const points = values
    .map((v, idx) => {
      const x = (idx / Math.max(values.length - 1, 1)) * 100;
      const y = 100 - ((v - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");
  const slaY = 100 - ((sla - min) / range) * 100;

  return (
    <svg className="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none">
      <defs>
        <linearGradient id="trendBand" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="rgba(31, 138, 91, 0.2)" />
          <stop offset="100%" stopColor="rgba(210, 31, 38, 0.12)" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="100" height="100" fill="url(#trendBand)" />
      <line x1="0" y1={slaY} x2="100" y2={slaY} stroke="var(--accent)" strokeDasharray="4 4" />
      <polyline fill="none" stroke={stroke} strokeWidth="3" points={points} />
    </svg>
  );
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<MetricRow[]>([]);
  const [sla, setSla] = useState({ compliance: 0.9, completeness: 0.85 });
  const [judgeRuns, setJudgeRuns] = useState<JudgeRun[]>([]);

  useEffect(() => {
    let active = true;
    async function fetchMetrics() {
      const res = await fetch(`${API_URL}/metrics?limit=24`);
      const data: MetricsResponse = await res.json();
      if (active) {
        setMetrics(data.metrics || []);
        if (data.sla) setSla(data.sla);
      }
    }

    async function fetchJudgeRuns() {
      const res = await fetch(`${API_URL}/judge-runs?limit=12`);
      const data = await res.json();
      if (active) setJudgeRuns(data.runs || []);
    }

    fetchMetrics();
    fetchJudgeRuns();
    const interval = setInterval(fetchMetrics, 5000);
    const judgeInterval = setInterval(fetchJudgeRuns, 10000);
    return () => {
      active = false;
      clearInterval(interval);
      clearInterval(judgeInterval);
    };
  }, []);

  const latest = metrics[0];
  const complianceSeries = useMemo(() => metrics.map((m) => m.compliance).reverse(), [metrics]);
  const completenessSeries = useMemo(() => metrics.map((m) => m.completeness).reverse(), [metrics]);
  const complianceAlert = latest && latest.compliance < sla.compliance;
  const completenessAlert = latest && latest.completeness < sla.completeness;

  return (
    <div>
      <Nav />
      <div className="container">
        <div className="dashboard-header">
          <div>
            <h1>AI Evaluation Dashboard</h1>
            <p>Batch metrics refreshed every 5 minutes.</p>
          </div>
          <span className="badge">Near Real Time</span>
        </div>

        {(complianceAlert || completenessAlert) && (
          <div className="alert">
            <strong>Attention required:</strong>
            {complianceAlert && <span> Compliance is below SLA ({(sla.compliance * 100).toFixed(0)}%).</span>}
            {completenessAlert && <span> Completeness is below SLA ({(sla.completeness * 100).toFixed(0)}%).</span>}
          </div>
        )}

        <div className="grid">
          <div className="card">
            <div className="metric-row">
              <div>
                <div className="metric">{latest ? (latest.compliance * 100).toFixed(1) + "%" : "--"}</div>
                <div>Compliance</div>
              </div>
              <TrendChart values={complianceSeries} stroke="var(--success)" sla={sla.compliance} />
            </div>
          </div>
          <div className="card">
            <div className="metric-row">
              <div>
                <div className="metric">{latest ? (latest.completeness * 100).toFixed(1) + "%" : "--"}</div>
                <div>Completeness</div>
              </div>
              <TrendChart values={completenessSeries} stroke="var(--jerry-red)" sla={sla.completeness} />
            </div>
          </div>
          <div className="card">
            <div className="metric">{latest ? latest.guardrail_blocks : "--"}</div>
            <div>Guardrail Blocks</div>
          </div>
          <div className="card">
            <div className="metric">{latest ? latest.total_messages : "--"}</div>
            <div>Total Messages</div>
          </div>
        </div>

        <div className="panel" style={{ marginTop: 24 }}>
          <h2>Recent Batches</h2>
          <div className="grid">
            {metrics.map((m) => (
              <div key={m.id} className="card">
                <strong>{new Date(m.window_end).toLocaleTimeString()}</strong>
                <p>Compliance: {(m.compliance * 100).toFixed(1)}%</p>
                <p>Completeness: {(m.completeness * 100).toFixed(1)}%</p>
                <p>Blocks: {m.guardrail_blocks}</p>
                <p>Messages: {m.total_messages}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="panel" style={{ marginTop: 24 }}>
          <h2>LLM Judge Runs</h2>
          <div className="grid">
            {judgeRuns.map((run) => (
              <div key={run.id} className="card">
                <strong>
                  {run.scoring_id} {run.scoring_version}
                </strong>
                <p>Revision: {run.scoring_revision}</p>
                <p>Model: {run.model}</p>
                <p>Result: {JSON.stringify(run.parsed)}</p>
                <p>Time: {new Date(run.created_at).toLocaleTimeString()}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
