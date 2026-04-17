import torch.nn as nn
from torchvision import models

class ChartPatternCNN(nn.Module):
    def __init__(self, num_classes=20):
        super(ChartPatternCNN, self).__init__()
        self.model = models.resnet18(pretrained=True)

        in_features = self.model.fc.in_features
        self.model.fc = nn.Linear(in_features, num_classes)

    def forward(self, x):
        return self.model(x)

    def save_model(self, path):
        torch.save(self.state_dict(), path)

    def load_model(self, path, device):
        self.load_state_dict(torch.load(path, map_location=device))
        self.eval()
