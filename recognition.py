import torch
import torch.nn as nn
import numpy as np
from torchvision import transforms

class EmbeddingNet(nn.Module):
    def __init__(self, embedding_dim=128):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.fc = nn.Linear(128 * 12 * 12, embedding_dim)

    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = EmbeddingNet()
model.load_state_dict(torch.load("best_model.pt", map_location=device))
model.eval()
model = model.to(device)

transform = transforms.Compose([
    transforms.Resize((100, 100)),
    transforms.ToTensor(),
])

print("Model loaded. Device:", device)

from PIL import Image

def embedding_from_image(image):
    image_tensor = transform(image.convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model(image_tensor)
    return embedding.cpu().numpy()[0]

def get_embedding(image_path):
    return embedding_from_image(Image.open(image_path))
