from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.engine.physics import BatteryState, WindCondition
from app.engine.routing import find_path
from app.engine.simulation import SimDrone, simulation_engine
from app.models.drone import Drone, DroneStatus
from app.models.nofly_zone import NoFlyZone
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderRead

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/", response_model=list[OrderRead])
async def list_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order))
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderRead, status_code=201)
async def create_order(body: OrderCreate, db: AsyncSession = Depends(get_db)):
    order = Order(**body.model_dump())
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/{order_id}/dispatch", response_model=dict)
async def dispatch_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.pending.value:
        raise HTTPException(status_code=400, detail="Order is not pending")

    result = await db.execute(
        select(Drone).where(
            Drone.status == DroneStatus.idle.value,
            Drone.max_payload_kg >= order.package_weight_kg,
        )
    )
    drone = result.scalars().first()
    if not drone:
        raise HTTPException(status_code=409, detail="No available drone for this payload")

    nfz_result = await db.execute(select(NoFlyZone))
    nfz_geojsons = [z.polygon_geojson for z in nfz_result.scalars().all()]

    wind = simulation_engine.wind
    route_to_pickup = find_path(
        drone.latitude, drone.longitude,
        order.pickup_lat, order.pickup_lon,
        nfz_geojsons,
        wind_vector=wind.vector,
        payload_kg=0.0,
        battery_pct=drone.battery_pct,
        battery_capacity_mah=drone.battery_capacity_mah,
    )
    route_to_dropoff = find_path(
        order.pickup_lat, order.pickup_lon,
        order.dropoff_lat, order.dropoff_lon,
        nfz_geojsons,
        wind_vector=wind.vector,
        payload_kg=order.package_weight_kg,
        battery_pct=drone.battery_pct,
        battery_capacity_mah=drone.battery_capacity_mah,
    )

    if route_to_pickup.get("error") or route_to_dropoff.get("error"):
        raise HTTPException(status_code=422, detail="Cannot find valid path")

    full_path = route_to_pickup["path"] + route_to_dropoff["path"][1:]
    total_battery = route_to_pickup["battery_cost_pct"] + route_to_dropoff["battery_cost_pct"]
    total_distance = route_to_pickup["distance_km"] + route_to_dropoff["distance_km"]

    drone.status = DroneStatus.en_route.value
    order.status = OrderStatus.assigned.value
    order.assigned_drone_id = drone.id
    await db.commit()

    sim_drone = simulation_engine.drones.get(drone.id)
    if not sim_drone:
        sim_drone = SimDrone(
            drone_id=drone.id,
            lat=drone.latitude,
            lon=drone.longitude,
            battery=BatteryState(drone.battery_capacity_mah, drone.battery_pct),
            payload_kg=order.package_weight_kg,
            home_lat=drone.latitude,
            home_lon=drone.longitude,
        )
        simulation_engine.add_drone(sim_drone)
    else:
        sim_drone.payload_kg = order.package_weight_kg

    simulation_engine.assign_path(drone.id, full_path, order_id=order.id)

    return {
        "order_id": order.id,
        "drone_id": drone.id,
        "path": full_path,
        "total_distance_km": round(total_distance, 4),
        "estimated_battery_cost_pct": round(total_battery, 2),
    }
