const express = require("express");

const {
    uploadImage,
    scanPackage,
    getScanById
} = require("../controllers/scanController");

const upload = require("../middleware/uploadMiddleware");

const router = express.Router();

// Upload 1 to 6 package images
router.post(
    "/upload",
    upload.array("images", 6),
    uploadImage
);

// Start package scanning
router.post("/scan", scanPackage);

// Get scan by ID
router.get("/:id", getScanById);

module.exports = router;
