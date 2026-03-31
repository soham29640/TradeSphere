import torch
from PIL import Image
import torchvision.transforms as transforms

async def detect_pattern(file):
    image = Image.open(file.file).convert("RGB")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])

    input_tensor = transform(image).unsqueeze(0)

    # dummy output for now (replace with model)
    return {
        "pattern": "Head & Shoulders",
        "confidence": 92.5
    }