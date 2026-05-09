# download_uvh26_v2.py
import requests
import os
from tqdm import tqdm

print("📥 Téléchargement de UVH-26...")
print("⚠️ Cette méthode nécessite l'URL directe du dataset sur HuggingFace.\n")

# Note : Pour UVH-26, il faut utiliser l'API Hub
try:
    from huggingface_hub import snapshot_download, login
    
    # Optionnel : login si nécessaire (décommentez si demandé)
    # login()
    
    print("Connexion à HuggingFace Hub...")
    snapshot_download(
        repo_id="iisc-aim/UVH-26",
        repo_type="dataset",
        local_dir="./UVH-26",
        ignore_patterns=["*.h5", "*.pickle", ".git/*"],  # Ignore certains fichiers
        resume=True
    )
    print("\n✅ Téléchargement terminé !")
    
except ImportError:
    print("❌ huggingface-hub non installé")
    print("Exécutez : pip install huggingface-hub")
except Exception as e:
    print(f"❌ Erreur: {e}")