const mongoose = require("mongoose");

const complianceResultSchema = new mongoose.Schema(
    {
        scanId: {
            type: mongoose.Schema.Types.ObjectId,
            ref: "Scan",
            required: true
        },

        ruleId: {
            type: mongoose.Schema.Types.ObjectId,
            ref: "Rule",
            required: true
        },

        field: {
            type: String,
            required: true
        },

        extractedValue: {
            type: String,
            default: null
        },

        status: {
            type: String,
            enum: [
                "PASS",
                "ISSUE_DETECTED",
                "REVIEW_REQUIRED"
            ],
            required: true
        },

        reason: {
            type: String,
            required: true
        },

        confidence: {
            type: Number,
            default: 0
        },

        evidence: {
            type: String,
            default: null
        }
    },
    {
        timestamps: true
    }
);

module.exports = mongoose.model(
    "ComplianceResult",
    complianceResultSchema
);
