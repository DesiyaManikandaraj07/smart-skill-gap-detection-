import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email.trim(), password, fullName.trim());
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-card panel">
      <h2>Create account</h2>
      <p className="hint">Simple email/password — no OAuth required for this academic build.</p>
      <form onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="name">Full name</label>
          <input id="name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="password">Password (min 8)</label>
          <input id="password" type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <div className="error">{error}</div>}
        <div className="actions">
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "Creating…" : "Create account"}
          </button>
        </div>
      </form>
      <p className="muted" style={{ marginTop: "1rem", fontSize: "0.9rem" }}>
        Already registered? <Link to="/login">Sign in</Link>
      </p>
    </div>
  );
}
