export default function DroneList({ drones = [] }) {
  if (!drones.length) {
    return (
      <section className="panel">
        <h3>Fleet</h3>
        <p className="muted">No drones in simulation</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h3>Fleet ({drones.length})</h3>
      <ul className="drone-list">
        {drones.map((d) => (
          <li key={d.drone_id} className={`drone-item ${d.status}`}>
            <div className="drone-id">#{d.drone_id}</div>
            <div className="drone-info">
              <span className={`badge ${d.status}`}>{d.status}</span>
              <span className="battery">
                🔋 {d.battery_pct}%
              </span>
            </div>
            {d.returning_to_base && <div className="warning">Returning to base</div>}
          </li>
        ))}
      </ul>
    </section>
  );
}
