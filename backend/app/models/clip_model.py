import torch
import torch.nn as nn
import torch.nn.functional as F
import clip
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from typing import Union, List, Tuple, Optional, Dict
import asyncio
import logging
import math

logger = logging.getLogger(__name__)

class CLIPModel:
    """
    CLIP model wrapper for encoding images and text
    """
    
    def __init__(self, model_name: str = "ViT-B/32", device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        
        logger.info(f"Loading CLIP model {model_name} on {self.device}")
        
        # Load CLIP model
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.model.eval()
        
        # Image preprocessing
        self.image_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.48145466, 0.4578275, 0.40821073],
                std=[0.26862954, 0.26130258, 0.27577711]
            )
        ])
        
        logger.info("CLIP model loaded successfully")
    
    async def encode_image(self, image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """
        Encode image to embedding vector
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Preprocess image
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        
        # Generate embedding
        with torch.no_grad():
            image_features = self.model.encode_image(image_tensor)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy().flatten()
    
    async def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text to embedding vector
        Automatically truncates text to fit within CLIP's context length (77 tokens).
        """
        # Truncate text to fit within CLIP's context limit (~77 tokens, ~308 chars)
        max_length = 250  # Safe buffer for 77 tokens
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + "..."
        
        # Tokenize text
        text_tokens = clip.tokenize([text]).to(self.device)
        
        # Generate embedding
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        return text_features.cpu().numpy().flatten()
    
    async def encode_batch_images(self, images: List[Image.Image]) -> np.ndarray:
        """
        Encode batch of images
        """
        batch_tensors = []
        for image in images:
            tensor = self.preprocess(image).unsqueeze(0)
            batch_tensors.append(tensor)
        
        batch_tensor = torch.cat(batch_tensors, dim=0).to(self.device)
        
        with torch.no_grad():
            features = self.model.encode_image(batch_tensor)
            features = features / features.norm(dim=-1, keepdim=True)
        
        return features.cpu().numpy()
    
    async def encode_batch_texts(self, texts: List[str]) -> np.ndarray:
        """
        Encode batch of texts.
        Automatically truncates texts to fit within CLIP's context length (77 tokens).
        """
        # Truncate all texts to fit within CLIP's context limit
        max_length = 250
        truncated_texts = []
        for text in texts:
            if len(text) > max_length:
                text = text[:max_length].rsplit(' ', 1)[0] + "..."
            truncated_texts.append(text)
        
        text_tokens = clip.tokenize(truncated_texts).to(self.device)
        
        with torch.no_grad():
            features = self.model.encode_text(text_tokens)
            features = features / features.norm(dim=-1, keepdim=True)
        
        return features.cpu().numpy()
    
    def get_embedding_dim(self) -> int:
        """
        Get embedding dimension
        """
        return self.model.visual.output_dim if hasattr(self.model.visual, 'output_dim') else 512
    
    async def fuse_embeddings(
        self, 
        image_embedding: Optional[np.ndarray] = None,
        text_embedding: Optional[np.ndarray] = None,
        image_weight: float = 0.7,
        text_weight: float = 0.3,
        fusion_method: str = "weighted_avg"
    ) -> np.ndarray:
        """
        Fuse image and text embeddings using various methods
        
        Args:
            image_embedding: Image embedding vector
            text_embedding: Text embedding vector
            image_weight: Weight for image embedding
            text_weight: Weight for text embedding
            fusion_method: Method for fusion ('weighted_avg', 'concatenation', 'element_wise')
        """
        if image_embedding is None and text_embedding is None:
            raise ValueError("At least one embedding must be provided")
        
        if image_embedding is None:
            return text_embedding
        
        if text_embedding is None:
            return image_embedding
            
        # Ensure embeddings are normalized
        image_embedding = image_embedding / np.linalg.norm(image_embedding)
        text_embedding = text_embedding / np.linalg.norm(text_embedding)
        
        if fusion_method == "weighted_avg":
            # Weighted average fusion (as shown in diagram)
            fused = (image_weight * image_embedding + text_weight * text_embedding)
            fused = fused / np.linalg.norm(fused)  # Normalize result
            
        elif fusion_method == "concatenation":
            # Concatenate embeddings
            fused = np.concatenate([image_embedding, text_embedding])
            fused = fused / np.linalg.norm(fused)
            
        elif fusion_method == "element_wise":
            # Element-wise multiplication
            fused = image_embedding * text_embedding
            fused = fused / np.linalg.norm(fused)
            
        else:
            raise ValueError(f"Unknown fusion method: {fusion_method}")
            
        return fused
    
    def compute_contrastive_loss(
        self,
        image_embeddings: torch.Tensor,
        text_embeddings: torch.Tensor,
        temperature: float = 0.07
    ) -> torch.Tensor:
        """
        Compute contrastive loss between image and text embeddings (as shown in diagram)
        
        Args:
            image_embeddings: Batch of image embeddings
            text_embeddings: Batch of text embeddings
            temperature: Temperature parameter for softmax
        """
        # Normalize embeddings
        image_embeddings = F.normalize(image_embeddings, dim=-1)
        text_embeddings = F.normalize(text_embeddings, dim=-1)
        
        # Compute similarity matrix
        logits = torch.matmul(image_embeddings, text_embeddings.T) / temperature
        
        # Create labels (diagonal should be positive pairs)
        batch_size = image_embeddings.shape[0]
        labels = torch.arange(batch_size, device=image_embeddings.device)
        
        # Compute cross-entropy loss in both directions
        loss_i2t = F.cross_entropy(logits, labels)
        loss_t2i = F.cross_entropy(logits.T, labels)
        
        return (loss_i2t + loss_t2i) / 2