"""
Traitement d'images centralisé pour le solveur.
"""

from io import BytesIO
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from selenium.webdriver.common.by import By


class ImageProcessor:
    """Capture, conversion et sauvegarde debug des images."""

    @staticmethod
    def capture_cell(cell_element) -> Image.Image:
        """Capture l'image d'une cellule Selenium et retourne une image PIL RGB."""
        screenshot = cell_element.screenshot_as_png
        image = Image.open(BytesIO(screenshot)).convert("RGB")
        return image

    @staticmethod
    def preprocess(
        image: Image.Image,
        target_size=(224, 224),
        normalize=True,
    ) -> np.ndarray:
        image = image.convert("RGB").resize(target_size)
        image_np = np.array(image)

        if normalize:
            image_np = image_np.astype("float32") / 255.0

        return image_np

    @staticmethod
    def to_cv2(image_pil: Image.Image) -> np.ndarray:
        image_rgb = image_pil.convert("RGB")
        return cv2.cvtColor(np.array(image_rgb), cv2.COLOR_RGB2BGR)

    @staticmethod
    def save_debug_image(
        image: Image.Image,
        debug_dir: Optional[str],
        filename: str,
    ) -> None:
        if not debug_dir:
            return

        path = Path(debug_dir)
        path.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").save(path / filename)

    # ================================================================
    # ⭐ AJOUT : Capture de la grille complète
    # ================================================================
    @staticmethod
    def capture_full_grid(driver, debug_dir: Optional[str] = None, filename: str = "full_grid.png") -> Optional[Image.Image]:
        """Capture la grille complète du captcha"""
        try:
            grid_element = driver.find_element(By.CLASS_NAME, "rc-imageselect-target")
            screenshot = grid_element.screenshot_as_png
            image = Image.open(BytesIO(screenshot)).convert("RGB")

            if debug_dir:
                path = Path(debug_dir)
                path.mkdir(parents=True, exist_ok=True)
                image.save(path / filename)

            return image
        except Exception as e:
            return None