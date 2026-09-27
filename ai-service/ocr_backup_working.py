import os
import cv2
import json
import tempfile
from pathlib import Path

# Prevent PaddleOCR/PaddlePaddle PIR-related issues seen in some environments.
os.environ["FLAGS_enable_pir_api"] = "0"

from paddleocr import PaddleOCR


# ---------------------------------------------------------
# PADDLE OCR INITIALIZATION
# ---------------------------------------------------------

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def extract_result_data(res):
    """
    Convert PaddleOCR output into a simple structure.

    Returns:
        {
            "texts": [...],
            "confidences": [...],
            "boxes": [...]
        }
    """

    data = None

    if hasattr(res, "json"):
        data = res.json

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = None
    else:
        data = res

    if not isinstance(data, dict):
        return {
            "texts": [],
            "confidences": [],
            "boxes": []
        }

    # PaddleOCR may wrap the actual result inside "res".
    if "res" in data and isinstance(data["res"], dict):
        data = data["res"]

    texts = data.get("rec_texts", []) or []
    confidences = data.get("rec_scores", []) or []
    boxes = data.get("rec_boxes", []) or []

    return {
        "texts": texts,
        "confidences": confidences,
        "boxes": boxes
    }


def run_paddle_ocr(image_input):
    """
    Run PaddleOCR on one image/path.
    """

    result = ocr.predict(image_input)

    all_texts = []
    all_confidences = []
    all_boxes = []

    for res in result:

        extracted = extract_result_data(res)

        all_texts.extend(extracted["texts"])
        all_confidences.extend(extracted["confidences"])
        all_boxes.extend(extracted["boxes"])

    return {
        "texts": all_texts,
        "confidences": all_confidences,
        "boxes": all_boxes
    }


def normalize_ocr_key(text):
    """
    Normalize OCR text for duplicate detection.

    Example:

        "MAXIMUM RETAIL PRICE"
        "Maximum   Retail   Price"

    become the same key.
    """

    if text is None:
        return ""

    text = str(text).upper()

    # Normalize common OCR spacing.
    text = " ".join(text.split())

    # Remove unnecessary surrounding whitespace.
    return text.strip()


# ---------------------------------------------------------
# SINGLE IMAGE OCR
# ---------------------------------------------------------

def perform_ocr(image_path):
    """
    Perform OCR on one image.

    Two OCR variants are intentionally used:

        1. Original image
        2. Contrast-enhanced image

    We are NOT adding more OCR passes because multiple
    images already increase processing time.
    """

    image_path = str(image_path)

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not load image: {image_path}"
        )

    original = image

    # Convert to grayscale.
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Improve local contrast.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    contrast = clahe.apply(gray)

    variants = [
        ("original", original),
        ("contrast", contrast)
    ]

    candidates = []

    for variant_name, variant_image in variants:

        temp_path = None

        try:

            # PaddleOCR receives a temporary image file.
            with tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False
            ) as temp_file:

                temp_path = temp_file.name

            cv2.imwrite(
                temp_path,
                variant_image
            )

            result = run_paddle_ocr(temp_path)

            for i, text in enumerate(
                result["texts"]
            ):

                text = str(text).strip()

                if not text:
                    continue

                confidence = 0.0

                if i < len(
                    result["confidences"]
                ):
                    try:
                        confidence = float(
                            result["confidences"][i]
                        )
                    except Exception:
                        confidence = 0.0

                box = None

                if i < len(
                    result["boxes"]
                ):
                    box = result["boxes"][i]

                candidates.append({
                    "text": text,
                    "confidence": confidence,
                    "box": box,
                    "variant": variant_name,
                    "source_image": os.path.basename(
                        image_path
                    )
                })

        except Exception as error:

            print(
                f"OCR variant '{variant_name}' "
                f"failed for {image_path}: {error}"
            )

        finally:

            if (
                temp_path
                and os.path.exists(temp_path)
            ):
                os.remove(temp_path)

    # -----------------------------------------------------
    # REMOVE DUPLICATES WITHIN THIS IMAGE
    # -----------------------------------------------------

    unique_candidates = {}

    for candidate in candidates:

        key = normalize_ocr_key(
            candidate["text"]
        )

        if not key:
            continue

        if (
            key not in unique_candidates
            or candidate["confidence"]
            > unique_candidates[key]["confidence"]
        ):
            unique_candidates[key] = candidate

    ordered = sorted(
        unique_candidates.values(),
        key=lambda item: item["confidence"],
        reverse=True
    )

    texts = [
        item["text"]
        for item in ordered
    ]

    confidences = [
        item["confidence"]
        for item in ordered
    ]

    boxes = [
        item["box"]
        for item in ordered
    ]

    return {
        "texts": texts,
        "confidences": confidences,
        "boxes": boxes,
        "candidates": ordered,
        "image": os.path.basename(image_path)
    }


