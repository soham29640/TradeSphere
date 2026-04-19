import torch.nn as nn
from torchvision import models
 
 
class ChartPatternCNN(nn.Module):
    def __init__(self, num_classes=20, dropout=0.3):
        super().__init__()
 
        self.model = models.resnet18(weights="DEFAULT")
 
        in_features = self.model.fc.in_features
        # Added dropout before final layer to reduce overfitting
        self.model.fc = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes)
        )
 
    def forward(self, x):
        return self.model(x)
