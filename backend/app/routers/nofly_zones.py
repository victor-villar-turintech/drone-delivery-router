from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.nofly_zone import NoFlyZone
from app.schemas.nofly_zone import NoFlyZoneCreate, NoFlyZoneRead

router = APIRouter(prefix="/api/nofly-zones", tags=["no-fly zones"])


@router.get("/", response_model=list[NoFlyZoneRead])
async def list_zones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NoFlyZone))
    return result.scalars().all()


@router.post("/", response_model=NoFlyZoneRead, status_code=201)
async def create_zone(body: NoFlyZoneCreate, db: AsyncSession = Depends(get_db)):
    zone = NoFlyZone(**body.model_dump())
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone
