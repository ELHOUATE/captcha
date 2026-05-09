"""
Test final du solveur avec seuil de confiance à 70%
"""

import sys
import time

sys.path.insert(0, r'C:/Users/zineb/Downloads/solution_captcha')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from backend.captcha_solver import solve_captcha

print('='*60)
print('🧪 TEST FINAL V2 - SEUIL 70%')
print('='*60)

# Options anti-détection
options = Options()
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-blink-features=AutomationControlled')

print('\n1. Lancement du navigateur...')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Désactiver la détection webdriver
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

print('2. Chargement de la page démo...')
driver.get('https://www.google.com/recaptcha/api2/demo')
time.sleep(3)

print('3. Résolution du captcha...\n')

# Seuil à 0.7 (70% de confiance minimum)
success = solve_captcha(driver, models_dir='models/', debug=True, confidence_threshold=0.7)

print('\n' + '='*60)
print('📊 RÉSULTAT FINAL')
print('='*60)
print(f'✅ Succès: {success}')

if success:
    print('🎉 Le captcha a été résolu automatiquement !')
else:
    print('⚠️ Le captcha n\'a pas été résolu.')

print('\n⏳ Fermeture dans 5 secondes...')
time.sleep(5)
driver.quit()
print('👋 Test terminé')