"""
Debug spécifique pour le modèle YOLO
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

import numpy as np
import onnxruntime as ort
from PIL import Image

# Charger directement le modèle ONNX pour debug
model_path = Path("models/yolo26/motorcycle.onnx")

print(f"🔍 Debug du modèle: {model_path}")
print(f"   Existe: {model_path.exists()}")

if model_path.exists():
    # Charger le modèle
    session = ort.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
    
    print(f"\n📥 Entrées du modèle:")
    for inp in session.get_inputs():
        print(f"   - {inp.name}: shape={inp.shape}, type={inp.type}")
    
    print(f"\n📤 Sorties du modèle:")
    for out in session.get_outputs():
        print(f"   - {out.name}: shape={out.shape}, type={out.type}")
    
    # Trouver une image de test
    img_path = Path("dataset/motorcycle/images")
    if img_path.exists():
        images = list(img_path.glob("*.jpg")) + list(img_path.glob("*.png"))
        if images:
            print(f"\n📸 Test avec l'image: {images[0].name}")
            
            # Prétraiter l'image
            img = Image.open(images[0]).convert("RGB")
            img_resized = img.resize((640, 640))
            img_array = np.array(img_resized).astype(np.float32) / 255.0
            img_array = img_array.transpose(2, 0, 1)
            img_array = np.expand_dims(img_array, axis=0)
            
            print(f"   Shape de l'entrée: {img_array.shape}")
            
            # Inférence
            input_name = session.get_inputs()[0].name
            outputs = session.run(None, {input_name: img_array})
            
            print(f"\n📊 Sorties brutes:")
            for i, out in enumerate(outputs):
                print(f"   Sortie {i}: shape={out.shape}")
                print(f"      Min: {out.min():.6f}, Max: {out.max():.6f}")
                print(f"      Moyenne: {out.mean():.6f}")
                
                # Analyser la forme
                if len(out.shape) == 3:
                    if out.shape[2] == 6:
                        print(f"      ✅ Format détection [batch, 300, 6]")
                        detections = out[0]
                        valid_dets = [d for d in detections if d[4] > 0.5]
                        print(f"      Détections avec conf > 0.5: {len(valid_dets)}")
                        if valid_dets:
                            for d in valid_dets[:5]:
                                print(f"        - conf={d[4]:.4f}, class={int(d[5])}")
        else:
            print(f"\n❌ Aucune image trouvée dans {img_path}")
    else:
        print(f"\n❌ Dossier introuvable: {img_path}")