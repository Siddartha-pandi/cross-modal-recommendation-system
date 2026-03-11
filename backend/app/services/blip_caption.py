"""BLIP image captioning service for fashion query enrichment."""

import asyncio
import logging
import re
from contextlib import contextmanager
from typing import Optional

import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor
from transformers.utils import logging as transformers_logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


@contextmanager
def _quiet_hf_warnings():
    """Temporarily suppress noisy advisory warnings from HF/Transformers."""
    prev_level = transformers_logging.get_verbosity()
    hub_http_logger = logging.getLogger("huggingface_hub.utils._http")
    hub_logger = logging.getLogger("huggingface_hub")
    prev_http_level = hub_http_logger.level
    prev_hub_level = hub_logger.level

    transformers_logging.set_verbosity_error()
    hub_http_logger.setLevel(logging.ERROR)
    hub_logger.setLevel(logging.ERROR)
    try:
        yield
    finally:
        transformers_logging.set_verbosity(prev_level)
        hub_http_logger.setLevel(prev_http_level)
        hub_logger.setLevel(prev_hub_level)


class BlipCaptionService:
    """Wrapper around BLIP caption generation for uploaded query images."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self.model_name = model_name or settings.BLIP_MODEL
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = None
        self.model = None
        self._load_lock = asyncio.Lock()
        logger.info("BLIP caption service initialized in lazy mode on %s", self.device)

    def _load_model_sync(self) -> None:
        """Load BLIP artifacts synchronously (called from a thread)."""
        if self.processor is not None and self.model is not None:
            return
        logger.info("Loading BLIP model %s on %s", self.model_name, self.device)
        with _quiet_hf_warnings():
            # Prefer fast processor for lower per-request preprocessing latency.
            self.processor = BlipProcessor.from_pretrained(self.model_name, use_fast=True)
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        logger.info("BLIP caption service ready")

    async def _ensure_model_loaded(self) -> None:
        """Load model lazily and only once across concurrent requests."""
        if self.processor is not None and self.model is not None:
            return
        async with self._load_lock:
            if self.processor is None or self.model is None:
                await asyncio.to_thread(self._load_model_sync)

    def _cleanup_caption(self, caption: str) -> str:
        """Normalize and remove obvious repetition artifacts from model output."""
        if not caption:
            return ""

        # Remove extra whitespace and lowercase
        text = re.sub(r"\s+", " ", caption).strip().lower()
        
        # Remove common repeating phrases in fashion captions
        # e.g., "a a a a" -> "a"
        tokens = text.split(" ")
        if not tokens:
            return ""

        cleaned = []
        repeat_streak = 0
        prev = None

        for tok in tokens:
            if tok == prev:
                repeat_streak += 1
            else:
                repeat_streak = 0

            # If a token repeats too many times in a row, stop early.
            if repeat_streak >= 2:
                break

            cleaned.append(tok)
            prev = tok

        text = " ".join(cleaned)

        # Remove immediate repeated n-grams like "red dress red dress"
        # Match up to 4 words repeating
        for n in range(4, 0, -1):
            pattern = r"\b" + r"\s+".join([r"(\w+)"] * n) + r"\s+" + r"\s+".join([r"\\" + str(i+1) for i in range(n)]) + r"\b"
            text = re.sub(pattern, r" ".join([r"\\" + str(i+1) for i in range(n)]), text)

        # Remove common non-descriptive prefixes/suffixes that add noise
        artifacts = [
            "a fashion photo of", "a photo of", "product shot of", "close up of",
            "studio shot of", "isolated on white", "on a white background",
            "looking at camera", "standing in front of", "posing for",
            "high quality", "professional", "top view", "side view",
        ]
        for art in artifacts:
            text = text.replace(art, "").strip()

        # Clean up any resulting double spaces
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @staticmethod
    def _looks_degenerate(caption: str) -> bool:
        """Detect low-quality captions with heavy repetition or too little content."""
        if not caption:
            return True

        tokens = caption.split()
        if len(tokens) < 3:
            return True

        # Check unique ratio (too low means repetition)
        unique_ratio = len(set(tokens)) / max(len(tokens), 1)
        if unique_ratio < 0.4:  # Slightly more lenient than 0.5
            return True

        # Flag single-token spam like "hua hua hua ..."
        max_count = max(tokens.count(t) for t in set(tokens))
        if max_count >= 3:
            return True

        return False

    async def generate_caption(
        self,
        image: Image.Image,
        max_length: int = 40,  # Increased for more descriptive captions
        min_length: int = 8,   # Increased for substance
    ) -> str:
        """Generate a high-quality fashion-oriented caption from an input image."""

        def _generate(prompt: Optional[str] = None) -> str:
            if self.processor is None or self.model is None:
                return ""
            if prompt:
                inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.device)
            else:
                inputs = self.processor(images=image, return_tensors="pt").to(self.device)

            with torch.no_grad():
                # Optimized for 100% accuracy (best effort) using Beam Search with penalties
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    min_length=min_length,
                    num_beams=8,               # Increased for better search
                    do_sample=False,           # Deterministic for "accuracy"
                    no_repeat_ngram_size=2,    # Stronger repetition prevention
                    repetition_penalty=1.5,    # Increased penalty
                    length_penalty=1.0,
                    early_stopping=True,
                )
            caption = self.processor.decode(output[0], skip_special_tokens=True)
            return self._cleanup_caption(caption)

        def _run() -> str:
            # First pass: conditioned prompt to anchor fashion semantics.
            # "a fashion photo of" usually yields better e-commerce descriptions.
            caption = _generate(prompt="a fashion photo of")
            if not self._looks_degenerate(caption):
                # Clean up the prompt from the output if it remains
                if caption.startswith("a fashion photo of "):
                    caption = caption[len("a fashion photo of "):]
                return caption

            # Second pass: generic photo prompt
            fallback = _generate(prompt="a photo of")
            if not self._looks_degenerate(fallback):
                if fallback.startswith("a photo of "):
                    fallback = fallback[len("a photo of "):]
                return fallback

            # Third pass: pure captioning (no prompt)
            raw_caption = _generate(prompt=None)
            return raw_caption or fallback or caption

        try:
            await self._ensure_model_loaded()
            caption = await asyncio.to_thread(_run)
            logger.info("BLIP caption generated: '%s'", caption)
            return caption
        except Exception as e:
            logger.warning("BLIP caption generation failed: %s", e)
            return ""


# Fix: Export instance, not the class, for easier use
blip_caption_service = BlipCaptionService()
