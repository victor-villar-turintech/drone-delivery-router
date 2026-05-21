import { useEffect, useRef, useState, useCallback } from "react";
import { recordWsLatency } from "./useBenchmark";

const WS_URL =
  import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/simulation";

export default function useWebSocket() {
  const [simState, setSimState] = useState({ drones: [], wind: {} });
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState <= 1) return;
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (evt) => {
      const t0 = performance.now();
      try {
        setSimState(JSON.parse(evt.data));
      } catch {
        /* ignore malformed */
      }
      recordWsLatency(performance.now() - t0);
    };

    ws.onclose = () => {
      setConnected(false);
      reconnectTimer.current = setTimeout(connect, 2000);
    };

    ws.onerror = () => ws.close();
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { simState, connected };
}
