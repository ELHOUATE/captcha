"""
Test du solveur sur la page démo Google
"""

import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.captcha_solver import solve_captcha

# Configuration anti-détection
options = Options()
options.add_argument("--window-size=1280,900")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Désactiver les animations
driver.execute_script("""
    var style = document.createElement('style');
    style.innerHTML = '*, *::before, *::after { transition: none !important; animation: none !important; }';
    document.head.appendChild(style);
""")

try:
    print("="*60)
    print("🧪 TEST SOLVEUR reCAPTCHA v2")
    print("="*60)
    
    TEST_URL = "https://www.google.com/recaptcha/api2/demo"
    print(f"\n📂 Chargement de: {TEST_URL}")
    driver.get(TEST_URL)
    time.sleep(3)
    
    print("\n🤖 Résolution du captcha...")
    print("-" * 40)
    
    success = solve_captcha(
        driver=driver,
        debug=True,
        confidence_threshold=0.65,
        max_attempts=3
    )
    
    print("-" * 40)
    print("\n" + "="*60)
    print(f"📊 RÉSULTAT: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
    print("="*60)
    
    print("\n⏳ La page reste ouverte 15 secondes pour observer...")
    time.sleep(15)
    
finally:
    driver.quit()
    print("👋 Navigateur fermé")