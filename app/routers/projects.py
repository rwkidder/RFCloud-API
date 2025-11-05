from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_async import get_async_db
from app import models, schemas

router = APIRouter(prefix="/async/projects", tags=["Async Projects"])

# 🔹 Get all projects
@router.get("/", response_model=list[schemas.Project])
async def read_projects(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(models.Project))
    return result.scalars().all()

# 🔹 Get a single project by ID
@router.get("/{project_id}", response_model=schemas.Project)
async def read_project(project_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# 🔹 Create a new project
@router.post("/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
async def create_project(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_async_db)):
    db_project = models.Project(**project.dict())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project

# 🔹 Delete a project by ID
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
