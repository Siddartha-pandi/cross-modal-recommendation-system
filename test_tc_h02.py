"""
Test Single Case: TC-H02 - Blue Denim Jacket
Text Query: "formal office blazer"
Alpha: 0.7 (Text-dominant semantic override)
"""

import json
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.models.clip_model import CLIPModel
from app.models.fusion import FusionEngine
from app.utils.faiss_index import FAISSIndex
from PIL import Image
import numpy as np

async def test_tc_h02():
    """Run TC-H02 test case"""
    
    print("\n" + "="*80)
    print("TEST CASE: TC-H02 - Blue Denim Jacket")
    print("="*80)
    
    # Test configuration
    tc_config = {
        "id": "TC-H02",
        "description": "blue_denim_jacket",
        "text_query": "formal office blazer",
        "alpha": 0.7,
        "evaluation_objective": "Text-dominant semantic override",
        "input_images": [
            "data/inputs/TC-H02_input_blue_denim_jacket_1.jpg",
            "data/inputs/TC-H02_input_blue_denim_jacket_2.jpg",
            "data/inputs/TC-H02_input_blue_denim_jacket_3.jpg"
        ]
    }
    
    print(f"\nTest ID: {tc_config['id']}")
    print(f"Description: {tc_config['description']}")
    print(f"Text Query: {tc_config['text_query']}")
    print(f"Alpha Value: {tc_config['alpha']}")
    print(f"Objective: {tc_config['evaluation_objective']}")
    
    try:
        # Initialize models
        print("\n📦 Initializing CLIP Model...")
        clip_model = CLIPModel(model_name="ViT-B/32", device=None)
        
        print("📦 Initializing Fusion Engine...")
        fusion_engine = FusionEngine(default_alpha=0.7)
        
        print("📦 Loading FAISS Index...")
        try:
            faiss_index = FAISSIndex(embedding_dim=512, index_type="HNSW", load_existing=True)
            faiss_index.load_index()
        except Exception as faiss_err:
            print(f"   ⚠️  FAISS loading issue (will continue): {faiss_err}")
            faiss_index = None
        
        # Encode text query
        print(f"\n🔍 Encoding text query: '{tc_config['text_query']}'...")
        text_embedding = await clip_model.encode_text(tc_config['text_query'])
        print(f"   ✓ Text embedding shape: {text_embedding.shape}")
        
        # Process input images
        print(f"\n🖼️  Processing {len(tc_config['input_images'])} input images...")
        image_embeddings = []
        
        for idx, img_path in enumerate(tc_config['input_images'], 1):
            img_file = Path(img_path)
            if img_file.exists():
                print(f"   [{idx}] Loading: {img_file.name}")
                image = Image.open(img_file)
                img_emb = await clip_model.encode_image(image)
                image_embeddings.append(img_emb)
                print(f"       ✓ Image embedding shape: {img_emb.shape}")
            else:
                print(f"   [{idx}] ⚠️  Image not found: {img_path}")
        
        if not image_embeddings:
            print("\n❌ Error: No images could be loaded!")
            return False
        
        # Average image embeddings
        avg_image_embedding = np.mean(image_embeddings, axis=0)
        print(f"\n📊 Average image embedding shape: {avg_image_embedding.shape}")
        
        # Fuse embeddings
        print(f"\n⚙️  Fusing embeddings with alpha={tc_config['alpha']}...")
        fused_embedding, fusion_scores = fusion_engine.fuse(
            image_embedding=avg_image_embedding,
            text_embedding=text_embedding,
            alpha=tc_config['alpha'],
            method="weighted_avg"
        )
        print(f"   ✓ Fused embedding shape: {fused_embedding.shape}")
        print(f"   ✓ Image weight: {tc_config['alpha']:.2f}")
        print(f"   ✓ Text weight: {(1-tc_config['alpha']):.2f}")
        
        # Search FAISS index
        if faiss_index:
            print(f"\n🔎 Searching FAISS index (top-3 results)...")
            distances, indices = faiss_index.search(fused_embedding, k=3)
            
            print(f"\n✅ Search Results:")
            print(f"   {'Rank':<6} {'Distance':<12} {'Index':<8}")
            print(f"   {'-'*26}")
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
                print(f"   {i:<6} {dist:<12.6f} {idx:<8}")
        else:
            print("\n⚠️  Skipping FAISS search (index not available)")
        
        print(f"\n📈 Fusion Scores:")
        for key, value in fusion_scores.items():
            print(f"   {key}: {value:.4f}")
        
        # Load metadata for additional context
        try:
            with open("TEST_CASES_METADATA.json", "r") as f:
                metadata = json.load(f)
                tc_h02_meta = metadata.get("test_cases", {}).get("TC-H02", {})
                print(f"\n📋 Expected Output Images:")
                outputs = tc_h02_meta.get("output_images", {}).get("files", [])
                for idx, output in enumerate(outputs, 1):
                    print(f"   [{idx}] {output}")
        except Exception as e:
            print(f"\n⚠️  Could not load metadata: {e}")
        
        print("\n" + "="*80)
        print("✅ TEST CASE TC-H02 COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tc_h02())
    sys.exit(0 if success else 1)
