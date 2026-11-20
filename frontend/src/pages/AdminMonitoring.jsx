import React, { useState, useEffect } from "react";
import { Activity, Server, ShieldAlert, Cpu, ExternalLink, RefreshCw, CheckCircle2 } from "lucide-react";
import { getMonitoringData } from "../services/api";
import StatCard from "../components/StatCard";

export default function AdminMonitoring() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadMonitoring = async () => {
    try {
      setLoading(true);
      const res = await getMonitoringData();
      setData(res);
    } catch (err) {
      console.error("Failed to load monitoring data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMonitoring();
    const interval = setInterval(loadMonitoring, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="monitoring-page">
      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>System Health & Prometheus Telemetry</h3>
            <p className="panel-sub">
              Live observability metrics, API latency histograms, and multi-agent workload counters.
            </p>
          </div>
          <button className="btn-secondary-sm" onClick={loadMonitoring}>
            <RefreshCw size={14} />
            <span>Refresh Telemetry</span>
          </button>
        </div>

        {/* Live Gauges */}
        <div className="stats-grid">
          <StatCard
            title="Service Status"
            value={data?.status || "OPERATIONAL"}
            subtitle="FastAPI + SQLite + ChromaDB"
            icon={CheckCircle2}
            color="green"
            loading={loading}
          />
          <StatCard
            title="Active Concurrent Requests"
            value={data?.active_concurrent_requests ?? 0}
            subtitle="In-flight verification requests"
            icon={Cpu}
            color="blue"
            loading={loading}
          />
          <StatCard
            title="Total Verification Requests"
            value={data?.total_verification_requests ?? 0}
            subtitle="Successful verification calls"
            icon={Activity}
            color="purple"
            loading={loading}
          />
          <StatCard
            title="Human Escalations Recorded"
            value={data?.total_human_escalations ?? 0}
            subtitle="Flagged for human investigation"
            icon={ShieldAlert}
            color="orange"
            loading={loading}
          />
        </div>

        {/* Telemetry Architecture Overview */}
        <div className="dossier-section" style={{ marginTop: "24px" }}>
          <h4>Telemetry Infrastructure Endpoints</h4>
          <div className="telemetry-endpoints-grid">
            <div className="endpoint-card">
              <strong>Prometheus Metrics Scrape Target</strong>
              <p>Exposes Prometheus text-formatted metrics at /metrics for scraper ingestion.</p>
              <a href="http://localhost:8000/metrics" target="_blank" rel="noreferrer" className="btn-link-ext">
                <span>View Raw /metrics</span>
                <ExternalLink size={14} />
              </a>
            </div>

            <div className="endpoint-card">
              <strong>Prometheus Server (Docker: 9090)</strong>
              <p>Time-series database collecting DisputeAI request durations and request rates.</p>
              <span className="font-mono">http://localhost:9090</span>
            </div>

            <div className="endpoint-card">
              <strong>Grafana Dashboard (Docker: 3000)</strong>
              <p>Pre-configured visual dashboards with request rate graphs and latency percentiles.</p>
              <span className="font-mono">http://localhost:3000 (admin / admin)</span>
            </div>

            <div className="endpoint-card">
              <strong>Locust Load Testing Suite</strong>
              <p>Simulates concurrent customer dispute submissions and administrator reviews.</p>
              <span className="font-mono">locust -f monitoring/locustfile.py</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
