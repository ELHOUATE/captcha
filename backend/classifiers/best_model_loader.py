"""
Chargeur de modèles - version corrigée
Usage prévu : CAPTCHA propriétaire / environnement de test contrôlé.
"""

import os
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO, RTDETR


class BestClassifierLoader:
    CLASS_ALIASES: Dict[str, List[str]] = {
        "car": ["car", "cars", "voiture", "voitures", "auto"],
        "bus": ["bus", "buses", "autobus"],
        "truck": ["truck", "trucks", "camion", "camions"],
        "bicycle": ["bicycle", "bicycles", "bike", "bikes", "vélo", "vélos", "velo", "velos"],
        "motorcycle": ["motorcycle", "motorcycles", "moto", "motos", "motorbike"],
        "boat": ["boat", "boats", "bateau", "bateaux"],
        "train": ["train", "trains"],
        "traffic_light": ["traffic light", "traffic lights", "feu", "feux", "feu rouge"],
        "stop_sign": ["stop sign", "stop signs", "panneau stop", "stop"],
        "fire_hydrant": ["fire hydrant", "fire hydrants", "hydrant", "borne incendie"],
        "person": ["person", "people", "personne", "personnes"],
        "crosswalk": [
            "crosswalk", "crosswalks",
            "passage piéton", "passages piétons",
            "zebra crossing", "pedestrian crossing",
            "clous"
        ],
    }

    COCO_NAMES: Dict[str, str] = {
        "car": "car",
        "bus": "bus",
        "truck": "truck",
        "bicycle": "bicycle",
        "motorcycle": "motorcycle",
        "boat": "boat",
        "train": "train",
        "traffic_light": "traffic light",
        "stop_sign": "stop sign",
        "fire_hydrant": "fire hydrant",
        "person": "person",
    }

    def __init__(self, models_dir: str = "models/", debug: bool = True):
        self.debug = debug
        self.models_dir = models_dir
        self.custom_models: Dict[str, object] = {}
        self.fallback_model = None
        self._coco_id_cache: Dict[str, int] = {}

        self.model_configs = {
            "car": {"type": "rtdetr", "subdir": "rtdetr", "file": "car.pt"},
            "bus": {"type": "rtdetr", "subdir": "rtdetr", "file": "bus.pt"},
            "truck": {"type": "rtdetr", "subdir": "rtdetr", "file": "truck.pt"},
            "bicycle": {"type": "rtdetr", "subdir": "rtdetr", "file": "bicycle.pt"},
            "stop_sign": {"type": "rtdetr", "subdir": "rtdetr", "file": "stop_sign.pt"},
            "traffic_light": {"type": "rtdetr", "subdir": "rtdetr", "file": "traffic_light.pt"},
            "motorcycle": {"type": "yolo", "subdir": "yolo26", "file": "motorcycle.pt"},
            "fire_hydrant": {"type": "yolo", "subdir": "yolo26", "file": "fire_hydrant.pt"},
        }

        self._load_models()

    def _log(self, msg: str):
        if self.debug:
            print(msg)

    @staticmethod
    def _normalize(text: str) -> str:
        text = str(text).lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = text.replace("_", " ").replace("-", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def normalize_class_name(self, raw_text: str) -> Optional[str]:
        normalized = self._normalize(raw_text)
        for internal, aliases in self.CLASS_ALIASES.items():
            for alias in aliases:
                if self._normalize(alias) in normalized:
                    return internal
        return None

    def _load_models(self):
        self._log("🔄 Chargement des modèles personnalisés...")

        for class_name, config in self.model_configs.items():
            path = os.path.join(self.models_dir, config["subdir"], config["file"])

            if not os.path.exists(path):
                self.custom_models[class_name] = None
                self._log(f"   ⚠️ Modèle absent pour {class_name}: {path}")
                continue

            try:
                if config["type"] == "rtdetr":
                    model = RTDETR(path)
                else:
                    model = YOLO(path)

                model.verbose = False
                self.custom_models[class_name] = model
                names = getattr(model, "names", {})
                self._log(f"   ✅ {class_name} chargé | classes: {names}")

            except Exception as e:
                self.custom_models[class_name] = None
                self._log(f"   ❌ Erreur {class_name}: {e}")

        self._log("🔄 Chargement fallback YOLO COCO...")
        try:
            self.fallback_model = YOLO("yolov8x.pt")
            self.fallback_model.verbose = False
            self._log("   ✅ Fallback chargé (yolov8x.pt)")

            for idx, name in self.fallback_model.names.items():
                self._coco_id_cache[self._normalize(name)] = int(idx)

        except Exception as e:
            self._log(f"   ⚠️ Erreur fallback: {e}")
            self.fallback_model = None

    def list_available_classes(self) -> List[str]:
        available = [c for c, m in self.custom_models.items() if m is not None]
        if self.fallback_model is not None:
            available += [c for c in self.COCO_NAMES.keys() if c not in available]
        return sorted(set(available))

    def has_model(self, class_name: str) -> bool:
        internal = self.normalize_class_name(class_name) or class_name
        return self.custom_models.get(internal) is not None or self._get_coco_id(internal) is not None

    def _get_coco_id(self, internal: str) -> Optional[int]:
        if not self.fallback_model:
            return None

        coco_name = self.COCO_NAMES.get(internal)
        if not coco_name:
            return None

        return self._coco_id_cache.get(self._normalize(coco_name))

    def _pil_to_cv(self, img: Image.Image) -> np.ndarray:
        return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)

    def _resize_with_padding(self, img: np.ndarray, target_size: int = 640) -> np.ndarray:
        h, w = img.shape[:2]
        scale = target_size / max(h, w)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        resized = cv2.resize(img, (new_w, new_h))
        padded = np.ones((target_size, target_size, 3), dtype=np.uint8) * 114

        y_offset = (target_size - new_h) // 2
        x_offset = (target_size - new_w) // 2
        padded[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
        return padded

    def _model_class_matches_target(self, model, cls_id: int, target_internal: str) -> bool:
        names = getattr(model, "names", {}) or {}

        if len(names) <= 1:
            return True

        detected_name = names.get(int(cls_id), "")
        detected_norm = self._normalize(detected_name)
        aliases = self.CLASS_ALIASES.get(target_internal, [target_internal])

        return any(self._normalize(alias) == detected_norm for alias in aliases)

    def _extract_best_custom_detection(self, result, model, target_internal: str) -> Tuple[bool, float]:
        if result.boxes is None or len(result.boxes) == 0:
            return False, 0.0

        cls_ids = result.boxes.cls.cpu().numpy() if result.boxes.cls is not None else np.zeros(len(result.boxes))
        confs = result.boxes.conf.cpu().numpy() if result.boxes.conf is not None else []

        best_conf = 0.0
        found = False
        for cls_id, conf in zip(cls_ids, confs):
            if self._model_class_matches_target(model, int(cls_id), target_internal):
                found = True
                best_conf = max(best_conf, float(conf))

        return found, best_conf

    def predict_batch(
        self,
        images: List[Image.Image],
        target: str,
        confidence_threshold: float = 0.55,
    ) -> List[Tuple[bool, float]]:
        if not images:
            return []

        internal = self.normalize_class_name(target) or target
        images_cv = [self._pil_to_cv(img) for img in images]

        custom = self.custom_models.get(internal)
        if custom is not None:
            resized_images = [self._resize_with_padding(img, target_size=640) for img in images_cv]
            results = custom(resized_images, conf=confidence_threshold, verbose=False, imgsz=640)

            out = []
            for r in results:
                found, conf = self._extract_best_custom_detection(r, custom, internal)
                out.append((found and conf >= confidence_threshold, conf))
            return out

        target_id = self._get_coco_id(internal)
        if target_id is not None and self.fallback_model is not None:
            results = self.fallback_model(images_cv, conf=confidence_threshold, verbose=False, imgsz=640)
            out = []
            for r in results:
                found = False
                max_conf = 0.0
                if r.boxes is not None and len(r.boxes) > 0:
                    cls_ids = r.boxes.cls.cpu().numpy()
                    confs = r.boxes.conf.cpu().numpy()
                    for cls_id, conf in zip(cls_ids, confs):
                        if int(cls_id) == target_id:
                            found = True
                            max_conf = max(max_conf, float(conf))
                out.append((found and max_conf >= confidence_threshold, max_conf))
            return out

        return [(False, 0.0)] * len(images)

    def predict_single(
        self,
        image: Image.Image,
        target: str,
        confidence_threshold: float = 0.55,
    ) -> Tuple[bool, float]:
        return self.predict_batch([image], target, confidence_threshold)[0]