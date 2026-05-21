export default function OrderList({ orders = [], onDispatch }) {
  const pending = orders.filter((o) => o.status === "pending");
  const active = orders.filter((o) => ["assigned", "in_transit"].includes(o.status));
  const completed = orders.filter((o) => o.status === "delivered");

  return (
    <section className="panel">
      <h3>Orders</h3>

      {pending.length > 0 && (
        <div className="order-group">
          <h4>Pending ({pending.length})</h4>
          {pending.map((o) => (
            <div key={o.id} className="order-card pending">
              <div className="order-header">
                <span>Order #{o.id}</span>
                <span className={`badge priority-${o.priority}`}>{o.priority}</span>
              </div>
              <div className="order-details">
                <span>{o.package_weight_kg} kg</span>
              </div>
              <button className="dispatch-btn" onClick={() => onDispatch(o.id)}>
                Dispatch
              </button>
            </div>
          ))}
        </div>
      )}

      {active.length > 0 && (
        <div className="order-group">
          <h4>Active ({active.length})</h4>
          {active.map((o) => (
            <div key={o.id} className="order-card active">
              <div className="order-header">
                <span>Order #{o.id}</span>
                <span className="badge assigned">Drone #{o.assigned_drone_id}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {completed.length > 0 && (
        <div className="order-group">
          <h4>Delivered ({completed.length})</h4>
        </div>
      )}

      {orders.length === 0 && <p className="muted">No orders yet</p>}
    </section>
  );
}
