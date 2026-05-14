/**
 * Axios client with JWT injection.
 *
 * Reads the token from localStorage on every request, so logout/login
 * are reflected automatically. Override the base URL via REACT_APP_API_URL.
 */
import axios from "axios";

const baseURL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL,
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ccrts_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-redirect to login on 401 / 403 (except for the login endpoint itself)
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err?.response?.status;
    const url = err?.config?.url || "";
    if (status === 401 && !url.includes("/auth/login")) {
      localStorage.removeItem("ccrts_token");
      localStorage.removeItem("ccrts_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export default api;
