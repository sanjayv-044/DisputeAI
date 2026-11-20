import React, { useState, useEffect } from "react";
import { Search, Eye, FileText, ShieldAlert, CheckCircle, Clock, X, Upload, Download, AlertTriangle, ShieldCheck } from "lucide-react";
import { getCustomerDisputes, getCustomerDisputeDetail, uploadDisputeDocument } from "../services/api";
import { StatusBadge, RiskBadge } from "../components/StatusBadge";

export default function CustomerTrackDisputes({ selectedDisputeId, onClearSelection }) {
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  const [activeDispute, setActiveDispute] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getCustomerDisputes();
      setDisputes(data);
    } catch (err) {
      console.error("Failed to load customer complaints:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openDetail = async (disputeId) => {
    try {
      setDetailLoading(true);
      setUploadMsg("");
      const detail = await getCustomerDisputeDetail(disputeId);
      setActiveDispute(detail);
    } catch (err) {
      console.error("Failed to load dispute detail:", err);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDisputeId) {
      openDetail(selectedDisputeId);
    }
  }, [selectedDisputeId]);

  const handleUploadAdditionalEvidence = async (e) => {
    e.preventDefault();
    if (!uploadFile || !activeDispute) return;
    setUploading(true);
    try {
      await uploadDisputeDocument(activeDispute.dispute_id, uploadFile);
      setUploadMsg("Evidence document successfully uploaded!");
      setUploadFile(null);
      // Reload detail
      openDetail(activeDispute.dispute_id);
    } catch (err) {
      setUploadMsg("Upload failed. Verify file type and size.");
    } finally {
      setUploading(false);
    }
  };

  const filtered = disputes.filter((d) => {
    const matchesSearch =
      (d.dispute_id || "").toLowerCase().includes(search.toLowerCase()) ||
      (d.transaction_id || "").toLowerCase().includes(search.toLowerCase()) ||
      (d.fraud_type || "").toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "All" || d.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="track-disputes-page">
      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>My Banking Disputes & Complaint Tracker</h3>
            <p className="panel-sub">
              Monitor investigation findings, RBI liability determinations, and bank shadow reversal statuses.
            </p>
          </div>
          <button className="btn-secondary-sm" onClick={loadData}>
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="filters-bar">
          <div className="search-box">
            <Search size={16} color="#64748b" />
            <input
              type="text"
              placeholder="Search by Dispute ID, Transaction ID, Fraud Type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

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
        </div>

        {/* Complaints Table */}
        {loading ? (
          <div className="loading-state">Loading your complaints...</div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <FileText size={36} color="#94a3b8" />
            <p>No complaints match your filters.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Dispute ID</th>
                  <th>Bank Name</th>
                  <th>Transaction ID</th>
                  <th>Disputed Amount</th>
                  <th>Channel</th>
                  <th>Reported Date</th>
                  <th>Fraud Category</th>
                  <th>Risk Score</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => (
                  <tr key={d.dispute_id}>
                    <td className="font-mono text-bold text-primary">{d.dispute_id}</td>
                    <td>{d.bank_name || "State Bank of India"}</td>
                    <td className="font-mono">{d.transaction_id}</td>
                    <td className="text-bold">₹{Number(d.amount).toLocaleString("en-IN")}</td>
                    <td><span className="channel-tag">{d.transaction_type}</span></td>
                    <td>{d.reported_date}</td>
                    <td>{d.fraud_type || "Evaluating..."}</td>
                    <td><RiskBadge level={d.risk_level} score={d.risk_score} /></td>
                    <td><StatusBadge status={d.status} /></td>
                    <td>
                      <button className="btn-table-action" onClick={() => openDetail(d.dispute_id)}>
                        <Eye size={14} />
                        <span>Track</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* DETAILED TRACKING MODAL */}
      {activeDispute && (
        <div className="modal-backdrop" onClick={() => setActiveDispute(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>Dispute Tracking & AI Investigation Dossier</h3>
                <span className="font-mono text-bold">{activeDispute.dispute_id}</span>
              </div>
              <button className="icon-btn-close" onClick={() => { setActiveDispute(null); onClearSelection?.(); }}>
                <X size={20} />
              </button>
            </div>

            <div className="modal-body">
              {/* Visual Resolution Stepper */}
              <div className="stepper-wrap">
                <div className={`step-item ${activeDispute.status ? "completed" : ""}`}>
                  <div className="step-circle"><CheckCircle size={16} /></div>
                  <span className="step-label">1. Dispute Filed</span>
                </div>
                <div className={`step-item ${activeDispute.status !== "Pending" ? "completed" : "current"}`}>
                  <div className="step-circle"><Clock size={16} /></div>
                  <span className="step-label">2. AI Multi-Agent Triage</span>
                </div>
                <div className={`step-item ${activeDispute.liability_verdict !== "PENDING_ASSESSMENT" ? "completed" : ""}`}>
                  <div className="step-circle"><ShieldAlert size={16} /></div>
                  <span className="step-label">3. Liability Determined</span>
                </div>
                <div className={`step-item ${(activeDispute.status || "").toLowerCase().includes("resolved") ? "completed" : ""}`}>
                  <div className="step-circle"><CheckCircle size={16} /></div>
                  <span className="step-label">4. Bank Resolution</span>
                </div>
              </div>

              {/* Status & Summary Cards */}
              <div className="modal-stats-grid">
                <div className="modal-stat-box">
                  <span className="box-label">Current Status</span>
                  <StatusBadge status={activeDispute.status} />
                </div>
                <div className="modal-stat-box">
                  <span className="box-label">Assessed Fraud Category</span>
                  <strong className="text-bold">{activeDispute.fraud_type || "Classifying..."}</strong>
                </div>
                <div className="modal-stat-box">
                  <span className="box-label">Risk Evaluation</span>
                  <RiskBadge level={activeDispute.risk_level} score={activeDispute.risk_score} />
                </div>
                <div className="modal-stat-box">
                  <span className="box-label">Liability Verdict</span>
                  <strong className="text-highlight">{activeDispute.liability_verdict || "Evaluating..."}</strong>
                </div>
              </div>

              {/* Transaction Specs */}
              <div className="dossier-section">
                <h4>Transaction Specifications</h4>
                <div className="details-grid-2">
                  <p><strong>Bank:</strong> {activeDispute.bank_name || "State Bank of India"}</p>
                  <p><strong>Transaction ID:</strong> <span className="font-mono">{activeDispute.transaction_id}</span></p>
                  <p><strong>Amount:</strong> ₹{Number(activeDispute.amount).toLocaleString("en-IN")}</p>
                  <p><strong>Instrument:</strong> {activeDispute.transaction_type}</p>
                  <p><strong>Transaction Date:</strong> {activeDispute.transaction_date}</p>
                  <p><strong>Reported Date:</strong> {activeDispute.reported_date}</p>
                  <p><strong>Authentication OTP Shared:</strong> {activeDispute.otp_shared ? "Yes (Reported Compromised)" : "No (Confidential)"}</p>
                  <p><strong>Escalation to Human Analyst:</strong> {activeDispute.escalated ? "Yes (Escalated)" : "Standard Review"}</p>
                </div>
              </div>

              {/* AI Multi-Agent Findings */}
              {activeDispute.dossier && (
                <div className="dossier-section ai-section">
                  <div className="section-head-badge">
                    <ShieldCheck size={18} color="#0284c7" />
                    <h4>AI Multi-Agent Investigation Findings</h4>
                  </div>
                  <div className="ai-report-box">
                    <p><strong>Liability Reasoning:</strong> {activeDispute.dossier.liability_reasoning}</p>
                    <p style={{ marginTop: "8px" }}><strong>Investigation Summary:</strong> {activeDispute.dossier.verification_summary}</p>
                    <p style={{ marginTop: "8px" }}><strong>Resolution Recommendation:</strong> {activeDispute.dossier.recommendation}</p>
                  </div>

                  {activeDispute.dossier.citations && activeDispute.dossier.citations.length > 0 && (
                    <div className="citations-list">
                      <h5>RBI Regulatory Citations Verified:</h5>
                      <ul>
                        {activeDispute.dossier.citations.map((c, idx) => (
                          <li key={idx}>
                            <strong>{c.source}</strong> (Page {c.page}) — <em>{c.status}</em>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Official Bank Resolution Note */}
              {activeDispute.final_resolution && (
                <div className="dossier-section resolution-box">
                  <h4>Official Bank Resolution</h4>
                  <p className="resolution-text">{activeDispute.final_resolution}</p>
                  {activeDispute.admin_remarks && (
                    <p className="remarks-text"><em>Investigator Remarks: {activeDispute.admin_remarks}</em></p>
                  )}
                </div>
              )}

              {/* Upload Additional Documents */}
              <div className="dossier-section upload-supplement">
                <h4>Supporting Evidence & Documents</h4>
                {activeDispute.evidence_files && activeDispute.evidence_files.length > 0 ? (
                  <div className="files-list">
                    {activeDispute.evidence_files.map((f, idx) => (
                      <div key={idx} className="file-chip">
                        <FileText size={16} />
                        <span>{f.filename} ({(f.file_size / 1024).toFixed(1)} KB)</span>
                        <span className="file-status">{f.verified_status}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="hint-text">No documents attached yet.</p>
                )}

                <form onSubmit={handleUploadAdditionalEvidence} className="inline-upload-form">
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg,.txt"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  />
                  <button type="submit" className="btn-secondary-sm" disabled={!uploadFile || uploading}>
                    <Upload size={14} />
                    <span>{uploading ? "Uploading..." : "Upload Evidence"}</span>
                  </button>
                </form>
                {uploadMsg && <p className="msg-box">{uploadMsg}</p>}
              </div>

              {/* Audit Timeline */}
              {activeDispute.history && activeDispute.history.length > 0 && (
                <div className="dossier-section">
                  <h4>Complaint Audit Trail</h4>
                  <div className="audit-timeline">
                    {activeDispute.history.map((h, idx) => (
                      <div key={idx} className="audit-entry">
                        <span className="audit-dot"></span>
                        <div className="audit-content">
                          <div className="audit-meta">
                            <strong>{h.action}</strong>
                            <small>{h.changed_by} • {new Date(h.created_at).toLocaleString()}</small>
                          </div>
                          {h.notes && <p className="audit-note">{h.notes}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setActiveDispute(null)}>
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
