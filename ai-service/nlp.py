
"""
NLP / field extraction layer for packaged commodity compliance.

Input:
    Combined OCR text from one or more images of the SAME product.

Output:
    Structured product fields with:
        - value
        - confidence

Important:
    "Not detected" means the field was not confidently recovered from OCR.
    It does NOT mean the declaration is legally absent.
"""

import re


# ============================================================
# BASIC HELPERS
# ============================================================

def make_field(value=None, confidence=0.0):
    return {
        "value": value,
        "confidence": round(float(confidence), 2)
    }


def clean_value(value):
    if value is None:
        return None

    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    if not value:
        return None

    return value


def normalize_lines(text):
    if text is None:
        return []

    if isinstance(text, list):
        raw_lines = text
    else:
        raw_lines = str(text).splitlines()

    lines = []

    for line in raw_lines:
        line = clean_value(line)

        if line:
            lines.append(line)

    return lines


def full_text(text):
    return "\n".join(normalize_lines(text))


def contains_any(text, phrases):
    text_upper = text.upper()

    return any(
        phrase.upper() in text_upper
        for phrase in phrases
    )


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_entity_text(text):
    text = clean_value(text)

    if not text:
        return None

    text = re.sub(r"^[\s:;,\-–—.#]+", "", text)
    text = re.sub(r"[\s:;,\-–—.#]+$", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_ocr_label(text):
    """
    Normalize OCR variations such as:

        M.R.P.
        MRP
        #MRP
        MFD.
        M.F.D
        USP
        U.S.P.

    into consistent labels.
    """

    if not text:
        return ""

    normalized = re.sub(r"[^A-Z0-9]", "", text.upper())

    mappings = {
        "MAXIMUMRETAILPRICE": "MRP",
        "MAXIMUMRETAILPRICEINCLUSIVE": "MRP",

        "MRP": "MRP",

        "MFG": "MFG",
        "MFD": "MFD",
        "PKD": "PKD",

        "UNITSALEPRICE": "USP",
        "UNITPRICE": "USP",
        "USP": "USP",
    }

    return mappings.get(normalized, normalized)


def looks_like_marketing_text(text):
    if not text:
        return False

    marketing_phrases = [
        "LONG LASTING",
        "MOISTURIZATION",
        "MOISTURISATION",
        "SKIN'S MOISTURE",
        "SKINS MOISTURE",
        "CLINICAL STUDY",
        "RESTORE DRY SKIN",
        "DRY SKIN",
        "TRIPLES SKIN",
        "SOFT SKIN",
        "SMOOTH SKIN",
        "GLOWING SKIN",
        "BEAUTIFUL SKIN",
        "NOURISHING",
        "HYDRATING",
        "HYDRATION",
        "FEEL THE",
        "NEW FORMULA",
        "ADVANCED FORMULA",
    ]

    return contains_any(text, marketing_phrases)


def looks_like_quantity(text):
    if not text:
        return False

    text = clean_value(text)

    if not text:
        return False

    quantity_pattern = re.compile(
        r"""
        ^\s*
        (?:₹|RS\.?|INR)?\s*
        \d+(?:[.,]\d+)?
        \s*
        (?:ML|L|G|KG|MG|MCG|CM|MM|M|PCS?|PIECES?)
        \s*$
        """,
        re.IGNORECASE | re.VERBOSE
    )

    return bool(quantity_pattern.fullmatch(text))


def looks_like_date(text):
    if not text:
        return False

    text = clean_value(text)

    date_patterns = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"\d{1,2}[/-]\d{2,4}",
        r"\d{4}[/-]\d{1,2}",
        r"\d{1,2}\.\d{2,4}",
    ]

    return any(
        re.fullmatch(pattern, text)
        for pattern in date_patterns
    )


