"""
Vérifie que les modèles ONNX récemment exportés ont le bon format
"""
import onnx
from pathlib import Path

models_dir = Path("models/rtdetr")
yolo_dir = Path("models/yolo26")

print("=" * 60)
print("VÉRIFICATION DES MODÈLES ONNX")
print("=" * 60)

# Vérifier les modèles RT-DETR
print("\n📁 MODÈLES RT-DETR:")
for model_path in models_dir.glob("*.onnx"):
    try:
        model = onnx.load(str(model_path))
        output_shape = model.graph.output[0].type.tensor_type.shape.dim
        
        # Extraire les dimensions
        dims = [dim.dim_value for dim in output_shape]
        print(f"\n  {model_path.name}:")
        print(f"    - Shape: {dims}")
        
        if len(dims) == 3 and dims[2] == 5:
            print(f"    ✅ Format DÉTECTION (batch, 300, 5) - x1,y1,x2,y2,conf")
        elif len(dims) == 3 and dims[2] == 6:
            print(f"    ✅ Format DÉTECTION avec classe (batch, 300, 6)")
        else:
            print(f"    ⚠️ Format non standard: {dims}")
            
    except Exception as e:
        print(f"  ❌ Erreur chargement {model_path.name}: {e}")

# Vérifier les modèles YOLO
print("\n📁 MODÈLES YOLO:")
for model_path in yolo_dir.glob("*.onnx"):
    try:
        model = onnx.load(str(model_path))
        output_shape = model.graph.output[0].type.tensor_type.shape.dim
        dims = [dim.dim_value for dim in output_shape]
        print(f"\n  {model_path.name}:")
        print(f"    - Shape: {dims}")
        
        if len(dims) == 3 and dims[2] == 6:
            print(f"    ✅ Format YOLO standard (batch, 300, 6)")
        else:
            print(f"    ⚠️ Format: {dims}")
            
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

print("\n" + "=" * 60)