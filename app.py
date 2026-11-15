"""HEMOVISION AI - Flask app (academic research prototype; NOT a diagnostic tool)."""
import base64, hashlib, hmac, io, json, os, random, re, secrets, uuid
from datetime import datetime
from functools import wraps
import cv2, joblib, numpy as np, pandas as pd
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import User, Screening, db
from utils.preprocessing import decode_image, preprocess
from utils.feature_extraction import IMAGE_FEATURES, MODEL_FEATURES, extract_features
from utils.pdf_report import TIPS, TIPS_NOTE, build_pdf

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
with app.app_context():
    db.create_all()          # creates tables on first start

GENDERS, BLOODS = {"Male": 0, "Female": 1, "Other": 2}, {"", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


# ---------- ML model (MODEL MODE if file exists, else DEMO MODE) ----------
def load_model():
    if os.path.exists(Config.MODEL_PATH):
        try:
            info = json.load(open(Config.INFO_PATH)) if os.path.exists(Config.INFO_PATH) else {}
            return joblib.load(Config.MODEL_PATH), info
        except Exception as e:
            print("[WARN] model load failed, using DEMO MODE:", e)
    return None, {}

MODEL, INFO = load_model()
MODEL_LABEL = "Demo Mode" if MODEL is None else ("Synthetic ML Prototype" if INFO.get("trained_on") == "synthetic" else "ML Model")
MODEL_STATUS = {"Demo Mode": "DEMO MODE · ML model not connected",
                "Synthetic ML Prototype": "Prototype ML model"}.get(MODEL_LABEL, "MODEL MODE")


def risk_level(score):
    return "Low Screening Risk" if score < 0.35 else "Moderate Screening Risk" if score < 0.6 else "Higher Screening Risk"


def classify(age, gender, feats, seed):
    if MODEL is None:   # DEMO: clearly labelled sample output, not a prediction
        score = round(random.Random(hashlib.md5(seed).hexdigest()).uniform(0.1, 0.9), 3)
    else:
        row = {"age": age, "gender_encoded": GENDERS.get(gender, 2), **feats}
        X = pd.DataFrame([row])[MODEL_FEATURES]            # same feature order as train_model.py
        score = float(MODEL.predict_proba(X)[0][list(MODEL.classes_).index(1)])
    return score, ("Possible Anemia Risk" if score >= 0.5 else "Low Anemia Risk"), round(max(score, 1 - score), 3)


def compare(cur, prev):
    if not prev: return None
    c, p = round(cur.risk_score * 100), round(prev.risk_score * 100); d = c - p
    msg = (f"Screening risk decreased by {abs(d)} percentage points compared with the previous screening. Screening risk trend improved." if d < 0
           else f"Screening risk increased by {d} percentage points compared with the previous record." if d > 0
           else "Screening risk is unchanged compared with the previous record.")
    return {"previous": p, "current": c, "change": d, "message": msg}


def previous_of(s):
    return Screening.query.filter(Screening.user_id == s.user_id, Screening.id < s.id).order_by(Screening.id.desc()).first()


# ---------- session, CSRF, auth ----------
@app.before_request
def before():
    g.user = db.session.get(User, session["uid"]) if "uid" in session else None
    session.setdefault("csrf", secrets.token_hex(16))
    if request.method == "POST":
        tok = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        if not hmac.compare_digest(tok, session["csrf"]): abort(400)


@app.context_processor
def ctx():
    return {"user": g.user, "csrf_token": session.get("csrf", ""), "model_status": MODEL_STATUS}


def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not g.user:
            flash("Please log in to continue.", "info"); return redirect(url_for("login"))
        return f(*a, **k)
    return w


def own_screening(sid):   # a patient can only ever reach their own records (404 hides existence)
    s = db.session.get(Screening, sid)
    if not s or s.user_id != g.user.id: abort(404)
    return s


def validate_profile(f, new=True):
    e, out = [], {}
    out["full_name"] = f.get("full_name", "").strip()
    if not re.fullmatch(r"[\w .'\-]{2,80}", out["full_name"]): e.append("Enter a valid full name.")
    try:
        out["age"] = int(f.get("age", "")); assert 1 <= out["age"] <= 120
    except Exception: e.append("Enter a valid age (1-120).")
    out["gender"] = f.get("gender", "")
    if out["gender"] not in GENDERS: e.append("Select a gender.")
    out["phone"] = f.get("phone", "").strip()
    if not re.fullmatch(r"\+?\d{7,15}", out["phone"]): e.append("Enter a valid phone number (7-15 digits).")
    out["blood_group"] = f.get("blood_group", "")
    if out["blood_group"] not in BLOODS: e.append("Invalid blood group.")
    return out, e


def check_password(pw, pw2):
    if pw != pw2: return "Passwords do not match."
    if len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw): return "Password must be 8+ characters with letters and numbers."


