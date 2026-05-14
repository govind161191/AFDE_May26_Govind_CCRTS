import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate(location.state?.from?.pathname || "/", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Login failed");
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">
          <span aria-hidden="true">🛎️</span>
          <h1>CCRTS</h1>
          <p>Customer Complaint &amp; Resolution Tracking</p>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          <h2>Sign in</h2>
          {error && <div className="form-error-banner">{error}</div>}
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? "Signing in…" : "Sign In"}
          </button>
          <div className="auth-foot">
            New here? <Link to="/register">Create a customer account</Link>
          </div>
        </form>
        <div className="auth-hint">
          <strong>Demo accounts</strong>
          <ul>
            <li>Admin: admin@ccrts.io / Admin@123</li>
            <li>Supervisor: sarah@ccrts.io / Super@123</li>
            <li>Agent: alex@ccrts.io / Agent@123</li>
            <li>Customer: govind@example.com / Customer@123</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
