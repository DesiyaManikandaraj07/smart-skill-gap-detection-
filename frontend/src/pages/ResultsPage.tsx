import { Link } from "react-router-dom";
import type { AnalyzeResponse } from "../api/client";
import { ScoreGauge } from "../components/ScoreGauge";
import { SkillChips } from "../components/SkillChips";
import { Roadmap } from "../components/Roadmap";
import { WhatIf } from "../components/WhatIf";
import { RESULT_KEY } from "./AnalyzePage";

function loadResult(): AnalyzeResponse | null {
  const raw = sessionStorage.getItem(RESULT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AnalyzeResponse;
  } catch {
    return null;
  }
}

export function ResultsPage() {
  const result = loadResult();

  if (!result) {
    return (
      <div className="panel">
        <h2>No analysis yet</h2>
        <p className="hint">Run an analysis first. Results stay in this browser session.</p>
        <Link className="btn btn-primary" to="/">Go to analyze</Link>
      </div>
    );
  }

  const summary = result.summary;
  const maxAbs = Math.max(...result.explanations.map((e) => Math.abs(e.contribution)), 0.01);

  return (
    <>
      <section className="hero" style={{ paddingBottom: "0.75rem" }}>
        <h1>{result.candidate_name}</h1>
        <p>
          {result.role_title ? `Target: ${result.role_title}` : "Custom JD"} ·{" "}
          {result.profile.skills.length} skills ·{" "}
          {result.profile.experience_years.toFixed(1)} yrs
          {result.profile.cgpa != null ? ` · CGPA ${result.profile.cgpa}` : ""}
        </p>
      </section>

      {!result.eligible && (
        <div className="banner danger">
          <strong>Hard gates failed.</strong> Effective selection outlook is capped — skills alone cannot clear
          CGPA / experience / location / degree filters in a real ATS.
        </div>
      )}
      {result.eligible && result.selection_likelihood_pct >= 70 && (
        <div className="banner ok">
          <strong>Eligible and competitive on paper.</strong> Keep strengthening weak evidence and remaining gaps.
        </div>
      )}

      <div className="panel">
        <ScoreGauge
          value={result.selection_likelihood_pct}
          effective={result.effective_selection_pct}
          confidence={result.confidence}
          blocked={!result.eligible}
        />
        <p className="disclaimer">{result.disclaimer}</p>
      </div>

      {summary && (
        <div className="panel">
          <h2>Coaching summary</h2>
          <p className="hint">{summary.headline}</p>
          <div className="grid-2">
            <div>
              <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem" }}>What you did right</h3>
              <ul className="summary-list">
                {summary.strengths.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem" }}>Where to improve</h3>
              <ul className="summary-list">
                {summary.improvements.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
          {!!summary.critical_blockers.length && (
            <div style={{ marginTop: "1rem" }}>
              <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem", color: "var(--danger)" }}>Critical blockers</h3>
              <ul className="summary-list">
                {summary.critical_blockers.map((s) => (
                  <li key={s} style={{ background: "var(--danger-soft)", borderColor: "#fecdca" }}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          <p className="muted" style={{ marginTop: "0.85rem", fontSize: "0.9rem" }}>{summary.effective_note}</p>
        </div>
      )}

      {summary?.gates?.length ? (
        <div className="panel">
          <h2>Objective requirements</h2>
          <p className="hint">Hard filters that override skill scores in real hiring pipelines.</p>
          <ul className="gate-list">
            {summary.gates.map((g) => (
              <li key={g.key} className={g.passed ? "pass" : g.severity === "hard" ? "fail" : ""}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                  <strong>{g.label}</strong>
                  <span className="muted">{g.passed ? "Pass" : "Fail"} · {g.severity}</span>
                </div>
                <div className="muted" style={{ fontSize: "0.88rem", marginTop: "0.25rem" }}>
                  Required: {g.required} · Observed: {g.observed}
                </div>
                <div style={{ marginTop: "0.35rem", fontSize: "0.9rem" }}>{g.advice}</div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="panel">
        <h2>Required skills vs your profile</h2>
        <p className="hint">Role requirements, matches, gaps, and weakly evidenced skills.</p>
        <div style={{ marginBottom: "0.85rem" }}>
          <h3 style={{ margin: "0 0 0.45rem", fontSize: "0.85rem" }}>Required for JD</h3>
          <div className="chip-row">
            {(result.required_skills || result.job_skills).map((s) => (
              <span className="chip req" key={s}>{s}</span>
            ))}
          </div>
        </div>
        <SkillChips
          matched={result.matched_skills}
          missing={result.missing_skills}
          weak={result.weak_skills}
        />
      </div>

      <div className="grid-2">
        <div className="panel">
          <h2>Learn next</h2>
          <p className="hint">Ranked by estimated score lift and demand.</p>
          <ul className="learn-list">
            {result.learn_next.map((item) => (
              <li key={item.skill}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                  <strong>#{item.demand_rank} {item.skill}</strong>
                  <span style={{ color: "var(--accent-ink)", fontFamily: "var(--mono)" }}>+{item.impact_pct}</span>
                </div>
                <div className="bar">
                  <span style={{ width: `${Math.min(100, item.impact_pct * 8)}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h2>Why this score</h2>
          <p className="hint">Feature contributions from the selection model.</p>
          <ul className="explain-list">
            {result.explanations.map((e) => (
              <li key={e.feature}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{e.feature.replace(/_/g, " ")}</span>
                  <span style={{ color: e.direction === "positive" ? "var(--ok)" : "var(--danger)", fontFamily: "var(--mono)" }}>
                    {e.contribution >= 0 ? "+" : ""}
                    {e.contribution.toFixed(3)}
                  </span>
                </div>
                <div className="bar">
                  <span
                    style={{
                      width: `${(Math.abs(e.contribution) / maxAbs) * 100}%`,
                      background: e.direction === "positive" ? "var(--accent)" : "var(--danger)",
                    }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="panel">
        <h2>Learning roadmap</h2>
        <p className="hint">Courses, projects, certifications, and time estimates.</p>
        <Roadmap items={result.roadmap} />
      </div>

      <div className="panel">
        <h2>What-if simulation</h2>
        <WhatIf result={result} />
      </div>

      <div className="actions">
        <Link className="btn btn-ghost" to="/">Analyze another</Link>
      </div>
    </>
  );
}
