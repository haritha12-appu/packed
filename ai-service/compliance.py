# compliance.py
"""
Legal Metrology (Packaged Commodities) compliance screening engine.

IMPORTANT:
This is an AI-assisted screening system.

"NOT_DETECTED" means the declaration was not confidently recovered
from the submitted images/OCR. It does NOT by itself prove that the
declaration is physically absent from the package.

The final legal determination must be made by an authorized officer.
"""

import re
from datetime import datetime


class LegalMetrologyRuleEngine:

    RULESET_VERSION = "PCR-2011-screening-config"

    def __init__(self, product_data):
        self.data = product_data or {}

        self.checks = []
        self.warnings = []

    # ============================================================
    # BASIC HELPERS
    # ============================================================

    def get_value(self, field_name):
        value = self.data.get(field_name)

        if isinstance(value, dict):
            return value.get("value")

        return value

    def get_confidence(self, field_name):
        value = self.data.get(field_name)

        if isinstance(value, dict):
            try:
                return float(value.get("confidence", 0.0))
            except (TypeError, ValueError):
                return 0.0

        return 0.0

    def is_empty(self, value):
        if value is None:
            return True

        if isinstance(value, str):
            return not value.strip()

        return False

    def clean_text(self, value):
        if value is None:
            return ""

        return str(value).strip()

    def add_check(
        self,
        field,
        declaration,
        status,
        value,
        rule,
        reason,
        confidence=0.0,
        applicability="Applicable"
    ):
        self.checks.append({
            "field": field,
            "declaration": declaration,
            "status": status,
            "value": value,
            "rule": rule,
            "reason": reason,
            "confidence": round(float(confidence), 2),
            "applicability": applicability
        })

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    def valid_quantity(self, value):
        if self.is_empty(value):
            return False

        pattern = re.compile(
            r"^\s*\d+(?:\.\d+)?\s*"
            r"(?:mg|g|kg|mcg|ml|l|cm|mm|m|"
            r"number|nos?|pcs?|pieces?)\s*$",
            re.IGNORECASE
        )

        return bool(pattern.match(str(value)))

    def valid_mrp(self, value):
        if self.is_empty(value):
            return False

        text = str(value).upper()

        return bool(
            re.search(
                r"(?:₹|RS\.?|INR)\s*\d+(?:\.\d+)?",
                text
            )
        )

    def valid_email(self, value):
        if self.is_empty(value):
            return False

        pattern = (
            r"^[A-Z0-9._%+-]+"
            r"@[A-Z0-9.-]+\.[A-Z]{2,}$"
        )

        return bool(
            re.match(
                pattern,
                str(value),
                re.IGNORECASE
            )
        )

    def valid_phone(self, value):
        if self.is_empty(value):
            return False

        digits = re.sub(r"\D", "", str(value))

        if len(digits) == 10 and digits[0] in "6789":
            return True

        if digits.startswith("1800") and len(digits) >= 10:
            return True

        if digits.startswith("91") and len(digits) == 12:
            return True

        return False

    def valid_date(self, value):
        if self.is_empty(value):
            return False

        text = str(value).strip()

        patterns = [
            r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$",
            r"^\d{1,2}[/-]\d{2,4}$",
            r"^\d{4}[/-]\d{1,2}$",
            r"^\d{1,2}\.\d{2,4}$",
        ]

        return any(
            re.match(pattern, text)
            for pattern in patterns
        )

    # ============================================================
    # PRODUCT IDENTITY
    # ============================================================

    def check_product_name(self):
        value = self.get_value("product_name")
        confidence = self.get_confidence("product_name")

        if self.is_empty(value):
            self.add_check(
                "product_name",
                "Product identification",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(c)",
                "Product/common identification was not confidently detected in the submitted images.",
                confidence
            )
        else:
            self.add_check(
                "product_name",
                "Product identification",
                "DETECTED",
                value,
                "Rule 6(1)(c)",
                "Product/common identification was detected by the OCR/NLP pipeline.",
                confidence
            )

    def check_generic_name(self):
        value = self.get_value("generic_name")
        confidence = self.get_confidence("generic_name")

        if self.is_empty(value):
            self.add_check(
                "generic_name",
                "Common / generic name",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(c)",
                "The common or generic name was not confidently detected.",
                confidence
            )
        else:
            self.add_check(
                "generic_name",
                "Common / generic name",
                "DETECTED",
                value,
                "Rule 6(1)(c)",
                "Common/generic name detected.",
                confidence
            )

    # ============================================================
    # MANUFACTURER / PACKER / IMPORTER
    # ============================================================

    def check_responsible_entity(self):
        manufacturer = self.get_value("manufacturer")
        packer = self.get_value("packer")
        importer = self.get_value("importer")

        confidence = max(
            self.get_confidence("manufacturer"),
            self.get_confidence("packer"),
            self.get_confidence("importer")
        )

        entities = []

        if manufacturer:
            entities.append(f"Manufacturer: {manufacturer}")

        if packer:
            entities.append(f"Packer: {packer}")

        if importer:
            entities.append(f"Importer: {importer}")

        if entities:
            self.add_check(
                "manufacturer_packer_importer",
                "Name and address of manufacturer / packer / importer",
                "DETECTED",
                "; ".join(entities),
                "Rule 6(1)(a)",
                "At least one responsible entity declaration was detected.",
                confidence
            )
        else:
            self.add_check(
                "manufacturer_packer_importer",
                "Name and address of manufacturer / packer / importer",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(a)",
                "No manufacturer, packer or importer declaration was confidently recovered from the submitted images. Verification of the package is required.",
                confidence
            )

    # ============================================================
    # COUNTRY OF ORIGIN
    # ============================================================

    def check_country_of_origin(self):
        value = self.get_value("country_of_origin")
        imported = self.get_value("imported")
        confidence = self.get_confidence("country_of_origin")

        if imported is False:
            if value:
                self.add_check(
                    "country_of_origin",
                    "Country of origin",
                    "DETECTED",
                    value,
                    "Rule 6(1)(b)",
                    "Country-of-origin text was detected; the package was also identified as domestic based on available OCR.",
                    confidence,
                    "Conditionally applicable to imported products"
                )
            else:
                self.add_check(
                    "country_of_origin",
                    "Country of origin",
                    "NOT_APPLICABLE",
                    None,
                    "Rule 6(1)(b)",
                    "Country-of-origin declaration is specifically relevant where the product is imported.",
                    confidence,
                    "Conditionally applicable to imported products"
                )

            return

        if imported is True:
            if value:
                self.add_check(
                    "country_of_origin",
                    "Country of origin",
                    "DETECTED",
                    value,
                    "Rule 6(1)(b)",
                    "Country of origin was detected for an imported product.",
                    confidence
                )
            else:
                self.add_check(
                    "country_of_origin",
                    "Country of origin",
                    "NOT_DETECTED",
                    None,
                    "Rule 6(1)(b)",
                    "The product appears to be imported but country-of-origin information was not confidently detected.",
                    confidence
                )

            return

        # Unknown import status.
        if value:
            self.add_check(
                "country_of_origin",
                "Country of origin",
                "DETECTED",
                value,
                "Rule 6(1)(b)",
                "Country-of-origin information was detected.",
                confidence,
                "Applicability could not be fully determined from OCR"
            )
        else:
            self.add_check(
                "country_of_origin",
                "Country of origin",
                "REVIEW",
                None,
                "Rule 6(1)(b)",
                "Country of origin was not detected and import status could not be confidently determined.",
                confidence,
                "Applicability uncertain"
            )

    # ============================================================
    # NET QUANTITY
    # ============================================================

    def check_net_quantity(self):
        value = self.get_value("net_quantity")
        confidence = self.get_confidence("net_quantity")

        if self.is_empty(value):
            self.add_check(
                "net_quantity",
                "Net quantity",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(d)",
                "Net quantity was not confidently detected.",
                confidence
            )

        elif self.valid_quantity(value):
            self.add_check(
                "net_quantity",
                "Net quantity",
                "DETECTED",
                value,
                "Rule 6(1)(d)",
                "Net quantity was detected in a recognized unit of weight, measure or number.",
                confidence
            )

        else:
            self.add_check(
                "net_quantity",
                "Net quantity",
                "REVIEW",
                value,
                "Rule 6(1)(d)",
                "A quantity-like value was detected but its format requires verification.",
                confidence
            )

    # ============================================================
    # MANUFACTURING / PACKING DATE
    # ============================================================

    def check_manufacturing_date(self):
        manufacturing = self.get_value("manufacturing_date")
        packed = self.get_value("packed_date")

        confidence = max(
            self.get_confidence("manufacturing_date"),
            self.get_confidence("packed_date")
        )

        # Do NOT silently treat packed date as manufacturing date.
        if manufacturing:
            if self.valid_date(manufacturing):
                self.add_check(
                    "manufacturing_date",
                    "Month and year of manufacture / relevant date declaration",
                    "DETECTED",
                    manufacturing,
                    "Rule 6(1)(e)",
                    "A manufacturing date was detected.",
                    self.get_confidence("manufacturing_date")
                )
            else:
                self.add_check(
                    "manufacturing_date",
                    "Month and year of manufacture / relevant date declaration",
                    "REVIEW",
                    manufacturing,
                    "Rule 6(1)(e)",
                    "A manufacturing date was detected but its format requires verification.",
                    self.get_confidence("manufacturing_date")
                )

        elif packed:
            self.add_check(
                "manufacturing_date",
                "Month and year of manufacture / relevant date declaration",
                "REVIEW",
                packed,
                "Rule 6(1)(e)",
                "A packed date was detected, but it must not automatically be treated as a manufacturing date. Verify the applicable package declaration.",
                confidence
            )

        else:
            self.add_check(
                "manufacturing_date",
                "Month and year of manufacture / relevant date declaration",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(e)",
                "No applicable manufacturing/packing/import date declaration was confidently recovered from the submitted images.",
                confidence
            )

    # ============================================================
    # BEST BEFORE
    # ============================================================

    def check_best_before(self):
        value = self.get_value("best_before")
        confidence = self.get_confidence("best_before")

        # The rule is conditional for commodities that may become
        # unfit for human consumption. Do not universally fail
        # cosmetics simply because best-before was not OCR detected.
        category = self.clean_text(
            self.get_value("product_category")
        ).lower()

        if value:
            self.add_check(
                "best_before",
                "Best before / use by",
                "DETECTED",
                value,
                "Rule 6(1)(f)",
                "Best-before/use-by information was detected.",
                confidence,
                "Applicable where the commodity may become unfit for human consumption"
            )
            return

        if category in {
            "food",
            "beverage",
            "food_product"
        }:
            self.add_check(
                "best_before",
                "Best before / use by",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(f)",
                "This product category may require a best-before/use-by declaration. It was not confidently detected.",
                confidence
            )
        else:
            self.add_check(
                "best_before",
                "Best before / use by",
                "NOT_APPLICABLE",
                None,
                "Rule 6(1)(f)",
                "Best-before/use-by is not treated as universally applicable to this detected product category by this screening configuration.",
                confidence,
                "Conditional"
            )

    # ============================================================
    # MRP
    # ============================================================

    def check_mrp(self):
        value = self.get_value("mrp")
        confidence = self.get_confidence("mrp")

        if self.is_empty(value):
            self.add_check(
                "mrp",
                "Maximum Retail Price (MRP), inclusive of all taxes",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(g)",
                "MRP was not confidently detected in the submitted images. The package should be visually verified.",
                confidence
            )

        elif self.valid_mrp(value):
            self.add_check(
                "mrp",
                "Maximum Retail Price (MRP), inclusive of all taxes",
                "DETECTED",
                value,
                "Rule 6(1)(g)",
                "MRP was detected in a recognizable price format. Tax-inclusive wording and physical presentation require verification where applicable.",
                confidence
            )

        else:
            self.add_check(
                "mrp",
                "Maximum Retail Price (MRP), inclusive of all taxes",
                "REVIEW",
                value,
                "Rule 6(1)(g)",
                "A possible MRP was detected but its format requires verification.",
                confidence
            )

    # ============================================================
    # CONSUMER CARE
    # ============================================================

    def check_consumer_care(self):
        consumer_care = self.get_value("consumer_care")
        phone = self.get_value("consumer_care_phone")
        email = self.get_value("consumer_care_email")

        confidence = max(
            self.get_confidence("consumer_care"),
            self.get_confidence("consumer_care_phone"),
            self.get_confidence("consumer_care_email")
        )

        details = []

        if consumer_care:
            details.append(str(consumer_care))

        if phone:
            details.append(f"Phone: {phone}")

        if email:
            details.append(f"Email: {email}")

        if details:
            self.add_check(
                "consumer_care",
                "Consumer care details",
                "DETECTED",
                "; ".join(details),
                "Rule 6(1)(h)",
                "Consumer-care information was detected. Contact details should be visually verified for completeness and accuracy.",
                confidence
            )
        else:
            self.add_check(
                "consumer_care",
                "Consumer care details",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(h)",
                "Consumer-care details were not confidently recovered from the submitted images.",
                confidence
            )

    # ============================================================
    # DIMENSIONS
    # ============================================================

    def check_dimensions(self):
        value = self.get_value("dimensions")
        confidence = self.get_confidence("dimensions")

        if value:
            self.add_check(
                "dimensions",
                "Dimensions where relevant",
                "DETECTED",
                value,
                "Rule 6(1)(i)",
                "Dimension information was detected.",
                confidence,
                "Applicable where size/dimensions are relevant to the commodity"
            )
        else:
            self.add_check(
                "dimensions",
                "Dimensions where relevant",
                "REVIEW",
                None,
                "Rule 6(1)(i)",
                "Dimensions were not obtained through OCR. Applicability depends on the commodity and should be verified during inspection.",
                confidence,
                "Conditional"
            )

    # ============================================================
    # UNIT SALE PRICE
    # ============================================================

    def check_unit_sale_price(self):
        value = self.get_value("unit_sale_price")
        confidence = self.get_confidence("unit_sale_price")

        if value:
            self.add_check(
                "unit_sale_price",
                "Unit sale price",
                "DETECTED",
                value,
                "Rule 6(1)(j) / Rule 6(11)",
                "Unit sale price information was detected. Its numerical basis and applicable unit should be verified against net quantity.",
                confidence
            )
        else:
            self.add_check(
                "unit_sale_price",
                "Unit sale price",
                "NOT_DETECTED",
                None,
                "Rule 6(1)(j) / Rule 6(11)",
                "Unit sale price was not confidently detected. Applicability/exceptions should be verified for the package type.",
                confidence,
                "Subject to applicable exceptions"
            )

    # ============================================================
    # VISUAL / RULE 9
    # ============================================================

    def check_visual_requirements(self):
        legibility = self.get_value("legibility")
        prominence = self.get_value("prominence")
        placement = self.get_value("placement")

        # Legibility
        if legibility:
            self.add_check(
                "legibility",
                "Legibility and prominence",
                "DETECTED",
                legibility,
                "Rule 9(1)",
                "Visual legibility information was supplied to the engine.",
                self.get_confidence("legibility")
            )
        else:
            self.add_check(
                "legibility",
                "Legibility and prominence",
                "REVIEW",
                None,
                "Rule 9(1)(a)",
                "OCR can detect text but cannot by itself establish the legal visual standard of legibility and prominence. Manual/image review is required.",
                0.0
            )

        # Prominence
        if prominence:
            self.add_check(
                "prominence",
                "Prominence of declarations",
                "DETECTED",
                prominence,
                "Rule 9(1)(a)",
                "Prominence information was supplied to the engine.",
                self.get_confidence("prominence")
            )
        else:
            self.add_check(
                "prominence",
                "Prominence of declarations",
                "REVIEW",
                None,
                "Rule 9(1)(a)",
                "Visual prominence cannot be established from OCR text alone. Manual/image review is required.",
                0.0
            )

        # Placement
        if placement:
            self.add_check(
                "placement",
                "Placement / presentation",
                "DETECTED",
                placement,
                "Rule 9",
                "Placement information was supplied to the engine.",
                self.get_confidence("placement")
            )
        else:
            self.add_check(
                "placement",
                "Placement / presentation",
                "REVIEW",
                None,
                "Rule 9",
                "Package layout and placement require image-level/manual verification.",
                0.0
            )

    # ============================================================
    # CONSISTENCY CHECKS
    # ============================================================

    def check_quantity_consistency(self):
        quantity = self.get_value("net_quantity")

        if self.is_empty(quantity):
            return

        # Basic sanity check.
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*(ml|l|g|kg|mg)",
            str(quantity),
            re.IGNORECASE
        )

        if not match:
            return

        number = float(match.group(1))
        unit = match.group(2).lower()

        if number <= 0:
            self.add_check(
                "quantity_consistency",
                "Quantity consistency",
                "REVIEW",
                quantity,
                "Screening validation",
                "Detected net quantity is not a positive value.",
                self.get_confidence("net_quantity")
            )

    def check_mrp_consistency(self):
        mrp = self.get_value("mrp")

        if not mrp:
            return

        match = re.search(
            r"(?:₹|RS\.?|INR)\s*(\d+(?:\.\d+)?)",
            str(mrp),
            re.IGNORECASE
        )

        if not match:
            self.add_check(
                "mrp_consistency",
                "MRP format consistency",
                "REVIEW",
                mrp,
                "Screening validation",
                "MRP was detected but its numerical format could not be fully validated.",
                self.get_confidence("mrp")
            )

    # ============================================================
    # RUN ALL CHECKS
    # ============================================================

    def run_checks(self):
        self.checks = []

        self.check_product_name()
        self.check_generic_name()

        self.check_responsible_entity()

        self.check_country_of_origin()

        self.check_net_quantity()

        self.check_manufacturing_date()

        self.check_best_before()

        self.check_mrp()

        self.check_consumer_care()

        self.check_dimensions()

        self.check_unit_sale_price()

        self.check_visual_requirements()

        self.check_quantity_consistency()

        self.check_mrp_consistency()

        return self.checks

    # ============================================================
    # AI SCREENING CONFIDENCE
    # ============================================================

    def calculate_ai_confidence(self):
        """
        Average confidence of detected NLP fields.

        This is NOT a legal compliance score.
        """

        confidence_fields = [
            "product_name",
            "generic_name",
            "manufacturer",
            "packer",
            "importer",
            "country_of_origin",
            "net_quantity",
            "mrp",
            "unit_sale_price",
            "manufacturing_date",
            "packed_date",
            "best_before",
            "consumer_care",
            "consumer_care_phone",
            "consumer_care_email",
            "product_category",
        ]

        values = []

        for field in confidence_fields:
            value = self.get_value(field)
            confidence = self.get_confidence(field)

            if not self.is_empty(value):
                values.append(confidence)

        if not values:
            return 0.0

        return round(
            sum(values) / len(values),
            2
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def calculate_summary(self):
        total = len(self.checks)

        detected = sum(
            1 for c in self.checks
            if c["status"] == "DETECTED"
        )

        not_detected = sum(
            1 for c in self.checks
            if c["status"] == "NOT_DETECTED"
        )

        review = sum(
            1 for c in self.checks
            if c["status"] == "REVIEW"
        )

        not_applicable = sum(
            1 for c in self.checks
            if c["status"] == "NOT_APPLICABLE"
        )

        applicable = total - not_applicable

        if applicable > 0:
            coverage = detected / applicable
        else:
            coverage = 0.0

        return {
            "total_checks": total,
            "detected": detected,
            "not_detected": not_detected,
            "review_required": review,
            "not_applicable": not_applicable,
            "declaration_coverage": round(
                coverage,
                2
            )
        }

    # ============================================================
    # OVERALL ASSESSMENT
    # ============================================================

    def calculate_overall_status(self):
        """
        Important:
        Never call OCR absence a confirmed legal violation.

        Possible statuses:
            SCREENING_PASS
            POTENTIAL_NON_COMPLIANCE
            VERIFICATION_REQUIRED
        """

        not_detected = [
            check for check in self.checks
            if check["status"] == "NOT_DETECTED"
        ]

        review = [
            check for check in self.checks
            if check["status"] == "REVIEW"
        ]

        # Missing declarations detected by OCR pipeline.
        if not_detected:
            return (
                "POTENTIAL_NON_COMPLIANCE",
                "One or more applicable declarations were not detected in the submitted images. This is a screening result and requires package/officer verification."
            )

        # No obvious missing declaration, but visual verification
        # remains necessary.
        if review:
            return (
                "VERIFICATION_REQUIRED",
                "Required declarations were detected or not shown as missing, but one or more visual/conditional checks require verification."
            )

        return (
            "SCREENING_PASS",
            "No missing applicable declaration was identified by the current automated screening configuration."
        )

    # ============================================================
    # REPORT
    # ============================================================

    def build_report(self):
        self.run_checks()

        summary = self.calculate_summary()

        ai_confidence = self.calculate_ai_confidence()

        overall_status, overall_reason = (
            self.calculate_overall_status()
        )

        return {
            "ruleset_version": self.RULESET_VERSION,

            "assessment": {
                "status": overall_status,
                "reason": overall_reason,
                "ai_screening_confidence": ai_confidence
            },

            "summary": summary,

            "declarations": self.checks,

            "limitations": [
                "Not detected means the declaration was not confidently recovered from the submitted images; it does not by itself prove physical absence from the package.",
                "Declarations may appear on another package panel that was not submitted.",
                "OCR errors, blur, glare, orientation and packaging design may affect extraction.",
                "Legibility, prominence and placement require image-level or manual verification.",
                "Conditional declarations depend on the product/package category and applicable provisions.",
                "Final legal determination must be made by an authorized Legal Metrology officer."
            ],

            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
