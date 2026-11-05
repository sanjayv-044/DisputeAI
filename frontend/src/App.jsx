import { useState, useEffect } from "react";

import {
  LayoutDashboard,
  FilePlus,
  History,
  BrainCircuit,
  AlertTriangle,
  ShieldCheck,
  CreditCard,
  Clock,
  CheckCircle,
  TrendingUp,
  Bell,
  Search,
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
} from "recharts";

import { getDisputes, createDispute } from "./services/api";

import "./App.css";

const COLORS = ["#2563eb", "#7c3aed", "#06b6d4", "#f59e0b", "#10b981"];

// MAIN APPLICATION

function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // FETCH DISPUTES FROM DATABASE

  const loadDisputes = async () => {
    try {
      setError("");
      const data = await getDisputes();
      setDisputes(data);
    } catch (err) {
      console.error("Database retrieval failed:", err);
      setError(
        "Unable to retrieve disputes. Check whether the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDisputes();
  }, []);

  // SIDEBAR NAVIGATION

  const navigation = [
    { name: "Dashboard", icon: LayoutDashboard },
    { name: "Submit Dispute", icon: FilePlus },
    { name: "Dispute History", icon: History },
    { name: "AI Recommendations", icon: BrainCircuit },
    { name: "Human Escalation", icon: AlertTriangle },
  ];

  // PAGE ROUTING

  const renderPage = () => {
    switch (activePage) {
      case "Dashboard":
        return (
          <Dashboard
            disputes={disputes}
            loading={loading}
            error={error}
            setActivePage={setActivePage}
          />
        );

      case "Submit Dispute":
        return (
          <SubmitDispute
            loadDisputes={loadDisputes}
            setActivePage={setActivePage}
          />
        );

      case "Dispute History":
        return (
          <DisputeHistory
            disputes={disputes}
            loading={loading}
            error={error}
          />
        );

      case "AI Recommendations":
        return (
          <Recommendations
            disputes={disputes}
            loading={loading}
            error={error}
          />
        );

      case "Human Escalation":
        return (
          <Escalations
            disputes={disputes}
            loading={loading}
            error={error}
          />
        );

      default:
        return (
          <Dashboard
            disputes={disputes}
            loading={loading}
            error={error}
            setActivePage={setActivePage}
          />
        );
    }
  };

  return (
    <div className="app-container">
      {/* SIDEBAR */}

      <aside className="sidebar">
        <div>
          <div className="brand">
            <div className="brand-icon">
              <ShieldCheck size={27} />
            </div>

            <div>
              <h2>DisputeAI</h2>
              <span>Banking Intelligence</span>
            </div>
          </div>

          <div className="nav-section">
            <p className="nav-label">MAIN MENU</p>

            {navigation.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.name}
                  className={`nav-item ${
                    activePage === item.name ? "active" : ""
                  }`}
                  onClick={() => setActivePage(item.name)}
                >
                  <Icon size={19} />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="sidebar-bottom">
          <ShieldCheck size={20} />

          <div>
            <strong>Secure System</strong>
            <span>AI-powered dispute triage</span>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}

      <main className="main-content">
        <header className="topbar">
          <div>
            <h2>{activePage}</h2>
            <p>Unauthorised Transaction & Card Dispute Triage</p>
          </div>

          <div className="topbar-right">
            <button className="icon-button">
              <Search size={19} />
            </button>

            <button className="icon-button">
              <Bell size={19} />
            </button>

            <div className="profile">
              <div className="avatar">SA</div>

              <div>
                <strong>System Admin</strong>
                <span>Administrator</span>
              </div>
            </div>
          </div>
        </header>

        <div className="page-content">{renderPage()}</div>
      </main>
    </div>
  );
}

// DASHBOARD

