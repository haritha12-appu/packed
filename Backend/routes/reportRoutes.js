const express = require("express");

const {
    getReportByScanId,
    createReport
} = require("../controllers/reportController");

const router = express.Router();

router.get("/:scanId", getReportByScanId);

router.post("/", createReport);

module.exports = router;
