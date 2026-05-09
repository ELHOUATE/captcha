# ================================================================
# 📥 Téléchargement Open Images V7 — Classes reCAPTCHA v2
# ✅ Train + Validation + Test séparés
# ================================================================

import fiftyone as fo
import fiftyone.zoo as foz
from pathlib import Path
import os, glob

# ================================================================
# ⚙️ CONFIGURATION
# ================================================================

OUTPUT_DIR = Path("recaptcha_dataset")

MAX_TRAIN = 3000
MAX_VAL   = 300
MAX_TEST  = 300

CLASSES_OIV7 = [
    "Car",
    "Bus",
    "Bicycle",
    "Motorcycle",
    "Truck",
    "Traffic light",
    "Fire hydrant",
    "Bridge",
    "Staircase",
    "Chimney",
    "Palm tree",
    "Taxi",
    "Mountain",
    "Stop sign",
]

CLASS_MAPPING = {
    "Car": "car",
    "Bus": "bus",
    "Bicycle": "bicycle",
    "Motorcycle": "motorcycle",
    "Truck": "truck",
    "Traffic light": "traffic light",
    "Fire hydrant": "fire hydrant",
    "Bridge": "bridge",
    "Staircase": "stairs",
    "Chimney": "chimney",
    "Palm tree": "palm tree",
    "Taxi": "taxi",
    "Mountain": "mountain or hill",
    "Stop sign": "stop sign",
}

# ================================================================
# 🧹 Nettoyage caches
# ================================================================

print("🧹 Nettoyage des caches...")
for cache in glob.glob(str(OUTPUT_DIR / "**" / "*.cache"), recursive=True):
    os.remove(cache)
    print(f"   Supprimé : {cache}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ================================================================
# 📥 Fonction téléchargement
# ================================================================

def download_oiv7_split(split_name, max_samples, dataset_name):
    print(f"\n📥 Téléchargement {split_name.upper()} ({max_samples} images)...")
    dataset = foz.load_zoo_dataset(
        "open-images-v7",
        split=split_name,
        label_types=["detections"],
        classes=CLASSES_OIV7,
        max_samples=max_samples,
        dataset_name=dataset_name,
        overwrite=True,
    )
    print(f"✅ {split_name} téléchargé : {len(dataset)} images")
    return dataset

# ================================================================
# 📥 Téléchargement des 3 splits séparés
# ================================================================

dataset_train = download_oiv7_split(
    split_name="train",
    max_samples=MAX_TRAIN,
    dataset_name="oiv7_recaptcha_train",
)

dataset_val = download_oiv7_split(
    split_name="validation",
    max_samples=MAX_VAL,
    dataset_name="oiv7_recaptcha_validation",
)

dataset_test = download_oiv7_split(
    split_name="test",
    max_samples=MAX_TEST,
    dataset_name="oiv7_recaptcha_test",
)

# ================================================================
# 💾 Export YOLO
# ================================================================

train_dir = OUTPUT_DIR / "train"
val_dir   = OUTPUT_DIR / "validation"
test_dir  = OUTPUT_DIR / "test"

print("\n💾 Export TRAIN en format YOLO...")
dataset_train.export(
    export_dir=str(train_dir),
    dataset_type=fo.types.YOLOv5Dataset,
    label_field="ground_truth",
    classes=CLASSES_OIV7,
    overwrite=True,
)

print("💾 Export VALIDATION en format YOLO...")
dataset_val.export(
    export_dir=str(val_dir),
    dataset_type=fo.types.YOLOv5Dataset,
    label_field="ground_truth",
    classes=CLASSES_OIV7,
    overwrite=True,
)

print("💾 Export TEST en format YOLO...")
dataset_test.export(
    export_dir=str(test_dir),
    dataset_type=fo.types.YOLOv5Dataset,
    label_field="ground_truth",
    classes=CLASSES_OIV7,
    overwrite=True,
)

# ================================================================
# 📝 Création data.yaml final
# ================================================================

final_names = list(CLASS_MAPPING.values())

yaml_content = f"""train: {str((train_dir / 'images').resolve())}
val: {str((val_dir / 'images').resolve())}
test: {str((test_dir / 'images').resolve())}

nc: {len(final_names)}
names:
""" + "".join([f"  - {name}\n" for name in final_names])

yaml_path = OUTPUT_DIR / "data.yaml"

with open(yaml_path, "w", encoding="utf-8") as f:
    f.write(yaml_content)

print(f"\n✅ data.yaml créé : {yaml_path}")

# ================================================================
# 📊 Résumé
# ================================================================

train_imgs = list((train_dir / "images").glob("*.*"))
val_imgs   = list((val_dir / "images").glob("*.*"))
test_imgs  = list((test_dir / "images").glob("*.*"))

train_labels = list((train_dir / "labels").glob("*.txt"))
val_labels   = list((val_dir / "labels").glob("*.txt"))
test_labels  = list((test_dir / "labels").glob("*.txt"))

print("\n" + "=" * 60)
print("✅ TÉLÉCHARGEMENT + EXPORT TERMINÉ")
print("=" * 60)
print(f"📁 Dossier dataset : {OUTPUT_DIR.resolve()}")
print(f"🖼️ Train images      : {len(train_imgs)}")
print(f"🏷️ Train labels      : {len(train_labels)}")
print(f"🖼️ Validation images : {len(val_imgs)}")
print(f"🏷️ Validation labels : {len(val_labels)}")
print(f"🖼️ Test images       : {len(test_imgs)}")
print(f"🏷️ Test labels       : {len(test_labels)}")
print(f"📄 YAML              : {yaml_path}")
print(f"🏷️ Classes           : {len(final_names)}")
print("=" * 60)

print("\n⚠️ Note : 'Crosswalk' n'existe pas dans Open Images V7.")
print("Tu dois l’ajouter depuis Roboflow si tu veux cette classe.")