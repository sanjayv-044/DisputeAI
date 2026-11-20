import React from "react";

export function StatusBadge({ status }) {
  const s = (status || "").toLowerCase();
  let badgeClass = "badge-neutral";

  if (s.includes("approved") || s === "resolved") {
    badgeClass = "badge-success";
  } else if (s.includes("rejected")) {
    badgeClass = "badge-danger";
  } else if (s.includes("escalated")) {
    badgeClass = "badge-purple";
  } else if (s.includes("investigation") || s.includes("review")) {
    badgeClass = "badge-primary";
  } else if (s.includes("pending")) {
    badgeClass = "badge-warning";
  }

  return <span className={`badge ${badgeClass}`}>{status || "Pending"}</span>;
}

export function RiskBadge({ level, score }) {
  const l = (level || "").toLowerCase();
  let badgeClass = "badge-neutral";

  if (l === "critical") {
    badgeClass = "badge-critical";
  } else if (l === "high") {
    badgeClass = "badge-danger";
  } else if (l === "medium") {
    badgeClass = "badge-warning";
  } else if (l === "low") {
    badgeClass = "badge-success";
  }

  return (
    <span className={`badge ${badgeClass}`}>
      {level || "Medium"} {score !== undefined && score !== null ? `(${score})` : ""}
    </span>
  );
}
