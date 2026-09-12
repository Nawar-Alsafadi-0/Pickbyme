"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type LoginResponse = {
  access_token: string;
  account: { role: "creator" | "provider" | "customer" | "admin" };
};

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      const result = await apiFetch<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      });
      localStorage.setItem("pickbyme_token", result.access_token);
      localStorage.setItem("pickbyme_role", result.account.role);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth">
      <div className="card">
        <span className="pill">Welcome back</span>
        <h1>Login to PickByMe</h1>
        <form onSubmit={submit}>
          <label>Email</label>
          <input className="input" name="email" type="email" required />
          <label>Password</label>
          <input className="input" name="password" type="password" minLength={8} required />
          {error && <p className="muted">{error}</p>}
          <button className="btn primary" disabled={loading}>{loading ? "Signing in..." : "Login"}</button>
        </form>
      </div>
    </main>
  );
}
