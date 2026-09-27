
import json

from preprocessing import preprocess_image
from ocr import get_selected_text
from nlp import process_ocr_text
from compliance import LegalMetrologyRuleEngine


# ============================================================
# IMAGE PATH
# ============================================================

IMAGE_PATH = "uploads/1789886606804-456615738.jpeg"


# ============================================================
# NLP → RULE ENGINE ADAPTER
# ============================================================

def nlp_to_rule_engine(nlp_data):

    def get_value(field):
        value = nlp_data.get(field, {})

        if isinstance(value, dict):
            return value.get("value")

        return value

    return {
        # Product information
        "product_name": get_value("product_name"),
        "generic_name": get_value("generic_name"),

        # Responsible entities
        "manufacturer": get_value("manufacturer"),
        "packer": get_value("packer"),
        "importer": get_value("importer"),

        # Origin
        "country_of_origin": get_value("country_of_origin"),
        "imported": get_value("imported"),

        # Quantity / price
        "net_quantity": get_value("net_quantity"),
        "mrp": get_value("mrp"),
        "unit_sale_price": get_value("unit_sale_price"),

        # Dates
        "packed_date": get_value("packed_date"),
        "manufacturing_date": get_value("manufacturing_date"),
        "best_before": get_value("best_before"),

        # Consumer care
        "consumer_care": get_value("consumer_care"),
        "consumer_care_phone": get_value("consumer_care_phone"),
        "consumer_care_email": get_value("consumer_care_email"),

        # Product category
        "product_category": get_value("product_category") or "general",

        # Visual checks
        # These require image/visual analysis and therefore
        # remain manual review for now.
        "dimensions": None,
        "legibility": None,
        "prominence": None,
        "placement": None,
    }


# ============================================================
# PRINT HELPER
# ============================================================

