import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 30000,
});

// Request interceptor to attach JWT token
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("disputeai_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Error handling helper
export const getApiErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
    }
    return JSON.stringify(detail);
  }
  if (error.code === "ECONNABORTED") return "Request timed out. Please try again.";
  if (error.code === "ERR_NETWORK") return "Cannot connect to DisputeAI backend server. Ensure backend is running at http://127.0.0.1:8000";
  return error.message || "An unexpected error occurred.";
};

// ==========================================
// AUTHENTICATION APIS
// ==========================================

export const loginUser = async (email, password) => {
  const response = await API.post("/api/auth/login", { email, password });
  return response.data;
};

export const registerUser = async (data) => {
  const response = await API.post("/api/auth/register", data);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await API.get("/api/auth/me");
  return response.data;
};

// ==========================================
// CUSTOMER APIS
// ==========================================

export const submitDispute = async (disputeData) => {
  const response = await API.post("/api/customer/disputes", disputeData);
  return response.data;
};

export const getCustomerDisputes = async () => {
  const response = await API.get("/api/customer/disputes");
  return response.data;
};

export const getCustomerDisputeDetail = async (disputeId) => {
  const response = await API.get(`/api/customer/disputes/${encodeURIComponent(disputeId)}`);
  return response.data;
};

export const uploadDisputeDocument = async (disputeId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await API.post(`/api/customer/disputes/${encodeURIComponent(disputeId)}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};

export const getCustomerNotifications = async () => {
  const response = await API.get("/api/customer/notifications");
  return response.data;
};

// ==========================================
// ADMIN APIS
// ==========================================

export const getAdminAnalytics = async () => {
  const response = await API.get("/api/admin/analytics");
  return response.data;
};

export const getAdminDisputes = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.status && filters.status !== "All") params.append("status", filters.status);
  if (filters.risk_level && filters.risk_level !== "All") params.append("risk_level", filters.risk_level);
  if (filters.fraud_type && filters.fraud_type !== "All") params.append("fraud_type", filters.fraud_type);
  if (filters.search) params.append("search", filters.search);

  const response = await API.get(`/api/admin/disputes?${params.toString()}`);
  return response.data;
};

export const getAdminDisputeDetail = async (disputeId) => {
  const response = await API.get(`/api/admin/disputes/${encodeURIComponent(disputeId)}`);
  return response.data;
};

export const executeAdminAction = async (disputeId, action, remarks = "", resolution = "") => {
  const response = await API.post(`/api/admin/disputes/${encodeURIComponent(disputeId)}/action`, {
    action,
    remarks,
    final_resolution: resolution
  });
  return response.data;
};

export const updateDisputeStatus = async (disputeId, status, remarks = "") => {
  const response = await API.post(`/api/admin/disputes/${encodeURIComponent(disputeId)}/status`, {
    status,
    remarks
  });
  return response.data;
};

export const getEvaluationMetrics = async () => {
  const response = await API.get("/api/admin/evaluation");
  return response.data;
};

export const getMonitoringData = async () => {
  const response = await API.get("/api/admin/monitoring");
  return response.data;
};

// Legacy API aliases for backward compatibility
export const getDisputes = getCustomerDisputes;
export const createDispute = async (form) => {
  return submitDispute({
    customer_name: form.customer || form.customer_name,
    customer_email: form.email || form.customer_email,
    transaction_id: form.transactionId || form.transaction_id,
    amount: Number(form.amount),
    transaction_type: form.transactionType || form.transaction_type,
    transaction_date: form.transactionDate || form.transaction_date,
    reported_date: form.reportedDate || form.reported_date,
    fraud_description: form.fraudDescription || form.fraud_description,
    otp_shared: form.otpShared === "Yes" || form.otp_shared === true
  });
};

export default API;
