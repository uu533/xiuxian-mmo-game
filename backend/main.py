from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_tables
from backend.routes import action, auth, character, dev, inventory, log, progression, sect

app = FastAPI(title="多人在线修仙文字游戏 MVP", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(log.router)
app.include_router(progression.router)
app.include_router(sect.router)
app.include_router(dev.router)
