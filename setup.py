from setuptools import setup, find_packages

setup(
    name="captcha-solver",
    version="1.0.0",
    description="Solveur de reCAPTCHA v2 avec RT-DETR et YOLOv26",
    author="Votre Nom",
    packages=find_packages(),
    install_requires=[
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
        "ultralytics>=8.0.0",
        "opencv-python>=4.8.0",
        "pillow>=10.0.0",
        "numpy>=1.24.0",
    ],
    python_requires=">=3.10",
)