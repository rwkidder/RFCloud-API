#from fastapi import FastAPI, Depends
#from sqlalchemy.orm import Session
#from .db import SessionLocal
#from . import models
from fastapi import FastAPI
from app.routers import projects, nodes, linkbudget, health, fresnel
from app.routers import analyze, linktests, plot, project_analysis, analyze_async  # new async version

app = FastAPI(title="RFCloud API", version="0.4")

app.include_router(projects.router)
app.include_router(nodes.router)
app.include_router(linkbudget.router)
app.include_router(health.router)
app.include_router(fresnel.router)
app.include_router(analyze.router)
app.include_router(linktests.router)
app.include_router(plot.router)
app.include_router(project_analysis.router)
app.include_router(analyze_async.router)

#print("Routers loaded:", app.routes)
