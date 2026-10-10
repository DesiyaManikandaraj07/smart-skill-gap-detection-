import type { RoadmapItem } from "../api/client";

export function Roadmap({ items }: { items: RoadmapItem[] }) {
  if (!items.length) {
    return <p className="muted">No roadmap items — your skills already cover this role.</p>;
  }
  return (
    <ul className="roadmap-list">
      {items.map((item) => (
        <li key={item.skill}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
            <strong>{item.skill}</strong>
            <span className="muted">~{item.weeks} weeks</span>
          </div>
          <p className="muted" style={{ margin: "0.35rem 0 0.6rem", fontSize: "0.9rem" }}>{item.rationale}</p>
          {!!item.courses.length && (
            <div style={{ marginBottom: "0.35rem" }}>
              <span className="muted" style={{ fontSize: "0.75rem", textTransform: "uppercase" }}>Courses</span>
              <ul style={{ margin: "0.2rem 0 0", paddingLeft: "1.1rem" }}>
                {item.courses.map((c) => <li key={c}>{c}</li>)}
              </ul>
            </div>
          )}
          {!!item.projects.length && (
            <div style={{ marginBottom: "0.35rem" }}>
              <span className="muted" style={{ fontSize: "0.75rem", textTransform: "uppercase" }}>Projects</span>
              <ul style={{ margin: "0.2rem 0 0", paddingLeft: "1.1rem" }}>
                {item.projects.map((c) => <li key={c}>{c}</li>)}
              </ul>
            </div>
          )}
          {!!item.certs.length && (
            <div>
              <span className="muted" style={{ fontSize: "0.75rem", textTransform: "uppercase" }}>Certifications</span>
              <ul style={{ margin: "0.2rem 0 0", paddingLeft: "1.1rem" }}>
                {item.certs.map((c) => <li key={c}>{c}</li>)}
              </ul>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
