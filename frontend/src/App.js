import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import ComplaintRegistrationPage from "./pages/ComplaintRegistrationPage";
import ComplaintListPage from "./pages/ComplaintListPage";
import ComplaintDetailPage from "./pages/ComplaintDetailPage";
import AgentQueuePage from "./pages/AgentQueuePage";
import EscalationsPage from "./pages/EscalationsPage";
import ReportsPage from "./pages/ReportsPage";
import UserManagementPage from "./pages/UserManagementPage";

export default function App() {
  const { user, hasRole } = useAuth();

  // Customers go to their complaints list as "home"; staff go to dashboard
  const home = user
    ? hasRole("Customer")
      ? <Navigate to="/complaints" replace />
      : <DashboardPage />
    : <Navigate to="/login" replace />;

  return (
    <div className="app">
      {user && <Navbar />}
      <main className={user ? "main-content" : ""}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route path="/" element={<ProtectedRoute>{home}</ProtectedRoute>} />

          <Route path="/complaints" element={
            <ProtectedRoute>
              <ComplaintListPage title="Complaints"
                subtitle={hasRole("Customer") ? "Your registered complaints" : "All complaints"} />
            </ProtectedRoute>} />

          <Route path="/complaints/new" element={
            <ProtectedRoute><ComplaintRegistrationPage /></ProtectedRoute>} />

          <Route path="/complaints/:id" element={
            <ProtectedRoute><ComplaintDetailPage /></ProtectedRoute>} />

          <Route path="/queue" element={
            <ProtectedRoute roles={["Support Agent"]}><AgentQueuePage /></ProtectedRoute>} />

          <Route path="/escalations" element={
            <ProtectedRoute roles={["Admin", "Supervisor"]}><EscalationsPage /></ProtectedRoute>} />

          <Route path="/reports" element={
            <ProtectedRoute roles={["Admin", "Supervisor"]}><ReportsPage /></ProtectedRoute>} />

          <Route path="/users" element={
            <ProtectedRoute roles={["Admin"]}><UserManagementPage /></ProtectedRoute>} />

          <Route path="*" element={<div className="page"><h1>404</h1></div>} />
        </Routes>
      </main>
      {user && (
        <footer className="footer">
          CCRTS — AFDE Capstone Phase 1 • Built by Govind
        </footer>
      )}
    </div>
  );
}
