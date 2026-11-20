import React, { useState, useEffect } from "react";
import { Search, Eye, Filter, RefreshCw, FileText } from "lucide-react";
import { getAdminDisputes } from "../services/api";
import { StatusBadge, RiskBadge } from "../components/StatusBadge";

export default function AdminDisputes({ onSelectDispute, defaultFilter = {} }) {
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState(defaultFilter.status || "All");
  const [riskFilter, setRiskFilter] = useState(defaultFilter.risk_level || "All");
  const [fraudFilter, setFraudFilter] = useState(defaultFilter.fraud_type || "All");

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getAdminDisputes({
        status: statusFilter,
        risk_level: riskFilter,
        fraud_type: fraudFilter,
        search: search.trim()
      });
      setDisputes(data || []);
    } catch (err) {
      console.error("Failed to load admin disputes:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, riskFilter, fraudFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadData();
  };

  return (
    <div className="admin-disputes-page">
      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>All Customer Banking Complaints ({disputes.length})</h3>
            <p className="panel-sub">Inspect individual dispute files, AI multi-agent findings, and regulatory citations.</p>
          </div>
          <button className="btn-secondary-sm" onClick={loadData}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Filters Bar */}
        <div className="filters-bar-grid">
          <form onSubmit={handleSearchSubmit} className="search-box">
            <Search size={16} color="#64748b" />
            <input
              type="text"
              placeholder="Search by Dispute ID, Customer Name, Transaction ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </form>

          <div className="filter-group">
            <label>Status:</label>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="All">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="In Investigation">In Investigation</option>
              <option value="Under Review">Under Review</option>
              <option value="Escalated">Escalated</option>
              <option value="Resolved - Refund Approved">Resolved - Refund Approved</option>
              <option value="Resolved - Dispute Rejected">Resolved - Dispute Rejected</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Risk Level:</label>
            <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
              <option value="All">All Risks</option>
              <option value="Critical">Critical (&ge; 85)</option>
              <option value="High">High (65 - 84)</option>
              <option value="Medium">Medium (40 - 64)</option>
              <option value="Low">Low (&lt; 40)</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Fraud Category:</label>
            <select value={fraudFilter} onChange={(e) => setFraudFilter(e.target.value)}>
              <option value="All">All Categories</option>
              <option value="UPI Fraud">UPI Fraud</option>
              <option value="Credit/Debit Card Fraud">Credit/Debit Card Fraud</option>
              <option value="Phishing Fraud">Phishing Fraud</option>
              <option value="Internet Banking Fraud">Internet Banking Fraud</option>
              <option value="Identity Theft">Identity Theft</option>
            </select>
          </div>
        </div>

        {/* Data Table */}
        {loading ? (
          <div className="loading-state">Loading complaints ledger...</div>
        ) : disputes.length === 0 ? (
          <div className="empty-state">
            <FileText size={36} color="#94a3b8" />
            <p>No complaints match the specified query filters.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Dispute ID</th>
                  <th>Customer Name</th>
                  <th>Bank Name</th>
                  <th>Transaction ID</th>
                  <th>Amount</th>
                  <th>Channel</th>
                  <th>Fraud Category</th>
                  <th>Risk Score</th>
                  <th>Liability Verdict</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {disputes.map((d) => (
                  <tr key={d.dispute_id}>
                    <td className="font-mono text-bold text-primary">{d.dispute_id}</td>
                    <td>{d.customer_name}</td>
                    <td>{d.bank_name || "State Bank of India"}</td>
                    <td className="font-mono">{d.transaction_id}</td>
                    <td className="text-bold">₹{Number(d.amount).toLocaleString("en-IN")}</td>
                    <td><span className="channel-tag">{d.transaction_type}</span></td>
                    <td>{d.fraud_type}</td>
                    <td><RiskBadge level={d.risk_level} score={d.risk_score} /></td>
                    <td><span className="liability-tag">{d.liability_verdict || "PENDING"}</span></td>
                    <td><StatusBadge status={d.status} /></td>
                    <td>
                      <button className="btn-table-action" onClick={() => onSelectDispute(d.dispute_id)}>
                        <Eye size={14} />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
