"""
Test d'intégration simple
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.captcha_solver import solve_captcha, CaptchaSolver


def test_import():
    """Vérifie que les imports fonctionnent"""
    print("✅ Import réussi")
    
    solver = CaptchaSolver(debug=False)
    print("✅ Solver instancié")
    
    return True


if __name__ == "__main__":
    test_import()