import React, { useEffect, useState } from "react";
import StatCard from "../components/StatCard";
import { getDashboard } from "../services/userService";
import { sweepEscalations } from "../services/complaintService";
import Toast from "../components/Toast";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState({ message: "" });

  const refresh = () =>
    getDashboard().then(setStats).catch((e) => setError(e?.message || "Failed to load"));

  useEffect(() => { refresh(); }, []);

  const runSweep = async () => {
    try {
      const r = await sweepEscalations();
      setToast({ message: `Escalation sweep: ${r.escalated} complaints escalated`, type: "info" });
      refresh();
    } catch (e) {
      setToast({ message: e?.response?.data?.detail || "Sweep failed", type: "error" });
    }
  };

  if (error) return <div className="error-banner">{error}</div>;
  if (!stats) return <div className="loading">Loading dashboard…</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Operational overview</p>
        </div>
        <button className="btn btn-secondary" onClick={runSweep}>Run Escalation Sweep</button>
      </div>

      <div className="stat-grid">
        <StatCard label="Total Complaints"   value={stats.total_complaints}        accent="accent-blue" />
        <StatCard label="Open"               value={stats.open_complaints}         accent="accent-purple" />
        <StatCard label="In Progress"        value={stats.in_progress_complaints}  accent="accent-amber" />
        <StatCard label="Resolved"           value={stats.resolved_complaints}     accent="accent-green" />
        <StatCard label="Escalated"          value={stats.escalated_complaints}    accent="accent-red" />
        <StatCard label="SLA Breaches"       value={stats.sla_breaches}            accent="accent-red"
                  hint={stats.sla_breaches > 0 ? "Action required" : "All on track"} />
        <StatCard label="Avg Resolution"     value={stats.avg_resolution_hours != null ? `${stats.avg_resolution_hours} h` : "—"}
                  accent="accent-blue" />
        <StatCard label="Closed"             value={stats.closed_complaints}       accent="accent-gray" />
      </div>

      <div className="grid-2">
        <div>
          <h2 className="section-title">By Category</h2>
          <Bars data={stats.by_category} colorClass="bar-blue" />
        </div>
        <div>
          <h2 className="section-title">By Priority</h2>
          <Bars data={stats.by_priority} colorClass="bar-amber" />
        </div>
      </div>

      <h2 className="section-title">Agent Performance</h2>
      {stats.agent_performance.length === 0 ? (
        <div className="empty-state">No support agents registered yet.</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr><th>Agent</th><th>Assigned</th><th>Resolved</th><th>SLA Breaches</th><th>Resolution Rate</th></tr>
          </thead>
          <tbody>
            {stats.agent_performance.map((a) => (
              <tr key={a.agent_id}>
                <td>{a.agent_name}</td>
                <td>{a.assigned}</td>
                <td>{a.resolved}</td>
                <td>{a.sla_breaches > 0 ? <span className="badge badge-red">{a.sla_breaches}</span> : 0}</td>
                <td>{a.assigned ? `${Math.round((a.resolved / a.assigned) * 100)}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <Toast {...toast} onClose={() => setToast({ message: "" })} />
    </div>
  );
}

function Bars({ data, colorClass }) {
  if (!data || data.length === 0) {
    return <div className="empty-state">No data yet.</div>;
  }
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="bars">
      {data.map((d) => (
        <div className="bar-row" key={d.category}>
          <div className="bar-label">{d.category}</div>
          <div className="bar-track">
            <div className={`bar-fill ${colorClass}`} style={{ width: `${(d.count / max) * 100}%` }} />
          </div>
          <div className="bar-count">{d.count}</div>
        </div>
      ))}
    </div>
  );
}
