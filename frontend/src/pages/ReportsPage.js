import React, { useEffect, useState } from "react";
import { getDashboard } from "../services/userService";
import StatCard from "../components/StatCard";

export default function ReportsPage() {
  const [stats, setStats] = useState(null);

  useEffect(() => { getDashboard().then(setStats); }, []);

  if (!stats) return <div className="loading">Loading reports…</div>;

  const totalActive = stats.open_complaints + stats.in_progress_complaints + stats.escalated_complaints;
  const closureRate = stats.total_complaints
    ? Math.round(((stats.resolved_complaints + stats.closed_complaints) / stats.total_complaints) * 100)
    : 0;

  return (
    <div className="page">
      <h1 className="page-title">Reports</h1>
      <p className="page-subtitle">Service quality and trend analysis</p>

      <div className="stat-grid">
        <StatCard label="Closure Rate" value={`${closureRate}%`} accent="accent-green" />
        <StatCard label="Active Complaints" value={totalActive} accent="accent-amber" />
        <StatCard label="SLA Breaches" value={stats.sla_breaches} accent="accent-red" />
        <StatCard label="Avg Resolution (h)"
                  value={stats.avg_resolution_hours != null ? stats.avg_resolution_hours : "—"} accent="accent-blue" />
      </div>

      <h2 className="section-title">Complaint Category Analysis</h2>
      <table className="data-table">
        <thead><tr><th>Category</th><th>Count</th><th>Share</th></tr></thead>
        <tbody>
          {stats.by_category.map((row) => {
            const share = stats.total_complaints ? Math.round((row.count / stats.total_complaints) * 100) : 0;
            return (
              <tr key={row.category}>
                <td>{row.category}</td>
                <td>{row.count}</td>
                <td>
                  <div className="bar-track" style={{ width: 220 }}>
                    <div className="bar-fill bar-blue" style={{ width: `${share}%` }} />
                  </div>
                  <span className="muted" style={{ marginLeft: 8 }}>{share}%</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h2 className="section-title">Priority Distribution</h2>
      <table className="data-table">
        <thead><tr><th>Priority</th><th>Count</th></tr></thead>
        <tbody>
          {stats.by_priority.map((row) => (
            <tr key={row.category}><td>{row.category}</td><td>{row.count}</td></tr>
          ))}
        </tbody>
      </table>

      <h2 className="section-title">Agent Performance</h2>
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
              <td>{a.sla_breaches}</td>
              <td>{a.assigned ? `${Math.round((a.resolved / a.assigned) * 100)}%` : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
