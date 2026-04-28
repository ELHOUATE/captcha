# ============================================
# main.py — Serveur FastAPI (backend complet)
# ============================================

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from typing import List
from datetime import datetime, timedelta
from pathlib import Path
import uuid, random

from database import get_db, Image, Classe, Session as SessionModel, Tentative

# ── App FastAPI ────────────────────────────────────────────────────────────────
app = FastAPI(title="CAPTCHA v2 API", version="1.0.0")

# Autoriser le frontend à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les images du dataset
DATASET_DIR = Path("../dataset")

# ── Schémas Pydantic ───────────────────────────────────────────────────────────
class VerifyRequest(BaseModel):
    token: str
    selected: List[int]   # indices 0-8 des cases cliquées


# ── Route 1 : GET /generate ────────────────────────────────────────────────────
@app.get("/generate")
def generate(db: Session = Depends(get_db)):
    """
    Choisit une classe aléatoire, pioche 9 images depuis MySQL
    (mélange d'images avec et sans l'objet), crée un token de session.
    """

    # 1. Choisir une classe aléatoire
    classes  = db.query(Classe).all()
    if not classes:
        raise HTTPException(status_code=500, detail="Aucune classe en base de données")
    classe = random.choice(classes)

    # 2. Piocher des images qui contiennent l'objet (4-5)
    images_correctes = (
        db.query(Image)
        .filter(Image.classe_id == classe.id, Image.contient_objet == True)
        .order_by(func.rand())
        .limit(5)
        .all()
    )

    # 3. Piocher des images qui ne contiennent PAS l'objet (4-5)
    images_incorrectes = (
        db.query(Image)
        .filter(Image.classe_id == classe.id, Image.contient_objet == False)
        .order_by(func.rand())
        .limit(4)
        .all()
    )

    # Vérification
    if len(images_correctes) < 3 or len(images_incorrectes) < 3:
        raise HTTPException(
            status_code=500,
            detail=f"Pas assez d'images pour la classe '{classe.nom}'. Lance yolo_labeler.py d'abord."
        )

    # 4. Mélanger les 9 images
    neuf_images = images_correctes + images_incorrectes
    random.shuffle(neuf_images)

    # 5. Créer le token de session (expire dans 120 secondes)
    token = str(uuid.uuid4())
    ids_images   = [img.id for img in neuf_images]
    ids_correctes = [img.id for img in neuf_images if img.contient_objet]

    session = SessionModel(
        token      = token,
        classe_id  = classe.id,
        image_ids  = ids_images,
        correctes  = ids_correctes,
        expires_at = datetime.utcnow() + timedelta(seconds=120),
    )
    db.add(session)
    db.commit()

    # 6. Retourner au frontend
    return {
        "token":   token,
        "classe":  classe.nom,
        "label":   classe.label_fr,
        "images":  [f"/image/{img.chemin}" for img in neuf_images],
    }


# ── Route 2 : POST /verify ─────────────────────────────────────────────────────
@app.post("/verify")
def verify(data: VerifyRequest, request: Request, db: Session = Depends(get_db)):
    """
    Reçoit le token et les indices cliqués.
    Compare avec les bonnes réponses stockées dans MySQL.
    """

    ip = request.client.host

    # 1. Vérifier anti-abus : max 5 tentatives par IP par minute
    une_minute = datetime.utcnow() - timedelta(minutes=1)
    tentatives_recentes = (
        db.query(Tentative)
        .filter(Tentative.ip == ip, Tentative.created_at >= une_minute)
        .count()
    )
    if tentatives_recentes >= 5:
        raise HTTPException(status_code=429, detail="Trop de tentatives. Attends 1 minute.")

    # 2. Récupérer la session
    session = db.query(SessionModel).filter(SessionModel.token == data.token).first()

    if not session:
        return {"success": False, "reason": "token invalide"}

    if session.utilise:
        return {"success": False, "reason": "token déjà utilisé"}

    if datetime.utcnow() > session.expires_at:
        return {"success": False, "reason": "token expiré"}

    # 3. Marquer la session comme utilisée
    session.utilise = True
    db.commit()

    # 4. Convertir indices → IDs images
    ids_images = session.image_ids          # [12, 34, 67, 8, 91, 3, 55, 22, 44]
    ids_correctes = set(session.correctes)  # {12, 67, 91, 55}

    ids_cliques = set()
    for i in data.selected:
        if 0 <= i < len(ids_images):
            ids_cliques.add(ids_images[i])

    # 5. Calculer le score
    bonnes    = len(ids_cliques & ids_correctes)
    mauvaises = len(ids_cliques - ids_correctes)
    total     = len(ids_correctes)
    score     = bonnes / total if total > 0 else 0

    succes = score >= 0.75 and mauvaises <= 1

    # 6. Sauvegarder la tentative
    tentative = Tentative(
        token  = data.token,
        succes = succes,
        score  = round(score, 2),
        ip     = ip,
    )
    db.add(tentative)
    db.commit()

    return {
        "success": succes,
        "score":   f"{bonnes}/{total}",
    }


# ── Route 3 : GET /image/{chemin} ─────────────────────────────────────────────
@app.get("/image/{classe}/{filename}")
def get_image(classe: str, filename: str):
    """Sert une image depuis le dataset."""
    path = DATASET_DIR / classe / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image introuvable")
    return FileResponse(str(path))


# ── Route 4 : GET /stats (bonus) ──────────────────────────────────────────────
@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    """Statistiques globales du CAPTCHA."""
    total      = db.query(Tentative).count()
    reussies   = db.query(Tentative).filter(Tentative.succes == True).count()
    taux       = round(reussies / total * 100, 1) if total > 0 else 0
    nb_images  = db.query(Image).count()

    return {
        "total_tentatives":  total,
        "tentatives_reussies": reussies,
        "taux_succes":       f"{taux}%",
        "nb_images_dataset": nb_images,
    }