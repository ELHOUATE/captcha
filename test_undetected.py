"""
Test avec undetected-chromedriver (contourne la détection)
"""

import sys
import time

sys.path.insert(0, r'C:/Users/zineb/Downloads/solution_captcha')

import undetected_chromedriver as uc
from backend.captcha_solver import solve_captcha

print('='*60)
print('🧪 TEST AVEC UNDETECTED-CHROMEDRIVER')
print('='*60)

print('\n1. Lancement du navigateur (mode anti-détection)...')
driver = uc.Chrome()

print('2. Chargement de la page démo...')
driver.get('https://www.google.com/recaptcha/api2/demo')
time.sleep(3)

print('3. Résolution du captcha...\n')
success = solve_captcha(driver, models_dir='models/', debug=True)

print('\n' + '='*60)
print('📊 RÉSULTAT FINAL')
print('='*60)
print(f'✅ Succès: {success}')

time.sleep(5)
driver.quit()