# ---------------------------------------------------------
# SINGLE IMAGE TEXT
# ---------------------------------------------------------

def get_selected_text(image_path):
    """
    Existing single-image interface.

    This is kept so existing code does not immediately break.
    """

    result = perform_ocr(image_path)

    texts = result.get(
        "texts",
        []
    )

    selected_text = "\n".join(
        str(text).strip()
        for text in texts
        if str(text).strip()
    )

    if not selected_text:

        raise RuntimeError(
            "PaddleOCR could not extract text."
        )

    return selected_text


# ---------------------------------------------------------
# MULTI-IMAGE OCR
# ---------------------------------------------------------

def perform_ocr_on_images(image_paths):
    """
    Perform OCR on multiple images belonging to the
    SAME packaged commodity.

    Example:

        [
            "front.jpg",
            "back.jpg",
            "side.jpg"
        ]

    Each image is processed separately.

    Then all OCR results are combined and duplicates
    are removed across images.
    """

    if not image_paths:
        raise ValueError(
            "No image paths were provided."
        )

    all_candidates = []

    image_results = []

    for index, image_path in enumerate(
        image_paths,
        start=1
    ):

        image_path = str(image_path)

        print(
            f"Processing image "
            f"{index}/{len(image_paths)}: "
            f"{image_path}"
        )

        try:

            result = perform_ocr(
                image_path
            )

            image_results.append(result)

            for candidate in result.get(
                "candidates",
                []
            ):

                candidate_copy = dict(
                    candidate
                )

                candidate_copy[
                    "source_image"
                ] = os.path.basename(
                    image_path
                )

                all_candidates.append(
                    candidate_copy
                )

        except Exception as error:

            print(
                f"OCR failed for image "
                f"{image_path}: {error}"
            )

            # Keep processing the other images.
            image_results.append({
                "image": os.path.basename(
                    image_path
                ),
                "texts": [],
                "confidences": [],
                "boxes": [],
                "candidates": [],
                "error": str(error)
            })

    # -----------------------------------------------------
    # CROSS-IMAGE DEDUPLICATION
    # -----------------------------------------------------

    unique_candidates = {}

    for candidate in all_candidates:

        key = normalize_ocr_key(
            candidate.get("text")
        )

        if not key:
            continue

        # If the same declaration appears in
        # front + back + side images, keep the
        # highest-confidence occurrence.
        if (
            key not in unique_candidates
            or candidate.get(
                "confidence",
                0.0
            )
            > unique_candidates[key].get(
                "confidence",
                0.0
            )
        ):

            unique_candidates[key] = candidate

    # -----------------------------------------------------
    # ORDER RESULTS
    # -----------------------------------------------------

    ordered = sorted(
        unique_candidates.values(),
        key=lambda item: item.get(
            "confidence",
            0.0
        ),
        reverse=True
    )

    combined_texts = [
        item["text"]
        for item in ordered
        if item.get("text")
    ]

    combined_confidences = [
        item.get("confidence", 0.0)
        for item in ordered
    ]

    combined_boxes = [
        item.get("box")
        for item in ordered
    ]

    # -----------------------------------------------------
    # OCR SUMMARY
    # -----------------------------------------------------

    successful_images = sum(
        1
        for result in image_results
        if result.get("texts")
    )

    average_confidence = 0.0

    if combined_confidences:

        average_confidence = round(
            sum(combined_confidences)
            / len(combined_confidences),
            4
        )

    return {
        "image_count": len(image_paths),

        "successful_images": successful_images,

        "failed_images":
            len(image_paths)
            - successful_images,

        "texts": combined_texts,

        "confidences":
            combined_confidences,

        "boxes":
            combined_boxes,

        "candidates":
            ordered,

        "average_confidence":
            average_confidence,

        "image_results":
            image_results
    }


# ---------------------------------------------------------
# MULTI-IMAGE TEXT
# ---------------------------------------------------------

def get_selected_text_from_images(image_paths):
    """
    Return one combined OCR text block for multiple images
    of the SAME product.

    This is the function that the new pipeline will use.
    """

    result = perform_ocr_on_images(
        image_paths
    )

    texts = result.get(
        "texts",
        []
    )

    selected_text = "\n".join(
        str(text).strip()
        for text in texts
        if str(text).strip()
    )

    if not selected_text:

        raise RuntimeError(
            "PaddleOCR could not extract text "
            "from any of the submitted images."
        )

    return selected_text


# ---------------------------------------------------------
# MULTI-IMAGE FULL RESULT
# ---------------------------------------------------------

def get_ocr_result_from_images(image_paths):
    """
    Public helper for the main pipeline.

    Unlike get_selected_text_from_images(),
    this returns the complete OCR result,
    including confidence and source-image information.
    """

    return perform_ocr_on_images(
        image_paths
    )
