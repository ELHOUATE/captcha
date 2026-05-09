from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

IMAGE_DIR = PROJECT_DIR / "dataset"
SESSION_TTL_SECONDS = 300

# Seuils plus stricts pour éviter les confusions entre car/bus/truck
CLASS_THRESHOLDS = {
    "car": 0.92,
    "bus": 0.93,
    "truck": 0.90,
    "bicycle": 0.80,
    "stop_sign": 0.70,
    "traffic_light": 0.80,
}

def get_threshold(class_name: str) -> float:
    return CLASS_THRESHOLDS.get(class_name, 0.80)

CONF_THRESHOLD = 0.80

MODEL_MAP = {
    # "car": {
    #     "arch": "rtdetr",
    #     "path": PROJECT_DIR / "models" / "rtdetr" / "car.onnx",
    #     "image_folder": "car",
    #     "label_fr": "voitures",
    #     "class_id": 2,
    # },
    "bus": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "bus.onnx",
        "image_folder": "bus",
        "label_fr": "bus",
        "class_id": 5,
    },
    "truck": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "truck.onnx",
        "image_folder": "truck",
        "label_fr": "camions",
        "class_id": 7,
    },
    "bicycle": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "bicycle.onnx",
        "image_folder": "bicycle",
        "label_fr": "vélos",
        "class_id": 1,
    },
    "stop_sign": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "stop_sign.onnx",
        "image_folder": "stop sign",
        "label_fr": "panneaux stop",
        "class_id": 11,
    },
    "traffic_light": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "traffic_light.onnx",
        "image_folder": "traffic light",
        "label_fr": "feux de circulation",
        "class_id": 9,
    },
}