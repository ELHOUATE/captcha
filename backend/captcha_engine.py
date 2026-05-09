import base64
import math
import random
import uuid
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
import onnxruntime as ort

from config import IMAGE_DIR, MODEL_MAP, CONF_THRESHOLD, get_threshold


# Taille pour l'affichage dans le frontend
DISPLAY_SIZE = 640
# Taille pour le modèle (ne pas changer, les modèles sont entraînés sur 640)
MODEL_SIZE = 640

MAX_GENERATION_ATTEMPTS = 5

CLASSES = list(MODEL_MAP.keys())


class BoxesWrapper:
    """Wrapper pour les boîtes de détection compatibles avec l'interface YOLO"""
    
    def __init__(self, boxes_data):
        self._boxes = boxes_data
        self.conf = np.array([b['conf'] for b in boxes_data]) if boxes_data else np.array([])
        self.cls = np.array([b['cls'] for b in boxes_data]) if boxes_data else np.array([])
        self.xyxy = np.array([b['xyxy'] for b in boxes_data]) if boxes_data else np.array([])
    
    def __len__(self):
        return len(self._boxes)
    
    def __iter__(self):
        return iter(self._boxes)


class ONNXRuntimeResults:
    """Wrapper pour les résultats ONNX compatibles avec l'interface YOLO"""
    
    def __init__(self, outputs, arch: str, class_id: int, conf_threshold: float):
        self.outputs = outputs
        self.arch = arch
        self.class_id = class_id
        self.conf_threshold = conf_threshold
        self.boxes = self._parse_outputs()
    
    def _parse_outputs(self):
        """Parse les sorties ONNX selon l'architecture"""
        if self.arch == "yolo":
            return self._parse_yolo_output()
        else:  # rtdetr
            return self._parse_rtdetr_output()
    
    def _parse_yolo_output(self):
        """Parse la sortie YOLO standard [1, 300, 6] avec sigmoïde"""
        output = self.outputs[0]
        
        boxes_data = []
        
        # Format YOLO: [1, 300, 6] = [x1, y1, x2, y2, raw_conf, class_id]
        if len(output.shape) == 3 and output.shape[2] == 6:
            detections = output[0]
            
            for det in detections:
                # Appliquer la sigmoïde pour transformer en probabilité (0-1)
                raw_conf = float(det[4])
                conf = 1.0 / (1.0 + np.exp(-raw_conf))
                
                if conf < self.conf_threshold:
                    continue
                
                class_id = int(det[5])
                
                if self.class_id is not None and class_id != self.class_id:
                    continue
                
                x1, y1, x2, y2 = det[0:4]
                
                boxes_data.append({
                    'xyxy': [float(x1), float(y1), float(x2), float(y2)],
                    'conf': conf,
                    'cls': class_id
                })
        
        return BoxesWrapper(boxes_data) if boxes_data else None
    
    def _parse_rtdetr_output(self):
        """Parse la sortie RT-DETR (format [1, 300, 5])"""
        output = self.outputs[0]
    
        boxes_data = []
    
        if len(output.shape) == 3 and output.shape[2] == 5:
            detections = output[0]
        
            for det in detections:
                conf = float(det[4])
            
                # Appliquer un seuil plus strict selon la classe
                if self.class_id == 2:  # car
                    # Les car ont souvent des faux positifs sur bus/truck
                    final_threshold = max(self.conf_threshold, 0.90)
                elif self.class_id == 7:  # truck
                    # Les truck se font confondre avec bus
                    final_threshold = max(self.conf_threshold, 0.92)
                elif self.class_id == 5:  # bus
                    final_threshold = max(self.conf_threshold, 0.88)
                else:
                    final_threshold = self.conf_threshold
            
                if conf > final_threshold:
                    boxes_data.append({
                        'xyxy': [float(det[0]), float(det[1]), float(det[2]), float(det[3])],
                        'conf': conf,
                        'cls': self.class_id if self.class_id is not None else 0
                    })
    
        return BoxesWrapper(boxes_data) if boxes_data else None


