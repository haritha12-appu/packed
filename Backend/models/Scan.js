const mongoose = require("mongoose");

const scanSchema = new mongoose.Schema(
    {
        userId: {
            type: mongoose.Schema.Types.ObjectId,
            ref: "User",
            required: true
        },

        imagePath: {
            type: String,
            required: true
        },

        category: {
            type: String,
            default: null
        },

        subcategory: {
            type: String,
            default: null
        },

        ocrText: {
            type: String,
            default: ""
        },

        extractedData: {
            productName: {
                type: String,
                default: null
            },

            manufacturer: {
                type: String,
                default: null
            },

            packer: {
                type: String,
                default: null
            },

            importer: {
                type: String,
                default: null
            },

            netQuantity: {
                type: String,
                default: null
            },

            mrp: {
                type: String,
                default: null
            },

            manufacturingDate: {
                type: String,
                default: null
            },

            bestBefore: {
                type: String,
                default: null
            },

            countryOfOrigin: {
                type: String,
                default: null
            },

            consumerCare: {
                type: String,
                default: null
            }
        },

        classificationConfidence: {
            type: Number,
            default: 0
        },

        status: {
            type: String,
            enum: [
                "PROCESSING",
                "SCREENING_PASSED",
                "ISSUE_DETECTED",
                "REVIEW_REQUIRED"
            ],
            default: "PROCESSING"
        }
    },
    {
        timestamps: true
    }
);

module.exports = mongoose.model("Scan", scanSchema);
