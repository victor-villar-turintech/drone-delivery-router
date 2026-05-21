from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.hub import Hub
from app.schemas.hub import HubCreate, HubRead

router = APIRouter(prefix="/api/hubs", tags=["hubs"])


@router.get("/", response_model=list[HubRead])
async def list_hubs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hub))
    return result.scalars().all()


@router.post("/", response_model=HubRead, status_code=201)
async def create_hub(body: HubCreate, db: AsyncSession = Depends(get_db)):
    hub = Hub(**body.model_dump())
    db.add(hub)
    await db.commit()
    await db.refresh(hub)
    return hub
