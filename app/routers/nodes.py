from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.db_async import get_async_db

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.get("/", response_model=list[schemas.Node])
async def read_nodes(project_id: int | None = None, db: AsyncSession = Depends(get_async_db)):
    stmt = select(models.TopologyNode)
    if project_id:
        stmt = stmt.where(models.TopologyNode.project_id == project_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=schemas.Node, status_code=status.HTTP_201_CREATED)
async def create_node(node: schemas.NodeCreate, db: AsyncSession = Depends(get_async_db)):
    db_node = models.TopologyNode(**node.dict())
    db.add(db_node)
    await db.commit()
    await db.refresh(db_node)
    return db_node