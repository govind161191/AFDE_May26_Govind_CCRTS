/**
 * AuthContext — owns the current user, token, and login/logout actions.
 *
 * Persists token + user to localStorage so a page reload keeps the session.
 */
import React, { createContext, useContext, useEffect, useState } from "react";
import api from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ccrts_user")); }
    catch { return null; }
  });
  const [loading, setLoading] = useState(false);

  // On mount, validate the cached token by hitting /auth/me
  useEffect(() => {
    const token = localStorage.getItem("ccrts_token");
    if (!token || !user) return;
    api.get("/auth/me")
      .then((r) => {
        setUser(r.data);
        localStorage.setItem("ccrts_user", JSON.stringify(r.data));
      })
      .catch(() => logout());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const r = await api.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("ccrts_token", r.data.access_token);
      localStorage.setItem("ccrts_user", JSON.stringify(r.data.user));
      setUser(r.data.user);
      return r.data.user;
    } finally {
      setLoading(false);
    }
  };

  const register = async (payload) => {
    await api.post("/auth/register", payload);
    return login(payload.email, payload.password);
  };

  const logout = () => {
    localStorage.removeItem("ccrts_token");
    localStorage.removeItem("ccrts_user");
    setUser(null);
  };

  const hasRole = (...roles) => user && roles.includes(user.role_name);

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
