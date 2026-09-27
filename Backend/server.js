const express = require("express");
const dotenv = require("dotenv");
const cors = require("cors");

const connectDB = require("./config/db");

// Load environment variables
dotenv.config();

// Connect to MongoDB
// MongoDB will be configured later.
// The backend can be started after MongoDB is available.
connectDB();

const app = express();

// Middleware
app.use(
    cors({
        origin: "http://localhost:5173"
    })
);

app.use(express.json());

// Routes
const scanRoutes = require("./routes/scanRoutes");
const ruleRoutes = require("./routes/ruleRoutes");
const reportRoutes = require("./routes/reportRoutes");

// Route URLs
app.use("/api/scan", scanRoutes);
app.use("/api/rules", ruleRoutes);
app.use("/api/reports", reportRoutes);

// Serve uploaded images
app.use("/uploads", express.static("uploads"));

// Home route
app.get("/", (req, res) => {
    res.json({
        success: true,
        message: "PackSure AI Backend is running"
    });
});

// Health check route
app.get("/api/health", (req, res) => {
    res.json({
        success: true,
        message: "Backend is healthy"
    });
});

// Port
const PORT = process.env.PORT || 5000;

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
