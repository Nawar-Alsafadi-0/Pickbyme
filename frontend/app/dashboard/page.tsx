"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Summary = { conversions: number; gross_amount: string; commission_amount: string };

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [role, setRole] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("pickbyme_token");
    const storedRole = localStorage.getItem("pickbyme_role") ?? "";
    setRole(storedRole);
    if (!token || !["creator", "provider"].includes(storedRole)) {
      setError("Login with a creator or provider account first.");
      return;
    }
    apiFetch<Summary>(`/dashboard/${storedRole}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load dashboard"));
  }, []);

  return (
    <main className="section">
      <span className="pill">{role || "Dashboard"}</span>
      <h1>{role === "provider" ? "Provider dashboard" : "Creator dashboard"}</h1>
      {error && <p className="muted">{error}</p>}
      {summary && (
        <div className="stats">
          <div className="stat"><span className="muted">Conversions</span><strong>{summary.conversions}</strong></div>
          <div className="stat"><span className="muted">Gross sales</span><strong>{summary.gross_amount} OMR</strong></div>
          <div className="stat"><span className="muted">Creator commissions</span><strong>{summary.commission_amount} OMR</strong></div>
        </div>
      )}
    </main>
  );
}
