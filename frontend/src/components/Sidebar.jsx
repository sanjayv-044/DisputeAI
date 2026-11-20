import React from "react";
import {
  LayoutDashboard,
  FilePlus,
  History,
  ShieldAlert,
  BarChart3,
  SearchCheck,
  Activity,
  Sliders,
  User,
  LogOut,
  ShieldCheck,
  FileText
} from "lucide-react";

export default function Sidebar({ user, activeTab, setActiveTab, onLogout }) {
  const isAdmin = user?.role === "admin";

  const customerNav = [
    { id: "dashboard", label: "My Dashboard", icon: LayoutDashboard },
    { id: "submit-dispute", label: "Submit Dispute", icon: FilePlus },
    { id: "my-complaints", label: "Track Complaints", icon: History },
    { id: "profile", label: "My Profile", icon: User },
  ];

  const adminNav = [
    { id: "admin-analytics", label: "Analytics Dashboard", icon: BarChart3 },
    { id: "admin-disputes", label: "All Complaints", icon: FileText },
    { id: "admin-escalations", label: "High-Risk & Escalated", icon: ShieldAlert },
    { id: "admin-evaluation", label: "AI Evaluation Suite", icon: SearchCheck },
    { id: "admin-monitoring", label: "Telemetry & Metrics", icon: Activity },
  ];

  const currentNav = isAdmin ? adminNav : customerNav;

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={26} color="#06b6d4" />
          </div>
          <div>
            <h2>DisputeAI</h2>
            <span>Banking Intelligence</span>
          </div>
        </div>

        <div className="role-pill">
          <span className={`role-indicator ${isAdmin ? "indicator-admin" : "indicator-customer"}`}></span>
          <span className="role-text">{isAdmin ? "Admin Portal" : "Customer Portal"}</span>
        </div>

        <nav className="nav-menu">
          <p className="nav-heading">NAVIGATION</p>
          {currentNav.map((item) => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                className={`nav-btn ${active ? "active" : ""}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={18} className="nav-icon" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="sidebar-bottom">
        <div className="user-brief">
          <div className="user-avatar">{user?.full_name?.slice(0, 2).toUpperCase() || "US"}</div>
          <div className="user-info">
            <strong>{user?.full_name || "User"}</strong>
            <span>{user?.email || ""}</span>
          </div>
        </div>
        <button className="logout-btn" onClick={onLogout} title="Log out">
          <LogOut size={16} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
