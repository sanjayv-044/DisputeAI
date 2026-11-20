import React, { useState, useEffect } from "react";
import {
  X,
  ShieldCheck,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Clock,
  Send,
  Building,
  UserCheck,
  Scale
} from "lucide-react";
import { getAdminDisputeDetail, executeAdminAction, updateDisputeStatus } from "../services/api";
import { StatusBadge, RiskBadge } from "../components/StatusBadge";

export default function AdminDisputeDetail({ disputeId, onClose, onUpdated }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [actionType, setActionType] = useState("");
  const [remarks, setRemarks] = useState("");
  const [resolutionText, setResolutionText] = useState("");
  const [submittingAction, setSubmittingAction] = useState(false);
  const [actionMsg, setActionMsg] = useState("");

  const loadDetail = async () => {
    try {
      setLoading(true);
      const res = await getAdminDisputeDetail(disputeId);
      setData(res);
    } catch (err) {
      console.error("Failed to load dispute dossier:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (disputeId) {
      loadDetail();
    }
  }, [disputeId]);

  const handleAction = async (action) => {
    if (!disputeId) return;
    setSubmittingAction(true);
    setActionMsg("");
    try {
      const res = await executeAdminAction(disputeId, action, remarks, resolutionText);
      setActionMsg(`Action '${action.toUpperCase()}' successfully executed! New Status: ${res.status}`);
      setTimeout(() => {
        loadDetail();
        onUpdated?.();
      }, 1200);
    } catch (err) {
      setActionMsg("Action execution failed. Please verify administrative permissions.");
    } finally {
      setSubmittingAction(false);
    }
  };

  if (!disputeId) return null;

  const dispute = data?.dispute;
  const dossier = data?.dossier;
  const citations = data?.citations || [];
  const evidenceFiles = data?.evidence_files || [];
  const history = data?.history || [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card modal-card-wide" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <h3>Dispute Dossier & AI Multi-Agent Investigation Report</h3>
            <span className="font-mono text-bold text-primary">{disputeId}</span>
          </div>
          <button className="icon-btn-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div className="modal-body loading-state">Retrieving case dossier from database...</div>
        ) : !dispute ? (
          <div className="modal-body empty-state">Dispute not found.</div>
        ) : (
          <div className="modal-body">
            {/* Top Stat Ribbon */}
            <div className="modal-stats-grid">
              <div className="modal-stat-box">
                <span className="box-label">Current Status</span>
                <StatusBadge status={dispute.status} />
              </div>
              <div className="modal-stat-box">
                <span className="box-label">Fraud Category</span>
                <strong className="text-bold">{dispute.fraud_type}</strong>
              </div>
              <div className="modal-stat-box">
                <span className="box-label">Risk Evaluation</span>
                <RiskBadge level={dispute.risk_level} score={dispute.risk_score} />
              </div>
              <div className="modal-stat-box">
                <span className="box-label">Liability Verdict</span>
                <strong className="text-highlight">{dispute.liability_verdict || "PENDING"}</strong>
              </div>
            </div>

            {/* Customer & Transaction Overview */}
            <div className="dossier-section">
              <h4>1. Customer & Transaction Particulars</h4>
              <div className="details-grid-3">
                <p><strong>Customer Name:</strong> {dispute.customer_name}</p>
                <p><strong>Customer Email:</strong> {dispute.customer_email || "N/A"}</p>
                <p><strong>Bank Name:</strong> {dispute.bank_name || "State Bank of India"}</p>
                <p><strong>Transaction ID:</strong> <span className="font-mono">{dispute.transaction_id}</span></p>
                <p><strong>Disputed Amount:</strong> ₹{Number(dispute.amount).toLocaleString("en-IN")}</p>
                <p><strong>Payment Channel:</strong> <span className="channel-tag">{dispute.transaction_type}</span></p>
                <p><strong>Transaction Date:</strong> {dispute.transaction_date}</p>
                <p><strong>Reported Date:</strong> {dispute.reported_date}</p>
                <p><strong>OTP/PIN Shared:</strong> {dispute.otp_shared ? "YES (Third Party Disclosed)" : "NO (Protected)"}</p>
              </div>

              <div className="narrative-box">
                <strong>Customer Narrative:</strong>
                <p>{dispute.fraud_description}</p>
              </div>
            </div>

            {/* AI Classification & Risk Breakdown */}
            <div className="dossier-section">
              <h4>2. Fraud Classification & Risk Diagnostics</h4>
              <div className="details-grid-2">
                <p><strong>Classified Category:</strong> {dispute.fraud_type}</p>
                <p><strong>Risk Score:</strong> {dispute.risk_score}/100 ({dispute.risk_level} Priority: {dispute.priority})</p>
                <p><strong>Human Escalation Flag:</strong> {dispute.escalated ? "FLAGGED FOR HUMAN INVESTIGATION" : "Standard Automated Review"}</p>
                <p><strong>Claimed by Customer:</strong> {dispute.fraud_type_claimed || "Unspecified"}</p>
              </div>
              {dispute.classification_explanation && (
                <div className="explanation-callout">
                  <strong>Diagnostic Rationale:</strong>
                  <p>{dispute.classification_explanation}</p>
                </div>
              )}
            </div>

            {/* Multi-Agent Dossier */}
            {dossier && (
              <div className="dossier-section ai-dossier-panel">
                <div className="section-head-badge">
                  <ShieldCheck size={20} color="#0284c7" />
                  <h4>3. LangGraph Multi-Agent Investigation Dossier</h4>
                </div>

                {/* Agent 1 Findings */}
                <div className="agent-block">
                  <span className="agent-tag">Agent 1: Investigation Agent</span>
                  <p>{dossier.agent_findings}</p>
                </div>

                {/* Agent 2 Verification Summary */}
                <div className="agent-block">
                  <span className="agent-tag">Agent 2: Verification Agent</span>
                  <p>{dossier.verification_summary}</p>
                </div>

                {/* Agent 3 Liability Assessment */}
                <div className="agent-block">
                  <span className="agent-tag">Agent 3: Liability Assessment Agent</span>
                  <div className="liability-banner">
                    <strong>Verdict: {dossier.liability_status}</strong>
                    <p>{dossier.liability_reasoning}</p>
                  </div>
                </div>

                {/* Agent 4 Recommendation */}
                <div className="agent-block">
                  <span className="agent-tag">Agent 4: Recommendation & Escalation Agent</span>
                  <div className="rec-box">
                    <strong>Suggested Action:</strong>
                    <p>{dossier.recommendation}</p>
                  </div>
                </div>

                {/* Verified RBI Citations */}
                {citations && citations.length > 0 && (
                  <div className="citations-table-wrap">
                    <h5>Official RBI Circular References Cited:</h5>
                    <table className="mini-table">
                      <thead>
                        <tr>
                          <th>Document Source</th>
                          <th>Page</th>
                          <th>Status</th>
                          <th>Verification Caveat</th>
                        </tr>
                      </thead>
                      <tbody>
                        {citations.map((c, idx) => (
                          <tr key={idx}>
                            <td className="font-mono">{c.source}</td>
                            <td>Page {c.page}</td>
                            <td><span className="badge badge-primary">{c.status}</span></td>
                            <td>{c.caveat}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Supporting Documents */}
            <div className="dossier-section">
              <h4>4. Evidence Files & Documents</h4>
              {evidenceFiles.length === 0 ? (
                <p className="hint-text">No evidence documents uploaded for this dispute.</p>
              ) : (
                <div className="files-list">
                  {evidenceFiles.map((f, idx) => (
                    <div key={idx} className="file-chip">
                      <FileText size={16} />
                      <span>{f.filename} ({(f.file_size / 1024).toFixed(1)} KB)</span>
                      <span className="file-status">{f.verified_status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Official Resolution & Remarks */}
            {dispute.final_resolution && (
              <div className="dossier-section resolution-box">
                <h4>Official Recorded Resolution</h4>
                <p className="resolution-text">{dispute.final_resolution}</p>
                {dispute.admin_remarks && (
                  <p className="remarks-text"><em>Investigator Remarks: {dispute.admin_remarks}</em></p>
                )}
              </div>
            )}

            {/* Audit History Timeline */}
            <div className="dossier-section">
              <h4>5. Complaint History & Audit Trail</h4>
              <div className="audit-timeline">
                {history.map((h, idx) => (
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

            {/* Administrative Action Center */}
            <div className="dossier-section admin-actions-box">
              <h4>6. Administrative Decision & Case Concurrence</h4>
              <p className="hint-text">
                As System Administrator, retain final decision authority to approve shadow reversal credit, reject dispute, or escalate for manual forensic audit.
              </p>

              <div className="admin-action-inputs">
                <label className="form-group full-width">
                  <span className="form-label">Investigation Remarks / Audit Notes</span>
                  <input
                    type="text"
                    placeholder="Enter internal investigation remarks or regulatory justification..."
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                  />
                </label>

                <label className="form-group full-width">
                  <span className="form-label">Final Resolution Statement (Dispatched to Customer)</span>
                  <input
                    type="text"
                    placeholder="e.g. Approved provisional credit of disputed amount pursuant to RBI Para 9."
                    value={resolutionText}
                    onChange={(e) => setResolutionText(e.target.value)}
                  />
                </label>
              </div>

              {actionMsg && <div className="alert-box alert-success">{actionMsg}</div>}

              <div className="action-buttons-row">
                <button
                  className="btn-success"
                  onClick={() => handleAction("approve")}
                  disabled={submittingAction}
                >
                  <CheckCircle size={16} />
                  <span>Approve Recommendation & Authorize Credit</span>
                </button>

                <button
                  className="btn-danger"
                  onClick={() => handleAction("reject")}
                  disabled={submittingAction}
                >
                  <XCircle size={16} />
                  <span>Reject Dispute</span>
                </button>

                <button
                  className="btn-purple"
                  onClick={() => handleAction("escalate")}
                  disabled={submittingAction}
                >
                  <AlertTriangle size={16} />
                  <span>Escalate for Human Investigation</span>
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
}
