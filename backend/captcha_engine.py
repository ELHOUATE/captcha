import base64
import math
import random
import uuid
from io import BytesIO
from pathlib import Path
from PIL import Image

from config import IMAGE_DIR, MODEL_MAP, CONF_THRESHOLD

IMG_SIZE = 150
TILE_SIZE = 120
GRID_COLS_4X4 = 4
GRID_ROWS_4X4 = 4

CLASSES = list(MODEL_MAP.keys())


class ModelCache:
    def __init__(self):
        self._cache = {}

    def get(self, class_name: str):
        if class_name not in MODEL_MAP:
            raise ValueError(f"Classe inconnue: {class_name}")

        if class_name not in self._cache:
            from ultralytics import YOLO, RTDETR

            cfg = MODEL_MAP[class_name]
            model_path = Path(cfg["path"])

            if not model_path.exists():
                raise FileNotFoundError(f"Modèle introuvable: {model_path}")

            if cfg["arch"] == "rtdetr":
                self._cache[class_name] = RTDETR(str(model_path))
            else:
                self._cache[class_name] = YOLO(str(model_path))

            print(f"[OK] Modèle chargé: {class_name} -> {model_path}")

        return self._cache[class_name]


def pil_to_b64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def get_image_paths(class_name: str):
    folder = IMAGE_DIR / class_name / "images"

    return (
        list(folder.glob("*.jpg")) +
        list(folder.glob("*.jpeg")) +
        list(folder.glob("*.png"))
    )


def class_has_images(class_name: str) -> bool:
    return bool(get_image_paths(class_name))


def load_random_images(class_name: str, n: int, size=(IMG_SIZE, IMG_SIZE)):
    paths = get_image_paths(class_name)

    if not paths:
        raise FileNotFoundError(
            f"Aucune image trouvée dans: {IMAGE_DIR / class_name / 'images'}"
        )

    if len(paths) < n:
        paths = (paths * math.ceil(n / len(paths)))[:n]
        selected = paths
    else:
        selected = random.sample(paths, n)

    items = []

    for p in selected:
        img = Image.open(p).convert("RGB").resize(size, Image.LANCZOS)

        items.append({
            "path": str(p),
            "pil": img,
            "b64": pil_to_b64(img),
        })

    return items


def load_distractor_image(exclude_class: str):
    other_classes = [
        c for c in CLASSES
        if c != exclude_class and class_has_images(c)
    ]

    if not other_classes:
        raise RuntimeError(
            "Il faut ajouter des images dans au moins deux classes pour générer un CAPTCHA."
        )

    return load_random_images(random.choice(other_classes), 1)[0]


def load_random_large_image(class_name: str):
    paths = get_image_paths(class_name)

    if not paths:
        raise FileNotFoundError(
            f"Aucune image trouvée dans: {IMAGE_DIR / class_name / 'images'}"
        )

    p = random.choice(paths)

    img = Image.open(p).convert("RGB").resize(
        (TILE_SIZE * GRID_COLS_4X4, TILE_SIZE * GRID_ROWS_4X4),
        Image.LANCZOS
    )

    return {
        "path": str(p),
        "pil": img,
    }


def normalize_name(name: str) -> str:
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def detect(model, img: Image.Image, target_class: str) -> bool:
    results = model.predict(source=img, conf=CONF_THRESHOLD, verbose=False)

    for r in results:
        for box in r.boxes:
            detected_name = normalize_name(r.names[int(box.cls)])

            if detected_name == target_class:
                return True

    return False


def detect_in_tiles(model, img: Image.Image, target_class: str):
    correct_indices = []

    width, height = img.size
    tile_w = width // GRID_COLS_4X4
    tile_h = height // GRID_ROWS_4X4

    for row in range(GRID_ROWS_4X4):
        for col in range(GRID_COLS_4X4):
            left = col * tile_w
            top = row * tile_h
            right = left + tile_w
            bottom = top + tile_h

            tile = img.crop((left, top, right, bottom))

            if detect(model, tile, target_class):
                index = row * GRID_COLS_4X4 + col
                correct_indices.append(index)

    return correct_indices


class CaptchaEngine:
    def __init__(self):
        self.models = ModelCache()

    def available_classes(self):
        return [c for c in CLASSES if class_has_images(c)]

    def build_challenge(self):
        challenge_type = random.choice(["3x3", "4x4"])

        if challenge_type == "3x3":
            return self.build_challenge_3x3()

        return self.build_challenge_4x4()

    def build_challenge_3x3(self):
        available = self.available_classes()

        if len(available) < 2:
            raise RuntimeError(
                "Ajoute des images dans au moins deux dossiers dataset/<classe>/images."
            )

        target_class = random.choice(available)
        model = self.models.get(target_class)
        label_fr = MODEL_MAP[target_class]["label_fr"]

        n_positive = random.randint(3, 5)

        positives = load_random_images(target_class, n_positive)

        distractors = [
            load_distractor_image(target_class)
            for _ in range(9 - n_positive)
        ]

        cells = positives + distractors
        random.shuffle(cells)

        correct_indices = []
        images = []

        for i, item in enumerate(cells):
            images.append(item["b64"])

            if detect(model, item["pil"], target_class):
                correct_indices.append(i)

        if not correct_indices:
            for i, item in enumerate(cells):
                image_parent_class = Path(item["path"]).parent.parent.name

                if image_parent_class == target_class:
                    correct_indices.append(i)

        return {
            "id": str(uuid.uuid4()),
            "type": 1,
            "target_class": target_class,
            "label_fr": label_fr,
            "instruction": f"Sélectionnez toutes les images avec des {label_fr}",
            "images": images,
            "grid_size": {"cols": 3, "rows": 3},
            "correct_indices": correct_indices,
        }

    def build_challenge_4x4(self):
        available = self.available_classes()

        if len(available) < 1:
            raise RuntimeError(
                "Ajoute des images dans au moins un dossier dataset/<classe>/images."
            )

        target_class = random.choice(available)
        model = self.models.get(target_class)
        label_fr = MODEL_MAP[target_class]["label_fr"]

        large = load_random_large_image(target_class)
        img = large["pil"]

        images = []

        tile_w = img.size[0] // GRID_COLS_4X4
        tile_h = img.size[1] // GRID_ROWS_4X4

        for row in range(GRID_ROWS_4X4):
            for col in range(GRID_COLS_4X4):
                left = col * tile_w
                top = row * tile_h
                right = left + tile_w
                bottom = top + tile_h

                tile = img.crop((left, top, right, bottom))
                images.append(pil_to_b64(tile))

        correct_indices = detect_in_tiles(model, img, target_class)

        if not correct_indices:
            correct_indices = [5, 6, 9, 10]

        return {
            "id": str(uuid.uuid4()),
            "type": 2,
            "target_class": target_class,
            "label_fr": label_fr,
            "instruction": f"Sélectionnez toutes les cases contenant des {label_fr}",
            "images": images,
            "grid_size": {"cols": 4, "rows": 4},
            "correct_indices": correct_indices,
        }