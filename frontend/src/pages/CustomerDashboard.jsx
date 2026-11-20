import React from "react";
import { CreditCard, Clock, CheckCircle, AlertTriangle, FilePlus, ShieldCheck, ArrowRight } from "lucide-react";
import StatCard from "../components/StatCard";
import { StatusBadge, RiskBadge } from "../components/StatusBadge";

export default function CustomerDashboard({ user, disputes = [], onNavigate, onSelectDispute }) {
  const total = disputes.length;
  const pending = disputes.filter((d) => d.status === "Pending").length;
  const inInvestigation = disputes.filter((d) => d.status === "In Investigation" || d.status === "Under Review").length;
  const resolved = disputes.filter((d) => (d.status || "").toLowerCase().includes("resolved")).length;

  return (
    <div className="dashboard-view">
      {/* Welcome Banner */}
      <div className="hero-banner">
        <div className="hero-content">
          <h1>Welcome, {user?.full_name || "Customer"} 👋</h1>
          <p>
            DisputeAI automatically triages, verifies, and resolves banking transaction disputes under Reserve Bank of India (RBI) consumer protection directives.
          </p>
          <div className="hero-actions">
            <button className="btn-primary" onClick={() => onNavigate("submit-dispute")}>
              <FilePlus size={18} />
              <span>Submit New Dispute</span>
            </button>
            <button className="btn-secondary" onClick={() => onNavigate("my-complaints")}>
              <span>Track All Complaints</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
        <div className="hero-badge">
          <ShieldCheck size={48} color="#06b6d4" />
          <span>RBI Circular 2017/18 Protected</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="stats-grid">
        <StatCard title="Total Disputes" value={total} subtitle="Lifetime complaints filed" icon={CreditCard} color="blue" />
        <StatCard title="Pending Review" value={pending} subtitle="Awaiting initial verification" icon={Clock} color="orange" />
        <StatCard title="In AI Investigation" value={inInvestigation} subtitle="LangGraph multi-agent analysis" icon={AlertTriangle} color="purple" />
        <StatCard title="Resolved Disputes" value={resolved} subtitle="Completed determinations" icon={CheckCircle} color="green" />
      </div>

      {/* Recent Complaints Table */}
      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>Recent Complaints</h3>
            <p className="panel-sub">Status of your recently submitted transaction disputes</p>
          </div>
          <button className="btn-link" onClick={() => onNavigate("my-complaints")}>
            View All ({total})
          </button>
        </div>

        {disputes.length === 0 ? (
          <div className="empty-state">
            <CreditCard size={36} color="#94a3b8" />
            <p>You have not submitted any disputes yet.</p>
            <button className="btn-primary-sm" onClick={() => onNavigate("submit-dispute")}>
              File Your First Dispute
            </button>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Dispute ID</th>
                  <th>Transaction ID</th>
                  <th>Channel</th>
                  <th>Amount</th>
                  <th>Reported Date</th>
                  <th>Fraud Category</th>
                  <th>Risk Level</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {disputes.slice(0, 5).map((d) => (
                  <tr key={d.dispute_id}>
                    <td className="font-mono text-bold">{d.dispute_id}</td>
                    <td>{d.transaction_id}</td>
                    <td><span className="channel-tag">{d.transaction_type}</span></td>
                    <td className="text-bold">₹{Number(d.amount).toLocaleString("en-IN")}</td>
                    <td>{d.reported_date}</td>
                    <td>{d.fraud_type || "Evaluating..."}</td>
                    <td><RiskBadge level={d.risk_level} score={d.risk_score} /></td>
                    <td><StatusBadge status={d.status} /></td>
                    <td>
                      <button className="btn-table-action" onClick={() => onSelectDispute(d.dispute_id)}>
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* RBI Policy Highlights for Customer */}
      <div className="rbi-guidance-card">
        <div className="guidance-header">
          <ShieldCheck size={22} color="#0284c7" />
          <h4>Your Rights Under RBI Zero Liability Guidelines (July 6, 2017)</h4>
        </div>
        <div className="guidance-grid">
          <div className="guidance-item">
            <strong>Zero Customer Liability</strong>
            <p>Applies to third-party breaches where you notify the bank within 3 working days of receiving transaction alerts.</p>
          </div>
          <div className="guidance-item">
            <strong>10-Day Shadow Reversal</strong>
            <p>Banks must credit the full disputed amount to your account within 10 working days of notification.</p>
          </div>
          <div className="guidance-item">
            <strong>Limited Liability Window</strong>
            <p>Reporting between 4 to 7 working days caps your per-transaction liability between ₹5,000 and ₹10,000.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
