"""
Gestion simple du WebDriver pour tests autorisés.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class DriverManager:
    """Crée des drivers Chrome propres et stables."""

    @staticmethod
    def create_test_driver(headless=False, window_size="1280,900"):
        options = Options()

        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument(f"--window-size={window_size}")

        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        # ================================================================
        # ⭐ AJOUT : Désactiver les animations pour réduire les vibrations
        # ================================================================
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-transitions")
        options.add_argument("--disable-animations")
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--disable-background-timer-throttling")

        if headless:
            options.add_argument("--headless=new")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # ================================================================
        # ⭐ AJOUT : Désactiver les animations via JavaScript
        # ================================================================
        driver.execute_script("""
            var style = document.createElement('style');
            style.innerHTML = '*, *::before, *::after { transition: none !important; animation: none !important; scroll-behavior: auto !important; }';
            document.head.appendChild(style);
        """)

        return driver

    @staticmethod
    def create_driver_with_profile(
        profile_path=None,
        headless=False,
        window_size="1280,900",
    ):
        options = Options()

        if profile_path:
            options.add_argument(f"--user-data-dir={profile_path}")

        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument(f"--window-size={window_size}")

        # ⭐ AJOUT : Mêmes options anti-vibrations
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-transitions")
        options.add_argument("--disable-animations")

        if headless:
            options.add_argument("--headless=new")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # ⭐ AJOUT : Désactiver les animations via JavaScript
        driver.execute_script("""
            var style = document.createElement('style');
            style.innerHTML = '*, *::before, *::after { transition: none !important; animation: none !important; scroll-behavior: auto !important; }';
            document.head.appendChild(style);
        """)

        return driver