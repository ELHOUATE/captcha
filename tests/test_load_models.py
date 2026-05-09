"""
Test de chargement des modèles
À exécuter pour vérifier que tous les modèles sont trouvés
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.classifiers.best_model_loader import BestClassifierLoader

print("="*60)
print("🧪 TEST DE CHARGEMENT DES MODÈLES")
print("="*60)

# Charger les modèles
loader = BestClassifierLoader(models_dir="models/", debug=True)

print("\n" + "="*60)
print("📊 RÉSULTAT")
print("="*60)

available = loader.list_available_classes()
print(f"✅ Classes chargées ({len(available)}): {', '.join(available)}")

# Vérifier les classes attendues
expected = ['car', 'bus', 'truck', 'bicycle', 'stop_sign', 'traffic_light', 'motorcycle', 'fire_hydrant']
missing = [c for c in expected if c not in available]

if missing:
    print(f"⚠️ Classes manquantes: {missing}")
else:
    print("✅ Toutes les classes sont disponibles !")