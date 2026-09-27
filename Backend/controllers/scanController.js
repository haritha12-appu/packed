// controllers/scanController.js

const {
    processPackageImages
} = require("../services/aiServices");


// ============================================================
// UPLOAD PACKAGE IMAGES
// ============================================================

const uploadImage = async (req, res) => {

    try {

        if (
            !req.files ||
            req.files.length === 0
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Please upload at least one package image"

            });
        }


        const files = req.files.map((file) => ({

            filename:
                file.filename,

            originalName:
                file.originalname,

            path:
                file.path,

            size:
                file.size,

            mimetype:
                file.mimetype

        }));


        res.status(200).json({

            success: true,

            message:
                `${files.length} package image(s) uploaded successfully`,

            files:
                files

        });


    } catch (error) {

        console.error(
            "Image upload error:",
            error
        );


        res.status(500).json({

            success: false,

            message:
                "Image upload failed",

            error:
                error.message

        });

    }
};


// ============================================================
// START PACKAGE SCANNING
// ============================================================

const scanPackage = async (req, res) => {

    try {

        const {
            imagePaths
        } = req.body;


        // ----------------------------------------------------
        // Validate image paths
        // ----------------------------------------------------

        if (
            !imagePaths ||
            !Array.isArray(imagePaths) ||
            imagePaths.length === 0
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Image paths are required"

            });

        }


        // ----------------------------------------------------
        // Maximum 6 images
        // ----------------------------------------------------

        if (imagePaths.length > 6) {

            return res.status(400).json({

                success: false,

                message:
                    "Maximum 6 package images are allowed"

            });

        }


        console.log(
            `Starting AI analysis for ${imagePaths.length} image(s)...`
        );


        // ----------------------------------------------------
        // PROCESS ALL IMAGES TOGETHER
        //
        // Important:
        // These images belong to ONE product.
        //
        // FastAPI performs:
        // OpenCV → OCR → combine → NLP → rule engine
        //
        // only ONCE at product level.
        // ----------------------------------------------------

        const aiResult =
            await processPackageImages(
                imagePaths
            );


        // ----------------------------------------------------
        // Handle AI failure
        // ----------------------------------------------------

        if (
            !aiResult ||
            aiResult.success === false
        ) {

            return res.status(500).json({

                success: false,

                message:
                    "AI analysis failed",

                error:
                    aiResult?.error ||
                    aiResult?.message ||
                    "Unknown AI service error"

            });

        }


        // ----------------------------------------------------
        // Return ONE product-level result
        // ----------------------------------------------------

        res.status(200).json({

            success: true,

            message:
                "Package scanning completed",

            totalImages:
                imagePaths.length,

            results:
                aiResult

        });


    } catch (error) {

        console.error(
            "Package scanning error:",
            error
        );


        res.status(500).json({

            success: false,

            message:
                "Package scanning failed",

            error:
                error.message

        });

    }
};


// ============================================================
// GET SCAN BY ID
// ============================================================

const getScanById = async (req, res) => {

    try {

        const scanId =
            req.params.id;


        res.status(200).json({

            success: true,

            message:
                "Scan details retrieved",

            scanId:
                scanId

        });


    } catch (error) {

        res.status(500).json({

            success: false,

            message:
                "Could not retrieve scan",

            error:
                error.message

        });

    }
};


// ============================================================
// EXPORTS
// ============================================================

module.exports = {

    uploadImage,

    scanPackage,

    getScanById

};
