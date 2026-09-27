const express = require("express");

const {
    getAllRules,
    getRulesByCategory,
    getRuleById,
    createRule,
    updateRule,
    deleteRule
} = require("../controllers/ruleController");

const router = express.Router();

router.get("/", getAllRules);

router.get("/category/:category", getRulesByCategory);

router.get("/:id", getRuleById);

router.post("/", createRule);

router.put("/:id", updateRule);

router.delete("/:id", deleteRule);

module.exports = router;
