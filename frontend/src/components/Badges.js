import React from "react";

const STATUS_COLORS = {
  "Open": "blue",
  "Assigned": "purple",
  "In Progress": "amber",
  "Pending Customer Response": "amber",
  "Escalated": "red",
  "Resolved": "green",
  "Closed": "gray",
};

const PRIORITY_COLORS = {
  "Critical": "red",
  "High": "amber",
  "Medium": "blue",
  "Low": "gray",
};

export function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] || "gray";
  return <span className={`badge badge-${color}`}>{status}</span>;
}

export function PriorityBadge({ priority }) {
  const color = PRIORITY_COLORS[priority] || "gray";
  return <span className={`badge badge-${color}`}>{priority}</span>;
}

export function SLABadge({ breached }) {
  return breached
    ? <span className="badge badge-red">⚠ SLA Breach</span>
    : <span className="badge badge-green">On Track</span>;
}
