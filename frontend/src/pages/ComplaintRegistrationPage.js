import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createComplaint, listCategories } from "../services/complaintService";
import Toast from "../components/Toast";

export default function ComplaintRegistrationPage() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({ category_id: "", subject: "", description: "", priority: "Medium" });
  const [errors, setErrors] = useState({});
  const [toast, setToast] = useState({ message: "" });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    listCategories().then((c) => {
      setCategories(c);
      if (c.length) setForm((f) => ({ ...f, category_id: c[0].category_id }));
    });
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const validate = () => {
    const e = {};
    if (!form.category_id) e.category_id = "Pick a category";
    if (!form.subject.trim() || form.subject.length < 3) e.subject = "Subject must be at least 3 characters";
    if (!form.description.trim() || form.description.length < 10) e.description = "Describe the issue in at least 10 characters";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      const c = await createComplaint({
        ...form,
        category_id: parseInt(form.category_id, 10),
      });
      setToast({ message: `Complaint ${c.complaint_number} registered`, type: "success" });
      setTimeout(() => navigate(`/complaints/${c.complaint_id}`), 600);
    } catch (e) {
      setToast({ message: e?.response?.data?.detail || "Submission failed", type: "error" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Register a Complaint</h1>
      <p className="page-subtitle">Tell us what's wrong — we'll take it from there.</p>

      <form onSubmit={handleSubmit} className="card form" style={{ maxWidth: 720 }}>
        <div className="form-group">
          <label>Category *</label>
          <select value={form.category_id} onChange={set("category_id")}>
            <option value="">-- Select --</option>
            {categories.map((c) => (
              <option key={c.category_id} value={c.category_id}>{c.category_name}</option>
            ))}
          </select>
          {errors.category_id && <span className="form-error">{errors.category_id}</span>}
        </div>

        <div className="form-group">
          <label>Subject *</label>
          <input value={form.subject} onChange={set("subject")} placeholder="Short summary, e.g. 'Wrong invoice amount'" />
          {errors.subject && <span className="form-error">{errors.subject}</span>}
        </div>

        <div className="form-group">
          <label>Description *</label>
          <textarea rows={6} value={form.description} onChange={set("description")}
            placeholder="What happened? Steps to reproduce, expected vs. actual, dates and reference numbers…" />
          {errors.description && <span className="form-error">{errors.description}</span>}
        </div>

        <div className="form-group">
          <label>Priority</label>
          <select value={form.priority} onChange={set("priority")}>
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
            <option>Critical</option>
          </select>
          <div className="form-help">
            SLA: Critical 4h • High 24h • Medium 48h • Low 72h
          </div>
        </div>

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>Cancel</button>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Submitting…" : "Submit Complaint"}
          </button>
        </div>
      </form>

      <Toast {...toast} onClose={() => setToast({ message: "" })} />
    </div>
  );
}
