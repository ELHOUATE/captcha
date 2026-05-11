"""
Solveur Google reCAPTCHA v2 - Version finale
Sélecteurs corrects pour Google reCAPTCHA
"""

import os
import time
from io import BytesIO
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

from classifiers.best_model_loader import BestClassifierLoader


class CaptchaSolver:
    # ⭐ SÉLECTEURS CORRECTS POUR GOOGLE reCAPTACHA
    CHECKBOX_IFRAME_XPATH = "//iframe[@title='reCAPTCHA']"
    CHALLENGE_IFRAME_XPATH = "//iframe[contains(@title, 'recaptcha challenge')]"
    CHECKBOX_ID = "recaptcha-anchor"
    TILE_CLASS = "rc-imageselect-tile"
    INSTRUCTIONS_CLASS = "rc-imageselect-instructions"
    VERIFY_BUTTON_ID = "recaptcha-verify-button"

    def __init__(
        self,
        models_dir="models/",
        debug=True,
        confidence_threshold=0.60,
        max_attempts=3,
        save_debug_crops=False,
        debug_crops_dir="debug_crops",
    ):
        self.debug = debug
        self.confidence_threshold = confidence_threshold
        self.max_attempts = max_attempts
        self.save_debug_crops = save_debug_crops
        self.debug_crops_dir = debug_crops_dir

        if self.save_debug_crops:
            os.makedirs(self.debug_crops_dir, exist_ok=True)

        self._log("🔄 Chargement des modèles...")
        self.classifier = BestClassifierLoader(models_dir, debug=debug)
        self._log(f"📌 Classes disponibles: {self.classifier.list_available_classes()}")

    def solve(self, driver, timeout=30):
        for attempt in range(self.max_attempts):
            self._log(f"\n📌 Tentative {attempt + 1}/{self.max_attempts}")

            try:
                if not self._click_checkbox(driver, timeout):
                    continue

                if not self._enter_challenge_iframe(driver, timeout):
                    if self._is_success(driver):
                        return True
                    continue

                if self._solve_grid(driver, timeout):
                    return True

            except Exception as e:
                self._log(f"❌ Erreur tentative {attempt + 1}: {e}")
                if "invalid session id" in str(e).lower():
                    break

        self._log("❌ Échec après toutes les tentatives")
        return False

    def _click_checkbox(self, driver, timeout=10) -> bool:
        try:
            driver.switch_to.default_content()
            captcha_iframe = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, self.CHECKBOX_IFRAME_XPATH))
            )
            driver.switch_to.frame(captcha_iframe)
            checkbox = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.ID, self.CHECKBOX_ID))
            )
            driver.execute_script("arguments[0].click();", checkbox)
            self._log("☑️ Clic sur checkbox")
            time.sleep(2)
            return True
        except Exception as e:
            self._log(f"⚠️ Erreur checkbox: {e}")
            return False

    def _enter_challenge_iframe(self, driver, timeout=15) -> bool:
        try:
            driver.switch_to.default_content()
            challenge_iframe = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, self.CHALLENGE_IFRAME_XPATH))
            )
            driver.switch_to.frame(challenge_iframe)
            self._log("✅ Iframe défi chargé")
            time.sleep(1)
            return True
        except Exception as e:
            self._log(f"⚠️ Aucun défi détecté: {e}")
            return False

    def _click_skip(self, driver) -> bool:
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and "skip" in btn.text.lower():
                    driver.execute_script("arguments[0].click();", btn)
                    self._log("⏭️ Clic sur Skip")
                    return True
        except:
            pass
        return False

    def _click_next(self, driver) -> bool:
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and "next" in btn.text.lower():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", btn)
                    self._log("⏭️ Clic sur Next")
                    return True
        except:
            pass
        return False

    def _detect_challenge_type(self, instruction: str, cells) -> str:
        instruction_lower = instruction.lower()
        is_multi_round = ("until none left" in instruction_lower or 
                          "click verify once there are none left" in instruction_lower or
                          "none left" in instruction_lower)
        is_4x4 = len(cells) == 16

        if is_multi_round and is_4x4:
            return "type4"
        if is_multi_round:
            return "type3"
        if is_4x4:
            return "type2"
        return "type1"

    def _get_cells(self, driver, timeout=30):
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, self.TILE_CLASS))
            )
            cells = driver.find_elements(By.CLASS_NAME, self.TILE_CLASS)
            return [c for c in cells if c.is_displayed()]
        except:
            return []

    def _get_instruction(self, driver, timeout=30) -> str:
        try:
            elem = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, self.INSTRUCTIONS_CLASS))
            )
            text = elem.text.strip()
            self._log(f"📝 Consigne: {text[:100]}...")
            return text
        except:
            return ""

    def _capture_cells(self, driver, cells, round_num=1) -> List[Image.Image]:
        images = []
        for idx, cell in enumerate(cells):
            try:
                if not cell.is_displayed():
                    images.append(Image.new("RGB", (224, 224), color="black"))
                    continue

                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'auto'});", cell)
                time.sleep(0.1)
                img = Image.open(BytesIO(cell.screenshot_as_png)).convert("RGB")
                images.append(img)

                if self.save_debug_crops:
                    filename = os.path.join(self.debug_crops_dir, f"round{round_num}_cell{idx}.png")
                    img.save(filename)

            except Exception as e:
                self._log(f"⚠️ Capture cellule {idx}: {str(e)[:80]}")
                images.append(Image.new("RGB", (224, 224), color="black"))
        return images

    def _click_verify(self, driver) -> bool:
        try:
            btn = driver.find_element(By.ID, self.VERIFY_BUTTON_ID)
            if btn.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.2)
                driver.execute_script("arguments[0].click();", btn)
                self._log("🔘 Clic sur Vérifier")
                return True
        except:
            pass
        return False

    def _is_success(self, driver) -> bool:
        try:
            driver.switch_to.default_content()
            iframe = driver.find_element(By.XPATH, self.CHECKBOX_IFRAME_XPATH)
            driver.switch_to.frame(iframe)
            checkbox = driver.find_element(By.ID, self.CHECKBOX_ID)
            if checkbox.get_attribute("aria-checked") == "true":
                self._log("✅ Succès détecté")
                return True
        except:
            pass
        return False

    def _has_new_grid(self, driver) -> bool:
        try:
            driver.switch_to.default_content()
            challenge_iframe = driver.find_element(By.XPATH, self.CHALLENGE_IFRAME_XPATH)
            driver.switch_to.frame(challenge_iframe)
            cells = driver.find_elements(By.CLASS_NAME, self.TILE_CLASS)
            return len([c for c in cells if c.is_displayed()]) >= 4
        except:
            return False

    def _click_cell(self, driver, cell, idx):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'auto'});", cell)
            time.sleep(0.15)
            driver.execute_script("arguments[0].click();", cell)
            self._log(f"      ✓ Cellule {idx}")
            return True
        except Exception as e:
            self._log(f"      ⚠️ Échec clic {idx}: {str(e)[:50]}")
            return False

    def _is_session_valid(self, driver) -> bool:
        try:
            driver.current_url
            return True
        except:
            return False

    def _get_threshold_for_class(self, target: str, is_grid_4x4: bool) -> float:
        CLASS_THRESHOLDS = {
            "car": 0.65,
            "bus": 0.75,
            "truck": 0.75,
            "bicycle": 0.75,
            "motorcycle": 0.55,
            "traffic_light": 0.65,
            "stop_sign": 0.70,
            "fire_hydrant": 0.40,
        }

        return CLASS_THRESHOLDS.get(target, self.confidence_threshold)

    def _solve_single_round(self, driver, cells, target, is_grid_4x4, round_num=1) -> List[int]:
        current_threshold = self._get_threshold_for_class(target, is_grid_4x4)
        self._log(f"📌 Seuil pour {target}: {current_threshold:.2f}")
        
        images = self._capture_cells(driver, cells, round_num=round_num)
        predictions = self.classifier.predict_batch(images, target, confidence_threshold=current_threshold)

        to_click = []
        for i, (contains, conf) in enumerate(predictions):
            status = "✅" if contains else "❌"
            self._log(f"   Cellule {i}: {status} score={conf:.2f}")
            if contains:
                to_click.append(i)

        # Stocker les scores pour utilisation ultérieure
        self._last_predictions = predictions

        if len(to_click) == 0:
            self._log("⚠️ Aucune cellule positive avec le seuil actuel")
            return []

        return to_click

    def _solve_grid(self, driver, timeout=30) -> bool:
        cells = self._get_cells(driver, timeout)
        if not cells:
            return self._is_success(driver)

        instruction = self._get_instruction(driver, timeout)
        if not instruction:
            return False

        target = self.classifier.normalize_class_name(instruction)
        if not target:
            self._log(f"❌ Classe non reconnue: {instruction[:80]}")
            return False

        self._log(f"🎯 Classe cible: {target}")

        if not self.classifier.has_model(target):
            self._log(f"❌ Aucun modèle pour {target}")
            return False

        challenge_type = self._detect_challenge_type(instruction, cells)
        is_grid_4x4 = len(cells) == 16
        self._log(f"📌 Type: {challenge_type.upper()} | cellules={len(cells)}")

        # ============================================================
        # TYPE 3 & 4 : Multi-rounds
        # ============================================================
        if challenge_type in ["type3", "type4"]:
            round_num = 1
            max_rounds = 5
            total_clicks = 0

            while round_num <= max_rounds:
                self._log(f"\n📍 Round {round_num}")
                
                if not self._is_session_valid(driver):
                    self._log("⚠️ Session perdue, fin du challenge")
                    break
                
                cells = self._get_cells(driver, timeout)
                if not cells:
                    break

                to_click = self._solve_single_round(driver, cells, target, is_grid_4x4, round_num=round_num)

                if not to_click:
                    self._log("⚠️ Aucune cellule positive - Fin du challenge")
                    break

                # Pour TYPE3, limiter à 4 clics maximum si trop de clics
                if challenge_type == "type3" and len(to_click) > 4:
                    predictions = getattr(self, '_last_predictions', [])
                    if predictions:
                        scored = [(idx, predictions[idx][1]) for idx in to_click if idx < len(predictions)]
                        scored.sort(key=lambda x: x[1], reverse=True)
                        to_click = [idx for idx, _ in scored[:4]]
                        self._log(f"   🔄 Limité à 4 clics: {to_click}")

                self._log(f"🖱️ Clic sur {len(to_click)} cellule(s)")
                for idx in to_click:
                    if idx < len(cells):
                        if self._click_cell(driver, cells[idx], idx):
                            total_clicks += 1
                        time.sleep(0.2)

                time.sleep(1.5)

                if challenge_type == "type4" and self._click_next(driver):
                    time.sleep(1)
                    round_num += 1
                    continue

                if not self._has_new_grid(driver):
                    self._log("✅ Plus de grille, fin des rounds")
                    break

                round_num += 1

            self._log(f"📊 Total clics: {total_clicks}")
            time.sleep(1)
            self._click_verify(driver)
            time.sleep(2.5)
            return self._is_success(driver)

        # ============================================================
        # TYPE 1 & 2 : Single round
        # ============================================================
        else:
            to_click = self._solve_single_round(driver, cells, target, is_grid_4x4, round_num=1)

            if not to_click:
                self._log("⚠️ Aucune cellule positive")
                if "click skip" in instruction.lower():
                    self._click_skip(driver)
                    time.sleep(1)
                    return self._is_success(driver)
                return False

            # ⭐ VÉRIFICATION POUR TYPE1 (3x3)
            if challenge_type == "type1":
                # Limiter à 4 clics maximum
                if len(to_click) > 4:
                    predictions = getattr(self, '_last_predictions', [])
                    if predictions:
                        scored = [(idx, predictions[idx][1]) for idx in to_click if idx < len(predictions)]
                        scored.sort(key=lambda x: x[1], reverse=True)
                        to_click = [idx for idx, _ in scored[:4]]
                        self._log(f"   🔄 {len(scored)} clics → garde les 4 meilleurs: {to_click}")
                
                # Ne pas forcer un minimum de 3 clics
                if len(to_click) == 0:
                    self._log("⚠️ Aucune cellule positive pour TYPE1")
                    return False

            # ⭐ POUR TYPE2 (4x4) : on garde TOUS les clics
            elif challenge_type == "type2":
                self._log(f"   📌 4x4: {len(to_click)} cellules à cliquer")

            self._log(f"🖱️ Clic sur {len(to_click)} cellule(s)")
            for idx in to_click:
                if idx < len(cells):
                    self._click_cell(driver, cells[idx], idx)
                    time.sleep(0.2)

            time.sleep(1.5)
            self._click_verify(driver)
            time.sleep(2.5)
            return self._is_success(driver)

    def _log(self, msg):
        if self.debug:
            print(msg)


def solve_captcha(
    driver,
    models_dir="models/",
    debug=True,
    confidence_threshold=0.60,
    max_attempts=3,
    save_debug_crops=False,
):
    solver = CaptchaSolver(
        models_dir=models_dir,
        debug=debug,
        confidence_threshold=confidence_threshold,
        max_attempts=max_attempts,
        save_debug_crops=save_debug_crops,
    )
    return solver.solve(driver)