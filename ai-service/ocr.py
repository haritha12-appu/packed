import os
import re
from pathlib import Path

from paddleocr import PaddleOCR


# ---------------------------------------------------------
# PaddleOCR
# ---------------------------------------------------------
# Keep one OCR inference per image.
# This avoids running a second full OCR pass on CLAHE output.
#
# enable_mkldnn=False is kept because this is the configuration
# already working reliably in the current environment.
# ---------------------------------------------------------

ocr_engine = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(text):
    if text is None:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _text_key(text):
    text = _normalize_text(text).lower()

    # Remove punctuation and spacing differences so that
    # repeated OCR text from different package panels can
    # be deduplicated.
    return re.sub(r"[^a-z0-9]+", "", text)


# ---------------------------------------------------------
# Run PaddleOCR on one image
# ---------------------------------------------------------

def _run_ocr(image_path):
    result = ocr_engine.predict(image_path)

    lines = []

    for page in result:

        # PaddleOCR 3.x returns structured result objects.
        data = page.json

        if callable(data):
            data = data()

        if isinstance(data, str):
            import json
            data = json.loads(data)

        if isinstance(data, dict):
            data = data.get("res", data)

        if not isinstance(data, dict):
            continue

        texts = data.get("rec_texts", [])
        scores = data.get("rec_scores", [])
        boxes = data.get("rec_boxes", [])

        for index, text in enumerate(texts):

            text = _normalize_text(text)

            if not text:
                continue

            confidence = 0.0

            if index < len(scores):
                confidence = _safe_float(
                    scores[index]
                )

            box = None

            if index < len(boxes):
                try:
                    box = boxes[index].tolist()
                except AttributeError:
                    box = boxes[index]

            lines.append({
                "text": text,
                "confidence": confidence,
                "box": box
            })

    return lines


# ---------------------------------------------------------
# Single-image OCR
# ---------------------------------------------------------

def perform_ocr(image_path):
    """
    Backward-compatible OCR function.

    Returns:
        list of dictionaries containing:
        text
        confidence
        box
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    print(
        f"Processing image: {image_path}"
    )

    return _run_ocr(image_path)


# ---------------------------------------------------------
# Selected text from one image
# ---------------------------------------------------------

def get_selected_text(image_path):
    """
    Backward-compatible helper.
    """

    results = perform_ocr(image_path)

    return [
        item["text"]
        for item in results
        if item.get("text")
    ]


# ---------------------------------------------------------
# Multiple-image OCR
# ---------------------------------------------------------

def perform_ocr_on_images(image_paths):
    """
    Run OCR once on each submitted image.

    Images should represent different panels/views
    of the SAME packaged product.
    """

    if not image_paths:
        return {
            "image_count": 0,
            "successful_images": [],
            "failed_images": [],
            "texts": [],
            "confidences": [],
            "boxes": [],
            "candidates": [],
            "average_confidence": 0.0,
            "image_results": []
        }

    all_candidates = []
    successful_images = []
    failed_images = []
    image_results = []

    for index, image_path in enumerate(image_paths, start=1):

        print(
            f"Processing image {index}/{len(image_paths)}: "
            f"{image_path}"
        )

        image_name = os.path.basename(image_path)

        try:
            results = perform_ocr(image_path)

            successful_images.append(image_name)

            image_candidates = []

            for item in results:

                text = item.get("text")

                if not text:
                    continue

                candidate = {
                    "text": text,
                    "confidence": _safe_float(
                        item.get("confidence")
                    ),
                    "box": item.get("box"),
                    "image": image_name
                }

                image_candidates.append(candidate)
                all_candidates.append(candidate)

            image_results.append({
                "image": image_name,
                "success": True,
                "text_count": len(image_candidates),
                "results": image_candidates
            })

        except Exception as error:

            failed_images.append({
                "image": image_name,
                "error": str(error)
            })

            image_results.append({
                "image": image_name,
                "success": False,
                "error": str(error)
            })

            print(
                f"OCR failed for {image_name}: {error}"
            )

    # -----------------------------------------------------
    # Deduplicate OCR text across all submitted images
    # -----------------------------------------------------

    unique = {}

    for candidate in all_candidates:

        key = _text_key(
            candidate["text"]
        )

        if not key:
            continue

        if (
            key not in unique
            or candidate["confidence"]
            > unique[key]["confidence"]
        ):
            unique[key] = candidate

    selected_candidates = list(
        unique.values()
    )

    selected_candidates.sort(
        key=lambda item: item["confidence"],
        reverse=True
    )

    texts = [
        item["text"]
        for item in selected_candidates
    ]

    confidences = [
        item["confidence"]
        for item in selected_candidates
    ]

    boxes = [
        item["box"]
        for item in selected_candidates
        if item.get("box") is not None
    ]

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    return {
        "image_count": len(image_paths),

        "successful_images":
            successful_images,

        "failed_images":
            failed_images,

        "texts":
            texts,

        "confidences":
            confidences,

        "boxes":
            boxes,

        "candidates":
            selected_candidates,

        "average_confidence":
            round(
                average_confidence,
                4
            ),

        "image_results":
            image_results
    }


# ---------------------------------------------------------
# Combined text from multiple images
# ---------------------------------------------------------

def get_selected_text_from_images(image_paths):

    result = perform_ocr_on_images(
        image_paths
    )

    return result["texts"]


# ---------------------------------------------------------
# Complete OCR result
# ---------------------------------------------------------

def get_ocr_result_from_images(image_paths):

    return perform_ocr_on_images(
        image_paths
    )


# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    test_image = (
        "../Backend/uploads/"
        "1789893450076-94170956.jpeg"
    )

    result = get_ocr_result_from_images(
        [test_image]
    )

    print("\n==============================")
    print("OCR TEST RESULT")
    print("==============================")

    print(
        "Images:",
        result["image_count"]
    )

    print(
        "Successful:",
        result["successful_images"]
    )

    print(
        "Failed:",
        result["failed_images"]
    )

    print(
        "Unique OCR lines:",
        len(result["texts"])
    )

    print(
        "Average confidence:",
        result["average_confidence"]
    )

    print("\n--- OCR TEXT ---")

    for text in result["texts"]:
        print(text)
