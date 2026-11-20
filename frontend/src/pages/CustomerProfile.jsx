import React from "react";
import { User, Mail, Phone, ShieldCheck, Key, Building2 } from "lucide-react";

export default function CustomerProfile({ user }) {
  return (
    <div className="profile-page-container">
      <div className="panel profile-panel">
        <div className="panel-header">
          <div>
            <h3>Customer Profile & Banking Security Settings</h3>
            <p className="panel-sub">Manage your verified customer identity and notification preferences.</p>
          </div>
          <span className="badge badge-success">Verified Account</span>
        </div>

        <div className="profile-grid">
          <div className="profile-card">
            <div className="profile-avatar-large">
              {user?.full_name?.slice(0, 2).toUpperCase() || "CU"}
            </div>
            <h4>{user?.full_name || "Customer Account"}</h4>
            <span className="profile-role-tag">Retail Banking Customer</span>

            <div className="profile-details-list">
              <div className="detail-row">
                <Mail size={16} />
                <span>{user?.email}</span>
              </div>
              <div className="detail-row">
                <Phone size={16} />
                <span>{user?.phone || "+91-9876501234"}</span>
              </div>
              <div className="detail-row">
                <Building2 size={16} />
                <span>Primary Bank: State Bank of India</span>
              </div>
            </div>
          </div>

          <div className="profile-security-card">
            <h4>Regulatory Compliance & Data Protection</h4>
            <div className="security-notice">
              <ShieldCheck size={28} color="#059669" />
              <div>
                <strong>RBI Master Direction Protected</strong>
                <p>
                  Your customer disputes and uploaded banking evidence are encrypted in storage,
                  strictly isolated per-user under RBI Information Security Guidelines.
                </p>
              </div>
            </div>

            <div className="profile-settings-list">
              <div className="setting-item">
                <div>
                  <strong>Automated SMS & Email Alerts</strong>
                  <p>Mandatory electronic notifications on complaint registration and status changes</p>
                </div>
                <input type="checkbox" defaultChecked disabled />
              </div>

              <div className="setting-item">
                <div>
                  <strong>Shadow Reversal Tracking</strong>
                  <p>Real-time telemetry for 10-day provisional credit eligibility</p>
                </div>
                <input type="checkbox" defaultChecked disabled />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
