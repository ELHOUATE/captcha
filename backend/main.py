from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from captcha_engine import CaptchaEngine
from config import SESSION_TTL_SECONDS

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Mon CAPTCHA IA", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/dataset", StaticFiles(directory=str(BASE_DIR / "dataset")), name="dataset")
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

engine = CaptchaEngine()
SESSIONS = {}

class VerifyRequest(BaseModel):
    captcha_id: str
    selected_indices: List[int]

@app.get("/")
def home():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/api/captcha/challenge")
def generate_challenge():
    try:
        challenge = engine.build_challenge()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    SESSIONS[challenge["id"]] = {
        "answer": challenge["correct_indices"],
        "expires_at": datetime.utcnow() + timedelta(seconds=SESSION_TTL_SECONDS),
        "used": False,
    }

    return {
        "id": challenge["id"],
        "type": challenge["type"],
        "target_class": challenge["target_class"],
        "label_fr": challenge["label_fr"],
        "instruction": challenge["instruction"],
        "images": challenge["images"],
        "grid_size": challenge["grid_size"],
    }

@app.post("/api/captcha/verify")
def verify_captcha(data: VerifyRequest):
    session = SESSIONS.get(data.captcha_id)
    if not session:
        return {"success": False, "error": "CAPTCHA invalide ou expiré."}
    if session["used"]:
        return {"success": False, "error": "CAPTCHA déjà utilisé."}
    if datetime.utcnow() > session["expires_at"]:
        SESSIONS.pop(data.captcha_id, None)
        return {"success": False, "error": "CAPTCHA expiré."}

    session["used"] = True
    correct = set(session["answer"])
    selected = set(data.selected_indices)

    success = selected == correct
    SESSIONS.pop(data.captcha_id, None)

    return {
        "success": success,
        "score": f"{len(selected & correct)}/{len(correct)}",
        "error": None if success else "Sélection incorrecte. Réessayez."
    }

@app.get("/api/health")
def health():
    return {"status": "ok"}