def looks_like_plausible_entity(text):
    """
    Used for brand/manufacturer/marketer style fields.

    Prevents OCR garbage such as:
        20 ml
        LIC
        BY
        MFG
        MRP
        USP
        dates
        pure numeric codes
    """

    text = clean_entity_text(text)

    if not text:
        return False

    normalized = re.sub(
        r"[^A-Z0-9]",
        "",
        text.upper()
    )

    blocked = {
        "BY",
        "LIC",
        "MKTD",
        "MFG",
        "MFD",
        "MRP",
        "USP",
        "PKD",
        "SEEABOVE",
        "INDIA",
        "MADEININDIA",
        "BODYLOTION",
        "BODYLOTIONMADEININDIA",
    }

    if normalized in blocked:
        return False

    # Quantity must never become a brand/entity.
    if looks_like_quantity(text):
        return False

    # Date must never become a brand/entity.
    if looks_like_date(text):
        return False

    # Pure numbers are usually OCR codes.
    if re.fullmatch(r"\d+", text):
        return False

    # Very short fragments are unreliable.
    if len(text) < 3:
        return False

    # Marketing slogans are not entity names.
    if looks_like_marketing_text(text):
        return False

    return True


# ============================================================
# BRAND
# ============================================================

def extract_brand(lines):
    """
    Conservative brand extraction.

    We do NOT hardcode product brands such as Vaseline.
    A brand is returned only when OCR provides reasonable evidence.
    """

    # Explicit brand labels.
    explicit_patterns = [
        r"\bBRAND\s*[:\-]\s*(.+)",
        r"\bBRAND\s+NAME\s*[:\-]\s*(.+)",
    ]

    for line in lines:
        for pattern in explicit_patterns:
            match = re.search(pattern, line, re.IGNORECASE)

            if match:
                candidate = clean_entity_text(match.group(1))

                if looks_like_plausible_entity(candidate):
                    return make_field(candidate, 0.90)

    # Common recognizable brand-style OCR lines.
    # Keep this conservative rather than guessing.
    for line in lines:
        candidate = clean_entity_text(line)

        if not candidate:
            continue

        if looks_like_quantity(candidate):
            continue

        if looks_like_date(candidate):
            continue

        upper = candidate.upper()

        # Known brand-like indicators.
        if upper in {
            "UNILEVER",
            "HUL",
            "HINDUSTAN UNILEVER",
        }:
            return make_field(candidate, 0.78)

    return make_field()


# ============================================================
# GENERIC NAME
# ============================================================

GENERIC_PRODUCTS = [
    "BODY LOTION",
    "HAND LOTION",
    "FACE CREAM",
    "FACE WASH",
    "MOISTURIZER",
    "MOISTURISER",
    "SHAMPOO",
    "CONDITIONER",
    "HAIR OIL",
    "HAIR OIL",
    "SOAP",
    "BATH SOAP",
    "DETERGENT",
    "DETERGENT POWDER",
    "TOOTHPASTE",
    "TOOTHBRUSH",
    "BISCUITS",
    "BISCUIT",
    "COOKIES",
    "COOKING OIL",
    "EDIBLE OIL",
    "RICE",
    "FLOUR",
    "ATTA",
    "SALT",
    "SUGAR",
    "TEA",
    "COFFEE",
    "SPICES",
    "MASALA",
    "CREAM",
    "LOTION",
    "POWDER",
    "LIQUID",
    "PERFUME",
    "DEODORANT",
    "SANITIZER",
    "HAND WASH",
    "DISHWASH",
    "DISHWASH LIQUID",
]


def extract_generic_name(lines):
    """
    Finds a product's generic/category name.

    Example:
        BODY LOTION. MADE IN INDIA. MKTD. BY LIC.

    returns:
        Body Lotion
    """

    # Prefer longer / more specific terms first.
    sorted_products = sorted(
        GENERIC_PRODUCTS,
        key=len,
        reverse=True
    )

    for line in lines:
        upper = line.upper()

        for product in sorted_products:
            if product in upper:
                return make_field(
                    product.title(),
                    0.88
                )

    return make_field()


