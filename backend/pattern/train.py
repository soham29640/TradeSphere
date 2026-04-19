import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from torch.optim.lr_scheduler import StepLR
from torch.utils.data import random_split

from chart_dataset import ChartPatternDataset, get_train_transform, get_val_transform, get_dataloader
from model import ChartPatternCNN


# ── Config ────────────────────────────────────────────────────────────────────
IMAGE_DIR   = "data/processed/pattern/train_images"
LABEL_CSV   = "data/processed/pattern/train_labels.csv"
SAVE_PATH   = "models/pattern/chart_pattern_model.pth"
NUM_CLASSES = 20
BATCH_SIZE  = 32
NUM_EPOCHS  = 25
LR          = 1e-3
VAL_SPLIT   = 0.1          # 10 % held out for validation
THRESHOLD   = 0.5          # sigmoid threshold for binary prediction
PATIENCE    = 5            # early-stopping patience (epochs)
# ─────────────────────────────────────────────────────────────────────────────


def compute_pos_weights(label_csv: str, device: torch.device) -> torch.Tensor:
    """Inverse-frequency class weights for BCEWithLogitsLoss pos_weight."""
    df = pd.read_csv(label_csv)
    label_matrix = df.drop(columns=["Filename"], errors="ignore").to_numpy(dtype=np.float32)
    label_tensor = torch.tensor(label_matrix)

    pos_counts = label_tensor.sum(dim=0).clamp(min=1e-6)
    neg_counts = label_tensor.shape[0] - pos_counts
    pos_weight = (neg_counts / pos_counts).to(device)
    return pos_weight


def run_epoch(model, loader, criterion, optimizer, device, is_train: bool):
    model.train() if is_train else model.eval()

    total_loss = 0.0
    total_exact = 0
    n_samples = 0

    ctx = torch.enable_grad() if is_train else torch.no_grad()
    with ctx:
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            if is_train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            bs = images.size(0)
            total_loss += loss.item() * bs
            n_samples += bs

            predicted = (torch.sigmoid(outputs) > THRESHOLD).float()
            # Exact (all-label) match accuracy
            total_exact += (predicted == labels).all(dim=1).sum().item()

    avg_loss = total_loss / n_samples
    accuracy = 100.0 * total_exact / n_samples
    return avg_loss, accuracy


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # ── Build datasets ────────────────────────────────────────────────────────
    full_dataset = ChartPatternDataset(IMAGE_DIR, LABEL_CSV, transform=None)
    n_val   = max(1, int(len(full_dataset) * VAL_SPLIT))
    n_train = len(full_dataset) - n_val

    train_subset, val_subset = random_split(
        full_dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(42)
    )

    # Apply different transforms per split
    train_subset.dataset.transform = get_train_transform()   # augmented
    val_subset.dataset.transform   = get_val_transform()     # clean

    train_loader = torch.utils.data.DataLoader(
        train_subset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True
    )
    val_loader = torch.utils.data.DataLoader(
        val_subset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True
    )
    print(f"Train samples: {n_train} | Val samples: {n_val}")

    # ── Model / loss / optimiser ──────────────────────────────────────────────
    pos_weight = compute_pos_weights(LABEL_CSV, device)
    model      = ChartPatternCNN(num_classes=NUM_CLASSES).to(device)
    criterion  = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer  = optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler  = StepLR(optimizer, step_size=10, gamma=0.5)

    # ── Training loop ─────────────────────────────────────────────────────────
    best_val_loss   = float("inf")
    patience_count  = 0

    for epoch in range(1, NUM_EPOCHS + 1):
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device, is_train=True)
        val_loss,   val_acc   = run_epoch(model, val_loader,   criterion, optimizer, device, is_train=False)
        scheduler.step()

        print(
            f"Epoch {epoch:>2}/{NUM_EPOCHS} | "
            f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.2f}% | "
            f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.2f}%"
        )

        # ── Checkpoint best model ─────────────────────────────────────────────
        if val_loss < best_val_loss:
            best_val_loss  = val_loss
            patience_count = 0
            os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
            torch.save(model.state_dict(), SAVE_PATH)
            print(f"  ✔ Best model saved (val_loss={best_val_loss:.4f})")
        else:
            patience_count += 1
            if patience_count >= PATIENCE:
                print(f"  Early stopping triggered after {PATIENCE} epochs without improvement.")
                break

    print(f"\nTraining complete. Best model saved to '{SAVE_PATH}'.")


if __name__ == "__main__":
    main()