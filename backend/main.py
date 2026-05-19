import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_tables
from backend.routes import action, auth, auto_cultivation, character, dev, goals, inventory, log, progression, sect, life_skills

app = FastAPI(title="多人在线修仙文字游戏 MVP", version="1.0.0")

# CORS: allow configurable origins, default * for local dev
_cors_env = os.getenv("CORS_ORIGINS", "")
if _cors_env:
    _allow_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    _allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_tables()


@app.get("/")
def health() -> dict:
    return {"ok": True, "message": "Xiuxian MMO MVP API is running"}


app.include_router(auth.router)
app.include_router(character.router)
app.include_router(action.router)
app.include_router(inventory.router)
app.include_router(auto_cultivation.router)
app.include_router(log.router)
app.include_router(progression.router)
app.include_router(sect.router)
# Dev routes gated by ENABLE_DEV_ROUTES env var (default: disabled for public deployment)
if os.getenv("ENABLE_DEV_ROUTES", "").lower() in ("1", "true", "yes"):
    app.include_router(dev.router)
app.include_router(goals.router)
app.include_router(life_skills.router)