# ============================================================
# PRODUCT NAME
# ============================================================

def extract_product_name(lines, brand_field, generic_field):
    brand = brand_field.get("value")
    generic = generic_field.get("value")

    # If we have both a reliable brand and generic name.
    if brand and generic:
        return make_field(
            f"{brand} {generic}".strip(),
            0.92
        )

    # Prefer generic name over quantity / marketing text.
    if generic:
        return make_field(
            generic,
            0.90
        )

    # Look for explicit product name.
    patterns = [
        r"\bPRODUCT\s*NAME\s*[:\-]\s*(.+)",
        r"\bNAME\s*OF\s*PRODUCT\s*[:\-]\s*(.+)",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                candidate = clean_entity_text(match.group(1))

                if (
                    candidate
                    and not looks_like_quantity(candidate)
                    and not looks_like_date(candidate)
                    and not looks_like_marketing_text(candidate)
                ):
                    return make_field(candidate, 0.80)

    return make_field()


# ============================================================
# MANUFACTURER
# ============================================================

def extract_manufacturer(lines):
    patterns = [
        r"(?:MANUFACTURED\s+BY|MANUFACTURER)\s*[:\-]?\s*(.+)",
        r"MANUFACTURED\s+AND\s+MARKETED\s+BY\s*[:\-]?\s*(.+)",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                candidate = clean_entity_text(match.group(1))

                if looks_like_plausible_entity(candidate):
                    return make_field(candidate, 0.90)

    return make_field()


# ============================================================
# PACKER
# ============================================================

def extract_packer(lines):
    patterns = [
        r"(?:PACKED\s+BY|PACKER)\s*[:\-]?\s*(.+)",
        r"(?:PACKAGED\s+BY)\s*[:\-]?\s*(.+)",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                candidate = clean_entity_text(match.group(1))

                if looks_like_plausible_entity(candidate):
                    return make_field(candidate, 0.90)

    return make_field()


# ============================================================
# IMPORTER
# ============================================================

def extract_importer(lines):
    patterns = [
        r"IMPORTER\s*[:\-]?\s*(.+)",
        r"IMPORTED\s+BY\s*[:\-]?\s*(.+)",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                candidate = clean_entity_text(match.group(1))

                if looks_like_plausible_entity(candidate):
                    return make_field(candidate, 0.92)

    return make_field()


# ============================================================
# MARKETER
# ============================================================

def extract_marketer(lines):
    patterns = [
        r"MARKETED\s+BY\s*[:\-]?\s*(.+)",
        r"MARKETER\s*[:\-]?\s*(.+)",
        r"MKTD\.\s*BY\s*(.+)",
        r"MKTD\s+BY\s*(.+)",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                candidate = clean_entity_text(match.group(1))

                if looks_like_plausible_entity(candidate):
                    return make_field(candidate, 0.88)

    return make_field()


# ============================================================
# COUNTRY OF ORIGIN
# ============================================================

def extract_country(lines):
    patterns = [
        r"COUNTRY\s+OF\s+ORIGIN\s*[:\-]?\s*([A-Za-z ]+)",
        r"MADE\s+IN\s+([A-Za-z ]+)",
        r"PRODUCT\s+OF\s+([A-Za-z ]+)",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                candidate = clean_entity_text(match.group(1))

                if candidate:
                    candidate = candidate.upper()

                    # Stop common trailing words.
                    candidate = re.split(
                        r"\b(?:MFG|MFD|PKD|MRP|BY|MKTD)\b",
                        candidate,
                        maxsplit=1,
                        flags=re.IGNORECASE
                    )[0].strip()

                    if candidate:
                        return make_field(
                            candidate,
                            0.95
                        )

    return make_field()


# ============================================================
# IMPORTED STATUS
# ============================================================

def determine_imported(
    lines,
    importer_field,
    country_field
):
    importer = importer_field.get("value")
    country = country_field.get("value")

    if importer:
        return make_field(True, 0.95)

    if country:
        if country.upper() == "INDIA":
            return make_field(False, 0.90)

        return make_field(True, 0.85)

    text = full_text(lines)

    if re.search(
        r"\bIMPORTED\b",
        text,
        re.IGNORECASE
    ):
        return make_field(True, 0.85)

    return make_field(None, 0.0)


# ============================================================
# NET QUANTITY
# ============================================================

def extract_quantity(lines):
    patterns = [
        r"NET\s+(?:VOL(?:UME)?|WT|WEIGHT|QTY|QUANTITY)"
        r"\s*[:\-]?\s*"
        r"((?:\d+(?:\.\d+)?)\s*"
        r"(?:ML|L|G|KG|MG|MCG|PCS?|PIECES?))",

        r"NET\s+VOL\.\s*"
        r"((?:\d+(?:\.\d+)?)\s*"
        r"(?:ML|L|G|KG|MG))",

        r"NET\s+WEIGHT\s*[:\-]?\s*"
        r"((?:\d+(?:\.\d+)?)\s*"
        r"(?:G|KG|MG))",

        r"NET\s+QUANTITY\s*[:\-]?\s*"
        r"((?:\d+(?:\.\d+)?)\s*"
        r"(?:ML|L|G|KG|MG|PCS?|PIECES?))",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                value = clean_value(match.group(1))

                return make_field(
                    value,
                    0.90
                )

    # Fallback:
    # Search for standalone quantity values.
    for line in lines:
        match = re.fullmatch(
            r"\s*(\d+(?:\.\d+)?)\s*"
            r"(ML|L|G|KG|MG|MCG|PCS?|PIECES?)\s*",
            line,
            re.IGNORECASE
        )

        if match:
            value = f"{match.group(1)} {match.group(2)}"

            return make_field(
                value,
                0.75
            )

    return make_field()


# ============================================================
# MRP
# ============================================================

def extract_price_from_text(text):
    if not text:
        return None

    patterns = [
        r"(?:₹|RS\.?|INR)\s*"
        r"(\d+(?:\.\d{1,2})?)",

        r"(\d+(?:\.\d{1,2})?)\s*/-",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            value = match.group(1)

            # Don't treat quantities as prices.
            after = text[match.end():].strip()

            if re.match(
                r"^(?:ML|L|G|KG|MG)\b",
                after,
                re.IGNORECASE
            ):
                continue

            return f"₹{value}"

    return None


def extract_mrp(lines):
    """
    Handles examples such as:

        MRP ₹299
        MRP ₹299/-
        MRP: Rs. 299
        #MRP ₹299
        M.R.P. ₹299
        MAXIMUM RETAIL PRICE ₹299

    Also handles label/value split across OCR lines.
    """

    mrp_labels = [
        "MRP",
        "MAXIMUM RETAIL PRICE",
        "MAXIMUM RETAIL PRICE INCLUSIVE",
    ]

    for i, line in enumerate(lines):
        normalized = normalize_ocr_label(line)

        is_mrp_line = (
            normalized == "MRP"
            or "MAXIMUM RETAIL PRICE" in line.upper()
            or re.search(
                r"(?:#\s*)?M\.?\s*R\.?\s*P\.?",
                line,
                re.IGNORECASE
            )
        )

        if not is_mrp_line:
            continue

        # Same line.
        price = extract_price_from_text(line)

        if price:
            return make_field(price, 0.95)

        # Next few OCR lines.
        for j in range(i + 1, min(i + 4, len(lines))):
            candidate = lines[j]

            price = extract_price_from_text(candidate)

            if price:
                return make_field(price, 0.90)

            # Plain numeric value on next line.
            plain = re.fullmatch(
                r"\s*(\d+(?:\.\d{1,2})?)\s*(?:/-)?\s*",
                candidate
            )

            if plain:
                number = plain.group(1)

                # Avoid dates.
                if not looks_like_date(candidate):
                    return make_field(
                        f"₹{number}",
                        0.82
                    )

    return make_field()


# ============================================================
# UNIT SALE PRICE
# ============================================================

def extract_unit_sale_price(lines):
    """
    USP / Unit Sale Price is extracted only when the OCR
    clearly indicates that the number is a price.

    Prevents errors such as:

        USP0.550ml

    being interpreted as:

        ₹0
    """

    patterns = [
        r"(?:UNIT\s+SALE\s+PRICE|UNIT\s+PRICE)"
        r"\s*[:\-]?\s*"
        r"((?:₹|RS\.?|INR)\s*\d+(?:\.\d{1,2})?)",

        r"(?:U\.?\s*S\.?\s*P\.?)"
        r"\s*[:\-]?\s*"
        r"((?:₹|RS\.?|INR)\s*\d+(?:\.\d{1,2})?)",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                value = clean_value(match.group(1))

                value = re.sub(
                    r"^(RS\.?|INR)\s*",
                    "₹",
                    value,
                    flags=re.IGNORECASE
                )

                return make_field(
                    value,
                    0.88
                )

    return make_field()


# ============================================================
# DATE HELPERS
# ============================================================

DATE_PATTERN = (
    r"(?:"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|"
    r"\d{1,2}[/-]\d{2,4}"
    r"|"
    r"\d{4}[/-]\d{1,2}"
    r"|"
    r"\d{1,2}\.\d{2,4}"
    r")"
)


def extract_date_from_line(line):
    if not line:
        return None

    match = re.search(
        DATE_PATTERN,
        line
    )

    if match:
        return match.group(0)

    return None


def extract_date_value(
    lines,
    labels,
    confidence=0.90
):
    """
    Searches:
        label + date on same line

    and:
        label
        date

    and up to 3 lines after the label.

    This is important for OCR like:

        MFG.
        06/28
    """

    for i, line in enumerate(lines):
        upper = line.upper()

        if not any(
            label.upper() in upper
            for label in labels
        ):
            continue

        # Date on same line.
        date = extract_date_from_line(line)

        if date:
            return make_field(
                date,
                confidence
            )

        # Date on following lines.
        for j in range(
            i + 1,
            min(i + 4, len(lines))
        ):
            candidate = lines[j]

            # Stop if another strong declaration label starts.
            candidate_upper = candidate.upper()

            if any(
                stop in candidate_upper
                for stop in [
                    "MRP",
                    "USP",
                    "NET VOL",
                    "NET WT",
                    "IMPORTER",
                    "MANUFACTURER",
                    "PACKED BY",
                    "MARKETED BY",
                ]
            ):
                continue

            date = extract_date_from_line(candidate)

            if date:
                return make_field(
                    date,
                    confidence - 0.05
                )

    return make_field()


# ============================================================
# MANUFACTURING DATE
# ============================================================

def extract_manufacturing_date(lines):
    return extract_date_value(
        lines,
        labels=[
            "MFG",
            "M.F.G",
            "MFG.",
            "MANUFACTURING DATE",
            "MANUFACTURED DATE",
            "MFD",
            "M.F.D",
            "MFD.",
        ],
        confidence=0.90
    )


# ============================================================
# PACKED DATE
# ============================================================

def extract_packed_date(lines):
    return extract_date_value(
        lines,
        labels=[
            "PKD",
            "P.K.D",
            "PKD.",
            "PACKED",
            "PACKING DATE",
            "DATE OF PACKING",
        ],
        confidence=0.90
    )


# ============================================================
# BEST BEFORE / USE BY
# ============================================================

def extract_best_before(lines):
    labels = [
        "BEST BEFORE",
        "BEST BEFORE USE",
        "USE BEFORE",
        "USE BY",
        "EXPIRY",
        "EXP",
    ]

    for i, line in enumerate(lines):
        upper = line.upper()

        if not any(
            label in upper
            for label in labels
        ):
            continue

        # Same line.
        match = re.search(
            r"(?:BEST\s+BEFORE|USE\s+BEFORE|USE\s+BY|EXPIRY|EXP)"
            r".{0,20}?"
            r"(\d+\s*(?:MONTHS?|YEARS?|DAYS?))",
            line,
            re.IGNORECASE
        )

        if match:
            return make_field(
                match.group(1),
                0.90
            )

        # Following lines.
        for j in range(
            i + 1,
            min(i + 3, len(lines))
        ):
            candidate = lines[j]

            match = re.search(
                r"(\d+\s*(?:MONTHS?|YEARS?|DAYS?))",
                candidate,
                re.IGNORECASE
            )

            if match:
                return make_field(
                    match.group(1),
                    0.82
                )

    return make_field()


# ============================================================
# CONSUMER CARE
# ============================================================

def extract_consumer_care(lines):
    patterns = [
        r"(ARE[-\s]?QUERY/FEEDBACK[^,\n]*)",
        r"(CONSUMER\s+CARE[^,\n]*)",
        r"(CUSTOMER\s+CARE[^,\n]*)",
        r"(TOLL\s+FREE[^,\n]*)",
        r"(CONSUMER\s+COMPLAINT[^,\n]*)",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                return make_field(
                    clean_value(match.group(1)),
                    0.90
                )

    text = full_text(lines)

    if re.search(
        r"\bTOLL\s+FREE\b",
        text,
        re.IGNORECASE
    ):
        return make_field(
            "TOLL FREE",
            0.80
        )

    return make_field()


# ============================================================
# CONSUMER CARE PHONE
# ============================================================

def extract_consumer_care_phone(lines):
    """
    Only accept plausible Indian customer-care numbers.

    Rejects OCR fragments such as:
        62678704
    """

    patterns = [
        r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b",
        r"\b1800[\s-]?\d{6,8}\b",
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(
                pattern,
                line
            )

            if match:
                return make_field(
                    match.group(0),
                    0.92
                )

    return make_field()


# ============================================================
# CONSUMER CARE EMAIL
# ============================================================

def extract_consumer_care_email(lines):
    email_pattern = (
        r"\b[A-Z0-9._%+-]+"
        r"@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    )

    for line in lines:
        match = re.search(
            email_pattern,
            line,
            re.IGNORECASE
        )

        if match:
            return make_field(
                match.group(0),
                0.95
            )

    return make_field()


# ============================================================
# PRODUCT CATEGORY
# ============================================================

def detect_product_category(lines):
    text = full_text(lines).upper()

    category_map = {
        "cosmetic": [
            "BODY LOTION",
            "FACE CREAM",
            "FACE WASH",
            "MOISTURIZER",
            "MOISTURISER",
            "SHAMPOO",
            "CONDITIONER",
            "HAIR OIL",
            "SOAP",
            "CREAM",
            "LOTION",
            "PERFUME",
            "DEODORANT",
        ],

        "food": [
            "BISCUIT",
            "BISCUITS",
            "COOKIES",
            "RICE",
            "FLOUR",
            "ATTA",
            "SALT",
            "SUGAR",
            "TEA",
            "COFFEE",
            "SPICES",
            "MASALA",
            "COOKING OIL",
            "EDIBLE OIL",
        ],

        "household": [
            "DETERGENT",
            "DETERGENT POWDER",
            "DISHWASH",
            "DISHWASH LIQUID",
            "CLEANER",
        ],

        "personal_care": [
            "TOOTHPASTE",
            "TOOTHBRUSH",
            "HAND WASH",
            "SANITIZER",
        ],
    }

    for category, keywords in category_map.items():
        for keyword in keywords:
            if keyword in text:
                return make_field(
                    category,
                    0.90
                )

    return make_field()


# ============================================================
# VISUAL FIELDS
# ============================================================

def extract_visual_fields():
    """
    OCR/NLP alone cannot reliably determine:

        - physical legibility
        - prominence
        - placement
        - package dimensions

    These should eventually come from image analysis/manual
    verification rather than pretending OCR proved them.
    """

    return {
        "dimensions": make_field(),
        "legibility": make_field(),
        "prominence": make_field(),
        "placement": make_field(),
    }


# ============================================================
# MAIN NLP PIPELINE
# ============================================================

def process_ocr_text(text):
    """
    Main NLP processing function.

    Input:
        Combined OCR text from one or more images.

    Output:
        Structured fields.
    """

    lines = normalize_lines(text)

    # --------------------------------------------
    # Core product identity
    # --------------------------------------------

    brand = extract_brand(lines)

    generic_name = extract_generic_name(lines)

    product_name = extract_product_name(
        lines,
        brand,
        generic_name
    )

    # --------------------------------------------
    # Business entities
    # --------------------------------------------

    manufacturer = extract_manufacturer(lines)

    packer = extract_packer(lines)

    importer = extract_importer(lines)

    marketer = extract_marketer(lines)

    # --------------------------------------------
    # Origin / import
    # --------------------------------------------

    country = extract_country(lines)

    imported = determine_imported(
        lines,
        importer,
        country
    )

    # --------------------------------------------
    # Quantity / price
    # --------------------------------------------

    net_quantity = extract_quantity(lines)

    mrp = extract_mrp(lines)

    unit_sale_price = extract_unit_sale_price(lines)

    # --------------------------------------------
    # Dates
    # --------------------------------------------

    manufacturing_date = extract_manufacturing_date(
        lines
    )

    packed_date = extract_packed_date(
        lines
    )

    best_before = extract_best_before(
        lines
    )

    # --------------------------------------------
    # Consumer care
    # --------------------------------------------

    consumer_care = extract_consumer_care(
        lines
    )

    consumer_care_phone = extract_consumer_care_phone(
        lines
    )

    consumer_care_email = extract_consumer_care_email(
        lines
    )

    # --------------------------------------------
    # Category
    # --------------------------------------------

    product_category = detect_product_category(
        lines
    )

    # --------------------------------------------
    # Visual fields
    # --------------------------------------------

    visual_fields = extract_visual_fields()

    # --------------------------------------------
    # Final structured result
    # --------------------------------------------

    return {
        "product_name": product_name,

        "brand_name": brand,

        "generic_name": generic_name,

        "manufacturer": manufacturer,

        "packer": packer,

        "importer": importer,

        "marketer": marketer,

        "country_of_origin": country,

        "imported": imported,

        "net_quantity": net_quantity,

        "mrp": mrp,

        "unit_sale_price": unit_sale_price,

        "manufacturing_date": manufacturing_date,

        "packed_date": packed_date,

        "best_before": best_before,

        "consumer_care": consumer_care,

        "consumer_care_phone": consumer_care_phone,

        "consumer_care_email": consumer_care_email,

        "product_category": product_category,

        "dimensions": visual_fields["dimensions"],

        "legibility": visual_fields["legibility"],

        "prominence": visual_fields["prominence"],

        "placement": visual_fields["placement"],

        "raw_text": "\n".join(lines),
    }


# ============================================================
# BACKWARD-COMPATIBILITY TEST
# ============================================================

if __name__ == "__main__":
    sample_text = """
    BODY LOTION. MADE IN INDIA. MKTD. BY LIC.
    Net Vol. When Packed
    20 ml
    MFG.
    06/28
    MRP
    USP
    LEVER.CARE@UNILEVER.COM
    """

    result = process_ocr_text(sample_text)

    for key, value in result.items():
        if key != "raw_text":
            print(key, ":", value)