@app.route("/")
def index():
    return redirect(url_for("dashboard" if g.user else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form; data, errs = validate_profile(f)
        email, uname = f.get("email", "").strip().lower(), f.get("username", "").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 120: errs.append("Enter a valid email.")
        if not re.fullmatch(r"[a-z0-9_.]{3,30}", uname): errs.append("Username: 3-30 letters, numbers, . or _")
        pe = check_password(f.get("password", ""), f.get("confirm", ""))
        if pe: errs.append(pe)
        if not errs and User.query.filter((User.email == email) | (User.username == uname)).first():
            errs.append("Email or username is already registered.")
        if errs:
            for m in errs: flash(m, "error")
            return render_template("register.html", form=f)
        db.session.add(User(email=email, username=uname, password_hash=generate_password_hash(f["password"]), **data))
        db.session.commit(); flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user: return redirect(url_for("dashboard"))
    if request.method == "POST":
        ident = request.form.get("identifier", "").strip().lower()
        u = User.query.filter((User.email == ident) | (User.username == ident)).first()
        if u and check_password_hash(u.password_hash, request.form.get("password", "")):
            session.clear(); session["uid"] = u.id   # new session on login (prevents fixation)
            return redirect(url_for("dashboard"))
        flash("Invalid login details.", "error")
    return render_template("login.html")


@app.route("/forgot")
def forgot():
    flash("Password reset by email is not available in this prototype.", "info"); return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear(); flash("You have been logged out.", "info"); return redirect(url_for("login"))


# ---------- pages ----------
@app.route("/dashboard")
@login_required
def dashboard():
    mine = Screening.query.filter_by(user_id=g.user.id)
    latest = mine.order_by(Screening.id.desc()).first()
    return render_template("dashboard.html", latest=latest, total=mine.count(),
                           recent=mine.order_by(Screening.id.desc()).limit(5).all())


@app.route("/screening")
@login_required
def screening():
    return render_template("screening.html")


@app.route("/history")
@login_required
def history():
    page = request.args.get("page", 1, type=int)
    p = Screening.query.filter_by(user_id=g.user.id).order_by(Screening.id.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template("history.html", p=p)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        if request.form.get("action") == "password":
            f = request.form
            if not check_password_hash(g.user.password_hash, f.get("current", "")): flash("Current password is incorrect.", "error")
            elif check_password(f.get("password", ""), f.get("confirm", "")): flash(check_password(f.get("password", ""), f.get("confirm", "")), "error")
            else:
                g.user.password_hash = generate_password_hash(f["password"]); db.session.commit(); flash("Password updated.", "success")
        else:
            data, errs = validate_profile(request.form)
            if errs: [flash(m, "error") for m in errs]
            else:
                for k, v in data.items(): setattr(g.user, k, v)
                db.session.commit(); flash("Profile updated.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html")


@app.route("/result/<int:sid>")
@login_required
def result(sid):
    s = own_screening(sid)
    return render_template("result.html", s=s, cmp=compare(s, previous_of(s)), tips=TIPS, tips_note=TIPS_NOTE)


@app.route("/image/<int:sid>")
@login_required
def image(sid):
    s = own_screening(sid)
    path = os.path.join(Config.UPLOAD_DIR, os.path.basename(s.image_path or ""))
    if not s.image_path or not os.path.exists(path): abort(404)
    return send_file(path, mimetype="image/jpeg")


@app.route("/image/<int:sid>/<kind>")
@login_required
def image_view(sid, kind):
    """Grayscale / CLAHE-enhanced views of the patient's own captured image (computed on demand, same pipeline as analysis)."""
    s = own_screening(sid)
    if kind not in ("gray", "enhanced"): abort(404)
    path = os.path.join(Config.UPLOAD_DIR, os.path.basename(s.image_path or ""))
    img = cv2.imread(path) if s.image_path and os.path.exists(path) else None
    if img is None: abort(404)
    enhanced, resized = preprocess(img)
    out = enhanced if kind == "enhanced" else cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    ok, buf = cv2.imencode(".png", out)
    return send_file(io.BytesIO(buf.tobytes()), mimetype="image/png")


@app.route("/report/<int:sid>")
@login_required
def report(sid):
    s = own_screening(sid)                                  # verifies screening.user_id == current user
    name = re.sub(r"\W+", "_", g.user.full_name).strip("_") or "Patient"
    return send_file(build_pdf(g.user, s, compare(s, previous_of(s))), mimetype="application/pdf", as_attachment=True,
                     download_name=f"HemoVision_Report_{name}_{s.screening_date:%Y-%m-%d}.pdf")


@app.route("/api/trend")
@login_required
def api_trend():
    rows = Screening.query.filter_by(user_id=g.user.id).order_by(Screening.screening_date, Screening.id).all()
    return jsonify({"points": [{"id": r.id, "date": r.screening_date.strftime("%d %b %H:%M"), "risk": round(r.risk_score * 100)} for r in rows],
                    "comparison": compare(rows[-1], rows[-2]) if len(rows) > 1 else None})


# ---------- analysis ----------
@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    try:
        b64 = (request.get_json(silent=True) or {}).get("image", "")
        if not re.match(r"data:image/(jpeg|png);base64,", b64): return jsonify(error="Please capture an image."), 400
        raw = base64.b64decode(b64.split(",", 1)[1], validate=True)
        img = decode_image(raw)                               # decoding also validates it is a real image
        if img is None or min(img.shape[:2]) < 64: return jsonify(error="Unable to analyze image."), 400
        enhanced, _ = preprocess(img)
        feats = extract_features(enhanced)
        score, pred, conf = classify(g.user.age, g.user.gender, feats, raw)
        s = Screening(user_id=g.user.id, prediction=pred, risk_level=risk_level(score), risk_score=round(score, 4),
                      confidence=conf, model_mode=MODEL_LABEL, screening_date=datetime.now(), **feats)
        db.session.add(s); db.session.flush()                 # get id for a unique filename
        fn = f"u{g.user.id}_s{s.id}_{uuid.uuid4().hex[:8]}.jpg"
        cv2.imwrite(os.path.join(Config.UPLOAD_DIR, fn), img); s.image_path = fn   # re-encoded JPEG; never overwrites
        db.session.commit()
        return jsonify(screening_id=s.id, prediction=pred, risk_level=s.risk_level, confidence=conf, model_mode=MODEL_LABEL,
                       features=feats, screening_date=s.screening_date.isoformat(), redirect=url_for("result", sid=s.id))
    except Exception as e:
        db.session.rollback(); app.logger.exception(e)       # details only in the server log
        return jsonify(error="Unable to analyze image."), 500


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def err(e):
    msg = {400: "Your session expired. Please reload and try again.", 404: "Page not found."}.get(getattr(e, "code", 500), "Something went wrong.")
    return render_template("error.html", msg=msg), getattr(e, "code", 500)


if __name__ == "__main__":
    print("STATUS:", MODEL_STATUS)
    app.run(host="127.0.0.1", port=5000, debug=False)
