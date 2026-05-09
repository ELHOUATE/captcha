"""
Test sur la page démo Google
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.driver_manager import DriverManager
from backend.captcha_solver import solve_captcha


def test_demo():
    print("="*60)
    print("🧪 TEST SUR PAGE DÉMO GOOGLE")
    print("="*60)
    
    # Lancer le navigateur
    print("\n1. Lancement du navigateur...")
    driver = DriverManager.create_test_driver()
    
    # Page démo
    print("2. Chargement de la page démo...")
    driver.get("https://www.google.com/recaptcha/api2/demo")
    time.sleep(3)
    
    # Résoudre
    print("3. Résolution du captcha...")
    start = time.time()
    success = solve_captcha(driver, models_dir="models/", debug=True)
    elapsed = time.time() - start
    
    # Résultat
    print("\n" + "="*60)
    print("📊 RÉSULTAT")
    print("="*60)
    print(f"✅ Succès: {success}")
    print(f"⏱️  Temps: {elapsed:.2f} secondes")
    
    time.sleep(5)
    driver.quit()
    
    return success


if __name__ == "__main__":
    success = test_demo()
    exit(0 if success else 1)