import React, { useState, useEffect } from "react";
import "./App.css";

import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";

// Auth Pages
import Login from "./pages/Login";
import Register from "./pages/Register";

// Customer Pages
import CustomerDashboard from "./pages/CustomerDashboard";
import CustomerSubmitDispute from "./pages/CustomerSubmitDispute";
import CustomerTrackDisputes from "./pages/CustomerTrackDisputes";
import CustomerProfile from "./pages/CustomerProfile";

// Admin Pages
import AdminDashboard from "./pages/AdminDashboard";
import AdminDisputes from "./pages/AdminDisputes";
import AdminDisputeDetail from "./pages/AdminDisputeDetail";
import AdminEvaluation from "./pages/AdminEvaluation";
import AdminMonitoring from "./pages/AdminMonitoring";

import { getCustomerDisputes, getCustomerNotifications, getCurrentUser } from "./services/api";

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem("disputeai_user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [authView, setAuthView] = useState("login"); // "login" | "register"
  const [activeTab, setActiveTab] = useState("dashboard");
  const [disputes, setDisputes] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [selectedDisputeId, setSelectedDisputeId] = useState(null);

  // Synchronize authenticated session
  useEffect(() => {
    const token = localStorage.getItem("disputeai_token");
    if (token) {
      getCurrentUser()
        .then((u) => {
          setUser(u);
          localStorage.setItem("disputeai_user", JSON.stringify(u));
          if (u.role === "admin" && activeTab === "dashboard") {
            setActiveTab("admin-analytics");
          }
        })
        .catch(() => {
          handleLogout();
        });
    }
  }, []);

  // Load customer disputes and notifications
  const loadCustomerData = async () => {
    if (!user) return;
    try {
      const [disputeList, notifList] = await Promise.all([
        getCustomerDisputes(),
        getCustomerNotifications().catch(() => [])
      ]);
      setDisputes(disputeList || []);
      setNotifications(notifList || []);
    } catch (err) {
      console.warn("Telemetry polling:", err);
    }
  };

  useEffect(() => {
    if (user) {
      loadCustomerData();
      const interval = setInterval(loadCustomerData, 15000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    if (userData.role === "admin") {
      setActiveTab("admin-analytics");
    } else {
      setActiveTab("dashboard");
    }
    loadCustomerData();
  };

  const handleLogout = () => {
    localStorage.removeItem("disputeai_token");
    localStorage.removeItem("disputeai_user");
    setUser(null);
    setDisputes([]);
    setNotifications([]);
    setSelectedDisputeId(null);
    setAuthView("login");
    setActiveTab("dashboard");
  };

  const getPageTitle = () => {
    const map = {
      dashboard: "Customer Dashboard",
      "submit-dispute": "Submit Banking Dispute",
      "my-complaints": "Track Complaints",
      profile: "Customer Profile",
      "admin-analytics": "Risk Analytics Console",
      "admin-disputes": "All Banking Complaints",
      "admin-escalations": "High-Risk & Escalated Cases",
      "admin-evaluation": "AI Multi-Agent Evaluation",
      "admin-monitoring": "System Telemetry & Health",
    };
    return map[activeTab] || "DisputeAI Platform";
  };

  // If not authenticated, render Login or Register
  if (!user) {
    if (authView === "register") {
      return (
        <Register
          onRegisterSuccess={handleLoginSuccess}
          onSwitchToLogin={() => setAuthView("login")}
        />
      );
    }
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onSwitchToRegister={() => setAuthView("register")}
      />
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        user={user}
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          setSelectedDisputeId(null);
        }}
        onLogout={handleLogout}
      />

      {/* Main Workspace */}
      <main className="main-content">
        <Navbar
          user={user}
          activeTitle={getPageTitle()}
          notifications={notifications}
          onNotificationClick={(id) => {
            setSelectedDisputeId(id);
            if (user.role === "admin") {
              setActiveTab("admin-disputes");
            } else {
              setActiveTab("my-complaints");
            }
          }}
        />

        <div className="page-content">
          {/* CUSTOMER PORTAL VIEWS */}
          {user.role !== "admin" && (
            <>
              {activeTab === "dashboard" && (
                <CustomerDashboard
                  user={user}
                  disputes={disputes}
                  onNavigate={setActiveTab}
                  onSelectDispute={(id) => {
                    setSelectedDisputeId(id);
                    setActiveTab("my-complaints");
                  }}
                />
              )}

              {activeTab === "submit-dispute" && (
                <CustomerSubmitDispute
                  user={user}
                  onSubmitted={(id) => {
                    loadCustomerData();
                    setSelectedDisputeId(id);
                    setActiveTab("my-complaints");
                  }}
                  onCancel={() => setActiveTab("dashboard")}
                />
              )}

              {activeTab === "my-complaints" && (
                <CustomerTrackDisputes
                  selectedDisputeId={selectedDisputeId}
                  onClearSelection={() => setSelectedDisputeId(null)}
                />
              )}

              {activeTab === "profile" && <CustomerProfile user={user} />}
            </>
          )}

          {/* ADMIN PORTAL VIEWS */}
          {user.role === "admin" && (
            <>
              {activeTab === "admin-analytics" && (
                <AdminDashboard
                  onNavigate={setActiveTab}
                  onSelectDispute={(id) => setSelectedDisputeId(id)}
                />
              )}

              {activeTab === "admin-disputes" && (
                <AdminDisputes
                  onSelectDispute={(id) => setSelectedDisputeId(id)}
                />
              )}

              {activeTab === "admin-escalations" && (
                <AdminDisputes
                  defaultFilter={{ status: "Escalated" }}
                  onSelectDispute={(id) => setSelectedDisputeId(id)}
                />
              )}

              {activeTab === "admin-evaluation" && <AdminEvaluation />}

              {activeTab === "admin-monitoring" && <AdminMonitoring />}
            </>
          )}
        </div>
      </main>

      {/* ADMIN DISPUTE DOSSIER MODAL */}
      {user.role === "admin" && selectedDisputeId && (
        <AdminDisputeDetail
          disputeId={selectedDisputeId}
          onClose={() => setSelectedDisputeId(null)}
          onUpdated={() => {
            loadCustomerData();
          }}
        />
      )}
    </div>
  );
}
