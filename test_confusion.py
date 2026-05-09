"""
Test spécifique pour les confusions car/bus/truck
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from captcha_engine import CaptchaEngine
import base64
from io import BytesIO
from PIL import Image

engine = CaptchaEngine()
classes = ["car", "bus", "truck"]

for target in classes:
    print(f"\n{'='*50}")
    print(f"Test pour: {target}")
    print(f"{'='*50}")
    
    challenge = engine.build_challenge()
    
    # Forcer un challenge avec cette classe
    while challenge['target_class'] != target:
        challenge = engine.build_challenge()
    
    model = engine.models.get(target)
    threshold = 0.90  # Seuil de test
    
    for i, b64_img in enumerate(challenge['images']):
        img_bytes = base64.b64decode(b64_img)
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        
        results = model.predict(img, conf=threshold, imgsz=640)
        
        true_class = challenge['debug_classes'][i]
        is_correct = i in challenge['correct_indices']
        
        best_score = 0.0
        if results.boxes and len(results.boxes) > 0:
            best_score = float(max(results.boxes.conf))
        
        marker = "✅" if is_correct else "❌"
        if is_correct and best_score >= threshold:
            print(f"  {marker} Image {i}: {true_class} -> score={best_score:.4f} OK")
        elif is_correct and best_score < threshold:
            print(f"  ⚠️ Image {i}: {true_class} -> score={best_score:.4f} TROP BAS")
        elif not is_correct and best_score >= threshold:
            print(f"  ❌ Image {i}: {true_class} -> score={best_score:.4f} FAUX POSITIF")
        else:
            print(f"  ✅ Image {i}: {true_class} -> score={best_score:.4f} OK")