def print_field(name, field):

    if isinstance(field, dict):

        value = field.get("value")
        confidence = field.get("confidence", 0)

        if value is None or str(value).strip() == "":
            value = "Not detected"

        print(
            f"{name:<25}: "
            f"{value} "
            f"(confidence: {confidence:.2f})"
        )

    else:

        if field is None or str(field).strip() == "":
            field = "Not detected"

        print(f"{name:<25}: {field}")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("AI-POWERED PACKAGED COMMODITY COMPLIANCE PIPELINE")
    print("=" * 70)

    print(f"\nImage: {IMAGE_PATH}")

    # --------------------------------------------------------
    # STEP 1 — OPENCV PREPROCESSING
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("STEP 1 — OPENCV PREPROCESSING")
    print("-" * 70)

    try:

        preprocessing_result = preprocess_image(IMAGE_PATH)

        print(
            "Preprocessing completed successfully."
        )

        print(
            "Variants created:",
            list(preprocessing_result.keys())
        )

    except Exception as error:

        print(
            "Preprocessing failed:",
            error
        )

        return

    # --------------------------------------------------------
    # STEP 2 — PADDLEOCR
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("STEP 2 — PADDLEOCR TEXT EXTRACTION")
    print("-" * 70)

    try:

        selected_text = get_selected_text(IMAGE_PATH)

        print(
            "OCR completed successfully."
        )

        print("\nExtracted text:")
        print("-" * 50)

        print(selected_text)

        print("-" * 50)

    except Exception as error:

        print(
            "OCR failed:",
            error
        )

        return

    # --------------------------------------------------------
    # STEP 3 — NLP FIELD EXTRACTION
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("STEP 3 — NLP / FIELD EXTRACTION")
    print("-" * 70)

    try:

        nlp_result = process_ocr_text(
            selected_text
        )

        print(
            "NLP extraction completed successfully."
        )

    except Exception as error:

        print(
            "NLP extraction failed:",
            error
        )

        return

    # --------------------------------------------------------
    # IMPORTANT EXTRACTED FIELDS
    # --------------------------------------------------------

    print("\nDetected fields:")
    print("-" * 70)

    print_field(
        "Product Name",
        nlp_result.get("product_name")
    )

    print_field(
        "Generic Name",
        nlp_result.get("generic_name")
    )

    print_field(
        "Manufacturer",
        nlp_result.get("manufacturer")
    )

    print_field(
        "Packer",
        nlp_result.get("packer")
    )

    print_field(
        "Importer",
        nlp_result.get("importer")
    )

    print_field(
        "Country of Origin",
        nlp_result.get("country_of_origin")
    )

    print_field(
        "Imported",
        nlp_result.get("imported")
    )

    print_field(
        "Net Quantity",
        nlp_result.get("net_quantity")
    )

    print_field(
        "MRP",
        nlp_result.get("mrp")
    )

    print_field(
        "Packed Date",
        nlp_result.get("packed_date")
    )

    print_field(
        "Manufacturing Date",
        nlp_result.get("manufacturing_date")
    )

    print_field(
        "Best Before",
        nlp_result.get("best_before")
    )

    print_field(
        "Consumer Care",
        nlp_result.get("consumer_care")
    )

    print_field(
        "Consumer Care Phone",
        nlp_result.get("consumer_care_phone")
    )

    print_field(
        "Consumer Care Email",
        nlp_result.get("consumer_care_email")
    )

    print_field(
        "Unit Sale Price",
        nlp_result.get("unit_sale_price")
    )

    print_field(
        "Product Category",
        nlp_result.get("product_category")
    )

    # --------------------------------------------------------
    # STEP 4 — ADAPTER
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("STEP 4 — NLP → RULE ENGINE")
    print("-" * 70)

    rule_engine_data = nlp_to_rule_engine(
        nlp_result
    )

    print(
        "Rule-engine input prepared successfully."
    )

    # --------------------------------------------------------
    # STEP 5 — LEGAL METROLOGY RULE ENGINE
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("STEP 5 — LEGAL METROLOGY COMPLIANCE CHECK")
    print("-" * 70)

    try:

        engine = LegalMetrologyRuleEngine(
            rule_engine_data
        )

        final_report = engine.build_report()

        print(
            "Compliance analysis completed successfully."
        )

    except Exception as error:

        print(
            "Compliance engine failed:",
            error
        )

        return

    # --------------------------------------------------------
    # STEP 6 — SUMMARY
    # --------------------------------------------------------

    summary = final_report.get(
        "summary",
        {}
    )

    print("\n" + "=" * 70)
    print("COMPLIANCE SUMMARY")
    print("=" * 70)

    print(
        f"Overall Status       : "
        f"{summary.get('overall_status', 'UNKNOWN')}"
    )

    print(
        f"Compliance Score     : "
        f"{summary.get('compliance_score', 0)}%"
    )

    print(
        f"Total Checks         : "
        f"{summary.get('total_checks', 0)}"
    )

    print(
        f"Passed               : "
        f"{summary.get('passed', 0)}"
    )

    print(
        f"Failed               : "
        f"{summary.get('failed', 0)}"
    )

    print(
        f"Warnings             : "
        f"{summary.get('warnings', 0)}"
    )

    print(
        f"Manual Review        : "
        f"{summary.get('manual_review', 0)}"
    )

    print(
        f"Not Applicable       : "
        f"{summary.get('not_applicable', 0)}"
    )

    # --------------------------------------------------------
    # STEP 7 — INDIVIDUAL CHECKS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("INDIVIDUAL COMPLIANCE CHECKS")
    print("=" * 70)

    for check in final_report.get(
        "checks",
        []
    ):

        name = check.get(
            "check",
            "Unknown"
        )

        status = check.get(
            "status",
            "UNKNOWN"
        )

        message = check.get(
            "message",
            ""
        )

        print(
            f"\n[{status}] {name}"
        )

        print(
            f"    {message}"
        )

        if check.get("value") is not None:

            print(
                f"    Value: {check.get('value')}"
            )

    # --------------------------------------------------------
    # STEP 8 — VIOLATIONS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VIOLATIONS")
    print("=" * 70)

    violations = final_report.get(
        "violations",
        []
    )

    if violations:

        for index, violation in enumerate(
            violations,
            start=1
        ):

            print(
                f"\n{index}. "
                f"{violation.get('check', 'Unknown')}"
            )

            print(
                f"   {violation.get('message', '')}"
            )

    else:

        print(
            "No compliance violations detected."
        )

    # --------------------------------------------------------
    # STEP 9 — WARNINGS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("WARNINGS")
    print("=" * 70)

    warnings = final_report.get(
        "warnings",
        []
    )

    if warnings:

        for index, warning in enumerate(
            warnings,
            start=1
        ):

            print(
                f"\n{index}. "
                f"{warning.get('check', 'Unknown')}"
            )

            print(
                f"   {warning.get('message', '')}"
            )

    else:

        print(
            "No warnings."
        )

    # --------------------------------------------------------
    # STEP 10 — MANUAL REVIEW
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("MANUAL REVIEW ITEMS")
    print("=" * 70)

    manual_items = final_report.get(
        "manual_review_items",
        []
    )

    if manual_items:

        for index, item in enumerate(
            manual_items,
            start=1
        ):

            print(
                f"\n{index}. "
                f"{item.get('check', 'Unknown')}"
            )

            print(
                f"   {item.get('message', '')}"
            )

    else:

        print(
            "No manual review items."
        )

    # --------------------------------------------------------
    # STEP 11 — SAVE JSON REPORT
    # --------------------------------------------------------

    output_file = "pipeline_result.json"

    try:

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                final_report,
                file,
                indent=4,
                ensure_ascii=False
            )

        print("\n" + "=" * 70)

        print(
            f"Complete report saved to: {output_file}"
        )

        print("=" * 70)

    except Exception as error:

        print(
            "Could not save JSON report:",
            error
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

