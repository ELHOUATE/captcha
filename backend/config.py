from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

IMAGE_DIR = PROJECT_DIR / "dataset"
CONF_THRESHOLD = 0.25
SESSION_TTL_SECONDS = 300

MODEL_MAP = {
    "car": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "car.pt",
        "label_fr": "voitures",
    },
    "bus": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "bus.pt",
        "label_fr": "bus",
    },
    "truck": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "truck.pt",
        "label_fr": "camions",
    },
    "bicycle": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "bicycle.pt",
        "label_fr": "vélos",
    },
    "stop_sign": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "stop_sign.pt",
        "label_fr": "panneaux stop",
    },
    "traffic_light": {
        "arch": "rtdetr",
        "path": PROJECT_DIR / "models" / "rtdetr" / "traffic_light.pt",
        "label_fr": "feux de circulation",
    },
    "motorcycle": {
        "arch": "yolo",
        "path": PROJECT_DIR / "models" / "yolo26" / "motorcycle.pt",
        "label_fr": "motos",
    },
    "fire_hydrant": {
        "arch": "yolo",
        "path": PROJECT_DIR / "models" / "yolo26" / "fire_hydrant.pt",
        "label_fr": "bouches d’incendie",
    },
}