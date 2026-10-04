const fs = require("fs");
const path = require("path");

const AI_SERVICE_URL =
    "https://packed-ai-service.onrender.com/analyze";

const processPackageImages = async (imagePaths) => {
    try {

        if (!Array.isArray(imagePaths)) {
            imagePaths = [imagePaths];
        }

        if (imagePaths.length === 0) {
            throw new Error("No image files provided.");
        }

        if (imagePaths.length > 6) {
            throw new Error("Maximum 6 images are allowed.");
        }

        console.log(
            `Sending ${imagePaths.length} image(s) to AI service...`
        );

        const formData = new FormData();

        for (const imagePath of imagePaths) {

            if (!fs.existsSync(imagePath)) {
                throw new Error(
                    `Image file not found: ${imagePath}`
                );
            }

            const imageBuffer = fs.readFileSync(imagePath);

            const imageBlob = new Blob([imageBuffer]);

            formData.append(
                "files",
                imageBlob,
                path.basename(imagePath)
            );
        }

        const response = await fetch(
            AI_SERVICE_URL,
            {
                method: "POST",
                body: formData,
               signal: AbortSignal.timeout(120000)
            }
        );

        const responseText = await response.text();

        console.log(
            "AI service HTTP status:",
            response.status
        );

        console.log(
            "AI service raw response:",
            responseText
        );

        let result;

        try {
            result = responseText
                ? JSON.parse(responseText)
                : {};
        } catch {
            throw new Error(
                `AI service returned invalid JSON`
            );
        }

        if (!response.ok) {
            throw new Error(
                result.detail ||
                result.error ||
                "AI service returned an error"
            );
        }

        console.log(
            "AI processing completed successfully."
        );

        return result;

    } catch (error) {

        console.error(
            "AI service error:",
            error.message
        );

        return {
            success: false,
            message: "AI processing failed",
            error: error.message
        };
    }
};


const processPackageImage = async (imagePath) => {
    return processPackageImages([imagePath]);
};


module.exports = {
    processPackageImage,
    processPackageImages
};
