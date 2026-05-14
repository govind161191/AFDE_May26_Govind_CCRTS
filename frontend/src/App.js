import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import ComplaintListPage from "./pages/ComplaintListPage";
import ComplaintRegistrationPage from "./pages/ComplaintRegistrationPage";

export default function App() {
  const { user } = useAuth();
  return (
    <div className="app">
      {user && <Navbar />}
      <main className={user ? "main-content" : ""}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/complaints" element={<ProtectedRoute><ComplaintListPage title="Complaints" /></ProtectedRoute>} />
          <Route path="/complaints/new" element={<ProtectedRoute><ComplaintRegistrationPage /></ProtectedRoute>} />
        </Routes>
      </main>
    </div>
  );
}
