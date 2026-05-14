import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import NotificationBell from "./NotificationBell";

/**
 * Top navigation — links shown depend on the user's role.
 */
export default function Navbar() {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const links = [
    { to: "/", label: "Dashboard", roles: ["Admin", "Supervisor", "Support Agent"] },
    { to: "/complaints", label: "Complaints", roles: ["Admin", "Supervisor", "Support Agent", "Customer"] },
    { to: "/complaints/new", label: "+ New Complaint", roles: ["Customer", "Admin"] },
    { to: "/queue", label: "Work Queue", roles: ["Support Agent"] },
    { to: "/escalations", label: "Escalations", roles: ["Admin", "Supervisor"] },
    { to: "/reports", label: "Reports", roles: ["Admin", "Supervisor"] },
    { to: "/users", label: "Users", roles: ["Admin"] },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="brand-icon" aria-hidden="true">🛎️</span>
        <span className="brand-text">CCRTS</span>
        <span className="brand-tagline">Complaint Tracking</span>
      </div>
      <ul className="navbar-links">
        {links.filter((l) => hasRole(...l.roles)).map((l) => (
          <li key={l.to}>
            <NavLink to={l.to} end={l.to === "/"}
              className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
              {l.label}
            </NavLink>
          </li>
        ))}
      </ul>
      <div className="navbar-right">
        <NotificationBell />
        <span className="navbar-user">
          <span className="user-name">{user?.name}</span>
          <span className={`role-tag role-${(user?.role_name || "").replace(/\s/g, "-").toLowerCase()}`}>
            {user?.role_name}
          </span>
        </span>
        <button className="btn-logout" onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  );
}
