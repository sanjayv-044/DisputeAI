import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ==========================================
// CENTRALIZED ERROR MESSAGE HANDLING
// ==========================================

export const getApiErrorMessage = (error) => {
  if (error.response) {
    const status = error.response.status;
    const detail = error.response.data?.detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          const field = item.loc?.slice(1).join(".");
          return `${field ? field + ": " : ""}${item.msg}`;
        })
        .join("\n");
    }

    if (typeof detail === "string") {
      return detail;
    }

    switch (status) {
      case 400:
        return "Invalid request. Please check the submitted information.";
      case 401:
        return "Authentication required.";
      case 403:
        return "You do not have permission to perform this action.";
      case 404:
        return "The requested resource was not found.";
      case 409:
        return "A conflict occurred while processing your request.";
      case 422:
        return "Invalid input. Please verify all the fields.";
      case 500:
        return "Internal server error. Please try again later.";
      case 503:
        return "The backend service is currently unavailable.";
      default:
        return `Request failed with status ${status}.`;
    }
  }

  if (error.code === "ECONNABORTED") {
    return "Request timed out. Please try again.";
  }

  if (error.code === "ERR_NETWORK") {
    return "Cannot connect to the backend. Check whether the server is running.";
  }

  return error.message || "An unexpected error occurred.";
};

// ==========================================
// RESPONSE INTERCEPTOR
// ==========================================

API.interceptors.response.use(
  (response) => response,

  (error) => {
    const readableMessage = getApiErrorMessage(error);

    console.error("API Error:", {
      message: readableMessage,
      status: error.response?.status,
      url: error.config?.url,
    });

    // Convert backend validation details into readable text
    if (error.response?.data) {
      error.response.data.detail = readableMessage;
    }

    return Promise.reject(error);
  }
);

// ==========================================
// GET ALL DISPUTES
// ==========================================

export const getDisputes = async () => {
  const response = await API.get("/api/disputes");

  if (!Array.isArray(response.data)) {
    throw new Error("Invalid response received from the server.");
  }

  return response.data.map((d) => ({
    id: d.dispute_id,
    customer: d.customer_name,
    type: d.transaction_type,
    amount: d.amount,
    date: d.reported_date,
    status: d.status,
    transactionId: d.transaction_id,
    transactionDate: d.transaction_date,
    description: d.fraud_description,
    otpShared: d.otp_shared,

    fraudType: d.fraud_type,
    riskScore: d.risk_score,
    priority: d.priority,
    escalated: d.escalated,
    recommendation: d.recommendation,
  }));
};

// ==========================================
// SUBMIT NEW DISPUTE
// ==========================================

export const createDispute = async (form) => {
  const response = await API.post("/api/disputes", {
    customer_name: form.customer.trim(),
    transaction_id: form.transactionId.trim(),
    amount: Number(form.amount),
    transaction_type: form.transactionType,
    transaction_date: form.transactionDate,
    reported_date: form.reportedDate,
    fraud_description: form.fraudDescription.trim(),
    otp_shared: form.otpShared === "Yes",
  });

  return response.data;
};

// ==========================================
// GET INDIVIDUAL DISPUTE
// ==========================================

export const getDisputeById = async (disputeId) => {
  if (!disputeId) {
    throw new Error("Dispute ID is required.");
  }

  const response = await API.get(
    `/api/disputes/${encodeURIComponent(disputeId)}`
  );

  return response.data;
};

export default API;