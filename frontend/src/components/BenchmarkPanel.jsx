import { useState } from "react";

export default function BenchmarkPanel({ snapshot }) {
  const [expanded, setExpanded] = useState(false);

  if (!snapshot) return null;

  const { fps, renders, wsLatency, webVitals, memory } = snapshot;

  const wsArr = wsLatency || [];
  const wsAvg = wsArr.length
    ? (wsArr.reduce((a, b) => a + b, 0) / wsArr.length).toFixed(2)
    : "—";
  const wsMax = wsArr.length ? Math.max(...wsArr).toFixed(2) : "—";

  return (
    <section className="panel benchmark-panel">
      <h3
        onClick={() => setExpanded(!expanded)}
        style={{ cursor: "pointer", userSelect: "none" }}
      >
        Performance {expanded ? "▾" : "▸"}
      </h3>

      {expanded && (
        <div className="bench-content">
          <div className="bench-row">
            <span className="bench-label">FPS</span>
            <span className={`bench-value ${fps < 30 ? "warn" : ""}`}>{fps}</span>
          </div>

          {memory && (
            <div className="bench-row">
              <span className="bench-label">JS Heap</span>
              <span className="bench-value">
                {memory.usedMB} / {memory.totalMB} MB
              </span>
            </div>
          )}

          <div className="bench-row">
            <span className="bench-label">WS Latency (avg)</span>
            <span className="bench-value">{wsAvg} ms</span>
          </div>
          <div className="bench-row">
            <span className="bench-label">WS Latency (max)</span>
            <span className="bench-value">{wsMax} ms</span>
          </div>

          {Object.entries(webVitals).length > 0 && (
            <>
              <div className="bench-divider" />
              <div className="bench-section-title">Web Vitals</div>
              {Object.entries(webVitals).map(([k, v]) => (
                <div className="bench-row" key={k}>
                  <span className="bench-label">{k}</span>
                  <span className="bench-value">
                    {typeof v === "number" ? v.toFixed(1) : v}
                    {["FCP", "LCP", "TTFB", "INP"].includes(k) ? " ms" : ""}
                  </span>
                </div>
              ))}
            </>
          )}

          {Object.keys(renders).length > 0 && (
            <>
              <div className="bench-divider" />
              <div className="bench-section-title">Render Times</div>
              {Object.entries(renders).map(([name, r]) => (
                <div className="bench-row" key={name}>
                  <span className="bench-label">{name}</span>
                  <span className="bench-value">
                    {r.count}x avg {r.count ? (r.totalMs / r.count).toFixed(1) : 0} ms
                  </span>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </section>
  );
}
