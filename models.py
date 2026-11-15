from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    blood_group = db.Column(db.String(4), default="")
    created_at = db.Column(db.DateTime, default=datetime.now)
    screenings = db.relationship("Screening", backref="user", cascade="all, delete-orphan", order_by="Screening.id")

class Screening(db.Model):
    __tablename__ = "screenings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    screening_date = db.Column(db.DateTime, default=datetime.now, index=True)
    prediction = db.Column(db.String(40), nullable=False)
    risk_level = db.Column(db.String(40), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)      # probability of higher screening risk (0-1), used for the trend graph
    confidence = db.Column(db.Float, nullable=False)
    mean_intensity = db.Column(db.Float); std_intensity = db.Column(db.Float); contrast = db.Column(db.Float)
    homogeneity = db.Column(db.Float); energy = db.Column(db.Float); correlation = db.Column(db.Float); entropy = db.Column(db.Float)
    model_mode = db.Column(db.String(40))
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def is_higher(self): return self.prediction.startswith("Possible")
    @property
    def features(self):
        return {k: getattr(self, k) for k in ["mean_intensity", "std_intensity", "contrast", "homogeneity", "energy", "correlation", "entropy"]}
