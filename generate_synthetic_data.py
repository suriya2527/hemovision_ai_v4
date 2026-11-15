"""Synthetic dataset for software / ML-pipeline demonstration ONLY.
This dataset is synthetic and does not represent clinically validated patient data (not hospital records).
The feature-label relationships below are ARTIFICIAL relationships created for software and ML pipeline demonstration,
not medically established rules. The label is drawn first (from age/gender-dependent probability); features are then
sampled from overlapping class-conditional distributions, so the label is never a copy or function of the inputs."""
import os
import numpy as np, pandas as pd

SEED, N = 42, 4000
rng = np.random.default_rng(SEED)                      # fixed seed -> reproducible
age = rng.integers(5, 80, N)
gender = rng.choice([0, 1, 2], N, p=[0.48, 0.48, 0.04])   # 0 Male, 1 Female, 2 Other
p = np.clip(0.33 + 0.10 * (gender == 1) + 0.0015 * (age - 40), 0.05, 0.9)
y = (rng.random(N) < p).astype(int)                    # 0 = lower screening risk, 1 = higher anemia screening risk

def g(m0, shift, sd): return rng.normal(m0 + shift * y, sd)
df = pd.DataFrame({
    "age": age, "gender_encoded": gender,
    "mean_intensity": np.clip(g(125, 22, 18), 60, 230),
    "std_intensity": np.clip(g(44, -8, 7), 10, 80),
    "contrast": np.clip(g(140, -35, 38), 10, 400),
    "homogeneity": np.clip(g(0.26, 0.05, 0.05), 0.05, 0.6),
    "energy": np.clip(g(0.018, 0.004, 0.005), 0.003, 0.06),
    "correlation": np.clip(g(0.95, -0.015, 0.02), 0.7, 0.995),
    "entropy": np.clip(g(7.1, -0.2, 0.25), 5.5, 7.9),
    "label": y}).round(4)
os.makedirs("data", exist_ok=True)
df.to_csv("data/anemia_synthetic_dataset.csv", index=False)
print(f"Dataset generated successfully: {df.shape[0]} rows -> data/anemia_synthetic_dataset.csv")
print("Class balance:", df.label.value_counts().to_dict(), "| SYNTHETIC data - not clinically validated")
