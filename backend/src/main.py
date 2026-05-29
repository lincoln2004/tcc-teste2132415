import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import file_routes, model_routes

app = FastAPI(title="AnomalyDetect API", version="1.0.0")

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(file_routes.router, prefix="/api")
app.include_router(model_routes.router, prefix="/api")

@app.get("/")
def health():
    return {"status": "ok"}

@app.head("/")
def health_head():
    return None
