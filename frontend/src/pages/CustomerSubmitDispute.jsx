import React, { useState } from "react";
import { FilePlus, Upload, AlertCircle, CheckCircle2, ShieldCheck, ArrowLeft } from "lucide-react";
import { submitDispute, uploadDisputeDocument } from "../services/api";

export default function CustomerSubmitDispute({ user, onSubmitted, onCancel }) {
  const [form, setForm] = useState({
    customer_name: user?.full_name || "",
    customer_email: user?.email || "",
    bank_name: "State Bank of India",
    transaction_id: "",
    amount: "",
    transaction_type: "UPI",
    transaction_date: "",
    reported_date: new Date().toISOString().split("T")[0],
    fraud_type_claimed: "Unknown",
    fraud_description: "",
    otp_shared: "No",
  });

  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 10 * 1024 * 1024) {
        setError("File size cannot exceed 10 MB.");
        return;
      }
      setSelectedFile(file);
      setError("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");

    if (!form.customer_name.trim() || !form.transaction_id.trim() || !form.amount) {
      setError("Please fill in all mandatory fields.");
      return;
    }

    if (new Date(form.reported_date) < new Date(form.transaction_date)) {
      setError("Reported date cannot be earlier than transaction date.");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        customer_name: form.customer_name.trim(),
        customer_email: form.customer_email.trim(),
        bank_name: form.bank_name.trim(),
        transaction_id: form.transaction_id.trim(),
        amount: Number(form.amount),
        transaction_type: form.transaction_type,
        transaction_date: form.transaction_date,
        reported_date: form.reported_date,
        fraud_type_claimed: form.fraud_type_claimed,
        fraud_description: form.fraud_description.trim(),
        otp_shared: form.otp_shared === "Yes",
      };

      const result = await submitDispute(payload);

      // Upload file if selected
      if (selectedFile && result.dispute_id) {
        try {
          await uploadDisputeDocument(result.dispute_id, selectedFile);
        } catch (uploadErr) {
          console.warn("Document upload warning:", uploadErr);
        }
      }

      setSuccessMsg(`Dispute successfully filed with ID: ${result.dispute_id}. Background AI Multi-Agent investigation queued!`);
      setTimeout(() => {
        onSubmitted?.(result.dispute_id);
      }, 1800);
    } catch (err) {
      setError(typeof err.response?.data?.detail === "string" ? err.response.data.detail : "Failed to submit dispute. Check transaction ID uniqueness.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-page-container">
      <div className="panel form-panel">
        <div className="form-header">
          <div>
            <h3>Submit Banking Dispute & Fraud Report</h3>
            <p className="panel-sub">
              Your report will be processed through DisputeAI's 4-Agent LangGraph verification pipeline.
            </p>
          </div>
          {onCancel && (
            <button className="btn-secondary-sm" onClick={onCancel}>
              <ArrowLeft size={16} />
              <span>Back</span>
            </button>
          )}
        </div>

        {error && (
          <div className="alert-box alert-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="alert-box alert-success">
            <CheckCircle2 size={18} />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="dispute-form">
          <div className="form-section-title">
            <span>1. Customer & Bank Details</span>
          </div>

          <div className="form-row-2">
            <label className="form-group">
              <span className="form-label required">Customer Full Name</span>
              <input
                type="text"
                name="customer_name"
                value={form.customer_name}
                onChange={handleChange}
                placeholder="e.g. Rajesh Sharma"
                required
              />
            </label>

            <label className="form-group">
              <span className="form-label required">Customer Email</span>
              <input
                type="email"
                name="customer_email"
                value={form.customer_email}
                onChange={handleChange}
                placeholder="customer@email.com"
                required
              />
            </label>
          </div>

          <div className="form-row-2">
            <label className="form-group">
              <span className="form-label required">Issuing Bank Name</span>
              <select name="bank_name" value={form.bank_name} onChange={handleChange}>
                <option value="State Bank of India">State Bank of India (SBI)</option>
                <option value="HDFC Bank">HDFC Bank</option>
                <option value="ICICI Bank">ICICI Bank</option>
                <option value="Axis Bank">Axis Bank</option>
                <option value="Punjab National Bank">Punjab National Bank</option>
                <option value="Bank of Baroda">Bank of Baroda</option>
                <option value="Kotak Mahindra Bank">Kotak Mahindra Bank</option>
              </select>
            </label>

            <label className="form-group">
              <span className="form-label required">Transaction ID / UTR / Reference No.</span>
              <input
                type="text"
                name="transaction_id"
                value={form.transaction_id}
                onChange={handleChange}
                placeholder="e.g. TXN9876543210 or UPI123456"
                required
              />
            </label>
          </div>

          <div className="form-section-title">
            <span>2. Transaction Particulars</span>
          </div>

          <div className="form-row-3">
            <label className="form-group">
              <span className="form-label required">Disputed Amount (₹)</span>
              <input
                type="number"
                name="amount"
                min="1"
                step="0.01"
                value={form.amount}
                onChange={handleChange}
                placeholder="e.g. 15000"
                required
              />
            </label>

            <label className="form-group">
              <span className="form-label required">Payment Channel / Instrument</span>
              <select name="transaction_type" value={form.transaction_type} onChange={handleChange}>
                <option value="UPI">UPI (Google Pay, PhonePe, Paytm)</option>
                <option value="Card">Debit / Credit Card (POS / Online)</option>
                <option value="Internet Banking">Internet Banking (NEFT / RTGS / IMPS)</option>
              </select>
            </label>

            <label className="form-group">
              <span className="form-label required">Was OTP or PIN Shared?</span>
              <select name="otp_shared" value={form.otp_shared} onChange={handleChange}>
                <option value="No">No - OTP was NOT shared</option>
                <option value="Yes">Yes - OTP was shared with caller/link</option>
              </select>
            </label>
          </div>

          <div className="form-row-2">
            <label className="form-group">
              <span className="form-label required">Transaction Date</span>
              <input
                type="date"
                name="transaction_date"
                max={new Date().toISOString().split("T")[0]}
                value={form.transaction_date}
                onChange={handleChange}
                required
              />
            </label>

            <label className="form-group">
              <span className="form-label required">Date Notified to Bank</span>
              <input
                type="date"
                name="reported_date"
                max={new Date().toISOString().split("T")[0]}
                min={form.transaction_date || undefined}
                value={form.reported_date}
                onChange={handleChange}
                required
              />
            </label>
          </div>

          <div className="form-section-title">
            <span>3. Incident Description & Evidence</span>
          </div>

          <div className="form-row-2">
            <label className="form-group">
              <span className="form-label">Suspected Fraud Type (if known)</span>
              <select name="fraud_type_claimed" value={form.fraud_type_claimed} onChange={handleChange}>
                <option value="Unknown">I don't know / Not sure</option>
                <option value="UPI Fraud">UPI Collect Request / Fake QR Code</option>
                <option value="Credit/Debit Card Fraud">Card Cloned / ATM Skimmer / Card-Not-Present</option>
                <option value="Phishing Fraud">Phishing Link / Impersonation Call</option>
                <option value="Internet Banking Fraud">Netbanking Hacked / Unauthorized Beneficiary</option>
                <option value="Identity Theft">SIM Swap / Stolen KYC / Account Takeover</option>
              </select>
            </label>

            <label className="form-group">
              <span className="form-label">Attach Supporting Evidence (Receipt, SMS Screenshot, FIR)</span>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.txt"
                onChange={handleFileChange}
                className="file-input"
              />
              {selectedFile && <span className="file-hint">Attached: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>}
            </label>
          </div>

          <label className="form-group full-width">
            <span className="form-label required">Detailed Fraud Description</span>
            <textarea
              name="fraud_description"
              rows={4}
              value={form.fraud_description}
              onChange={handleChange}
              placeholder="Provide a chronological account of what occurred, SMS received, unauthorized debits observed, or third-party interactions..."
              minLength={10}
              maxLength={3000}
              required
            />
          </label>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={loading}>
              <ShieldCheck size={18} />
              <span>{loading ? "Analyzing with AI Agents..." : "Submit Banking Dispute"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
