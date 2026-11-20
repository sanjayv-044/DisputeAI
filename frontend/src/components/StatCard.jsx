import React from "react";

export default function StatCard({ title, value, subtitle, icon: Icon, color = "blue", loading = false }) {
  return (
    <div className={`stat-card stat-${color}`}>
      <div className="stat-card-header">
        <p className="stat-title">{title}</p>
        {Icon && (
          <div className={`stat-icon-wrap icon-${color}`}>
            <Icon size={20} />
          </div>
        )}
      </div>
      <h2 className="stat-value">{loading ? "..." : value}</h2>
      {subtitle && <span className="stat-subtitle">{subtitle}</span>}
    </div>
  );
}
