import { MapContainer, TileLayer, Marker, Popup, Polygon, Polyline } from "react-leaflet";
import L from "leaflet";

const SF_CENTER = [37.775, -122.418];

const droneIcon = (status) =>
  L.divIcon({
    className: "drone-marker",
    html: `<div class="drone-dot ${status}"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });

const hubIcon = L.divIcon({
  className: "hub-marker",
  html: '<div class="hub-dot"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

function parseGeoJSON(geojson) {
  try {
    const parsed = JSON.parse(geojson);
    return parsed.coordinates[0].map(([lng, lat]) => [lat, lng]);
  } catch {
    return [];
  }
}

export default function MapView({ drones = [], hubs = [], nfzones = [] }) {
  return (
    <div className="map-container">
      <MapContainer center={SF_CENTER} zoom={13} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {nfzones.map((z) => (
          <Polygon
            key={z.id}
            positions={parseGeoJSON(z.polygon_geojson)}
            pathOptions={{ color: "red", fillColor: "red", fillOpacity: 0.25 }}
          >
            <Popup>{z.name}</Popup>
          </Polygon>
        ))}

        {hubs.map((h) => (
          <Marker key={`hub-${h.id}`} position={[h.latitude, h.longitude]} icon={hubIcon}>
            <Popup>
              <strong>{h.name}</strong>
              <br />
              {h.is_charging_station ? "⚡ Charging" : "Base only"}
            </Popup>
          </Marker>
        ))}

        {drones.map((d) => (
          <Marker key={`drone-${d.drone_id}`} position={[d.lat, d.lon]} icon={droneIcon(d.status)}>
            <Popup>
              <strong>Drone #{d.drone_id}</strong>
              <br />
              Battery: {d.battery_pct}%
              <br />
              Status: {d.status}
              {d.returning_to_base && <><br />⚠️ Returning to base</>}
            </Popup>
          </Marker>
        ))}

        {drones
          .filter((d) => d.path && d.path.length > 1)
          .map((d) => (
            <Polyline
              key={`path-${d.drone_id}`}
              positions={d.path.map(([lat, lon]) => [lat, lon])}
              pathOptions={{ color: "#3b82f6", weight: 2, dashArray: "6 4" }}
            />
          ))}
      </MapContainer>
    </div>
  );
}
