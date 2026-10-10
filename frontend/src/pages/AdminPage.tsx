import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  fetchAdminAnalyses,
  fetchAdminStats,
  fetchAdminUsers,
  toggleUserActive,
  type AdminStats,
  type User,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function AdminPage() {
  const { user, loading } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [analyses, setAnalyses] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.is_admin) return;
    Promise.all([fetchAdminStats(), fetchAdminUsers(), fetchAdminAnalyses()])
      .then(([s, u, a]) => {
        setStats(s);
        setUsers(u);
        setAnalyses(a);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load admin data"));
  }, [user]);

  if (loading) return <p className="muted">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.is_admin) return <Navigate to="/" replace />;

  return (
    <>
      <section className="hero">
        <h1>Admin console</h1>
        <p>Users, analyses, and model health for the Arawind deployment.</p>
      </section>

      {error && <div className="error">{error}</div>}

      {stats && (
        <div className="panel">
          <h2>Overview</h2>
          <div className="stat-row">
            <div className="stat"><div className="n">{stats.users_total}</div><div className="k">Users</div></div>
            <div className="stat"><div className="n">{stats.analyses_total}</div><div className="k">Analyses</div></div>
            <div className="stat"><div className="n">{stats.analyses_today}</div><div className="k">Today</div></div>
            <div className="stat"><div className="n">{stats.avg_selection_pct.toFixed(1)}%</div><div className="k">Avg score</div></div>
            <div className="stat"><div className="n">{(stats.ineligible_rate * 100).toFixed(1)}%</div><div className="k">Ineligible</div></div>
          </div>
          <p className="muted" style={{ marginTop: "0.85rem" }}>
            Model: <strong>{stats.model_name}</strong>
            {stats.model_metrics?.test_f1 != null && <> · F1 {String(stats.model_metrics.test_f1)}</>}
            {stats.model_metrics?.test_roc_auc != null && <> · ROC-AUC {String(stats.model_metrics.test_roc_auc)}</>}
            {stats.model_metrics?.n_total != null && <> · train rows {String(stats.model_metrics.n_total)}</>}
          </p>
        </div>
      )}

      <div className="panel">
        <h2>Users</h2>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="num">{u.id}</td>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>{u.is_admin ? "Admin" : "User"}</td>
                  <td>{u.is_active ? "Active" : "Disabled"}</td>
                  <td>
                    {!u.is_admin && (
                      <button
                        type="button"
                        className="btn btn-ghost"
                        style={{ padding: "0.35rem 0.6rem", fontSize: "0.8rem" }}
                        onClick={async () => {
                          const updated = await toggleUserActive(u.id);
                          setUsers((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
                        }}
                      >
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>Recent analyses</h2>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>Candidate</th>
                <th>Role</th>
                <th>Skills %</th>
                <th>Effective %</th>
                <th>Eligible</th>
              </tr>
            </thead>
            <tbody>
              {analyses.map((a) => (
                <tr key={String(a.id)}>
                  <td className="num">{String(a.id)}</td>
                  <td>{String(a.user_email)}</td>
                  <td>{String(a.candidate_name)}</td>
                  <td>{String(a.role_title || "—")}</td>
                  <td className="num">{Number(a.selection_likelihood_pct).toFixed(1)}</td>
                  <td className="num">{Number(a.effective_selection_pct).toFixed(1)}</td>
                  <td>{a.eligible ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
