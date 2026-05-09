import requests
import time

API_URL = "http://localhost:5000"

print("="*50)
print("🧪 TEST DE L'API")
print("="*50)

# Test 1: Health
print("\n1. Test /health")
try:
    r = requests.get(f"{API_URL}/health")
    print(f"   ✅ Réponse: {r.json()}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 2: Status
print("\n2. Test /status")
try:
    r = requests.get(f"{API_URL}/status")
    print(f"   ✅ Réponse: {r.json()}")
except:
    print("   ⚠️ /status non disponible (normal si pas implémenté)")

# Test 3: Résolution captcha
print("\n3. Test /solve sur page démo")
try:
    r = requests.post(f"{API_URL}/solve", json={
        'url': 'https://www.google.com/recaptcha/api2/demo',
        'debug': True
    }, timeout=60)
    
    result = r.json()
    print(f"   📊 Résultat:")
    print(f"      Succès: {result.get('success')}")
    print(f"      Message: {result.get('message', 'N/A')}")
    if result.get('token'):
        print(f"      Token: {result['token'][:50]}...")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print("\n" + "="*50)
print("✅ Test terminé")