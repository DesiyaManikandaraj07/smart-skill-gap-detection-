type Props = {
  matched: string[];
  missing: string[];
  weak: string[];
};

export function SkillChips({ matched, missing, weak }: Props) {
  return (
    <div className="grid-2" style={{ gap: "1rem" }}>
      <div>
        <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.95rem" }}>Matched</h3>
        <div className="chip-row">
          {matched.length ? matched.map((s, i) => (
            <span className="chip match" key={s} style={{ animationDelay: `${i * 30}ms` }}>{s}</span>
          )) : <span className="muted">None yet</span>}
        </div>
      </div>
      <div>
        <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.95rem" }}>Missing</h3>
        <div className="chip-row">
          {missing.length ? missing.map((s, i) => (
            <span className="chip missing" key={s} style={{ animationDelay: `${i * 30}ms` }}>{s}</span>
          )) : <span className="muted">Fully covered</span>}
        </div>
      </div>
      <div style={{ gridColumn: "1 / -1" }}>
        <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.95rem" }}>Weak (mentioned lightly)</h3>
        <div className="chip-row">
          {weak.length ? weak.map((s) => (
            <span className="chip weak" key={s}>{s}</span>
          )) : <span className="muted">No weak matches flagged</span>}
        </div>
      </div>
    </div>
  );
}
