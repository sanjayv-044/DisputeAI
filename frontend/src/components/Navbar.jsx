import React, { useState } from "react";
import { Bell, Search, Shield, ChevronDown } from "lucide-react";

export default function Navbar({ user, activeTitle, notifications = [], onNotificationClick }) {
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <header className="topbar">
      <div>
        <h2 className="page-title">{activeTitle}</h2>
        <p className="page-sub">DisputeAI Automated Banking Dispute & Fraud Investigation System</p>
      </div>

      <div className="topbar-actions">
        {/* Notification Bell */}
        <div className="notification-wrapper">
          <button
            className="icon-btn"
            onClick={() => setShowNotifications(!showNotifications)}
            title="Notifications"
          >
            <Bell size={18} />
            {notifications.length > 0 && <span className="notification-badge">{notifications.length}</span>}
          </button>

          {showNotifications && (
            <div className="notification-dropdown">
              <div className="notification-header">
                <strong>Activity & Status Updates</strong>
                <span>{notifications.length} updates</span>
              </div>
              <div className="notification-list">
                {notifications.length === 0 ? (
                  <p className="no-notifications">No new notifications</p>
                ) : (
                  notifications.map((n, idx) => (
                    <div key={idx} className="notification-item" onClick={() => onNotificationClick?.(n.dispute_id)}>
                      <div className="notif-top">
                        <strong>{n.dispute_id}</strong>
                        <span>{n.status}</span>
                      </div>
                      <p>{n.notes || n.action}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Capsule */}
        <div className="user-profile-capsule">
          <div className="capsule-avatar">
            {user?.role === "admin" ? "AD" : "CU"}
          </div>
          <div className="capsule-meta">
            <strong>{user?.full_name || "Account"}</strong>
            <span>{user?.role === "admin" ? "System Admin" : "Verified Customer"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
