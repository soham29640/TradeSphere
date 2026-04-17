import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from torch.optim.lr_scheduler import StepLR
from chart_dataset import train_loader
from model import ChartPatternCNN

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    df = pd.read_csv("data/processed/train_labels.csv")
    label_matrix = df.drop(columns=["Filename"], errors="ignore").to_numpy()
    label_matrix = label_matrix.astype(np.float32)
    label_tensor = torch.tensor(label_matrix, dtype=torch.float)

    pos_counts = label_tensor.sum(dim=0)
    total_samples = label_tensor.shape[0]
    class_weights = total_samples / (pos_counts + 1e-6)
    class_weights = class_weights / class_weights.max()

    model = ChartPatternCNN(num_classes=20).to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=class_weights.to(device))
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = StepLR(optimizer, step_size=10, gamma=0.5)

    num_epochs = 25

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0
        total = 0
        correct = 0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device).float()

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * images.size(0)
            total += images.size(0)

            predicted = (torch.sigmoid(outputs) > 0.5).float()
            correct += (predicted == labels).all(dim=1).sum().item()

        avg_loss = total_loss / total
        accuracy = 100 * correct / total
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}%")

        scheduler.step()

    save_path = "models/chart_pattern_model.pth"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"Model saved to {save_path}")

if __name__ == "__main__":
    main()
