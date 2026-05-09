"""
Client qui demande à l'API d'ouvrir la page demo Google
"""

import requests
import time

API_URL = "http://localhost:5000/solve"

# ⭐ L'URL que l'API doit ouvrir
URL_A_OUVRIR = "https://www.google.com/recaptcha/api2/demo"

print("="*60)
print("🌐 APPEL DE L'API POUR OUVRIR GOOGLE DEMO")
print("="*60)
print(f"📍 API: {API_URL}")
print(f"📂 URL à ouvrir: {URL_A_OUVRIR}")
print("="*60)

# Appel à l'API
print("\n📡 Envoi de la requête...")
response = requests.post(API_URL, json={
    'url': URL_A_OUVRIR,
    'confidence_threshold': 0.65,
    'debug': True  # Affiche les logs dans l'API
})

print("\n📊 RÉSULTAT DE L'API:")
print("-" * 40)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Succès: {result.get('success')}")
    print(f"📝 Message: {result.get('message')}")
    if result.get('token'):
        print(f"🔑 Token: {result['token'][:50]}...")
else:
    print(f"❌ Erreur: {response.status_code}")
    print(response.text)

print("-" * 40)