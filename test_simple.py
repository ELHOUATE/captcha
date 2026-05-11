from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()
driver.get("https://www.google.com/recaptcha/api2/demo")
time.sleep(2)

# Cliquer sur la case
iframe = driver.find_element(By.XPATH, "//iframe[@title='reCAPTCHA']")
driver.switch_to.frame(iframe)
checkbox = driver.find_element(By.ID, "recaptcha-anchor")
checkbox.click()
time.sleep(3)

# Revenir à la page principale
driver.switch_to.default_content()

# Chercher l'iframe du défi
challenge_iframes = driver.find_elements(By.XPATH, "//iframe[contains(@title, 'recaptcha challenge')]")
print(f"Nombre d'iframes défi trouvées: {len(challenge_iframes)}")

if len(challenge_iframes) > 0:
    print("✅ DÉFI TROUVÉ - Le solveur devrait fonctionner")
else:
    print("❌ PAS DE DÉFI - Google bloque Selenium")

driver.quit()