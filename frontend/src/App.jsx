import { useState, useEffect, Profiler } from "react";
import useWebSocket from "./hooks/useWebSocket";
import useBenchmark, { onRenderCallback } from "./hooks/useBenchmark";
import MapView from "./components/MapView";
import Sidebar from "./components/Sidebar";
import BenchmarkPanel from "./components/BenchmarkPanel";

const API = import.meta.env.VITE_API_URL || "";

export default function App() {
  const { simState, connected } = useWebSocket();
  const { snapshot } = useBenchmark({ logIntervalMs: 5000 });
  const [orders, setOrders] = useState([]);
  const [hubs, setHubs] = useState([]);
  const [nfzones, setNfzones] = useState([]);

  useEffect(() => {
    fetch(`${API}/api/orders/`).then((r) => r.json()).then(setOrders).catch(() => {});
    fetch(`${API}/api/hubs/`).then((r) => r.json()).then(setHubs).catch(() => {});
    fetch(`${API}/api/nofly-zones/`).then((r) => r.json()).then(setNfzones).catch(() => {});
  }, []);

  const dispatchOrder = async (orderId) => {
    const resp = await fetch(`${API}/api/orders/${orderId}/dispatch`, { method: "POST" });
    if (resp.ok) {
      const updated = await fetch(`${API}/api/orders/`).then((r) => r.json());
      setOrders(updated);
    }
  };

  return (
    <div className="app-layout">
      <Profiler id="Sidebar" onRender={onRenderCallback}>
        <Sidebar
          drones={simState.drones}
          orders={orders}
          wind={simState.wind}
          connected={connected}
          onDispatch={dispatchOrder}
          benchmarkPanel={<BenchmarkPanel snapshot={snapshot} />}
        />
      </Profiler>
      <Profiler id="MapView" onRender={onRenderCallback}>
        <MapView
          drones={simState.drones}
          hubs={hubs}
          nfzones={nfzones}
        />
      </Profiler>
    </div>
  );
}
