import React, { useState, useEffect } from "react";
import {
  CreditCard,
  Clock,
  CheckCircle,
  AlertTriangle,
  ShieldAlert,
  BarChart2,
  TrendingUp,
  FileText,
  Activity,
  ArrowRight
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";
import StatCard from "../components/StatCard";
import { StatusBadge, RiskBadge } from "../components/StatusBadge";
import { getAdminAnalytics, getAdminDisputes } from "../services/api";

const PIE_COLORS = ["#0284c7", "#7c3aed", "#f59e0b", "#10b981", "#ef4444"];

export default function AdminDashboard({ onNavigate, onSelectDispute }) {
  const [analytics, setAnalytics] = useState(null);
  const [recentDisputes, setRecentDisputes] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [stats, disputes] = await Promise.all([
        getAdminAnalytics(),
        getAdminDisputes({ search: "" })
      ]);
      setAnalytics(stats);
      setRecentDisputes(disputes || []);
    } catch (err) {
      console.error("Failed to load admin analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="admin-dashboard-view">
      {/* Top Banner */}
      <div className="admin-welcome-banner">
        <div>
          <h2>Fraud Risk & Dispute Management Console</h2>
          <p>
            Real-time telemetry, LangGraph multi-agent investigations, and RBI regulatory compliance governance.
          </p>
        </div>
        <div className="banner-controls">
          <button className="btn-secondary-sm" onClick={loadData}>
            Refresh Analytics
          </button>
          <button className="btn-primary-sm" onClick={() => onNavigate("admin-disputes")}>
            Manage Complaints
          </button>
        </div>
      </div>

      {/* Primary Analytics KPI Grid */}
      <div className="stats-grid-8">
        <StatCard
          title="Total Complaints"
          value={analytics?.total_complaints ?? 0}
          subtitle="All registered cases"
          icon={CreditCard}
          color="blue"
          loading={loading}
        />
        <StatCard
          title="Pending Queue"
          value={analytics?.pending_complaints ?? 0}
          subtitle="Awaiting triage"
          icon={Clock}
          color="orange"
          loading={loading}
        />
        <StatCard
          title="In Investigation"
          value={analytics?.in_investigation ?? 0}
          subtitle="Agent workflow active"
          icon={Activity}
          color="purple"
          loading={loading}
        />
        <StatCard
          title="Under Review"
          value={analytics?.under_review ?? 0}
          subtitle="Agent report complete"
          icon={FileText}
          color="cyan"
          loading={loading}
        />
        <StatCard
          title="Resolved"
          value={analytics?.resolved_complaints ?? 0}
          subtitle="Settled & closed"
          icon={CheckCircle}
          color="green"
          loading={loading}
        />
        <StatCard
          title="High Risk"
          value={analytics?.high_risk_complaints ?? 0}
          subtitle="Score 65 to 84"
          icon={AlertTriangle}
          color="amber"
          loading={loading}
        />
        <StatCard
          title="Critical Risk"
          value={analytics?.critical_risk_complaints ?? 0}
          subtitle="Score >= 85"
          icon={ShieldAlert}
          color="red"
          loading={loading}
        />
        <StatCard
          title="Human Escalated"
          value={analytics?.escalated_complaints ?? 0}
          subtitle="Analyst review flagged"
          icon={ShieldAlert}
          color="indigo"
          loading={loading}
        />
      </div>

      {/* Visual Analytics Charts Grid */}
      <div className="charts-grid-2">
        {/* Fraud Category Distribution */}
        <div className="panel chart-panel">
          <div className="panel-header">
            <div>
              <h3>Fraud Category Distribution</h3>
              <p className="panel-sub">5 canonical categories identified by AI Classifier</p>
            </div>
            <BarChart2 size={18} color="#0284c7" />
          </div>

          <div className="chart-container">
            {analytics?.category_distribution && analytics.category_distribution.some((c) => c.value > 0) ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={analytics.category_distribution.filter((c) => c.value > 0)}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={95}
                    label
                  >
                    {analytics.category_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-chart">No category data recorded yet</div>
            )}
          </div>
        </div>

        {/* Complaint Status Distribution */}
        <div className="panel chart-panel">
          <div className="panel-header">
            <div>
              <h3>Complaint Status Lifecycle</h3>
              <p className="panel-sub">Disputes distribution across operational stages</p>
            </div>
            <TrendingUp size={18} color="#059669" />
          </div>

          <div className="chart-container">
            {analytics?.status_distribution ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={analytics.status_distribution}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0284c7" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-chart">Loading lifecycle data...</div>
            )}
          </div>
        </div>
      </div>

      {/* Critical & Escalated Cases Requiring Human Approval */}
      <div className="panel table-panel">
        <div className="panel-header">
          <div>
            <h3>Urgent Attention: High-Risk & Escalated Complaints</h3>
            <p className="panel-sub">Cases requiring administrative concurrence or manual investigation</p>
          </div>
          <button className="btn-link" onClick={() => onNavigate("admin-escalations")}>
            View All Escalations
          </button>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Dispute ID</th>
                <th>Customer Name</th>
                <th>Transaction ID</th>
                <th>Amount</th>
                <th>Fraud Category</th>
                <th>Risk Level</th>
                <th>Liability Verdict</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {recentDisputes
                .filter((d) => d.escalated || d.risk_level === "Critical" || d.risk_level === "High" || d.status === "Escalated")
                .slice(0, 6)
                .map((d) => (
                  <tr key={d.dispute_id}>
                    <td className="font-mono text-bold text-primary">{d.dispute_id}</td>
                    <td>{d.customer_name}</td>
                    <td className="font-mono">{d.transaction_id}</td>
                    <td className="text-bold">₹{Number(d.amount).toLocaleString("en-IN")}</td>
                    <td>{d.fraud_type}</td>
                    <td><RiskBadge level={d.risk_level} score={d.risk_score} /></td>
                    <td className="text-bold">{d.liability_verdict || "PENDING"}</td>
                    <td><StatusBadge status={d.status} /></td>
                    <td>
                      <button className="btn-table-action" onClick={() => onSelectDispute(d.dispute_id)}>
                        Review Dossier
                      </button>
                    </td>
                  </tr>
                ))}
              {recentDisputes.filter((d) => d.escalated || d.risk_level === "Critical" || d.status === "Escalated").length === 0 && (
                <tr>
                  <td colSpan="9" className="text-center py-4">No escalated or critical complaints currently pending review.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