function Dashboard({ disputes, loading, error, setActivePage }) {
  const total = disputes.length;

  const pending = disputes.filter(
    (d) => d.status === "Pending"
  ).length;

  const resolved = disputes.filter(
    (d) => d.status === "Approved"
  ).length;

  const escalated = disputes.filter(
    (d) => d.status === "Escalated"
  ).length;

  // STATISTICS FROM DATABASE

  const stats = [
    {
      title: "Total Disputes",
      value: total,
      icon: CreditCard,
      color: "blue",
    },
    {
      title: "Pending Cases",
      value: pending,
      icon: Clock,
      color: "orange",
    },
    {
      title: "Resolved Cases",
      value: resolved,
      icon: CheckCircle,
      color: "green",
    },
    {
      title: "Escalated Cases",
      value: escalated,
      icon: AlertTriangle,
      color: "purple",
    },
  ];

  // MONTHLY DISPUTE DATA

  const monthlyData = disputes.reduce((acc, dispute) => {
    const date = new Date(dispute.date);

    if (isNaN(date.getTime())) return acc;

    const month = date.toLocaleString("en-US", {
      month: "short",
    });

    const existing = acc.find(
      (item) => item.month === month
    );

    if (existing) {
      existing.disputes++;
    } else {
      acc.push({
        month,
        disputes: 1,
      });
    }

    return acc;
  }, []);

  // TRANSACTION TYPE DISTRIBUTION

  const fraudData = [
    {
      name: "UPI",
      value: disputes.filter((d) => d.type === "UPI").length,
    },
    {
      name: "Card",
      value: disputes.filter((d) => d.type === "Card").length,
    },
  ].filter((item) => item.value > 0);

  return (
    <>
      {/* WELCOME */}

      <div className="welcome-section">
        <div>
          <h1>Welcome to DisputeAI 👋</h1>
          <p>
            Monitor, investigate and manage customer disputes.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() => setActivePage("Submit Dispute")}
        >
          <FilePlus size={18} />
          New Dispute
        </button>
      </div>

      {error && (
        <div className="info-box">
          <p>{error}</p>
        </div>
      )}

      {/* STATISTICS */}

      <div className="stats-grid">
        {stats.map((stat) => {
          const Icon = stat.icon;

          return (
            <div className="stat-card" key={stat.title}>
              <div className={`stat-icon ${stat.color}`}>
                <Icon size={23} />
              </div>

              <p>{stat.title}</p>
              <h2>{loading ? "..." : stat.value}</h2>
              <span>Database records</span>
            </div>
          );
        })}
      </div>

      {/* CHARTS */}

      <div className="charts-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Dispute Overview</h3>
              <p>Dispute activity from database</p>
            </div>

            <TrendingUp color="#2563eb" />
          </div>

          <ResponsiveContainer width="100%" height={270}>
            <BarChart data={monthlyData}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
              />
              <XAxis dataKey="month" />
              <YAxis allowDecimals={false} />
              <Tooltip />

              <Bar
                dataKey="disputes"
                fill="#2563eb"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Transaction Distribution</h3>
              <p>UPI and Card disputes</p>
            </div>
          </div>

          {fraudData.length > 0 ? (
            <ResponsiveContainer width="100%" height={270}>
              <PieChart>
                <Pie
                  data={fraudData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label
                >
                  {fraudData.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={COLORS[index]}
                    />
                  ))}
                </Pie>

                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="info-box">
              <p>No transaction data available.</p>
            </div>
          )}
        </div>
      </div>

      {/* RECENT DISPUTES */}

      <div className="panel table-panel">
        <div className="panel-header">
          <div>
            <h3>Recent Disputes</h3>
            <p>Latest customer complaints</p>
          </div>

          <span className="view-label">Database Records</span>
        </div>

        {loading ? (
          <p>Loading disputes...</p>
        ) : (
          <DisputeTable disputes={disputes.slice(0, 5)} />
        )}
      </div>
    </>
  );
}

// REUSABLE DISPUTE TABLE

