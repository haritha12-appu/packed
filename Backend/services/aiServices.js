// services/aiServices.js

const fs = require("fs");
const path = require("path");


// ============================================================
// FASTAPI AI SERVICE
// ============================================================

const AI_SERVICE_URL = "http://127.0.0.1:8000/analyze";


// ============================================================
// PROCESS PACKAGE IMAGES
// Accepts one image or multiple images of the SAME product
// ============================================================

const processPackageImages = async (imagePaths) => {

    try {

        // ----------------------------------------------------
        // Normalize input
        // ----------------------------------------------------

        if (!Array.isArray(imagePaths)) {
            imagePaths = [imagePaths];
        }

        if (imagePaths.length === 0) {
            throw new Error("No image files provided.");
        }

        if (imagePaths.length > 6) {
            throw new Error(
                "Maximum 6 images are allowed."
            );
        }


        console.log(
            `Sending ${imagePaths.length} image(s) to AI service...`
        );


        // ----------------------------------------------------
        // Check all images
        // ----------------------------------------------------

        for (const imagePath of imagePaths) {

            if (!fs.existsSync(imagePath)) {

                throw new Error(
                    `Image file not found: ${imagePath}`
                );
            }
        }


        // ----------------------------------------------------
        // Create multipart form
        // ----------------------------------------------------

        const formData = new FormData();


        // ----------------------------------------------------
        // Add ALL images using the same field name
        //
        // FastAPI:
        // files: list[UploadFile]
        // ----------------------------------------------------

        for (const imagePath of imagePaths) {

            const imageBuffer =
                fs.readFileSync(imagePath);

            const imageBlob =
                new Blob([imageBuffer]);

            formData.append(
                "files",
                imageBlob,
                path.basename(imagePath)
            );
        }


        // ----------------------------------------------------
        // Send to FastAPI
        // ----------------------------------------------------

        const response = await fetch(
            AI_SERVICE_URL,
            {
                method: "POST",

                body: formData,

                // OCR can take some time
                signal: AbortSignal.timeout(
                    600000
                )
            }
        );


        // ----------------------------------------------------
        // Read response
        // ----------------------------------------------------

        const result =
            await response.json();


        // ----------------------------------------------------
        // Handle FastAPI error
        // ----------------------------------------------------

        if (!response.ok) {

            throw new Error(
                result.detail ||
                "AI service returned an error"
            );
        }


        console.log(
            "AI processing completed successfully."
        );


        console.log(
            `Processed ${imagePaths.length} image(s).`
        );


        // ----------------------------------------------------
        // Return REAL AI result
        // ----------------------------------------------------

        return result;


    } catch (error) {

        console.error(
            "AI service error:",
            error.message
        );


        return {

            success: false,

            message:
                "AI processing failed",

            error:
                error.message
        };
    }
};


// ============================================================
// BACKWARD COMPATIBILITY
// Existing backend code may still call:
// processPackageImage(imagePath)
// ============================================================

const processPackageImage = async (imagePath) => {

    return processPackageImages([
        imagePath
    ]);
};


// ============================================================
// EXPORTS
// ============================================================

module.exports = {

    processPackageImage,

    processPackageImages

};
