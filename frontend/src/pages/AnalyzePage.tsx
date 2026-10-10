import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeResume, fetchJobFeed, type JobFeedItem } from "../api/client";
import { JobFeed } from "../components/JobFeed";
import { UploadZone } from "../components/UploadZone";
import { useAuth } from "../auth/AuthContext";

export const RESULT_KEY = "ssg_last_result";

type JdMode = "feed" | "custom";

export function AnalyzePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [name, setName] = useState(user?.full_name || "");
  const [file, setFile] = useState<File | null>(null);
  const [extraSkills, setExtraSkills] = useState("");
  const [location, setLocation] = useState("");
  const [cgpa, setCgpa] = useState("");
  const [jobs, setJobs] = useState<JobFeedItem[]>([]);
  const [level, setLevel] = useState("all");
  const [roleId, setRoleId] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [jdMode, setJdMode] = useState<JdMode>("feed");
  const [loading, setLoading] = useState(false);
  const [feedLoading, setFeedLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.full_name && !name) setName(user.full_name);
  }, [user, name]);

  const loadFeed = useCallback(async (lvl: string, refresh = false) => {
    setFeedLoading(true);
    setError(null);
    try {
      const items = await fetchJobFeed({ level: lvl, source: "all", refresh });
      setJobs(items);
    } catch {
      setError("Could not load job feed. Is the API running?");
    } finally {
      setFeedLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFeed(level, false);
  }, [level, loadFeed]);

  function selectJob(job: JobFeedItem) {
    setJdMode("feed");
    setRoleId(job.id);
    setJobDescription(job.description);
  }

  function switchToCustom() {
    setJdMode("custom");
    setRoleId("");
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) return setError("Enter your name.");
    if (!file) return setError("Upload a PDF resume.");
    if (jdMode === "feed" && !roleId) {
      return setError("Select a job from the feed, or switch to Custom JD.");
    }
    if (jdMode === "custom" && !jobDescription.trim()) {
      return setError("Paste a custom job description.");
    }

    const form = new FormData();
    form.append("file", file);
    form.append("name", name.trim());
    form.append("extra_skills", extraSkills);
    form.append("role_id", jdMode === "feed" ? roleId : "");
    form.append("job_description", jobDescription);
    form.append("location", location);
    form.append("cgpa", cgpa);

    setLoading(true);
    try {
      const result = await analyzeResume(form);
      sessionStorage.setItem(RESULT_KEY, JSON.stringify(result));
      navigate("/results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const selected = jobs.find((j) => j.id === roleId);

  return (
    <>
      <section className="hero">
        <h1>Measure fit. Expose blockers. Close the gap.</h1>
        <p>
          Pick a live/curated job from the feed (entry → senior), or paste your own JD.
          Get selection likelihood, skill gaps, hard gates, and a coaching summary.
          {user ? " Signed in — results are saved." : " Sign in to save history."}
        </p>
      </section>

      <form onSubmit={onSubmit}>
        <div className="grid-2">
          <div className="panel">
            <h2>Candidate</h2>
            <p className="hint">PDF only. Optional CGPA/location improve hard-gate accuracy.</p>

            <div className="field">
              <label htmlFor="name">Name</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Alex Rivera" />
            </div>

            <div className="field">
              <label>Resume (PDF)</label>
              <UploadZone file={file} onFile={setFile} />
            </div>

            <div className="grid-2" style={{ gap: "0.75rem" }}>
              <div className="field">
                <label htmlFor="cgpa">CGPA (optional, 4.0 scale)</label>
                <input id="cgpa" value={cgpa} onChange={(e) => setCgpa(e.target.value)} placeholder="3.4" />
              </div>
              <div className="field">
                <label htmlFor="loc">Location (optional)</label>
                <input id="loc" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Bangalore" />
              </div>
            </div>

            <div className="field">
              <label htmlFor="extra">Additional skills</label>
              <textarea
                id="extra"
                value={extraSkills}
                onChange={(e) => setExtraSkills(e.target.value)}
                placeholder="Docker, Kubernetes, GraphQL…"
              />
            </div>
          </div>

          <div className="panel">
            <h2>Target job</h2>
            <p className="hint">
              Feed mixes curated market-style JDs (all levels) with Remotive remote postings.
              Custom JD always available.
            </p>

            <div className="mode-tabs" role="tablist" aria-label="Job source">
              <button
                type="button"
                className={`mode-tab ${jdMode === "feed" ? "active" : ""}`}
                onClick={() => setJdMode("feed")}
              >
                Job feed
              </button>
              <button
                type="button"
                className={`mode-tab ${jdMode === "custom" ? "active" : ""}`}
                onClick={switchToCustom}
              >
                Custom JD
              </button>
            </div>

            {jdMode === "feed" ? (
              <>
                {feedLoading && jobs.length === 0 ? (
                  <p className="muted">Loading job feed…</p>
                ) : (
                  <JobFeed
                    jobs={jobs}
                    selectedId={roleId}
                    onSelect={selectJob}
                    level={level}
                    onLevel={setLevel}
                    refreshing={feedLoading}
                    onRefresh={() => loadFeed(level, true)}
                  />
                )}
                {selected && (
                  <div className="selected-job-banner">
                    Selected: <strong>{selected.title}</strong> · {selected.company} ·{" "}
                    {selected.experience_level}
                  </div>
                )}
              </>
            ) : (
              <div className="field" style={{ marginTop: "0.75rem" }}>
                <label htmlFor="jd">Paste any job description</label>
                <textarea
                  id="jd"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste a full job description from LinkedIn, company careers page, etc…"
                  style={{ minHeight: 280 }}
                />
              </div>
            )}

            {jdMode === "feed" && (
              <details className="jd-preview">
                <summary>Preview selected JD text</summary>
                <pre>{jobDescription || "Select a job card to load its description."}</pre>
              </details>
            )}
          </div>
        </div>

        {error && <div className="error">{error}</div>}

        <div className="actions" style={{ marginTop: "1.1rem" }}>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "Analyzing…" : "Run full analysis"}
          </button>
        </div>
      </form>
    </>
  );
}
