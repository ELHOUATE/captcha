"""
Test spécifique pour RT-DETR
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

import base64
import random
from io import BytesIO
from PIL import Image

from captcha_engine import load_random_images, load_smart_distractor, ModelCache
from config import CONF_THRESHOLD, MODEL_MAP

print("=" * 70)
print("TEST SPÉCIFIQUE RT-DETR")
print("=" * 70)

# Choisir une classe RT-DETR à tester
target = "car"  # changer ici pour tester d'autres classes: "bus", "truck", etc.

print(f"\n🎯 Test avec la classe: {target}")

# Générer un challenge manuellement
n_positive = 4
positives = load_random_images(target, n_positive)
distractors = [load_smart_distractor(target) for _ in range(9 - n_positive)]
cells = positives + distractors
random.shuffle(cells)

images = []
correct_indices = []
debug_classes = []

for i, item in enumerate(cells):
    images.append(item["b64"])
    debug_classes.append(item.get("source_class"))
    if item.get("source_class") == target:
        correct_indices.append(i)

# Charger le modèle
cache = ModelCache()
model = cache.get(target)

print(f"\n🤖 Analyse des 9 images:")
print("-" * 50)

scored_images = []

for i, b64_img in enumerate(images):
    img_bytes = base64.b64decode(b64_img)
    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    
    results = model.predict(img, conf=CONF_THRESHOLD, imgsz=640)
    
    best_score = 0.0
    if results.boxes and len(results.boxes) > 0:
        best_score = float(max(results.boxes.conf))
    
    scored_images.append({"index": i, "score": best_score})
    
    is_correct = i in correct_indices
    marker = "✅" if is_correct else "❌"
    print(f"   {marker} Image {i}: score={best_score:.4f} | true_class={debug_classes[i]}")

print("-" * 50)

# Sélection
scored_images.sort(key=lambda x: -x["score"])
selected = [item["index"] for item in scored_images[:4]]
selected.sort()

print(f"\n📊 RÉSULTATS:")
print(f"   Indices sélectionnés: {selected}")
print(f"   Indices corrects: {correct_indices}")
print(f"   Succès: {set(selected) == set(correct_indices)}")
print(f"   Score: {len(set(selected) & set(correct_indices))}/{len(correct_indices)}")

print(f"\n📈 Scores détaillés (top 4):")
for item in sorted(scored_images, key=lambda x: -x["score"])[:4]:
    is_correct = "✅" if item["index"] in correct_indices else "❌"
    print(f"   {is_correct} Image {item['index']}: {item['score']:.4f}")