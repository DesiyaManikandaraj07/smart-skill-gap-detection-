import type { JobFeedItem } from "../api/client";

type Props = {
  jobs: JobFeedItem[];
  selectedId: string;
  onSelect: (job: JobFeedItem) => void;
  level: string;
  onLevel: (level: string) => void;
  refreshing?: boolean;
  onRefresh?: () => void;
};

const LEVELS = [
  { id: "all", label: "All levels" },
  { id: "entry", label: "Entry" },
  { id: "mid", label: "Mid" },
  { id: "senior", label: "Senior" },
];

export function JobFeed({ jobs, selectedId, onSelect, level, onLevel, refreshing, onRefresh }: Props) {
  return (
    <div>
      <div className="feed-toolbar">
        <div className="level-tabs" role="tablist" aria-label="Experience level">
          {LEVELS.map((l) => (
            <button
              key={l.id}
              type="button"
              role="tab"
              aria-selected={level === l.id}
              className={`level-tab ${level === l.id ? "active" : ""}`}
              onClick={() => onLevel(l.id)}
            >
              {l.label}
            </button>
          ))}
        </div>
        {onRefresh && (
          <button type="button" className="btn btn-ghost refresh-btn" onClick={onRefresh} disabled={refreshing}>
            {refreshing ? "Refreshing…" : "Refresh live"}
          </button>
        )}
      </div>

      <div className="job-feed" role="list">
        {jobs.length === 0 && (
          <p className="muted" style={{ padding: "0.75rem 0" }}>
            No jobs for this filter. Try another level or refresh live.
          </p>
        )}
        {jobs.map((job) => (
          <button
            type="button"
            key={job.id}
            role="listitem"
            className={`job-card ${selectedId === job.id ? "selected" : ""}`}
            onClick={() => onSelect(job)}
          >
            <div className="job-card-top">
              <span className={`level-pill ${job.experience_level}`}>{job.experience_level}</span>
              <span className="job-source">{job.source.replace(/_/g, " ")}</span>
            </div>
            <div className="job-title">{job.title}</div>
            <div className="job-meta">
              {job.company} · {job.category}
              {job.min_experience_years != null && job.min_experience_years > 0
                ? ` · ${job.min_experience_years}+ yrs`
                : " · early career OK"}
            </div>
            <p className="job-sum">{job.summary}</p>
            <div className="chip-row" style={{ marginTop: "0.45rem" }}>
              {job.required_skills.slice(0, 5).map((s) => (
                <span className="chip req" key={s}>{s}</span>
              ))}
              {job.required_skills.length > 5 && (
                <span className="muted" style={{ fontSize: "0.78rem" }}>+{job.required_skills.length - 5}</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
