# api.py - Version avec logs détaillés
import sys
import os
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from captcha_solver import solve_captcha

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "reCAPTCHA Solver"})

@app.route('/solve', methods=['GET', 'POST'])
def solve():
    if request.method == 'GET':
        url = request.args.get('url')
    else:
        data = request.get_json() or {}
        url = data.get('url')
    
    if not url:
        return jsonify({"success": False, "error": "Missing url"}), 400
    
    print(f"\n{'='*60}")
    print(f"🔍 Nouvelle requête: {url}")
    print(f"{'='*60}")
    
    try:
        print("🚀 1. Configuration du navigateur...")
        options = Options()
        options.add_argument("--window-size=1280,900")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        print("🚀 2. Lancement de Chrome...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"🚀 3. Chargement de l'URL: {url}")
        driver.get(url)
        print("⏳ 4. Attente 5 secondes...")
        time.sleep(5)
        
        print("🚀 5. Appel du solveur...")
        success = solve_captcha(driver, debug=True)
        print(f"📊 6. Résultat solveur: {success}")
        
        token = None
        if success:
            try:
                print("🔑 7. Récupération du token...")
                token = driver.execute_script("return document.getElementById('g-recaptcha-response').value")
                print(f"   Token: {token[:50] if token else 'None'}")
            except Exception as e:
                print(f"⚠️ Erreur token: {e}")
        
        print("🚀 8. Fermeture du navigateur...")
        driver.quit()
        
        print(f"📊 9. Retour: success={success}")
        return jsonify({
            "success": success, 
            "token": token,
            "message": "Captcha résolu" if success else "Échec"
        })
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 API démarrée sur http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)