class ONNXModelWrapper:
    """Wrapper unifié pour les modèles ONNX (RT-DETR et YOLO)"""
    
    def __init__(self, model_path: str, arch: str, class_id: int = None):
        self.model_path = str(model_path)
        self.arch = arch
        self.class_id = class_id
        self.session = None
        self.input_name = None
        self.output_names = None
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle ONNX avec les bons providers"""
        providers = ['CPUExecutionProvider']
        try:
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [out.name for out in self.session.get_outputs()]
            print(f"[OK] Modèle ONNX chargé: {self.model_path}")
        except Exception as e:
            print(f"[ERREUR] Impossible de charger {self.model_path}: {e}")
            raise
    
    def predict(self, source, conf=CONF_THRESHOLD, imgsz=MODEL_SIZE, verbose=False):
        """
        Prédiction sur une image
        """
        from PIL import Image as PILImage
        
        if isinstance(source, PILImage.Image):
            img = source
        elif isinstance(source, str):
            img = PILImage.open(source)
        elif isinstance(source, np.ndarray):
            img = PILImage.fromarray(source)
        else:
            raise ValueError(f"Type de source non supporté: {type(source)}")
        
        # Redimensionner à la taille attendue par le modèle (640x640)
        img_resized = img.resize((imgsz, imgsz), PILImage.LANCZOS)
        img_array = np.array(img_resized).astype(np.float32) / 255.0
        img_array = img_array.transpose(2, 0, 1)
        img_array = np.expand_dims(img_array, axis=0)
        
        outputs = self.session.run(self.output_names, {self.input_name: img_array})
        
        return ONNXRuntimeResults(outputs, self.arch, self.class_id, conf)


class ModelCache:
    def __init__(self):
        self._cache = {}

    def get(self, class_name: str):
        if class_name not in MODEL_MAP:
            raise ValueError(f"Classe inconnue: {class_name}")

        if class_name not in self._cache:
            cfg = MODEL_MAP[class_name]
            model_path = cfg["path"]
            arch = cfg["arch"]
            class_id = cfg.get("class_id")

            if not model_path.exists():
                raise FileNotFoundError(f"Modèle introuvable: {model_path}")

            self._cache[class_name] = ONNXModelWrapper(model_path, arch, class_id)
            print(f"[OK] Modèle ONNX chargé: {class_name}")

        return self._cache[class_name]


def pil_to_b64(img: Image.Image) -> str:
    """Convertit une image PIL en base64"""
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def get_image_paths(class_name: str):
    """Récupère tous les chemins d'images pour une classe"""
    folder_name = MODEL_MAP[class_name].get("image_folder", class_name)
    folder = IMAGE_DIR / folder_name / "images"
    return (
        list(folder.glob("*.jpg")) +
        list(folder.glob("*.jpeg")) +
        list(folder.glob("*.png"))
    )


def class_has_images(class_name: str) -> bool:
    """Vérifie si une classe a des images disponibles"""
    return bool(get_image_paths(class_name))


def load_random_images(class_name: str, n: int, size=None):
    """
    Charge n images aléatoires d'une classe
    size: tuple (largeur, hauteur) ou None pour garder la taille originale
    """
    paths = get_image_paths(class_name)

    if not paths:
        folder_name = MODEL_MAP[class_name].get("image_folder", class_name)
        raise FileNotFoundError(
            f"Aucune image trouvée dans: {IMAGE_DIR / folder_name / 'images'}"
        )

    if len(paths) < n:
        paths = (paths * math.ceil(n / len(paths)))[:n]
        selected = paths
    else:
        selected = random.sample(paths, n)

    items = []

    for p in selected:
        img = Image.open(p).convert("RGB")
        if size is not None:
            img = img.resize(size, Image.LANCZOS)

        items.append({
            "path": str(p),
            "source_class": class_name,
            "pil": img,
            "b64": pil_to_b64(img),
        })

    return items


def load_distractor_image(exclude_class: str):
    """Charge une image distracteur d'une autre classe"""
    other_classes = [
        c for c in CLASSES
        if c != exclude_class and class_has_images(c)
    ]

    if not other_classes:
        raise RuntimeError(
            "Il faut ajouter des images dans au moins deux classes pour générer un CAPTCHA."
        )

    random_class = random.choice(other_classes)
    return load_random_images(random_class, 1, size=None)[0]


def load_smart_distractor(target_class: str):
    """Version simplifiée - retourne un distracteur aléatoire"""
    return load_distractor_image(target_class)


class CaptchaEngine:
    def __init__(self):
        self.models = ModelCache()

    def available_classes(self):
        """Retourne la liste des classes disponibles"""
        return [c for c in CLASSES if class_has_images(c)]

    def build_challenge(self):
        """Génère un nouveau challenge CAPTCHA"""
        return self.build_challenge_3x3()

    def build_challenge_3x3(self, attempt: int = 1):
        """Génère un CAPTCHA 3x3 (9 images)"""
        available = self.available_classes()

        if len(available) < 2:
            raise RuntimeError(
                "Ajoute des images dans au moins deux dossiers dataset/<classe>/images."
            )

        target_class = random.choice(available)
        label_fr = MODEL_MAP[target_class]["label_fr"]

        n_positive = 4

        # Charger les images originales (SANS redimensionnement pour le modèle)
        positives = load_random_images(target_class, n_positive, size=None)
        distractors = [
            load_smart_distractor(target_class)
            for _ in range(9 - n_positive)
        ]

        cells = positives + distractors
        random.shuffle(cells)

        images = []
        correct_indices = []
        debug_classes = []

        for i, item in enumerate(cells):
            # Redimensionner pour l'affichage en 640x640 (même taille que le modèle)
            img = item["pil"]
            img_display = img.resize((DISPLAY_SIZE, DISPLAY_SIZE), Image.LANCZOS)
            images.append(pil_to_b64(img_display))
            debug_classes.append(item.get("source_class"))

            if item.get("source_class") == target_class:
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
            "debug_classes": debug_classes,
        }


engine = CaptchaEngine()


def generate_challenge():
    return engine.build_challenge()