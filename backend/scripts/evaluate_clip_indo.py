import torch
import clip
from PIL import Image
import json
import os
import sys
from tqdm import tqdm
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from torch.utils.data import Dataset, DataLoader

# Add the app directory to sys.path
repo_root = Path(__file__).resolve().parents[2]
sys.path.append(str(repo_root / "backend"))

from app.models.ml.clip_model import CLIPModel

class IndoFashionEvalDataset(Dataset):
    def __init__(self, data, image_root, preprocess):
        self.data = data
        self.image_root = image_root
        self.preprocess = preprocess

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        image_path = os.path.join(self.image_root, item['image_path'])
        
        try:
            image = self.preprocess(Image.open(image_path))
            return image, item['class_label'], item.get('product_title', ''), image_path
        except Exception:
            # Fallback for broken images
            return torch.zeros(3, 224, 224), "broken", "", image_path

def evaluate_clip_on_indo_fashion(
    data_paths: List[str], 
    image_root: str,
    class_labels: List[str] = None
):
    """
    Evaluate zero-shot performance of CLIP on Indo Fashion Dataset
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Load CLIP via our wrapper
    model_wrapper = CLIPModel(model_name="ViT-B/32", device=device)
    model = model_wrapper.model
    preprocess = model_wrapper.preprocess

    # Default 15 classes from Indo Fashion Dataset if not provided
    if not class_labels:
        class_labels = [
            "saree", "lehenga", "women kurta", "dupatta", "gowns", 
            "nehru jackets", "sherwanis", "men kurta", "men mojari", 
            "leggings", "salwar", "blouse", "palazzo", "dhoti pants", "petticoat"
        ]

    # Map labels to prompt templates
    prompts = [f"a photo of an Indian ethnic apparel: {label}" for label in class_labels]
    
    # Tokenize prompts
    text_tokens = clip.tokenize(prompts).to(device)
    with torch.no_grad():
        text_features = model.encode_text(text_tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)

    # Load dataset (Handle JSONL format for multiple files)
    data = []
    for data_path in data_paths:
        if not os.path.exists(data_path):
            print(f"Warning: Dataset JSON not found at {data_path}")
            continue

        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))

    if not data:
        print("Error: No data loaded from any of the provided paths.")
        return

    print(f"Loaded {len(data)} total samples from {len(data_paths)} files")

    correct_top1 = 0
    correct_top5 = 0
    total = 0
    
    # Per-class stats
    class_stats = {label: {"correct": 0, "total": 0} for label in class_labels}
    
    # Special term evaluation (e.g., Bandhani)
    special_terms = ["Bandhani", "Banarasi", "Chanderi", "Kanjivaram"]
    special_term_stats = {term: {"similarity_sum": 0, "count": 0} for term in special_terms}

    # Pre-compute special term features
    special_term_features = {}
    with torch.no_grad():
        for term in special_terms:
            term_token = clip.tokenize([f"a photo of a {term} style apparel"]).to(device)
            term_feature = model.encode_text(term_token)
            term_feature /= term_feature.norm(dim=-1, keepdim=True)
            special_term_features[term] = term_feature

    # Setup DataLoader for batching
    dataset = IndoFashionEvalDataset(data, image_root, preprocess)
    
    # Num workers determines how many CPU threads we use to load images from disk to RAM
    # Batch size dictates how many images are pushed to GPU locally
    dataloader = DataLoader(
        dataset, 
        batch_size=64, 
        shuffle=False, 
        num_workers=4, 
        pin_memory=True
    )

    # Iterate through batched dataset
    for images, labels, titles, image_paths in tqdm(dataloader, desc="Evaluating"):
        images = images.to(device)
        
        with torch.no_grad(), torch.amp.autocast(device_type=device):
            image_features = model.encode_image(images)
            image_features /= image_features.norm(dim=-1, keepdim=True)

            # Similarity
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            values, indices = similarity.topk(5, dim=-1)

        # Cast back to fp32 for subsequent compatibility
        image_features = image_features.float()

        # Unbatch properties and compute stats
        for i in range(len(images)):
            label = labels[i]
            title = titles[i]
            
            if label == "broken":
                continue

            total += 1
            class_stats[label]["total"] += 1

            # Top-1
            if class_labels[indices[i][0]] == label:
                correct_top1 += 1
                class_stats[label]["correct"] += 1
            
            # Top-5
            if label in [class_labels[idx] for idx in indices[i]]:
                correct_top5 += 1

            # Check special terms in title
            for term in special_terms:
                if term.lower() in title.lower():
                    # Calculate similarity between image and the specific precomputed term prompt
                    score = (image_features[i].unsqueeze(0) @ special_term_features[term].T).item()
                    special_term_stats[term]["similarity_sum"] += score
                    special_term_stats[term]["count"] += 1

    # Print results
    print("\n" + "="*50)
    print("CLIP ZERO-SHOT EVALUATION ON INDO FASHION")
    print("="*50)
    print(f"Top-1 Accuracy: {100.0 * correct_top1 / total:.2f}%")
    print(f"Top-5 Accuracy: {100.0 * correct_top5 / total:.2f}%")
    
    print("\nPER-CLASS ACCURACY:")
    for label, stats in class_stats.items():
        if stats["total"] > 0:
            acc = 100.0 * stats["correct"] / stats["total"]
            print(f"  {label:15}: {acc:.2f}% ({stats['correct']}/{stats['total']})")

    print("\nSPECIAL ETHNIC TERM ANALYSIS (Cosine Similarity):")
    for term, stats in special_term_stats.items():
        if stats["count"] > 0:
            avg_sim = stats["similarity_sum"] / stats["count"]
            print(f"  {term:10}: {avg_sim:.4f} (Found in {stats['count']} samples)")
        else:
            print(f"  {term:10}: N/A (term not found in sample titles)")
    print("="*50)

if __name__ == "__main__":
    # Example usage (User should update these paths)
    DATASET_PATHS = [
        "data/indo_fashion/train_data.json",
        "data/indo_fashion/val_data.json",
        "data/indo_fashion/test_data.json"
    ]
    IMAGE_ROOT = "data/indo_fashion"
    
    evaluate_clip_on_indo_fashion(DATASET_PATHS, IMAGE_ROOT)
