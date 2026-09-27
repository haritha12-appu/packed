import os
import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException

from preprocessing import preprocess_image
from ocr import get_ocr_result_from_images
from nlp import process_ocr_text
from compliance import LegalMetrologyRuleEngine


app = FastAPI(
    title="AI Packaged Commodity Compliance API",
    description="AI-powered packaged commodity compliance verification system",
    version="1.0.0"
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# NLP → RULE ENGINE DATA
# ============================================================

def nlp_to_rule_engine(nlp_result):

    def get_value(field_name):
        field = nlp_result.get(field_name, {})

        if not isinstance(field, dict):
            return field

        return field.get("value")

    return {
        "product_name": get_value("product_name"),
        "brand_name": get_value("brand_name"),
        "generic_name": get_value("generic_name"),

        "manufacturer": get_value("manufacturer"),
        "packer": get_value("packer"),
        "importer": get_value("importer"),
        "marketer": get_value("marketer"),

        "imported": get_value("imported"),
        "country_of_origin": get_value("country_of_origin"),

        "net_quantity": get_value("net_quantity"),

        "manufacturing_date": get_value(
            "manufacturing_date"
        ),

        "packed_date": get_value(
            "packed_date"
        ),

        "best_before": get_value(
            "best_before"
        ),

        "mrp": get_value("mrp"),

        "consumer_care": get_value(
            "consumer_care"
        ),

        "consumer_care_phone": get_value(
            "consumer_care_phone"
        ),

        "consumer_care_email": get_value(
            "consumer_care_email"
        ),

        "unit_sale_price": get_value(
            "unit_sale_price"
        ),

        "dimensions": get_value(
            "dimensions"
        ),

        "legibility": get_value(
            "legibility"
        ),

        "prominence": get_value(
            "prominence"
        ),

        "placement": get_value(
            "placement"
        ),

        "product_category": get_value(
            "product_category"
        )
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": (
            "AI Packaged Commodity "
            "Compliance API is running."
        ),
        "status": "online"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "AI Compliance Service"
    }


# ============================================================
# MULTI-IMAGE ANALYSIS
# ============================================================

@app.post("/analyze")
async def analyze_images(
    files: list[UploadFile] = File(...)
):

    # --------------------------------------------------------
    # Validate upload
    # --------------------------------------------------------

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No images were provided."
        )

    if len(files) > 6:
        raise HTTPException(
            status_code=400,
            detail="Maximum 6 images are allowed."
        )

    image_paths = []
    filenames = []

    try:

        # ----------------------------------------------------
        # Save uploaded images
        # ----------------------------------------------------

        for index, file in enumerate(files):

            if not file.filename:
                continue

            safe_name = os.path.basename(
                file.filename
            )

            file_path = (
                UPLOAD_DIR /
                f"{index}_{safe_name}"
            )

            with open(
                file_path,
                "wb"
            ) as buffer:

                shutil.copyfileobj(
                    file.file,
                    buffer
                )

            image_paths.append(
                str(file_path)
            )

            filenames.append(
                safe_name
            )

        if not image_paths:
            raise HTTPException(
                status_code=400,
                detail="No valid image files were uploaded."
            )

        # ----------------------------------------------------
        # PREPROCESSING
        # ----------------------------------------------------

        preprocessing_results = []

        for image_path in image_paths:

            try:

                variants = preprocess_image(
                    image_path
                )

                preprocessing_results.append({
                    "image": os.path.basename(
                        image_path
                    ),
                    "variants_created": list(
                        variants.keys()
                    )
                })

            except Exception as e:

                preprocessing_results.append({
                    "image": os.path.basename(
                        image_path
                    ),
                    "error": str(e)
                })

        # ----------------------------------------------------
        # OCR
        #
        # IMPORTANT:
        # OCR is performed on ALL uploaded images,
        # then combined and deduplicated.
        # ----------------------------------------------------

        ocr_result = get_ocr_result_from_images(
            image_paths
        )

        combined_text = "\n".join(
            ocr_result.get(
                "texts",
                []
            )
        )

        # ----------------------------------------------------
        # NLP
        #
        # NLP runs ONCE on combined OCR text.
        # ----------------------------------------------------

        nlp_result = process_ocr_text(
            combined_text
        )

        # ----------------------------------------------------
        # RULE ENGINE
        #
        # One product-level assessment.
        # ----------------------------------------------------

        rule_engine_input = nlp_to_rule_engine(
            nlp_result
        )

        engine = LegalMetrologyRuleEngine(
            rule_engine_input
        )

        compliance_result = engine.build_report()

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        return {
            "success": True,

            "product": {
                "image_count": len(image_paths),
                "filenames": filenames
            },

            "preprocessing": {
                "images_processed": len(
                    preprocessing_results
                ),
                "results": preprocessing_results
            },

            "ocr": {
                "image_count": ocr_result.get(
                    "image_count",
                    len(image_paths)
                ),

                "successful_images":
                    ocr_result.get(
                        "successful_images",
                        []
                    ),

                "failed_images":
                    ocr_result.get(
                        "failed_images",
                        []
                    ),

                "unique_text_lines":
                    len(
                        ocr_result.get(
                            "texts",
                            []
                        )
                    ),

                "average_confidence":
                    ocr_result.get(
                        "average_confidence",
                        0.0
                    ),

                "text": combined_text
            },

            "nlp": nlp_result,

            "compliance": compliance_result
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis failed: "
                f"{str(e)}"
            )
        )

    finally:

        for file in files:

            try:
                await file.close()

            except Exception:
                pass
