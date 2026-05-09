"""
Trouve le meilleur seuil pour chaque classe
Exécutez: python find_best_threshold.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

import random
from PIL import Image

from captcha_engine import load_random_images, load_smart_distractor
from config import MODEL_MAP

# Forcer le chargement des modèles
from captcha_engine import ModelCache
cache = ModelCache()

print("=" * 70)
print("RECHERCHE DU MEILLEUR SEUIL PAR CLASSE")
print("=" * 70)

# Classes à tester
classes_a_tester = ["car", "bus", "truck", "bicycle", "stop_sign", "traffic_light", "motorcycle", "fire_hydrant"]

# Pour stocker les meilleurs seuils
meilleurs_seuils = {}

for target_class in classes_a_tester:
    print(f"\n{'='*50}")
    print(f"🔍 Recherche pour: {target_class}")
    print(f"{'='*50}")
    
    # Vérifier si le modèle existe
    try:
        model = cache.get(target_class)
    except Exception as e:
        print(f"  ❌ Modèle non disponible: {e}")
        continue
    
    # Tester avec plusieurs combinaisons aléatoires
    seuils_a_tester = [0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.88, 0.9, 0.92, 0.95]
    results_par_seuil = {s: {"success": 0, "total": 0} for s in seuils_a_tester}
    
    # Faire plusieurs tests pour chaque classe
    n_tests = 10  # 10 challenges différents
    
    for test_num in range(n_tests):
        try:
            # Créer un challenge
            n_positive = 4
            positives = load_random_images(target_class, n_positive, size=None)
            distractors = [load_smart_distractor(target_class) for _ in range(9 - n_positive)]
            cells = positives + distractors
            random.shuffle(cells)
            
            correct_indices = [i for i, item in enumerate(cells) if item["source_class"] == target_class]
            
            # Tester chaque seuil
            for seuil in seuils_a_tester:
                scores = []
                for i, item in enumerate(cells):
                    img = item["pil"]
                    results = model.predict(img, conf=seuil, imgsz=640)
                    
                    best_score = 0.0
                    if results.boxes and len(results.boxes) > 0:
                        best_score = float(max(results.boxes.conf))
                    scores.append((i, best_score))
                
                scores.sort(key=lambda x: -x[1])
                selected = [i for i, score in scores if score >= seuil]
                
                success = set(selected) == set(correct_indices)
                results_par_seuil[seuil]["total"] += 1
                if success:
                    results_par_seuil[seuil]["success"] += 1
                    
        except Exception as e:
            print(f"  ⚠️ Erreur lors du test {test_num}: {e}")
            continue
    
    # Afficher les résultats
    print(f"\n  📊 Résultats sur {n_tests} tests:")
    print(f"  {'Seuil':<10} {'Succès':<10} {'Taux':<10}")
    print(f"  {'-'*30}")
    
    meilleur_taux = 0
    meilleur_seuil = 0.8
    
    for seuil in seuils_a_tester:
        stats = results_par_seuil[seuil]
        if stats["total"] > 0:
            taux = stats["success"] / stats["total"] * 100
            barre = "█" * int(taux / 10) + "░" * (10 - int(taux / 10))
            print(f"  {seuil:<10} {stats['success']}/{stats['total']:<7} {taux:5.1f}% {barre}")
            
            if taux > meilleur_taux:
                meilleur_taux = taux
                meilleur_seuil = seuil
        else:
            print(f"  {seuil:<10} 0/0{' '*7} 0.0% {'░'*10}")
    
    meilleurs_seuils[target_class] = meilleur_seuil
    print(f"\n  🏆 MEILLEUR SEUIL pour {target_class}: {meilleur_seuil} (taux de succès: {meilleur_taux:.1f}%)")

# Afficher le résumé final
print("\n" + "=" * 70)
print("RÉSUMÉ FINAL - SEUILS RECOMMANDÉS")
print("=" * 70)
print("\nCopiez ceci dans votre fichier config.py:\n")
print("CLASS_THRESHOLDS = {")
for class_name, seuil in meilleurs_seuils.items():
    # Ajuster légèrement pour être plus strict
    seuil_recommande = min(seuil + 0.02, 0.95)
    print(f'    "{class_name}": {seuil_recommande},')
print("}")
print("\n" + "=" * 70)
