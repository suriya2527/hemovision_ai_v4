"""Image preprocessing pipeline (OpenCV)."""
import cv2
import numpy as np

SIZE = 224


def decode_image(raw_bytes):
    """Decode raw image bytes to a BGR OpenCV image. Returns None if invalid."""
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    if arr.size == 0:
        return None
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def select_roi(img, fraction=0.6):
    """Option A: the central area of the image is used as the conjunctiva ROI.
    The user positions the lower eyelid inside the on-screen guide before capture.
    NOTE: Automatic conjunctiva segmentation is planned for the final implementation."""
    h, w = img.shape[:2]
    ch, cw = int(h * fraction), int(w * fraction)
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    return img[y0:y0 + ch, x0:x0 + cw]


def preprocess(img):
    """ROI -> resize 224x224 -> grayscale -> Gaussian blur -> CLAHE.
    Returns the enhanced grayscale image (uint8) and the resized colour ROI."""
    roi = select_roi(img)
    resized = cv2.resize(roi, (SIZE, SIZE), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)
    return enhanced, resized
