import DroneList from "./DroneList";
import OrderList from "./OrderList";

export default function Sidebar({ drones = [], orders = [], wind = {}, connected, onDispatch, benchmarkPanel }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>🛩️ Drone Delivery</h1>
        <span className={`status-dot ${connected ? "online" : "offline"}`} />
        <span className="status-text">{connected ? "Live" : "Disconnected"}</span>
      </div>

      {wind && (wind.speed_kmh !== undefined) && (
        <div className="wind-panel">
          <h3>Wind</h3>
          <p>{wind.speed_kmh} km/h @ {wind.direction_deg}°</p>
        </div>
      )}

      <DroneList drones={drones} />
      <OrderList orders={orders} onDispatch={onDispatch} />
      {benchmarkPanel}
    </aside>
  );
}
