import torch
import torch.nn as nn
import numpy as np
import os

# ===== НАСТРОЙКИ =====
EMB_PATH = "embeddings/chunk_embeddings.npy"
OUT_DIR = "embeddings_reduced"

INPUT_DIM = 768
LATENT_DIM = 128
EPOCHS = 20
BATCH_SIZE = 256
LR = 1e-3
# ====================

os.makedirs(OUT_DIR, exist_ok=True)

X = torch.tensor(np.load(EMB_PATH), dtype=torch.float32)

class AutoEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(INPUT_DIM, 512),
            nn.ReLU(),
            nn.Linear(512, LATENT_DIM)
        )
        self.decoder = nn.Sequential(
            nn.Linear(LATENT_DIM, 512),
            nn.ReLU(),
            nn.Linear(512, INPUT_DIM)
        )

    def forward(self, x):
        z = self.encoder(x)
        return z, self.decoder(z)

model = AutoEncoder()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
loss_fn = nn.MSELoss()

dataset = torch.utils.data.TensorDataset(X)
loader = torch.utils.data.DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

for epoch in range(EPOCHS):
    total_loss = 0
    for (batch,) in loader:
        z, recon = model(batch)
        loss = loss_fn(recon, batch)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1}: loss={total_loss/len(loader):.6f}")

with torch.no_grad():
    Z = model.encoder(X).numpy()

np.save(
    os.path.join(OUT_DIR, f"chunk_embeddings_autoenc_{LATENT_DIM}.npy"),
    Z
)

print("Autoencoder reduced shape:", Z.shape)
