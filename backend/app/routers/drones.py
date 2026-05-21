from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.drone import Drone
from app.schemas.drone import DroneCreate, DroneRead, DroneUpdate

router = APIRouter(prefix="/api/drones", tags=["drones"])


@router.get("/", response_model=list[DroneRead])
async def list_drones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Drone))
    return result.scalars().all()


@router.get("/{drone_id}", response_model=DroneRead)
async def get_drone(drone_id: int, db: AsyncSession = Depends(get_db)):
    drone = await db.get(Drone, drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    return drone


@router.post("/", response_model=DroneRead, status_code=201)
async def create_drone(body: DroneCreate, db: AsyncSession = Depends(get_db)):
    drone = Drone(**body.model_dump())
    db.add(drone)
    await db.commit()
    await db.refresh(drone)
    return drone


@router.patch("/{drone_id}", response_model=DroneRead)
async def update_drone(drone_id: int, body: DroneUpdate, db: AsyncSession = Depends(get_db)):
    drone = await db.get(Drone, drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(drone, k, v)
    await db.commit()
    await db.refresh(drone)
    return drone
