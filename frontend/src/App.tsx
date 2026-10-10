import { NavLink, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { AdminPage } from "./pages/AdminPage";
import { AnalyzePage } from "./pages/AnalyzePage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResultsPage } from "./pages/ResultsPage";

export default function App() {
  const { user, logout, loading } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">SkillGapAI</span>
          <span className="brand-sub">Skill gap & readiness</span>
        </div>
        <nav className="nav-pills">
          <NavLink to="/" end>Analyze</NavLink>
          <NavLink to="/results">Results</NavLink>
          {user?.is_admin && <NavLink to="/admin">Admin</NavLink>}
          {!loading && !user && <NavLink to="/login">Sign in</NavLink>}
          {!loading && !user && <NavLink to="/register">Register</NavLink>}
          {user && (
            <button type="button" className="nav-btn" onClick={logout}>
              {user.full_name.split(" ")[0]} · Sign out
            </button>
          )}
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<AnalyzePage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </div>
  );
}
