from ultralytics import YOLO, RTDETR
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"

MODELS = {
    "car": ("rtdetr", MODELS_DIR / "rtdetr/car.pt"),
    "bus": ("rtdetr", MODELS_DIR / "rtdetr/bus.pt"),
    "truck": ("rtdetr", MODELS_DIR / "rtdetr/truck.pt"),
    "bicycle": ("rtdetr", MODELS_DIR / "rtdetr/bicycle.pt"),
    "stop_sign": ("rtdetr", MODELS_DIR / "rtdetr/stop_sign.pt"),
    "traffic_light": ("rtdetr", MODELS_DIR / "rtdetr/traffic_light.pt"),
    "motorcycle": ("yolo", MODELS_DIR / "yolo26/motorcycle.pt"),
    "fire_hydrant": ("yolo", MODELS_DIR / "yolo26/fire_hydrant.pt"),
}

for name, (model_type, path) in MODELS.items():
    print(f"📦 Export {name} ({model_type})...")

    if not path.exists():
        print(f"❌ Fichier .pt introuvable: {path}")
        continue

    if model_type == "rtdetr":
        model = RTDETR(str(path))
        
        # ⚠️ IMPORTANT : opset=16 pour RT-DETR
        model.export(
            format="onnx",
            imgsz=640,
            simplify=True,
            opset=16,  # 👈 Changement ici : 12 -> 16
            dynamic=False,
            half=False,
        )
    else:
        model = YOLO(str(path))
        
        # YOLO peut rester en opset=12
        model.export(
            format="onnx",
            imgsz=640,
            simplify=True,
            opset=12,  # YOLO fonctionne avec 12
            dynamic=False,
            half=False,
        )
    
    print(f"✅ {name} exporté avec succès vers ONNX\n")