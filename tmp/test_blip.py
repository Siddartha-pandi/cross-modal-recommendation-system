
import asyncio
import sys
import os
from PIL import Image

# Add backend to path
sys.path.append(os.path.abspath("s:/Siddu/Final Year/cross-modal-recommendation-system/backend"))

from app.services.blip_caption import BlipCaptionService

async def test_blip():
    service = BlipCaptionService()
    img_path = "s:/Siddu/Final Year/cross-modal-recommendation-system/data/images/product_1.jpg"
    if not os.path.exists(img_path):
        print(f"Image not found: {img_path}")
        return
    
    image = Image.open(img_path).convert("RGB")
    caption = await service.generate_caption(image)
    print(f"Generated caption: {caption}")

if __name__ == "__main__":
    asyncio.run(test_blip())
