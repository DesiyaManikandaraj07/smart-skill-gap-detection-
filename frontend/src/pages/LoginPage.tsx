import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-card panel">
      <h2>Sign in</h2>
      <p className="hint">Email and password. Analyses save to your account when signed in.</p>
      <form onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <div className="error">{error}</div>}
        <div className="actions">
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </div>
      </form>
      <p className="muted" style={{ marginTop: "1rem", fontSize: "0.9rem" }}>
        No account? <Link to="/register">Create one</Link>
      </p>
      <p className="muted" style={{ fontSize: "0.8rem" }}>
        Admin demo: <code>admin@example.com</code> / <code>Admin@Arawind2026</code>
      </p>
    </div>
  );
}
