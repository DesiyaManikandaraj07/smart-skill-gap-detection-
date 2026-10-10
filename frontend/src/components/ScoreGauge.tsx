import { useEffect, useState } from "react";

type Props = {
  value: number;
  effective: number;
  confidence: number;
  blocked?: boolean;
};

export function ScoreGauge({ value, effective, confidence, blocked }: Props) {
  const [shown, setShown] = useState(0);
  const display = blocked ? effective : value;

  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const duration = 850;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(display * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [display]);

  return (
    <div className="score-wrap">
      <div className={`gauge ${blocked ? "blocked" : ""}`} style={{ ["--p" as string]: shown }}>
        <div className="gauge-value">
          <div className="pct">{shown.toFixed(0)}%</div>
          <div className="lbl">{blocked ? "effective" : "skills"}</div>
        </div>
      </div>
      <div>
        <h2 style={{ marginTop: 0 }}>Selection likelihood</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          Skills-model estimate for progressing an ATS-style screen. Hard gates can zero the effective outlook.
        </p>
        <div className="stat-row">
          <div className="stat">
            <div className="n">{value.toFixed(1)}%</div>
            <div className="k">Skills model</div>
          </div>
          <div className="stat">
            <div className="n">{effective.toFixed(1)}%</div>
            <div className="k">Effective</div>
          </div>
          <div className="stat">
            <div className="n">{(confidence * 100).toFixed(0)}%</div>
            <div className="k">Confidence</div>
          </div>
        </div>
      </div>
    </div>
  );
}