function DisputeTable({ disputes }) {
  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Dispute ID</th>
            <th>Customer</th>
            <th>Transaction Type</th>
            <th>Amount</th>
            <th>Date</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {disputes.map((item) => (
            <tr key={item.id}>
              <td className="id-text">{item.id}</td>
              <td>{item.customer}</td>
              <td>{item.type}</td>

              <td>
                ₹{Number(item.amount).toLocaleString("en-IN")}
              </td>

              <td>{item.date}</td>

              <td>
                <span
                  className={`status ${item.status.toLowerCase()}`}
                >
                  {item.status}
                </span>
              </td>
            </tr>
          ))}

          {disputes.length === 0 && (
            <tr>
              <td colSpan="6">No disputes found in database.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// SUBMIT DISPUTE FORM

function SubmitDispute({ loadDisputes, setActivePage }) {
  const [form, setForm] = useState({
    customer: "",
    transactionId: "",
    amount: "",
    transactionType: "UPI",
    transactionDate: "",
    reportedDate: "",
    fraudDescription: "",
    otpShared: "No",
  });

  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (submitting) return;

    if (
      new Date(form.reportedDate) <
      new Date(form.transactionDate)
    ) {
      alert(
        "Reported date cannot be earlier than transaction date."
      );
      return;
    }

    setSubmitting(true);

    try {
      const result = await createDispute(form);

      alert(
        `Dispute successfully saved!\nDispute ID: ${result.dispute_id}`
      );

      await loadDisputes();
      setActivePage("Dispute History");
    } catch (error) {
      console.error("Submission failed:", error);

      const message = error.response?.data?.detail;

      alert(
        typeof message === "string"
          ? message
          : JSON.stringify(
              message || "Unable to submit dispute."
            )
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="panel form-panel">
      <h3>Submit New Dispute</h3>

      <p>
        Enter the customer and transaction information.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <label>
            Customer Name

            <input
              name="customer"
              value={form.customer}
              onChange={handleChange}
              placeholder="Enter customer name"
              minLength="2"
              maxLength="100"
              required
            />
          </label>

          <label>
            Transaction ID

            <input
              name="transactionId"
              value={form.transactionId}
              onChange={handleChange}
              placeholder="Enter transaction ID"
              minLength="3"
              maxLength="100"
              required
            />
          </label>

          <label>
            Transaction Amount (₹)

            <input
              name="amount"
              type="number"
              min="0.01"
              step="0.01"
              value={form.amount}
              onChange={handleChange}
              placeholder="Enter amount"
              required
            />
          </label>

          <label>
            Transaction Type

            <select
              name="transactionType"
              value={form.transactionType}
              onChange={handleChange}
            >
              <option value="UPI">UPI</option>
              <option value="Card">Card</option>
            </select>
          </label>

          <label>
            Transaction Date

            <input
              name="transactionDate"
              type="date"
              max={new Date().toISOString().split("T")[0]}
              value={form.transactionDate}
              onChange={handleChange}
              required
            />
          </label>

          <label>
            Reported Date

            <input
              name="reportedDate"
              type="date"
              max={new Date().toISOString().split("T")[0]}
              min={form.transactionDate || undefined}
              value={form.reportedDate}
              onChange={handleChange}
              required
            />
          </label>

          <label>
            Was OTP shared?

            <select
              name="otpShared"
              value={form.otpShared}
              onChange={handleChange}
            >
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </label>

          <label className="full-width">
            Fraud Description

            <textarea
              name="fraudDescription"
              value={form.fraudDescription}
              onChange={handleChange}
              placeholder="Describe the unauthorised transaction..."
              minLength="5"
              maxLength="2000"
              required
            />
          </label>
        </div>

        <button
          className="primary-button"
          type="submit"
          disabled={submitting}
        >
          {submitting ? "Submitting..." : "Submit Dispute"}
        </button>
      </form>
    </div>
  );
}

// DISPUTE HISTORY

function DisputeHistory({ disputes, loading, error }) {
  return (
    <div className="panel table-panel">
      <h3>Dispute History</h3>
      <p>All submitted customer complaints.</p>

      {error && <p>{error}</p>}

      {loading ? (
        <p>Loading dispute records...</p>
      ) : (
        <DisputeTable disputes={disputes} />
      )}
    </div>
  );
}

// AI RECOMMENDATIONS

function Recommendations({ disputes, loading, error }) {
  const analyzedDisputes = disputes.filter(
    (dispute) =>
      dispute.riskScore !== null &&
      dispute.riskScore !== undefined
  );

  const getPriorityColor = (priority) => {
    switch ((priority || "").toLowerCase()) {
      case "critical":
        return "#dc2626";

      case "high":
        return "#ea580c";

      case "medium":
        return "#d97706";

      case "low":
        return "#16a34a";

      default:
        return "#64748b";
    }
  };

  return (
    <div>
      <div className="panel">
        <h3>AI Recommendations</h3>
        <p>
          AI-powered fraud risk assessment and recommendations.
        </p>
      </div>

      {error && (
        <div className="info-box">
          <p>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="panel">
          <p>Loading AI analysis...</p>
        </div>
      ) : analyzedDisputes.length === 0 ? (
        <div className="panel">
          <BrainCircuit size={35} />
          <h3>No AI analysis available</h3>
          <p>
            Submit a dispute to generate an AI assessment.
          </p>
        </div>
      ) : (
        analyzedDisputes.map((dispute) => (
          <div
            className="panel"
            key={dispute.id}
            style={{ marginTop: "20px" }}
          >
            <div className="panel-header">
              <div>
                <h3>{dispute.customer}</h3>
                <p>Dispute ID: {dispute.id}</p>
              </div>

              <span
                style={{
                  background: getPriorityColor(dispute.priority),
                  color: "#ffffff",
                  padding: "7px 14px",
                  borderRadius: "20px",
                  fontWeight: "600",
                }}
              >
                {dispute.priority || "Not classified"}
              </span>
            </div>

            <div className="stats-grid">
              <div className="stat-card">
                <p>Risk Score</p>
                <h2>{dispute.riskScore}/100</h2>
              </div>

              <div className="stat-card">
                <p>Fraud Type</p>
                <h3>{dispute.fraudType || "Unknown"}</h3>
              </div>

              <div className="stat-card">
                <p>Escalation</p>
                <h3>
                  {dispute.escalated
                    ? "Required"
                    : "Not Required"}
                </h3>
              </div>
            </div>

            <div style={{ marginTop: "20px" }}>
              <h4>AI Recommendation</h4>

              <div className="info-box">
                <BrainCircuit size={22} />

                <p>
                  {dispute.recommendation ||
                    "No recommendation available."}
                </p>
              </div>
            </div>

            <div style={{ marginTop: "15px" }}>
              <p>
                <strong>Transaction ID:</strong>{" "}
                {dispute.transactionId}
              </p>

              <p>
                <strong>Amount:</strong>{" "}
                ₹{Number(dispute.amount).toLocaleString("en-IN")}
              </p>

              <p>
                <strong>Transaction Type:</strong>{" "}
                {dispute.type}
              </p>

              <p>
                <strong>Reported Date:</strong>{" "}
                {dispute.date}
              </p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

// HUMAN ESCALATION

function Escalations({ disputes, loading, error }) {
  const escalated = disputes.filter(
    (d) => d.status === "Escalated"
  );

  return (
    <div className="panel">
      <h3>Human Escalation Centre</h3>
      <p>Cases requiring manual analyst review.</p>

      {error && <p>{error}</p>}

      {loading ? (
        <p>Loading cases...</p>
      ) : escalated.length === 0 ? (
        <div className="info-box">
          <ShieldCheck size={30} />

          <h3>No escalated cases</h3>

          <p>
            There are currently no escalated database records.
          </p>
        </div>
      ) : (
        <DisputeTable disputes={escalated} />
      )}
    </div>
  );
}

export default App;