# HEMOVISION AI – AI-Assisted Anemia Screening (Research Prototype)

## Project Overview
Patients register, log in, capture a lower-eyelid (conjunctiva) image with the laptop webcam, and receive an **anemia screening risk** estimate.
Results are stored in SQL, shown as a trend line graph, and exportable as a PDF. **Not a medical diagnosis** – confirmatory hemoglobin/CBC testing is required.

## Features
Register/login (hashed passwords, sessions, CSRF) · webcam capture · OpenCV preprocessing · GLCM/radiomics features · Random Forest inference ·
SQL history · Chart.js line trend · previous-vs-current comparison · general wellness tips for higher risk · per-screening PDF · profile + password change.

## Technology Stack
Flask, Flask-SQLAlchemy (SQLite; set `DATABASE_URL` for MySQL/PostgreSQL), OpenCV, NumPy, scikit-image, scikit-learn, pandas, joblib, ReportLab, Bootstrap 5, Chart.js.

## Folder Structure
`app.py config.py models.py generate_synthetic_data.py train_model.py` · `utils/` (preprocessing, feature_extraction, pdf_report) · `templates/` · `static/css|js` ·
`data/` (synthetic CSV) · `models/` (anemia_model.pkl, model_info.json) · `instance/` (hemovision.db, secret_key, uploads/).

## Installation
```
python -m venv venv
venv\Scripts\activate          (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
PowerShell blocked? Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.

## Database Setup
Tables are created automatically on first start (`db.create_all()`); no manual SQL. File: `instance/hemovision.db`.

## Generate Data, Train, Run
```
python generate_synthetic_data.py
python train_model.py
python app.py
```
Open http://127.0.0.1:5000. Without `models/anemia_model.pkl` the app runs in **DEMO MODE** (clearly labelled sample output).

## Camera Permission
Use Chrome/Edge at `http://127.0.0.1:5000`; allow the camera prompt. Close Zoom/Teams if the camera is in use. Windows: Settings → Privacy → Camera.

## PDF Reports
`/report/<id>` builds the PDF from SQL data; ownership is verified (`screening.user_id == current user`), otherwise 404.

## Image Storage & Privacy
Images are saved in `instance/uploads/` (not publicly served) as `u<user>_s<screening>_<random>.jpg` and shown only via an authenticated route.
To disable storage, skip the `cv2.imwrite` line in `/analyze`; to encrypt, encrypt bytes (e.g. `cryptography.Fernet`) before writing.

## Production Notes
CSRF is implemented for forms and `/analyze`. For deployment also add: HTTPS (`HTTPS=1` enables secure cookies), `SECRET_KEY` and `DATABASE_URL` environment variables, rate limiting on login, real password-reset email, a production WSGI server.

## Limitations
Synthetic training data (artificial relationships; no clinical validation) · controlled central ROI, no automatic conjunctiva segmentation yet ·
sensitive to lighting and camera differences · synthetic feature ranges may not match real webcam images, so live predictions are not meaningful · not a replacement for laboratory testing.

## Future Work
Real clinically approved dataset · automatic conjunctiva segmentation · camera colour calibration · lighting normalization · deep learning comparison ·
hemoglobin regression · model calibration · external clinical validation · explainable AI · offline smartphone deployment · encryption · cloud database.
