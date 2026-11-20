import React, { useState } from "react";
import { ShieldCheck, Lock, Mail, ArrowRight, UserCheck, AlertCircle } from "lucide-react";
import { loginUser } from "../services/api";

export default function Login({ onLoginSuccess, onSwitchToRegister }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    setLoading(true);
    try {
      const data = await loginUser(email, password);
      localStorage.setItem("disputeai_token", data.access_token);
      localStorage.setItem("disputeai_user", JSON.stringify(data.user));
      onLoginSuccess(data.user);
    } catch (err) {
      setError(
        typeof err.response?.data?.detail === "string"
          ? err.response.data.detail
          : "Invalid email or password. Please verify your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFillDemo = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError("");
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-icon">
            <ShieldCheck size={32} color="#06b6d4" />
          </div>
          <h2>DisputeAI</h2>
          <p>AI-Powered Banking Dispute Resolution Platform</p>
        </div>

        {error && (
          <div className="alert-box alert-error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <label className="form-group">
            <span className="form-label">Email Address</span>
            <div className="input-with-icon">
              <Mail size={16} />
              <input
                type="email"
                placeholder="name@disputeai.bank"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </label>

          <label className="form-group">
            <span className="form-label">Password</span>
            <div className="input-with-icon">
              <Lock size={16} />
              <input
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </label>

          <button type="submit" className="btn-primary full-width" disabled={loading}>
            <span>{loading ? "Authenticating..." : "Sign In to Portal"}</span>
            <ArrowRight size={16} />
          </button>
        </form>

        {/* Quick Demo Credentials */}
        <div className="demo-credentials-box">
          <p className="demo-title">One-Click Demonstration Logins:</p>
          <div className="demo-buttons">
            <button
              type="button"
              className="demo-pill admin-pill"
              onClick={() => handleFillDemo("admin@disputeai.bank", "Admin@DisputeAI2026")}
            >
              <strong>Admin Portal</strong>
              <span>admin@disputeai.bank</span>
            </button>
            <button
              type="button"
              className="demo-pill customer-pill"
              onClick={() => handleFillDemo("customer@disputeai.bank", "Customer@DisputeAI2026")}
            >
              <strong>Customer Portal</strong>
              <span>customer@disputeai.bank</span>
            </button>
          </div>
        </div>

        <div className="auth-footer">
          <span>New banking customer? </span>
          <button type="button" className="btn-link-inline" onClick={onSwitchToRegister}>
            Create an Account
          </button>
        </div>
      </div>
    </div>
  );
}
