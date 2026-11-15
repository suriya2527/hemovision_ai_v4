"""Train the prototype classifier on the SYNTHETIC dataset (not clinically validated)."""
import json, os
import joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from utils.feature_extraction import MODEL_FEATURES   # same feature order as app.py

df = pd.read_csv("data/anemia_synthetic_dataset.csv")
assert not df.isnull().any().any(), "Dataset has missing values"
print("No missing values. Rows:", len(df))
X, y = df[MODEL_FEATURES], df["label"]                 # label is NOT among the inputs
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

def evaluate(name, m):
    m.fit(Xtr, ytr); pred, prob = m.predict(Xte), m.predict_proba(Xte)[:, 1]
    r = {"accuracy": accuracy_score(yte, pred), "precision": precision_score(yte, pred), "recall": recall_score(yte, pred),
         "f1": f1_score(yte, pred), "roc_auc": roc_auc_score(yte, prob)}
    print(f"\n[{name}] " + "  ".join(f"{k}={v:.3f}" for k, v in r.items()))
    return {k: round(float(v), 4) for k, v in r.items()}, pred

rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=42, class_weight="balanced")
metrics, pred = evaluate("RandomForest (primary)", rf)
print("Confusion matrix [[TN FP] [FN TP]]:\n", confusion_matrix(yte, pred))
evaluate("SVM (comparison)", make_pipeline(StandardScaler(), SVC(probability=True, random_state=42)))
try:
    from xgboost import XGBClassifier; evaluate("XGBoost (comparison)", XGBClassifier(n_estimators=200, eval_metric="logloss"))
except ImportError:
    print("\n(XGBoost not installed - skipped optional comparison)")
print("Model training completed")
os.makedirs("models", exist_ok=True)
joblib.dump(rf, "models/anemia_model.pkl")
json.dump({"trained_on": "synthetic", "features": MODEL_FEATURES, "metrics": metrics,
           "note": "Synthetic-data prototype model - not clinically validated."}, open("models/model_info.json", "w"), indent=1)
print("Model saved successfully: models/anemia_model.pkl")
