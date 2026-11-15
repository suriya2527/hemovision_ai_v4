"""First-order + GLCM texture (radiomics-style) features."""
import numpy as np
from skimage.feature import graycomatrix, graycoprops

# The order MUST match the order used when training anemia_model.pkl
FEATURE_ORDER = ["mean_intensity", "std_intensity", "contrast", "homogeneity",
                 "energy", "correlation", "entropy"]


def extract_features(gray):
    """gray: 2-D uint8 array (preprocessed ROI). Returns dict of floats."""
    # GLCM: distance 1, four directions, averaged for rotation robustness
    glcm = graycomatrix(gray, distances=[1],
                        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
                        levels=256, symmetric=True, normed=True)
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    p = hist / hist.sum()
    p = p[p > 0]
    feats = {
        "mean_intensity": float(gray.mean()),
        "std_intensity": float(gray.std()),
        "contrast": float(graycoprops(glcm, "contrast").mean()),
        "homogeneity": float(graycoprops(glcm, "homogeneity").mean()),
        "energy": float(graycoprops(glcm, "energy").mean()),
        "correlation": float(graycoprops(glcm, "correlation").mean()),
        "entropy": float(-(p * np.log2(p)).sum()),  # Shannon entropy
    }
    return {k: round(v, 4) for k, v in feats.items()}

# Single source of truth for feature order: used by train_model.py AND app.py
IMAGE_FEATURES = FEATURE_ORDER
MODEL_FEATURES = ["age", "gender_encoded"] + IMAGE_FEATURES
