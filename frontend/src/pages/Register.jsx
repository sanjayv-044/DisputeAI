import React, { useState } from "react";
import { ShieldCheck, Lock, Mail, User, Phone, ArrowRight, AlertCircle } from "lucide-react";
import { registerUser } from "../services/api";

export default function Register({ onRegisterSuccess, onSwitchToLogin }) {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    password: "",
    confirm_password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.full_name || !form.email || !form.password) {
      setError("Please fill in all mandatory fields.");
      return;
    }

    if (form.password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }

    if (form.password !== form.confirm_password) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const data = await registerUser({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        password: form.password,
        role: "customer"
      });

      localStorage.setItem("disputeai_token", data.access_token);
      localStorage.setItem("disputeai_user", JSON.stringify(data.user));
      onRegisterSuccess(data.user);
    } catch (err) {
      setError(
        typeof err.response?.data?.detail === "string"
          ? err.response.data.detail
          : "Registration failed. An account with this email may already exist."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-icon">
            <ShieldCheck size={32} color="#06b6d4" />
          </div>
          <h2>Customer Registration</h2>
          <p>Register to submit transaction disputes and track shadow reversals</p>
        </div>

        {error && (
          <div className="alert-box alert-error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <label className="form-group">
            <span className="form-label">Full Name</span>
            <div className="input-with-icon">
              <User size={16} />
              <input
                type="text"
                name="full_name"
                placeholder="e.g. Priya Nair"
                value={form.full_name}
                onChange={handleChange}
                required
              />
            </div>
          </label>

          <label className="form-group">
            <span className="form-label">Email Address</span>
            <div className="input-with-icon">
              <Mail size={16} />
              <input
                type="email"
                name="email"
                placeholder="customer@email.com"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>
          </label>

          <label className="form-group">
            <span className="form-label">Phone Number</span>
            <div className="input-with-icon">
              <Phone size={16} />
              <input
                type="tel"
                name="phone"
                placeholder="+91-9876543210"
                value={form.phone}
                onChange={handleChange}
              />
            </div>
          </label>

          <label className="form-group">
            <span className="form-label">Password (Min 6 characters)</span>
            <div className="input-with-icon">
              <Lock size={16} />
              <input
                type="password"
                name="password"
                placeholder="••••••••••••"
                value={form.password}
                onChange={handleChange}
                required
              />
            </div>
          </label>

          <label className="form-group">
            <span className="form-label">Confirm Password</span>
            <div className="input-with-icon">
              <Lock size={16} />
              <input
                type="password"
                name="confirm_password"
                placeholder="••••••••••••"
                value={form.confirm_password}
                onChange={handleChange}
                required
              />
            </div>
          </label>

          <button type="submit" className="btn-primary full-width" disabled={loading}>
            <span>{loading ? "Creating Account..." : "Register & Enter Portal"}</span>
            <ArrowRight size={16} />
          </button>
        </form>

        <div className="auth-footer">
          <span>Already have an account? </span>
          <button type="button" className="btn-link-inline" onClick={onSwitchToLogin}>
            Sign In here
          </button>
        </div>
      </div>
    </div>
  );
}
