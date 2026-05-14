import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", phone: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">
          <span aria-hidden="true">🛎️</span>
          <h1>CCRTS</h1>
          <p>Create your customer account</p>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          <h2>Register</h2>
          {error && <div className="form-error-banner">{error}</div>}
          <div className="form-group">
            <label>Full name</label>
            <input value={form.name} onChange={set("name")} required />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={form.email} onChange={set("email")} required />
          </div>
          <div className="form-group">
            <label>Phone</label>
            <input value={form.phone} onChange={set("phone")} />
          </div>
          <div className="form-group">
            <label>Password (min 6 chars)</label>
            <input type="password" value={form.password} onChange={set("password")} required minLength={6} />
          </div>
          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? "Creating account…" : "Create account"}
          </button>
          <div className="auth-foot">
            Already have an account? <Link to="/login">Sign in</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
