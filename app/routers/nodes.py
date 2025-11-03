from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..db import get_db

router = APIRouter(prefix="/nodes", tags=["Nodes"])

@router.get("/", response_model=list[schemas.Node])
def read_nodes(project_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.TopologyNode)
    if project_id:
        query = query.filter(models.TopologyNode.project_id == project_id)
    return query.all()

@router.post("/", response_model=schemas.Node, status_code=status.HTTP_201_CREATED)
def create_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    db_node = models.TopologyNode(**node.dict())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node

@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(models.TopologyNode).filter(models.TopologyNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    db.commit()
