import { useEffect, useMemo, useState } from "react";
import { runWhatIf, type AnalyzeResponse, type WhatIfResponse } from "../api/client";

export function WhatIf({ result }: { result: AnalyzeResponse }) {
  const candidates = useMemo(
    () => result.learn_next.map((x) => x.skill).slice(0, 8),
    [result.learn_next],
  );
  const [selected, setSelected] = useState<string[]>([]);
  const [sim, setSim] = useState<WhatIfResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggle(skill: string) {
    setSelected((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill],
    );
  }

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError(null);
      try {
        const res = await runWhatIf({
          candidate_name: result.candidate_name,
          current_skills: result.profile.skills,
          add_skills: selected,
          job_skills: result.job_skills,
          experience_years: result.profile.experience_years,
          project_count: result.profile.projects.length,
          cert_count: result.profile.certifications.length,
          has_degree: result.profile.education.length > 0,
          eligible: result.eligible,
        });
        if (!cancelled) setSim(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Simulation failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [selected, result]);

  return (
    <div>
      <p className="hint" style={{ marginTop: 0 }}>
        Toggle skills you plan to learn. Skills score updates live; hard gates stay fixed.
      </p>
      <div className="chip-row" style={{ marginBottom: "1rem" }}>
        {candidates.map((s) => (
          <button
            type="button"
            key={s}
            className={`chip selectable ${selected.includes(s) ? "on" : ""}`}
            onClick={() => toggle(s)}
          >
            {selected.includes(s) ? "✓ " : "+ "}
            {s}
          </button>
        ))}
      </div>
      {error && <div className="error">{error}</div>}
      <div className="stat-row">
        <div className="stat">
          <div className="n">
            {loading ? "…" : `${sim?.selection_likelihood_pct ?? result.selection_likelihood_pct}%`}
          </div>
          <div className="k">Skills score</div>
        </div>
        <div className="stat">
          <div className="n">
            {loading ? "…" : `${sim?.effective_selection_pct ?? result.effective_selection_pct}%`}
          </div>
          <div className="k">Effective</div>
        </div>
        <div className="stat">
          <div className="n" style={{ color: (sim?.delta_pct ?? 0) >= 0 ? "var(--ok)" : "var(--danger)" }}>
            {loading ? "…" : `${(sim?.delta_pct ?? 0) >= 0 ? "+" : ""}${sim?.delta_pct ?? 0}`}
          </div>
          <div className="k">Delta</div>
        </div>
      </div>
      {sim?.note && <p className="muted" style={{ marginTop: "0.75rem", fontSize: "0.88rem" }}>{sim.note}</p>}
    </div>
  );
}
