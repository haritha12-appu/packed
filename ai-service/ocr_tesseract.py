import os
import re
import pytesseract
import cv2

from pytesseract import Output


# ---------------------------------------------------------
# Tesseract OCR
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
    return re.sub(r"[^a-z0-9]+", "", text)


# ---------------------------------------------------------
# Run OCR on one image
# ---------------------------------------------------------

def _run_ocr(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    data = pytesseract.image_to_data(
        image,
        lang="eng",
        config="--psm 11",
        output_type=Output.DICT
    )

    lines = []

    for index, raw_text in enumerate(data["text"]):
        text = _normalize_text(raw_text)

        if not text:
            continue

        confidence = _safe_float(
            data["conf"][index],
            default=-1
        )

        if confidence < 0:
            continue

        x = int(data["left"][index])
        y = int(data["top"][index])
        width = int(data["width"][index])
        height = int(data["height"][index])

        lines.append({
            "text": text,
            "confidence": confidence / 100.0,
            "box": [
                x,
                y,
                x + width,
                y + height
            ]
        })

    return lines


# ---------------------------------------------------------
# Single-image OCR
# ---------------------------------------------------------

def perform_ocr(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    print(f"Processing image with Tesseract: {image_path}")

    return _run_ocr(image_path)


def get_selected_text(image_path):
    return [
        item["text"]
        for item in perform_ocr(image_path)
        if item.get("text")
    ]


# ---------------------------------------------------------
# Multiple-image OCR
# ---------------------------------------------------------

def perform_ocr_on_images(image_paths):
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
        image_name = os.path.basename(image_path)

        print(
            f"Processing image {index}/{len(image_paths)} "
            f"with Tesseract: {image_name}"
        )

        try:
            results = perform_ocr(image_path)
            successful_images.append(image_name)

            image_candidates = []

            for item in results:
                candidate = {
                    "text": item["text"],
                    "confidence": item["confidence"],
                    "box": item["box"],
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

            print(f"OCR failed for {image_name}: {error}")

    unique = {}

    for candidate in all_candidates:
        key = _text_key(candidate["text"])

        if not key:
            continue

        if (
            key not in unique
            or candidate["confidence"] > unique[key]["confidence"]
        ):
            unique[key] = candidate

    selected_candidates = sorted(
        unique.values(),
        key=lambda item: item["confidence"],
        reverse=True
    )

    texts = [item["text"] for item in selected_candidates]
    confidences = [
        item["confidence"] for item in selected_candidates
    ]
    boxes = [
        item["box"]
        for item in selected_candidates
        if item.get("box") is not None
    ]

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences else 0.0
    )

    return {
        "image_count": len(image_paths),
        "successful_images": successful_images,
        "failed_images": failed_images,
        "texts": texts,
        "confidences": confidences,
        "boxes": boxes,
        "candidates": selected_candidates,
        "average_confidence": round(average_confidence, 4),
        "image_results": image_results
    }


def get_selected_text_from_images(image_paths):
    result = perform_ocr_on_images(image_paths)
    return result["texts"]


def get_ocr_result_from_images(image_paths):
    return perform_ocr_on_images(image_paths)


# ---------------------------------------------------------
# Standalone test
# ---------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python ocr_tesseract.py <image_path>"
        )
        raise SystemExit(1)

    result = get_ocr_result_from_images(sys.argv[1:])

    print("\n========== TESSERACT OCR RESULT ==========")
    print("Images:", result["image_count"])
    print("Successful:", result["successful_images"])
    print("Failed:", result["failed_images"])
    print("Unique OCR lines:", len(result["texts"]))
    print("Average confidence:", result["average_confidence"])

    print("\n--- EXTRACTED TEXT ---")

    for item in result["candidates"]:
        print(
            f'{item["text"]} '
            f'(confidence: {item["confidence"]:.2f})'
        )
