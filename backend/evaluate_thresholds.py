import os
import gc
from PIL import Image
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

from classifiers.best_model_loader import BestClassifierLoader


MODELS_DIR = "models/"
DATASET_DIR = "dataset"

# Diminuez à 8 ou 4 si votre PC est lent ou manque de RAM
BATCH_SIZE = 8

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

MODEL_CLASS_NAMES = {
    "traffic light": "traffic_light",
    "stop sign": "stop_sign",
    "fire hydrant": "fire_hydrant",
}

THRESHOLDS = [
    0.25, 0.30, 0.35, 0.40, 0.45,
    0.50, 0.55, 0.60, 0.65, 0.70,
    0.75, 0.80, 0.85,
]


def load_images(folder):
    images = []

    if not os.path.exists(folder):
        return images

    for filename in os.listdir(folder):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            path = os.path.join(folder, filename)
            try:
                img = Image.open(path).convert("RGB")
                images.append(img)
            except Exception as e:
                print(f"⚠️ Erreur image {path}: {e}")

    return images


def get_model_class_name(dataset_class_name):
    return MODEL_CLASS_NAMES.get(dataset_class_name, dataset_class_name)


def predict_in_batches(classifier, images, class_name, threshold, batch_size=BATCH_SIZE):
    all_predictions = []

    total = len(images)

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = images[start:end]

        preds = classifier.predict_batch(
            batch,
            class_name,
            confidence_threshold=threshold,
        )

        all_predictions.extend(preds)

        print(f"   batch {end}/{total} terminé", end="\r")

        del batch
        gc.collect()

    print()
    return all_predictions


def choose_best_threshold(results):
    """
    Priorité :
    1. precision >= 0.85 pour éviter les mauvais clics
    2. meilleur F1-score
    3. si aucun seuil n'a precision >= 0.85, prendre le meilleur F1-score global
    """

    candidates = [r for r in results if r["precision"] >= 0.85]

    if candidates:
        candidates.sort(key=lambda x: (x["f1"], x["precision"], x["recall"]), reverse=True)
        return candidates[0]

    results.sort(key=lambda x: (x["f1"], x["precision"], x["recall"]), reverse=True)
    return results[0]


def main():
    classifier = BestClassifierLoader(MODELS_DIR, debug=True)

    final_thresholds = {}

    for class_name in CLASSES:
        print("\n" + "=" * 70)
        print(f"TEST SEUILS POUR : {class_name}")
        print("=" * 70)

        model_class_name = get_model_class_name(class_name)

        positive_dir = os.path.join(DATASET_DIR, class_name, "images")
        positive_images = load_images(positive_dir)

        negative_images = []
        for other_class in CLASSES:
            if other_class == class_name:
                continue

            other_dir = os.path.join(DATASET_DIR, other_class, "images")
            negative_images.extend(load_images(other_dir))

        if not positive_images:
            print(f"⚠️ Aucune image positive trouvée : {positive_dir}")
            continue

        if not negative_images:
            print(f"⚠️ Aucune image négative trouvée pour {class_name}")
            continue

        images = positive_images + negative_images
        y_true = [1] * len(positive_images) + [0] * len(negative_images)

        print(f"Images positives : {len(positive_images)}")
        print(f"Images négatives : {len(negative_images)}")
        print(f"Total images : {len(images)}")
        print(f"Batch size : {BATCH_SIZE}")

        threshold_results = []

        for threshold in THRESHOLDS:
            print(f"\n--- Test seuil {threshold:.2f} ---")

            predictions = predict_in_batches(
                classifier,
                images,
                model_class_name,
                threshold,
                batch_size=BATCH_SIZE,
            )

            y_pred = [1 if contains else 0 for contains, conf in predictions]

            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            accuracy = accuracy_score(y_true, y_pred)

            threshold_results.append({
                "threshold": threshold,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "accuracy": accuracy,
            })

            print(
                f"seuil={threshold:.2f} | "
                f"precision={precision:.3f} | "
                f"recall={recall:.3f} | "
                f"f1={f1:.3f} | "
                f"accuracy={accuracy:.3f}"
            )

            del predictions
            del y_pred
            gc.collect()

        best = choose_best_threshold(threshold_results)
        final_thresholds[model_class_name] = best["threshold"]

        print(f"\n✅ Meilleur seuil conseillé pour {model_class_name}: {best['threshold']}")
        print(
            f"precision={best['precision']:.3f} | "
            f"recall={best['recall']:.3f} | "
            f"f1={best['f1']:.3f} | "
            f"accuracy={best['accuracy']:.3f}"
        )

        del images
        del positive_images
        del negative_images
        gc.collect()

    print("\n" + "=" * 70)
    print("SEUILS À METTRE DANS captcha_solver.py")
    print("=" * 70)

    print("CLASS_THRESHOLDS = {")
    for class_name, threshold in final_thresholds.items():
        print(f'    "{class_name}": {threshold},')
    print("}")


if __name__ == "__main__":
    main()