import os
import pandas as pd
from PIL import Image, UnidentifiedImageError
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms

class ChartPatternDataset(Dataset):
    def __init__(self, image_dir, label_csv, transform=None):
        self.image_dir = image_dir
        self.labels_df = pd.read_csv(label_csv)
        self.transform = transform

    def __len__(self):
        return len(self.labels_df)

    def __getitem__(self, idx):
        row = self.labels_df.iloc[idx]
        filename = str(row["Filename"])  
        label = row.iloc[1:].to_numpy(dtype='float32')

        image_path = os.path.join(self.image_dir, filename)
        try:
            image = Image.open(image_path).convert("RGB")
        except (FileNotFoundError, UnidentifiedImageError) as e:
            raise RuntimeError(f"Failed to load image: {image_path}. Error: {e}")

        if self.transform:
            image = self.transform(image)

        return image, label

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=5),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])


image_dir = "data/processed/train_images"
label_csv = "data/processed/train_labels.csv"

dataset = ChartPatternDataset(image_dir=image_dir, label_csv=label_csv, transform=transform)
train_loader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=0)  # Use 0 for Windows compatibility
