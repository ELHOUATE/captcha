"""
Debug pour voir exactement ce que les modèles détectent
Exécutez: python debug_detections.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

import base64
import random
from io import BytesIO
from PIL import Image

from captcha_engine import CaptchaEngine, load_random_images, load_smart_distractor
from config import MODEL_MAP

print("=" * 70)
print("DEBUG DÉTECTIONS DES MODÈLES")
print("=" * 70)

# Liste des classes à tester
classes_a_tester = ["car", "bus", "truck", "bicycle", "stop_sign", "traffic_light", "motorcycle", "fire_hydrant"]

engine = CaptchaEngine()

for target_class in classes_a_tester:
    print(f"\n{'='*50}")
    print(f"🎯 CLASSE TESTÉE: {target_class}")
    print(f"{'='*50}")
    
    # Vérifier si la classe a des images
    try:
        model = engine.models.get(target_class)
    except Exception as e:
        print(f"  ❌ Impossible de charger le modèle: {e}")
        continue
    
    # Créer un challenge manuel pour cette classe
    try:
        n_positive = 4
        positives = load_random_images(target_class, n_positive, size=None)
        distractors = [load_smart_distractor(target_class) for _ in range(9 - n_positive)]
        cells = positives + distractors
        random.shuffle(cells)
    except Exception as e:
        print(f"  ❌ Impossible de charger les images: {e}")
        continue
    
    print(f"\n  📊 Analyse des 9 images:")
    print(f"  {'Index':<6} {'True Class':<18} {'Score':<8} {'Détections'}")
    print(f"  {'-'*50}")
    
    seuil = 0.5  # Seuil bas pour voir toutes les détections
    
    for i, item in enumerate(cells):
        img = item["pil"]
        true_class = item["source_class"]
        is_positive = (true_class == target_class)
        
        results = model.predict(img, conf=seuil, imgsz=640)
        
        best_score = 0.0
        detections_info = ""
        
        if results.boxes and len(results.boxes) > 0:
            best_score = float(max(results.boxes.conf))
            # Afficher les classes détectées
            classes_detectees = []
            for box in results.boxes._boxes[:3]:
                cls_id = box.get('cls', 0)
                conf = box.get('conf', 0)
                # Trouver le nom de la classe
                class_name = "unknown"
                for name, cfg in MODEL_MAP.items():
                    if cfg.get('class_id') == cls_id:
                        class_name = name
                        break
                classes_detectees.append(f"{class_name}({conf:.2f})")
            detections_info = ", ".join(classes_detectees)
        
        marker = "✅" if is_positive else "❌"
        score_str = f"{best_score:.4f}" if best_score > 0 else "aucun"
        print(f"  {marker} {i:<5} {true_class:<18} {score_str:<8} {detections_info}")
    
    print(f"\n  💡 Résumé pour {target_class}:")
    
    # Tester avec différents seuils pour trouver le meilleur
    for seuil_test in [0.3, 0.5, 0.7, 0.8, 0.85, 0.9, 0.95]:
        scores = []
        for i, item in enumerate(cells):
            img = item["pil"]
            results = model.predict(img, conf=seuil_test, imgsz=640)
            best_score = 0.0
            if results.boxes and len(results.boxes) > 0:
                best_score = float(max(results.boxes.conf))
            scores.append((i, best_score, item["source_class"] == target_class))
        
        scores.sort(key=lambda x: -x[1])
        selected = [s[0] for s in scores[:4]]
        correct = [i for i, item in enumerate(cells) if item["source_class"] == target_class]
        
        success = set(selected) == set(correct)
        if success:
            print(f"     ✅ Seuil {seuil_test}: CORRECT - selected={selected}")
        else:
            print(f"     ❌ Seuil {seuil_test}: FAIL - selected={selected} | correct={correct}")

print("\n" + "=" * 70)
print("FIN DU DEBUG")
print("=" * 70)