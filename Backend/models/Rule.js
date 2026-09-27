const mongoose = require("mongoose");

const ruleSchema = new mongoose.Schema(
    {
        ruleId: {
            type: String,
            required: true,
            unique: true,
            trim: true
        },

        category: {
            type: String,
            required: true,
            trim: true
        },

        subcategory: {
            type: String,
            default: null,
            trim: true
        },

        field: {
            type: String,
            required: true
        },

        requirement: {
            type: String,
            required: true
        },

        validationType: {
            type: String,
            required: true
        },

        required: {
            type: Boolean,
            default: true
        },

        source: {
            type: String,
            required: true
        },

        version: {
            type: String,
            default: "current"
        },

        effectiveFrom: {
            type: Date,
            default: null
        },

        exceptions: {
            type: [String],
            default: []
        },

        status: {
            type: String,
            enum: ["active", "inactive"],
            default: "active"
        }
    },
    {
        timestamps: true
    }
);

module.exports = mongoose.model("Rule", ruleSchema);
