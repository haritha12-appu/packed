import cv2
import numpy as np


# ============================================================
# CREATE OCR VARIANTS
# ============================================================

def create_ocr_variants(image):

    variants = {}

    # 1. Grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    variants["grayscale"] = gray


    # 2. Contrast Enhancement using CLAHE
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    contrast = clahe.apply(gray)

    variants["contrast"] = contrast


    # 3. Denoising
    denoised = cv2.fastNlMeansDenoising(
        gray,
        None,
        10,
        7,
        21
    )

    variants["denoised"] = denoised


    # 4. Sharpening
    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])

    sharpened = cv2.filter2D(
        gray,
        -1,
        kernel
    )

    variants["sharpened"] = sharpened


    # 5. Adaptive Threshold
    adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    variants["adaptive"] = adaptive


    # 6. Otsu Threshold
    _, otsu = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    variants["otsu"] = otsu


    return variants


# ============================================================
# PREPROCESS IMAGE
# ============================================================

def preprocess_image(image_path):

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not load image: {image_path}"
        )

    return create_ocr_variants(image)

import cv2
import numpy as np


# ============================================================
# CREATE OCR VARIANTS
# ============================================================

def create_ocr_variants(image):

    variants = {}

    # 1. Grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    variants["grayscale"] = gray


    # 2. Contrast Enhancement using CLAHE
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    contrast = clahe.apply(gray)

    variants["contrast"] = contrast


    # 3. Denoising
    denoised = cv2.fastNlMeansDenoising(
        gray,
        None,
        10,
        7,
        21
    )

    variants["denoised"] = denoised


    # 4. Sharpening
    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])

    sharpened = cv2.filter2D(
        gray,
        -1,
        kernel
    )

    variants["sharpened"] = sharpened


    # 5. Adaptive Threshold
    adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    variants["adaptive"] = adaptive


    # 6. Otsu Threshold
    _, otsu = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    variants["otsu"] = otsu


    return variants


# ============================================================
# PREPROCESS IMAGE
# ============================================================

def preprocess_image(image_path):

    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(
            f"Could not load image: {image_path}"
        )

    return create_ocr_variants(image)
