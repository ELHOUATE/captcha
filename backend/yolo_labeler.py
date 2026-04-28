# ============================================
# yolo_labeler.py — Lance YOLO sur tout le dataset
# et remplit la table MySQL "images"
# À lancer UNE SEULE FOIS avant de déployer
# ============================================

from ultralytics import YOLO
from pathlib import Path
from database import SessionLocal, Image, Classe
import sys

# ── Configuration ──────────────────────────────────────────────────────────────
DATASET_DIR = Path("../dataset")   # dossier avec car/, boat/, truck/
MODELS_DIR  = Path("models")       # dossier avec car_best.pt, boat_best.pt...
CONFIDENCE  = 0.25                 # seuil de confiance YOLO

# Correspondance classe → fichier modèle
MODELS = {
    "car":   MODELS_DIR / "car_best.pt",
    "boat":  MODELS_DIR / "boat_best.pt",
    "truck": MODELS_DIR / "truck_best.pt",
}


def labeler():
    db = SessionLocal()

    try:
        for classe_nom, model_path in MODELS.items():

            # 1. Vérifier que le modèle existe
            if not model_path.exists():
                print(f"[SKIP] Modèle introuvable : {model_path}")
                continue

            # 2. Charger le modèle YOLO
            print(f"\n[YOLO] Chargement : {model_path}")
            model = YOLO(str(model_path))

            # 3. Récupérer la classe dans MySQL
            classe = db.query(Classe).filter(Classe.nom == classe_nom).first()
            if not classe:
                print(f"[ERREUR] Classe '{classe_nom}' introuvable dans MySQL")
                print(f"  → Lance d'abord : mysql -u root -p captcha_db < database/seed.sql")
                continue

            # 4. Parcourir les images du dataset
            dossier = DATASET_DIR / classe_nom
            if not dossier.exists():
                print(f"[SKIP] Dossier introuvable : {dossier}")
                continue

            images = list(dossier.glob("*.jpg")) + \
                     list(dossier.glob("*.jpeg")) + \
                     list(dossier.glob("*.png"))

            print(f"[INFO] {len(images)} images trouvées dans {dossier}")

            compteur = {"ajoutees": 0, "ignorees": 0}

            for img_path in images:
                chemin_relatif = str(img_path.relative_to(DATASET_DIR))

                # Vérifier si déjà dans MySQL
                existante = db.query(Image).filter(Image.chemin == chemin_relatif).first()
                if existante:
                    compteur["ignorees"] += 1
                    continue

                # 5. Lancer la détection YOLO
                results = model.predict(str(img_path), conf=CONFIDENCE, verbose=False)
                boxes   = results[0].boxes

                nb_objets      = len(boxes)
                contient_objet = nb_objets > 0
                confiance      = float(boxes.conf.max()) if nb_objets > 0 else 0.0

                # 6. Insérer dans MySQL
                nouvelle_image = Image(
                    classe_id      = classe.id,
                    chemin         = chemin_relatif,
                    contient_objet = contient_objet,
                    confiance_yolo = round(confiance, 4),
                    nb_objets      = nb_objets,
                )
                db.add(nouvelle_image)
                compteur["ajoutees"] += 1

                # Affichage progression
                symbole = "✓" if contient_objet else "✗"
                print(f"  {symbole} {img_path.name} — confiance: {confiance:.2f} — objets: {nb_objets}")

            db.commit()
            print(f"\n[OK] {classe_nom}: {compteur['ajoutees']} ajoutées, {compteur['ignorees']} ignorées")

    except Exception as e:
        db.rollback()
        print(f"\n[ERREUR] {e}")
        sys.exit(1)

    finally:
        db.close()

    print("\n[TERMINÉ] Base de données remplie avec succès !")
    print("Tu peux maintenant lancer : uvicorn main:app --reload")


if __name__ == "__main__":
    labeler()