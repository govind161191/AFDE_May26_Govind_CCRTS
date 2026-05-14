import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listComplaints, listCategories } from "../services/complaintService";
import { StatusBadge, PriorityBadge, SLABadge } from "../components/Badges";

const STATUSES = ["Open", "Assigned", "In Progress", "Pending Customer Response", "Escalated", "Resolved", "Closed"];
const PRIORITIES = ["Low", "Medium", "High", "Critical"];

export default function ComplaintListPage({ defaultFilters = {}, title = "Complaints", subtitle }) {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ status: "", priority: "", category_id: "", search: "", ...defaultFilters });
  const [loading, setLoading] = useState(false);

  const refresh = () => {
    setLoading(true);
    const params = {};
    if (filters.status) params.status = filters.status;
    if (filters.priority) params.priority = filters.priority;
    if (filters.category_id) params.category_id = filters.category_id;
    if (filters.search) params.search = filters.search;
    if (filters.escalated !== undefined) params.escalated = filters.escalated;
    listComplaints(params)
      .then(setItems)
      .finally(() => setLoading(false));
  };

  useEffect(() => { listCategories().then(setCategories).catch(() => {}); }, []);
  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, [JSON.stringify(filters)]);

  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });

  return (
    <div className="page">
      <h1 className="page-title">{title}</h1>
      {subtitle && <p className="page-subtitle">{subtitle}</p>}

      <div className="card filter-bar">
        <input className="filter-input" placeholder="Search by subject, description, or number…"
          value={filters.search} onChange={set("search")} />
        <select value={filters.status} onChange={set("status")}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select value={filters.priority} onChange={set("priority")}>
          <option value="">All priorities</option>
          {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
        </select>
        <select value={filters.category_id} onChange={set("category_id")}>
          <option value="">All categories</option>
          {categories.map((c) => <option key={c.category_id} value={c.category_id}>{c.category_name}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="loading">Loading complaints…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">No complaints match these filters.</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Number</th>
              <th>Subject</th>
              <th>Customer</th>
              <th>Agent</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Status</th>
              <th>SLA</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.complaint_id}>
                <td><Link to={`/complaints/${c.complaint_id}`} className="link">{c.complaint_number}</Link></td>
                <td>{c.subject}</td>
                <td>{c.customer_name}</td>
                <td>{c.assigned_agent_name || <span className="muted">unassigned</span>}</td>
                <td>{c.category_name}</td>
                <td><PriorityBadge priority={c.priority} /></td>
                <td><StatusBadge status={c.status} /></td>
                <td><SLABadge breached={c.sla_breached} /></td>
                <td className="muted">{new Date(c.created_date).toLocaleString()}</td>
                <td><Link className="btn btn-sm" to={`/complaints/${c.complaint_id}`}>Open</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
