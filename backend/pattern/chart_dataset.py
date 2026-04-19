import os
import pandas as pd
from PIL import Image, UnidentifiedImageError
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torch


class ChartPatternDataset(Dataset):
    def __init__(self, image_dir, label_csv, transform=None):
        self.image_dir = image_dir
        self.labels_df = pd.read_csv(label_csv)
        self.transform = transform

        # Validate that label columns exist beyond "Filename"
        if len(self.labels_df.columns) < 2:
            raise ValueError("Label CSV must have at least a 'Filename' column and one label column.")

    def __len__(self):
        return len(self.labels_df)

    def __getitem__(self, idx):
        row = self.labels_df.iloc[idx]
        filename = str(row["Filename"])
        label = torch.tensor(row.iloc[1:].values.astype("float32"), dtype=torch.float32)

        image_path = os.path.join(self.image_dir, filename)

        try:
            image = Image.open(image_path).convert("RGB")
        except (FileNotFoundError, UnidentifiedImageError) as e:
            raise RuntimeError(f"Error loading {image_path}: {e}")

        if self.transform:
            image = self.transform(image)

        return image, label


def get_train_transform():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(5),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])


def get_val_transform():
    """No augmentation for validation — only resize and normalize."""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])


def get_dataloader(image_dir, label_csv, batch_size=32, is_train=True, num_workers=2):
    """
    Returns a DataLoader for the given split.

    Args:
        image_dir  : Path to folder containing chart images.
        label_csv  : Path to the CSV with multi-label annotations.
        batch_size : Samples per batch.
        is_train   : If True, applies augmentation; otherwise uses val transform.
        num_workers: Number of parallel workers for loading.
    """
    transform = get_train_transform() if is_train else get_val_transform()
    dataset = ChartPatternDataset(image_dir, label_csv, transform)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=is_train,
        num_workers=num_workers,
        pin_memory=True
    )