import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Wraps a route element and redirects to /login when no user is logged in.
 * Optionally restricts to a set of roles.
 */
export default function ProtectedRoute({ children, roles }) {
  const { user, hasRole } = useAuth();
  const loc = useLocation();
  if (!user) return <Navigate to="/login" state={{ from: loc }} replace />;
  if (roles && !hasRole(...roles)) {
    return <div className="page"><h1 className="page-title">403 — Forbidden</h1>
      <p className="muted">You don't have permission to access this page.</p></div>;
  }
  return children;
}
