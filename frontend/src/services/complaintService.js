import api from "../api";

export const listComplaints = (params = {}) =>
  api.get("/complaints", { params }).then((r) => r.data);

export const getComplaint = (id) =>
  api.get(`/complaints/${id}`).then((r) => r.data);

export const createComplaint = (payload) =>
  api.post("/complaints", payload).then((r) => r.data);

export const updateComplaint = (id, payload) =>
  api.put(`/complaints/${id}`, payload).then((r) => r.data);

export const deleteComplaint = (id) =>
  api.delete(`/complaints/${id}`).then((r) => r.data);

export const getHistory = (id) =>
  api.get(`/complaints/${id}/history`).then((r) => r.data);

export const sweepEscalations = () =>
  api.post("/complaints/sweep-escalations").then((r) => r.data);

// Attachments
export const listAttachments = (id) =>
  api.get(`/complaints/${id}/attachments`).then((r) => r.data);
export const uploadAttachment = (id, file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post(`/complaints/${id}/attachments`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

// Feedback
export const submitFeedback = (id, payload) =>
  api.post(`/complaints/${id}/feedback`, payload).then((r) => r.data);
export const getFeedback = (id) =>
  api.get(`/complaints/${id}/feedback`).then((r) => r.data);

// Categories
export const listCategories = () =>
  api.get("/categories").then((r) => r.data);
