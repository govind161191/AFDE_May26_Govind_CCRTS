import api from "../api";

export const listUsers = (params = {}) => api.get("/users", { params }).then((r) => r.data);
export const listAgents = () => api.get("/users/agents").then((r) => r.data);
export const createUser = (payload) => api.post("/users", payload).then((r) => r.data);
export const updateUser = (id, payload) => api.put(`/users/${id}`, payload).then((r) => r.data);
export const deleteUser = (id) => api.delete(`/users/${id}`).then((r) => r.data);

export const getDashboard = () => api.get("/dashboard/stats").then((r) => r.data);

export const listNotifications = (unreadOnly = false) =>
  api.get("/notifications", { params: { unread_only: unreadOnly } }).then((r) => r.data);
export const markNotificationRead = (id) =>
  api.post(`/notifications/${id}/read`).then((r) => r.data);
export const markAllRead = () =>
  api.post(`/notifications/read-all`).then((r) => r.data);
