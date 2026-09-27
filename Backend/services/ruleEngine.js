// services/ruleEngine.js


// Check whether a text field is present
const checkTextPresent = (value) => {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return {
            status: "ISSUE_DETECTED",
            reason: "Required declaration was not detected"
        };
    }

    return {
        status: "PASS",
        reason: "Required declaration detected"
    };
};


// Check net quantity
const checkQuantity = (value) => {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return {
            status: "ISSUE_DETECTED",
            reason: "Net quantity was not detected"
        };
    }

    // Example format check
    const quantityPattern =
        /^[0-9]+(\.[0-9]+)?\s?(g|kg|ml|l|L|mg|m)$/i;

    if (!quantityPattern.test(value)) {
        return {
            status: "REVIEW_REQUIRED",
            reason: "Net quantity format needs verification"
        };
    }

    return {
        status: "PASS",
        reason: "Net quantity detected in a recognizable format"
    };
};


// Check MRP
const checkMRP = (value) => {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return {
            status: "ISSUE_DETECTED",
            reason: "MRP was not detected"
        };
    }

    return {
        status: "PASS",
        reason: "MRP declaration detected"
    };
};


// Check date
const checkDate = (value) => {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return {
            status: "ISSUE_DETECTED",
            reason: "Required date information was not detected"
        };
    }

    return {
        status: "PASS",
        reason: "Date information detected"
    };
};


// Select validator according to rule
const runValidator = (validator, value) => {

    switch (validator) {

        case "text_present":
            return checkTextPresent(value);

        case "quantity_validator":
            return checkQuantity(value);

        case "price_validator":
            return checkMRP(value);

        case "date_validator":
            return checkDate(value);

        default:
            return {
                status: "REVIEW_REQUIRED",
                reason: "Validator is not implemented"
            };
    }
};


// Main rule engine
const checkCompliance = async (extractedData, rules) => {

    try {

        const results = [];

        for (const rule of rules) {

            const field = rule.field;

            const value = extractedData[field];

            let result;

            // If the field is missing and rule is required
            if (
                (value === null ||
                value === undefined ||
                value === "") &&
                rule.required
            ) {

                result = {
                    status: "ISSUE_DETECTED",
                    reason: "Required declaration was not detected"
                };

            } else {

                result = runValidator(
                    rule.validationType,
                    value
                );
            }


            results.push({

                ruleId: rule.ruleId,

                field: field,

                extractedValue:
                    value ?? null,

                status: result.status,

                reason: result.reason,

                confidence:
                    value ? 95 : 0,

                evidence:
                    value ?? null
            });
        }


        // Determine overall result
        let overallStatus = "SCREENING_PASSED";


        const hasIssue = results.some(
            result =>
                result.status === "ISSUE_DETECTED"
        );


        const needsReview = results.some(
            result =>
                result.status === "REVIEW_REQUIRED"
        );


        if (hasIssue) {

            overallStatus = "ISSUE_DETECTED";

        } else if (needsReview) {

            overallStatus = "REVIEW_REQUIRED";
        }


        return {

            success: true,

            overallStatus: overallStatus,

            results: results
        };

    } catch (error) {

        console.error(
            "Rule engine error:",
            error.message
        );

        return {

            success: false,

            message: "Compliance checking failed",

            error: error.message
        };
    }
};


module.exports = {
    checkCompliance,
    runValidator
};
