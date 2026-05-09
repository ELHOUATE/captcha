"""
Test sur le vrai CAPTCHA (via l'API)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

import requests
import time

API_URL = "http://localhost:8000"

print("=" * 70)
print("TEST SUR LE VRAI CAPTCHA")
print("=" * 70)

# 1. Obtenir un challenge
print("\n1. Récupération d'un challenge...")
response = requests.get(f"{API_URL}/api/captcha/challenge")
challenge = response.json()

print(f"   ID: {challenge['id']}")
print(f"   Classe cible: {challenge['target_class']} ({challenge['label_fr']})")
print(f"   Images: {len(challenge['images'])}")

# 2. Résoudre avec le solveur
print("\n2. Résolution automatique...")
solve_data = {
    "images": challenge['images'],
    "target_class": challenge['target_class']
}

response = requests.post(f"{API_URL}/api/captcha/solve", json=solve_data)
solution = response.json()

selected_indices = solution['correct_indices']
print(f"   Indices sélectionnés: {selected_indices}")

# 3. Vérifier la réponse
print("\n3. Vérification...")
verify_data = {
    "captcha_id": challenge['id'],
    "selected_indices": selected_indices
}

response = requests.post(f"{API_URL}/api/captcha/verify", json=verify_data)
result = response.json()

print(f"   Succès: {result['success']}")
print(f"   Score: {result['score']}")
print(f"   Message: {result.get('error', 'OK')}")

print("\n" + "=" * 70)
if result['success']:
    print("🎉 CAPTCHA RÉSOLU AVEC SUCCÈS !")
else:
    print("❌ ÉCHEC - Besoin d'ajuster")
print("=" * 70)

# 4. Afficher les scores détaillés
if 'scores' in solution:
    print("\n📈 Scores des images (top 9):")
    for item in solution['scores'][:9]:
        is_correct = False
        if 'debug_classes' in challenge and item['index'] < len(challenge['debug_classes']):
            is_correct = challenge['debug_classes'][item['index']] == challenge['target_class']
        marker = "✅" if is_correct else "❌"
        print(f"   {marker} Image {item['index']}: {item['score']:.4f}")