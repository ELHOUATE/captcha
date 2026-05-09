import base64
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image as PILImage
from pydantic import BaseModel

from captcha_engine import CaptchaEngine
from config import SESSION_TTL_SECONDS, get_threshold


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


class SolveRequest(BaseModel):
    images: List[str]
    target_class: str


@app.get("/")
def home():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/api/captcha/challenge")
def get_challenge():
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
        "debug_classes": challenge.get("debug_classes", []),
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


@app.post("/api/captcha/solve")
def solve_captcha(data: SolveRequest):
    """
    Solver automatique avec détection correcte des classes
    """
    try:
        model = engine.models.get(data.target_class)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de charger le modèle pour {data.target_class}: {e}"
        )

    # Utiliser le seuil spécifique à la classe
    threshold = get_threshold(data.target_class)
    
    scored_images = []

    for i, b64_img in enumerate(data.images):
        try:
            img_bytes = base64.b64decode(b64_img)
            img = PILImage.open(BytesIO(img_bytes)).convert("RGB")

            results = model.predict(
                source=img,
                conf=threshold,
                imgsz=640,
                verbose=False
            )

            best_score = 0.0
            
            if results.boxes is not None and len(results.boxes) > 0:
                best_score = float(max(results.boxes.conf))

            scored_images.append({
                "index": i,
                "score": best_score
            })

            print(f"[SOLVER] image={i}, score={best_score:.4f} (threshold={threshold})")

        except Exception as e:
            print(f"[ERREUR SOLVER] Image {i}: {e}")
            scored_images.append({
                "index": i,
                "score": 0.0
            })

    # Trier par score décroissant
    scored_images.sort(key=lambda item: item["score"], reverse=True)

    # Stratégie: Prendre les 4 meilleurs scores (pas de seuil pour éviter les non-détections)
    correct_indices = [item["index"] for item in scored_images[:4]]
    correct_indices.sort()

    print(f"[SOLVER] target_class = {data.target_class}")
    print(f"[SOLVER] threshold = {threshold}")
    print(f"[SOLVER] selected indices = {correct_indices}")

    return {
        "success": True,
        "target_class": data.target_class,
        "correct_indices": correct_indices,
        "scores": scored_images,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}