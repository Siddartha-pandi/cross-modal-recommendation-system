import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import clip
from PIL import Image
import json
import os
import sys
from tqdm import tqdm
from pathlib import Path
from typing import List, Dict, Any

# Add the app directory to sys.path
repo_root = Path(__file__).resolve().parents[2]
sys.path.append(str(repo_root / "backend"))

from app.models.ml.clip_model import CLIPModel

class IndoFashionDataset(Dataset):
    def __init__(self, data_path, image_root, preprocess):
        self.data = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.data.append(json.loads(line))
        self.image_root = image_root
        self.preprocess = preprocess

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        image_path = os.path.join(self.image_root, item['image_path'])
        
        # Use product title as the caption for fine-tuning
        # (Alternatively, you could combine brand + title + category)
        caption = item.get('product_title', 'Indian apparel')
        
        try:
            image = self.preprocess(Image.open(image_path))
            tokens = clip.tokenize([caption], truncate=True)[0]
            return image, tokens
        except Exception as e:
            # Fallback for broken images
            return torch.zeros(3, 224, 224), clip.tokenize(["Indian apparel"])[0]

def finetune_clip(
    train_json: str,
    val_json: str,
    image_root: str,
    epochs: int = 5,
    batch_size: int = 32,
    lr: float = 5e-6
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Fine-tuning on {device}...")

    # Initialize CLIP
    model_wrapper = CLIPModel(model_name="ViT-B/32", device=device)
    model = model_wrapper.model
    preprocess = model_wrapper.preprocess

    # Prepare Data
    train_dataset = IndoFashionDataset(train_json, image_root, preprocess)
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=4, 
        pin_memory=True
    )
    
    # Optimizer
    # Note: We use a very small learning rate for fine-tuning
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=0.1)
    
    # Initialize Mixed Precision Scaler for speed optimization (only works on CUDA)
    scaler = torch.amp.GradScaler(device='cuda') if device == 'cuda' else None
    
    # Loss scaling is recommended for CLIP
    # model.logit_scale is a parameter in CLIP
    
    model.train()
    for epoch in range(epochs):
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        epoch_loss = 0
        
        for images, texts in pbar:
            images = images.to(device)
            texts = texts.to(device)
            
            optimizer.zero_grad()
            
            # Autocast enables mixed precision for much faster inference/training
            with torch.amp.autocast(device_type=device):
                # Forward pass
                logits_per_image, logits_per_text = model(images, texts)
                
                # Calculate contrastive loss manually or use the wrapper's method
                # CLIP's forward returns logits that are already scaled by exp(logit_scale)
                # Labels for contrastive loss are just the diagonal [0, 1, 2, ..., N]
                ground_truth = torch.arange(len(images), device=device)
                
                loss_img = nn.CrossEntropyLoss()(logits_per_image, ground_truth)
                loss_txt = nn.CrossEntropyLoss()(logits_per_text, ground_truth)
                loss = (loss_img + loss_txt) / 2
            
            # Backward pass with scaled gradients
            if scaler is not None:
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                optimizer.step()
            
            epoch_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})
            
        print(f"Epoch {epoch+1} average loss: {epoch_loss/len(train_loader):.4f}")
        
    # Save the fine-tuned weights
    save_path = repo_root / "backend" / "models" / "weights"
    save_path.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), save_path / "clip_indofashion_finetuned.pt")
    print(f"Fine-tuned model saved to {save_path}/clip_indofashion_finetuned.pt")

if __name__ == "__main__":
    # Check if data exists
    TRAIN_JSON = "data/indo_fashion/train_data.json"
    VAL_JSON = "data/indo_fashion/val_data.json"
    IMAGE_ROOT = "data/indo_fashion"
    
    if os.path.exists(TRAIN_JSON):
        finetune_clip(TRAIN_JSON, VAL_JSON, IMAGE_ROOT)
    else:
        print("Dataset not found at data/indo_fashion/")
        print("Please follow the instructions in evaluation/INSTRUCTIONS.md")
