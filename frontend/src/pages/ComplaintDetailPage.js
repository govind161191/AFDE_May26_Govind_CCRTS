import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getComplaint, updateComplaint, getHistory,
  listAttachments, uploadAttachment,
  submitFeedback, getFeedback,
} from "../services/complaintService";
import { listAgents } from "../services/userService";
import { useAuth } from "../context/AuthContext";
import { StatusBadge, PriorityBadge, SLABadge } from "../components/Badges";
import Modal from "../components/Modal";
import Toast from "../components/Toast";

const STATUSES = ["Open", "Assigned", "In Progress", "Pending Customer Response", "Escalated", "Resolved", "Closed"];
const PRIORITIES = ["Low", "Medium", "High", "Critical"];

export default function ComplaintDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const [c, setC] = useState(null);
  const [history, setHistory] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [agents, setAgents] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [toast, setToast] = useState({ message: "" });

  const [editStatus, setEditStatus] = useState(false);
  const [statusForm, setStatusForm] = useState({ status: "", comment: "", resolution_comment: "" });
  const [assignForm, setAssignForm] = useState({ assigned_agent_id: "", priority: "", comment: "" });
  const [feedbackForm, setFeedbackForm] = useState({ rating: 5, comments: "" });
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  const refresh = async () => {
    try {
      const data = await getComplaint(id);
      setC(data);
      setStatusForm((s) => ({ ...s, status: data.status }));
      setAssignForm((a) => ({ ...a, assigned_agent_id: data.assigned_agent_id || "", priority: data.priority }));
      setHistory(await getHistory(id));
      try { setAttachments(await listAttachments(id)); } catch { setAttachments([]); }
      if (data.status === "Resolved" || data.status === "Closed") {
        try { setFeedback(await getFeedback(id)); } catch { setFeedback(null); }
      }
    } catch (e) {
      setToast({ message: e?.response?.data?.detail || "Failed to load", type: "error" });
    }
  };

  useEffect(() => { refresh(); if (hasRole("Admin", "Supervisor")) listAgents().then(setAgents).catch(() => {}); /* eslint-disable-next-line */ }, [id]);

  if (!c) return <div className="loading">Loading complaint…</div>;

  const isMine = c.customer_id === user.user_id;
  const isAssignedAgent = c.assigned_agent_id === user.user_id;
  const canManage = hasRole("Admin", "Supervisor") || isAssignedAgent;

  const handleStatusSubmit = async () => {
    try {
      const payload = { status: statusForm.status, comment: statusForm.comment };
      if (statusForm.status === "Resolved") payload.resolution_comment = statusForm.resolution_comment;
      await updateComplaint(id, payload);
      setEditStatus(false);
      setStatusForm({ ...statusForm, comment: "", resolution_comment: "" });
      refresh();
      setToast({ message: "Status updated", type: "success" });
    } catch (e) {
      setToast({ message: e?.response?.data?.detail || "Update failed", type: "error" });
    }
  };

  const handleAssign = async (e) => {
    e.preventDefault();
    try {
      const payload = {};
      if (assignForm.assigned_agent_id) payload.assigned_agent_id = parseInt(assignForm.assigned_agent_id, 10);
      if (assignForm.priority && assignForm.priority !== c.priority) payload.priority = assignForm.priority;
      if (assignForm.comment) payload.comment = assignForm.comment;
      if (Object.keys(payload).length === 0) return;
      await updateComplaint(id, payload);
      setAssignForm({ ...assignForm, comment: "" });
      refresh();
      setToast({ message: "Complaint updated", type: "success" });
    } catch (e) {
      setToast({ message: e?.response?.data?.detail || "Update failed", type: "error" });
    }
  };

  const handleAttachmentUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadAttachment(id, file);
      e.target.value = "";
      const list = await listAttachments(id);
      setAttachments(list);
      setToast({ message: `Uploaded ${file.name}`, type: "success" });
    } catch (err) {
      setToast({ message: err?.response?.data?.detail || "Upload failed", type: "error" });
    }
  };

  const handleFeedbackSubmit = async () => {
    try {
      await submitFeedback(id, feedbackForm);
      setFeedbackOpen(false);
      refresh();
      setToast({ message: "Feedback submitted — thank you!", type: "success" });
    } catch (e) {
      setToast({ message: e?.response?.data?.detail || "Feedback failed", type: "error" });
    }
  };

  return (
    <div className="page">
      <button className="btn-back" onClick={() => navigate(-1)}>← Back</button>

      <div className="detail-header">
        <div>
          <h1 className="page-title">{c.subject}</h1>
          <div className="muted">{c.complaint_number} • {c.category_name}</div>
        </div>
        <div className="detail-badges">
          <PriorityBadge priority={c.priority} />
          <StatusBadge status={c.status} />
          <SLABadge breached={c.sla_breached} />
          {c.is_escalated && <span className="badge badge-red">🔥 Escalated</span>}
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 className="section-title">Details</h3>
          <dl className="kv">
            <dt>Customer</dt><dd>{c.customer_name}</dd>
            <dt>Assigned Agent</dt><dd>{c.assigned_agent_name || <em>unassigned</em>}</dd>
            <dt>Created</dt><dd>{new Date(c.created_date).toLocaleString()}</dd>
            <dt>SLA Deadline</dt><dd>{new Date(c.sla_deadline).toLocaleString()}</dd>
            <dt>Resolved</dt><dd>{c.resolved_date ? new Date(c.resolved_date).toLocaleString() : "—"}</dd>
            <dt>Closed</dt><dd>{c.closed_date ? new Date(c.closed_date).toLocaleString() : "—"}</dd>
          </dl>
          <h3 className="section-title">Description</h3>
          <p style={{ whiteSpace: "pre-wrap" }}>{c.description}</p>
          {c.resolution_comment && (
            <>
              <h3 className="section-title">Resolution</h3>
              <p style={{ whiteSpace: "pre-wrap" }}>{c.resolution_comment}</p>
            </>
          )}
        </div>

        <div>
          {canManage && (
            <div className="card">
              <h3 className="section-title">Update Status</h3>
              {!editStatus ? (
                <button className="btn btn-primary" onClick={() => setEditStatus(true)}>Change status / Add comment</button>
              ) : (
                <div className="form">
                  <div className="form-group">
                    <label>New status</label>
                    <select value={statusForm.status} onChange={(e) => setStatusForm({ ...statusForm, status: e.target.value })}>
                      {STATUSES.map((s) => <option key={s}>{s}</option>)}
                    </select>
                  </div>
                  {statusForm.status === "Resolved" && (
                    <div className="form-group">
                      <label>Resolution comment</label>
                      <textarea rows={3} value={statusForm.resolution_comment}
                        onChange={(e) => setStatusForm({ ...statusForm, resolution_comment: e.target.value })} />
                    </div>
                  )}
                  <div className="form-group">
                    <label>Audit comment (optional)</label>
                    <textarea rows={2} value={statusForm.comment}
                      onChange={(e) => setStatusForm({ ...statusForm, comment: e.target.value })} />
                  </div>
                  <div className="form-actions">
                    <button className="btn btn-secondary" onClick={() => setEditStatus(false)}>Cancel</button>
                    <button className="btn btn-primary" onClick={handleStatusSubmit}>Save</button>
                  </div>
                </div>
              )}
            </div>
          )}

          {hasRole("Admin", "Supervisor") && (
            <div className="card">
              <h3 className="section-title">Assign / Reprioritize</h3>
              <form className="form" onSubmit={handleAssign}>
                <div className="form-group">
                  <label>Assign to agent</label>
                  <select value={assignForm.assigned_agent_id} onChange={(e) => setAssignForm({ ...assignForm, assigned_agent_id: e.target.value })}>
                    <option value="">-- Pick agent --</option>
                    {agents.map((a) => (
                      <option key={a.user_id} value={a.user_id}>{a.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Priority</label>
                  <select value={assignForm.priority} onChange={(e) => setAssignForm({ ...assignForm, priority: e.target.value })}>
                    {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Comment</label>
                  <input value={assignForm.comment} onChange={(e) => setAssignForm({ ...assignForm, comment: e.target.value })} />
                </div>
                <div className="form-actions">
                  <button className="btn btn-primary" type="submit">Apply</button>
                </div>
              </form>
            </div>
          )}

          <div className="card">
            <h3 className="section-title">Attachments</h3>
            {attachments.length === 0 ? (
              <p className="muted">No files yet.</p>
            ) : (
              <ul className="att-list">
                {attachments.map((a) => (
                  <li key={a.attachment_id}>
                    📎 {a.file_name} <span className="muted">({new Date(a.uploaded_date).toLocaleString()})</span>
                  </li>
                ))}
              </ul>
            )}
            {(isMine || canManage) && (
              <label className="file-upload">
                <input type="file" onChange={handleAttachmentUpload} />
                <span className="btn btn-secondary btn-sm">+ Add attachment</span>
              </label>
            )}
          </div>

          {(c.status === "Resolved" || c.status === "Closed") && isMine && (
            <div className="card">
              <h3 className="section-title">Feedback</h3>
              {feedback ? (
                <>
                  <div>Rating: <strong>{"★".repeat(feedback.rating)}{"☆".repeat(5 - feedback.rating)}</strong></div>
                  {feedback.comments && <p>{feedback.comments}</p>}
                </>
              ) : (
                <button className="btn btn-primary" onClick={() => setFeedbackOpen(true)}>Give feedback</button>
              )}
            </div>
          )}
        </div>
      </div>

      <h2 className="section-title">History</h2>
      <table className="data-table">
        <thead><tr><th>When</th><th>Who</th><th>Change</th><th>Comment</th></tr></thead>
        <tbody>
          {history.map((h) => (
            <tr key={h.history_id}>
              <td className="muted">{new Date(h.updated_date).toLocaleString()}</td>
              <td>{h.updated_by_name}</td>
              <td>{h.old_status ? `${h.old_status} → ${h.new_status}` : `Created (${h.new_status})`}</td>
              <td>{h.comment || <span className="muted">—</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <Modal open={feedbackOpen} title="Rate your experience" onClose={() => setFeedbackOpen(false)}>
        <div className="form">
          <div className="form-group">
            <label>Rating</label>
            <div className="star-picker">
              {[1, 2, 3, 4, 5].map((n) => (
                <button key={n} type="button" className={"star" + (n <= feedbackForm.rating ? " on" : "")}
                  onClick={() => setFeedbackForm({ ...feedbackForm, rating: n })}>★</button>
              ))}
            </div>
          </div>
          <div className="form-group">
            <label>Comments (optional)</label>
            <textarea rows={4} value={feedbackForm.comments}
              onChange={(e) => setFeedbackForm({ ...feedbackForm, comments: e.target.value })} />
          </div>
          <div className="form-actions">
            <button className="btn btn-secondary" onClick={() => setFeedbackOpen(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleFeedbackSubmit}>Submit</button>
          </div>
        </div>
      </Modal>

      <Toast {...toast} onClose={() => setToast({ message: "" })} />
    </div>
  );
}
