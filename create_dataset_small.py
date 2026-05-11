import os
import random
import shutil
from pathlib import Path


SOURCE_DATASET = Path("dataset")
OUTPUT_DATASET = Path("dataset_small")

CLASSES = [
    "car",
    "bus",
    "truck",
    "bicycle",
    "motorcycle",
    "traffic light",
    "stop sign",
    "fire hydrant",
]

POSITIVE_IMAGES_PER_CLASS = 80
NEGATIVE_IMAGES_PER_OTHER_CLASS = 10

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def list_images(folder: Path):
    if not folder.exists():
        return []

    return [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


def clean_output():
    if OUTPUT_DATASET.exists():
        shutil.rmtree(OUTPUT_DATASET)

    OUTPUT_DATASET.mkdir(parents=True, exist_ok=True)


def copy_images(images, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)

    for img_path in images:
        target_path = destination / img_path.name

        # éviter écrasement si deux images ont le même nom
        if target_path.exists():
            target_path = destination / f"{img_path.stem}_{random.randint(1000,9999)}{img_path.suffix}"

        shutil.copy2(img_path, target_path)


def main():
    random.seed(42)

    clean_output()

    for class_name in CLASSES:
        print("\n" + "=" * 60)
        print(f"Création dataset_small pour : {class_name}")
        print("=" * 60)

        class_output = OUTPUT_DATASET / class_name

        # ==========================
        # POSITIVES
        # ==========================
        positive_source = SOURCE_DATASET / class_name / "images"
        positive_images = list_images(positive_source)

        random.shuffle(positive_images)
        selected_positive = positive_images[:POSITIVE_IMAGES_PER_CLASS]

        positive_dest = class_output / "positive"
        copy_images(selected_positive, positive_dest)

        print(f"✅ Positives copiées : {len(selected_positive)}")

        # ==========================
        # NEGATIVES
        # ==========================
        negative_dest = class_output / "negative"

        total_negatives = 0

        for other_class in CLASSES:
            if other_class == class_name:
                continue

            other_source = SOURCE_DATASET / other_class / "images"
            other_images = list_images(other_source)

            random.shuffle(other_images)
            selected_negative = other_images[:NEGATIVE_IMAGES_PER_OTHER_CLASS]

            # On met le nom de la classe négative dans le nom du fichier
            renamed_temp = []

            for img_path in selected_negative:
                new_name = f"{other_class.replace(' ', '_')}_{img_path.name}"
                temp_path = negative_dest / new_name
                negative_dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(img_path, temp_path)
                total_negatives += 1

        print(f"✅ Négatives copiées : {total_negatives}")

    print("\n" + "=" * 60)
    print("✅ dataset_small créé avec succès")
    print("=" * 60)
    print(f"Dossier créé : {OUTPUT_DATASET.resolve()}")


if __name__ == "__main__":
    main()