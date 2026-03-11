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
        self._text_embedding_cache: Dict[str, np.ndarray] = {}
        
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

    async def _encode_texts_cached(self, texts: List[str]) -> np.ndarray:
        """Encode texts and cache embeddings to avoid repeated CLIP calls."""
        uncached = [t for t in texts if t not in self._text_embedding_cache]
        if uncached:
            embeddings = await self.encode_batch_texts(uncached)
            for text, emb in zip(uncached, embeddings):
                self._text_embedding_cache[text] = emb

        return np.stack([self._text_embedding_cache[t] for t in texts], axis=0)

    async def _classify_image_labels(
        self,
        image: Union[Image.Image, np.ndarray],
        labels: List[str],
        prompt_template: str = "a product photo of {}",
    ) -> List[Tuple[str, float]]:
        """Classify an image against a closed label set using CLIP similarities."""
        if not labels:
            return []

        image_embedding = await self.encode_image(image)
        prompts = [prompt_template.format(label) for label in labels]
        text_embeddings = await self._encode_texts_cached(prompts)

        # Convert cosine similarities to probabilities over the label set.
        logits = text_embeddings @ image_embedding
        probs = np.exp(logits - np.max(logits))
        probs = probs / (np.sum(probs) + 1e-9)

        ranked = sorted(
            [(label, float(prob)) for label, prob in zip(labels, probs)],
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked

    @staticmethod
    def _pick_confident_label(
        ranked: List[Tuple[str, float]],
        min_prob: float,
        margin: float,
    ) -> Optional[str]:
        """Pick top label only when confidence is meaningfully above alternatives."""
        if not ranked:
            return None

        top_label, top_prob = ranked[0]
        second_prob = ranked[1][1] if len(ranked) > 1 else 0.0
        if top_prob >= min_prob and (top_prob - second_prob) >= margin:
            return top_label
        return None

    async def infer_fashion_attributes(
        self,
        image: Union[Image.Image, np.ndarray],
    ) -> Dict[str, List[str]]:
        """
        Infer structured fashion attributes directly from image using CLIP zero-shot prompts.

        Returns list-based fields compatible with the advanced retrieval pipeline.
        """
        categories = [
            "sneakers", "shoes", "boots", "sandals", "heels", "loafers", "flats",
            "t-shirt", "shirt", "dress", "jeans", "jacket", "hoodie", "kurti", "saree",
            "bag", "watch",
        ]
        colors = [
            "black", "white", "blue", "red", "green", "yellow", "brown", "grey",
            "pink", "beige", "navy", "olive",
        ]
        use_types = ["casual", "sports", "formal"]

        category_ranked = await self._classify_image_labels(
            image=image,
            labels=categories,
            prompt_template="a fashion product photo of {}",
        )
        color_ranked = await self._classify_image_labels(
            image=image,
            labels=colors,
            prompt_template="a close-up photo of a {} colored fashion item",
        )
        use_ranked = await self._classify_image_labels(
            image=image,
            labels=use_types,
            prompt_template="a {} style fashion outfit",
        )

        category = self._pick_confident_label(category_ranked, min_prob=0.20, margin=0.06)
        color = self._pick_confident_label(color_ranked, min_prob=0.20, margin=0.05)
        use_type = self._pick_confident_label(use_ranked, min_prob=0.34, margin=0.05)

        attrs: Dict[str, List[str]] = {
            "categories": [category] if category else [],
            "colors": [color] if color else [],
            "use_types": [use_type] if use_type else [],
            "occasions": [use_type] if use_type else [],
        }

        logger.info(
            "Image attributes inferred by CLIP: categories=%s colors=%s use_types=%s",
            attrs["categories"],
            attrs["colors"],
            attrs["use_types"],
        )
        return attrs
    
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
        # CLIP has a context length of 77 tokens (76 + 1 for end-of-sequence)
        max_tokens = 76
        
        # Split text into words
        words = text.split()
        
        # Build text incrementally, adding words until we hit the token limit
        current_text = ""
        for word in words:
            test_text = current_text + (" " if current_text else "") + word
            try:
                # Test if this text fits within token limit
                text_tokens = clip.tokenize([test_text]).to(self.device)
                # If we got here without error, update current_text
                current_text = test_text
            except RuntimeError as e:
                if "too long" in str(e):
                    # Adding this word would exceed limit, stop here
                    break
                else:
                    raise
        
        # Use the truncated text (fallback to at least one word if empty)
        if not current_text:
            current_text = words[0] if words else ""
        
        # Final tokenization with truncated text
        text_tokens = clip.tokenize([current_text]).to(self.device)
        
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
        Get embedding dimension.
        ViT-B/32 → 512, ViT-L/14 → 1024, ViT-H/14 → 1024.
        """
        # Try the direct attribute first (most CLIP implementations expose this)
        if hasattr(self.model.visual, "output_dim"):
            return int(self.model.visual.output_dim)
        # Fallback: derive from model_name string
        name_upper = self.model_name.upper()
        if "VIT-L" in name_upper or "VIT-H" in name_upper:
            return 1024
        return 512
    
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