from pathlib import Path
from ultralytics import YOLO

# =========================
# 1. Charger le modèle
# =========================
model_path = r"runs/detect/runs/yolo/yolov8n_bdd100k/weights/best.pt"
model = YOLO(model_path)

# =========================
# 2. Dossier des images réelles
# =========================
source_folder = Path(r"C:\Users\zineb\Desktop\real_test_images")

print("Vérification du dossier...")
print("Chemin :", source_folder)
print("Existe ?", source_folder.exists())

if not source_folder.exists():
    print("❌ Le dossier n'existe pas")
    exit()

images = list(source_folder.glob("*.jpg")) + list(source_folder.glob("*.jpeg")) + list(source_folder.glob("*.png"))

print("Nombre d'images trouvées :", len(images))

if len(images) == 0:
    print("❌ Aucune image trouvée dans le dossier")
    exit()

print("\nImages trouvées :")
for img in images:
    print("-", img.name)

# =========================
# 3. Faire la prédiction
# =========================
results = model.predict(
    source=str(source_folder),
    conf=0.25,
    imgsz=640,
    save=True
)

# =========================
# 4. Afficher les résultats
# =========================
print("\n===== RÉSULTATS =====\n")

for i, r in enumerate(results, start=1):
    image_name = Path(r.path).name
    print(f"Image {i}: {image_name}")

    if r.boxes is None or len(r.boxes) == 0:
        print("  -> Aucun objet détecté")
    else:
        classes = r.boxes.cls.tolist()
        confidences = r.boxes.conf.tolist()

        for cls_id, conf in zip(classes, confidences):
            class_name = model.names[int(cls_id)]
            print(f"  -> {class_name} ({conf:.2f})")

    print()

print("✅ Test terminé")
print("📁 Les images avec les boîtes sont enregistrées dans runs/detect/predict")
