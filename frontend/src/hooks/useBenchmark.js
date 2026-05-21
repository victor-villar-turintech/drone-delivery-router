/**
 * Frontend performance benchmarking utilities.
 *
 * Tracks:
 *  - Component render durations (React Profiler)
 *  - WebSocket message processing latency
 *  - Web Vitals (FCP, LCP, CLS, INP, TTFB)
 *  - JS heap memory usage (Chrome only)
 *  - Frames-per-second estimate
 */

import { useCallback, useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Metric store (singleton)
// ---------------------------------------------------------------------------
const _metrics = {
  renders: {},       // { componentName: { count, totalMs, lastMs, maxMs } }
  wsLatency: [],     // last N message processing times (ms)
  webVitals: {},     // { FCP: value, LCP: value, ... }
  memory: null,      // { usedJSHeapSize, totalJSHeapSize, jsHeapSizeLimit }
  fps: 0,
};

const WS_LATENCY_WINDOW = 100;

// ---------------------------------------------------------------------------
// Render tracking (for React.Profiler onRender callback)
// ---------------------------------------------------------------------------
export function onRenderCallback(id, _phase, actualDuration) {
  if (!_metrics.renders[id]) {
    _metrics.renders[id] = { count: 0, totalMs: 0, lastMs: 0, maxMs: 0 };
  }
  const entry = _metrics.renders[id];
  entry.count += 1;
  entry.totalMs += actualDuration;
  entry.lastMs = actualDuration;
  entry.maxMs = Math.max(entry.maxMs, actualDuration);
}

// ---------------------------------------------------------------------------
// WebSocket latency tracking
// ---------------------------------------------------------------------------
export function recordWsLatency(ms) {
  _metrics.wsLatency.push(ms);
  if (_metrics.wsLatency.length > WS_LATENCY_WINDOW) {
    _metrics.wsLatency.shift();
  }
}

// ---------------------------------------------------------------------------
// Memory snapshot (Chrome only)
// ---------------------------------------------------------------------------
function sampleMemory() {
  if (performance.memory) {
    _metrics.memory = {
      usedMB: Math.round(performance.memory.usedJSHeapSize / 1048576 * 10) / 10,
      totalMB: Math.round(performance.memory.totalJSHeapSize / 1048576 * 10) / 10,
      limitMB: Math.round(performance.memory.jsHeapSizeLimit / 1048576 * 10) / 10,
    };
  }
}

// ---------------------------------------------------------------------------
// FPS counter
// ---------------------------------------------------------------------------
let _fpsFrames = 0;
let _fpsLastTime = performance.now();

function _fpsLoop() {
  _fpsFrames++;
  const now = performance.now();
  if (now - _fpsLastTime >= 1000) {
    _metrics.fps = _fpsFrames;
    _fpsFrames = 0;
    _fpsLastTime = now;
  }
  requestAnimationFrame(_fpsLoop);
}

let _fpsStarted = false;
function startFpsCounter() {
  if (!_fpsStarted) {
    _fpsStarted = true;
    requestAnimationFrame(_fpsLoop);
  }
}

// ---------------------------------------------------------------------------
// Web Vitals initialization
// ---------------------------------------------------------------------------
let _vitalsInitialized = false;

async function initWebVitals() {
  if (_vitalsInitialized) return;
  _vitalsInitialized = true;
  try {
    const { onFCP, onLCP, onCLS, onINP, onTTFB } = await import("web-vitals");
    const record = (metric) => {
      _metrics.webVitals[metric.name] = Math.round(metric.value * 100) / 100;
    };
    onFCP(record);
    onLCP(record);
    onCLS(record);
    onINP(record);
    onTTFB(record);
  } catch {
    /* web-vitals not available */
  }
}

// ---------------------------------------------------------------------------
// Console logging
// ---------------------------------------------------------------------------
function logMetrics() {
  sampleMemory();
  const renderSummary = {};
  for (const [name, r] of Object.entries(_metrics.renders)) {
    renderSummary[name] = {
      renders: r.count,
      avgMs: r.count ? Math.round((r.totalMs / r.count) * 100) / 100 : 0,
      lastMs: Math.round(r.lastMs * 100) / 100,
      maxMs: Math.round(r.maxMs * 100) / 100,
    };
  }

  const wsArr = _metrics.wsLatency;
  const wsStats = wsArr.length > 0
    ? {
        count: wsArr.length,
        avgMs: Math.round((wsArr.reduce((a, b) => a + b, 0) / wsArr.length) * 100) / 100,
        maxMs: Math.round(Math.max(...wsArr) * 100) / 100,
        lastMs: Math.round(wsArr[wsArr.length - 1] * 100) / 100,
      }
    : { count: 0 };

  console.log(
    "%c[BENCH-FRONTEND]",
    "color: #22c55e; font-weight: bold",
    {
      fps: _metrics.fps,
      renders: renderSummary,
      wsLatency: wsStats,
      webVitals: { ..._metrics.webVitals },
      memory: _metrics.memory,
    },
  );
}

// ---------------------------------------------------------------------------
// React hook: useBenchmark
// ---------------------------------------------------------------------------
export default function useBenchmark({ logIntervalMs = 5000 } = {}) {
  const [snapshot, setSnapshot] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    startFpsCounter();
    initWebVitals();

    intervalRef.current = setInterval(() => {
      sampleMemory();
      logMetrics();
      setSnapshot({
        fps: _metrics.fps,
        renders: { ..._metrics.renders },
        wsLatency: [..._metrics.wsLatency],
        webVitals: { ..._metrics.webVitals },
        memory: _metrics.memory ? { ..._metrics.memory } : null,
      });
    }, logIntervalMs);

    return () => clearInterval(intervalRef.current);
  }, [logIntervalMs]);

  const resetCounters = useCallback(() => {
    _metrics.renders = {};
    _metrics.wsLatency = [];
  }, []);

  return { snapshot, metrics: _metrics, resetCounters };
}
