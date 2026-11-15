import os, secrets
BASE = os.path.dirname(os.path.abspath(__file__))
INSTANCE = os.path.join(BASE, "instance"); os.makedirs(INSTANCE, exist_ok=True)

def _secret():  # env var in production; otherwise a random key persisted once in instance/
    if os.environ.get("SECRET_KEY"): return os.environ["SECRET_KEY"]
    p = os.path.join(INSTANCE, "secret_key")
    if not os.path.exists(p): open(p, "w").write(secrets.token_hex(32))
    return open(p).read().strip()

class Config:
    SECRET_KEY = _secret()
    # Swap for MySQL/PostgreSQL via DATABASE_URL, e.g. postgresql+psycopg2://user:pw@host/db
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///hemovision.db")  # -> instance/hemovision.db
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("HTTPS", "0") == "1"   # set HTTPS=1 behind HTTPS
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    UPLOAD_DIR = os.path.join(INSTANCE, "uploads")   # outside /static so images are never publicly served
    MODEL_PATH = os.path.join(BASE, "models", "anemia_model.pkl")
    INFO_PATH = os.path.join(BASE, "models", "model_info.json")
