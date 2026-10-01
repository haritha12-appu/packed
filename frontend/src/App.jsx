import { useState } from "react";

const MAX_IMAGES = 6;

const LEGAL_METROLOGY_RULES_URL =
  "https://upload.indiacode.nic.in/showfile?actid=AC_CH_60_1205_00002_00002_1560405527490&filename=9_the_legal_metrology_%28package_commodities%29_rules%2C_2011.pdf&type=rule";

const RULE_REFERENCES = [
  {
    rule: "Rule 6",
    title: "Mandatory declarations",
    text: "Rule 6 specifies declarations required on packages, subject to the applicable provisions and exceptions."
  },
  {
    rule: "Rule 6(1)(a)",
    title: "Manufacturer / packer / importer",
    text: "Name and address information relating to the manufacturer, packer or importer, as applicable."
  },
  {
    rule: "Rule 6(1)(b)",
    title: "Country of origin",
    text: "Country of origin declaration for imported packages, as applicable."
  },
  {
    rule: "Rule 6(1)(c)",
    title: "Common / generic name",
    text: "Common or generic name of the commodity contained in the package."
  },
  {
    rule: "Rule 6(1)(d)",
    title: "Net quantity",
    text: "Net quantity expressed using the applicable unit of weight, measure or number."
  },
  {
    rule: "Rule 6(1)(e)",
    title: "Relevant date declaration",
    text: "Applicable month and year declaration relating to manufacture, packing or importation."
  },
  {
    rule: "Rule 6(1)(g)",
    title: "Maximum Retail Price",
    text: "Maximum Retail Price declaration, inclusive of all taxes, subject to applicable provisions."
  },
  {
    rule: "Rule 6(1)(h)",
    title: "Consumer care",
    text: "Consumer-care information as required under the applicable provisions."
  },
  {
    rule: "Rule 6(1)(i)",
    title: "Dimensions",
    text: "Dimensions where the requirement is applicable to the commodity or package."
  },
  {
    rule: "Rule 6(1)(j) / Rule 6(11)",
    title: "Unit sale price",
    text: "Unit sale price provisions, subject to applicable conditions and exceptions."
  },
  {
    rule: "Rule 9",
    title: "Manner of declaration",
    text: "Declarations are subject to presentation requirements including legibility and prominence. Rule 9 also addresses the manner in which declarations are presented on packages."
  }
];

function App() {
  const [selectedImages, setSelectedImages] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showRules, setShowRules] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  // =========================================================
  // IMAGE SELECTION
  // =========================================================

  const handleImageChange = (event) => {
    const files = Array.from(event.target.files || []);

    if (!files.length) return;

    const remainingSlots =
      MAX_IMAGES - selectedImages.length;

    const newFiles =
      files.slice(0, remainingSlots);

    const newUrls = newFiles.map((file) =>
      URL.createObjectURL(file)
    );

    setSelectedImages((prev) => [
      ...prev,
      ...newFiles
    ]);

    setPreviewUrls((prev) => [
      ...prev,
      ...newUrls
    ]);

    setShowResults(false);
    setAnalysisResult(null);
    setErrorMessage("");

    event.target.value = "";
  };

  const handleRemoveImage = (index) => {
    if (previewUrls[index]) {
      URL.revokeObjectURL(previewUrls[index]);
    }

    setSelectedImages((prev) =>
      prev.filter((_, i) => i !== index)
    );

    setPreviewUrls((prev) =>
      prev.filter((_, i) => i !== index)
    );

    setShowResults(false);
    setAnalysisResult(null);
    setErrorMessage("");
  };

  // =========================================================
  // ANALYZE
  // =========================================================

  const handleAnalyze = async () => {
    if (!selectedImages.length) return;

    setAnalyzing(true);
    setShowResults(false);
    setAnalysisResult(null);
    setErrorMessage("");

    try {
      const formData = new FormData();

      selectedImages.forEach((image) => {
        formData.append("images", image);
      });

      const uploadResponse = await fetch(
        "https://packed-backend.onrender.com/api/scan/upload",
        {
          method: "POST",
          body: formData
        }
      );

      const uploadData =
        await uploadResponse.json();

      if (
        !uploadResponse.ok ||
        !uploadData.success
      ) {
        throw new Error(
          uploadData.message ||
          "Image upload failed"
        );
      }

      if (
        !uploadData.files ||
        !uploadData.files.length
      ) {
        throw new Error(
          "No uploaded image paths were returned."
        );
      }

      const imagePaths =
        uploadData.files.map(
          (file) => file.path
        );

      const scanResponse = await fetch(
        "https://packed-backend.onrender.com/api/scan/scan",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json"
          },
          body: JSON.stringify({
            imagePaths
          })
        }
      );

      const scanData =
        await scanResponse.json();

      if (
        !scanResponse.ok ||
        !scanData.success
      ) {
        throw new Error(
          scanData.message ||
          "Package scanning failed"
        );
      }

      /*
       * IMPORTANT:
       * Backend returns one product-level result:
       *
       * scanData.results
       *
       * It is NOT an array.
       */
      setAnalysisResult(
        scanData.results
      );

      setShowResults(true);
    } catch (error) {
      console.error(
        "Analysis error:",
        error
      );

      setErrorMessage(
        error.message ||
        "Something went wrong while analyzing the product."
      );

      setShowResults(false);
    } finally {
      setAnalyzing(false);
    }
  };

  // =========================================================
  // RESET
  // =========================================================

  const handleReset = () => {
    previewUrls.forEach((url) =>
      URL.revokeObjectURL(url)
    );

    setSelectedImages([]);
    setPreviewUrls([]);
    setShowResults(false);
    setAnalysisResult(null);
    setErrorMessage("");
  };

  // =========================================================
  // PRINT
  // =========================================================

  const handlePrint = () => {
    window.print();
  };

  // =========================================================
  // BACKEND RESULT
  // =========================================================

  const result =
    analysisResult || {};

  const product =
    result.product || {};

  const ocr =
    result.ocr || {};

  const nlp =
    result.nlp || {};

  const compliance =
    result.compliance || {};

  const assessment =
    compliance.assessment || {};

  const summary =
    compliance.summary || {};

  const declarations =
    compliance.declarations || [];

  const limitations =
    compliance.limitations || [];

  // =========================================================
  // HELPERS
  // =========================================================

  const getFieldValue = (field) => {
    const value =
      nlp[field]?.value;

    if (
      value === null ||
      value === undefined ||
      String(value).trim() === ""
    ) {
      return "Not detected";
    }

    return value;
  };

  const formatConfidence = (value) => {
    if (
      value === null ||
      value === undefined ||
      Number(value) <= 0
    ) {
      return "Not available";
    }

    return `${(
      Number(value) * 100
    ).toFixed(1)}%`;
  };

  const getStatusClass = (status) => {
    if (
      status === "DETECTED" ||
      status === "PASS"
    ) {
      return "pass";
    }

    if (
      status === "NOT_DETECTED" ||
      status === "FAIL"
    ) {
      return "warning";
    }

    return "review";
  };

  const getStatusIcon = (status) => {
    if (
      status === "DETECTED" ||
      status === "PASS"
    ) {
      return "✓";
    }

    if (
      status === "NOT_DETECTED" ||
      status === "FAIL"
    ) {
      return "✗";
    }

    if (status === "NOT_APPLICABLE") {
      return "—";
    }

    return "!";
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "DETECTED":
        return "DETECTED";

      case "NOT_DETECTED":
        return "NOT DETECTED";

      case "NOT_APPLICABLE":
        return "NOT APPLICABLE";

      case "REVIEW":
        return "REVIEW";

      default:
        return status || "UNKNOWN";
    }
  };

  const notDetected =
    declarations.filter(
      (item) =>
        item.status === "NOT_DETECTED"
    );

  const reviewItems =
    declarations.filter(
      (item) =>
        item.status === "REVIEW"
    );

  const getOverallClass = () => {
    if (
      assessment.status ===
      "SCREENING_PASS"
    ) {
      return "pass";
    }

    return "warning";
  };

  const getOverallText = () => {
    switch (
      assessment.status
    ) {
      case "SCREENING_PASS":
        return "SCREENING PASS";

      case "POTENTIAL_NON_COMPLIANCE":
        return "POTENTIAL NON-COMPLIANCE";

      case "VERIFICATION_REQUIRED":
        return "VERIFICATION REQUIRED";

      default:
        return "SCREENING COMPLETED";
    }
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="header">

        <div className="brand">

          <div className="brand-icon">
            ⚖
          </div>

          <div>
            <h1>
              Packaged Compliance
            </h1>

            <p>
              AI-Powered Legal Metrology Verification
            </p>
          </div>

        </div>

        <button
          className="rule-badge"
          type="button"
          onClick={() => setShowRules(true)}
          aria-label="Open Legal Metrology Rules, 2011"
        >
          <span>
            LEGAL METROLOGY
          </span>

          <small>
            Rules, 2011 ↗
          </small>
        </button>

      </header>


      {/* =====================================================
          RULES MODAL
      ===================================================== */}

      {showRules && (

        <div
          className="rules-overlay"
          onClick={() => setShowRules(false)}
        >

          <div
            className="rules-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="rules-modal-header">

              <div>

                <span className="rules-kicker">
                  LEGAL REFERENCE
                </span>

                <h2>
                  Legal Metrology
                  <span> Rules, 2011</span>
                </h2>

                <p>
                  Key provisions referenced by
                  the packaged-commodity screening
                  configuration.
                </p>

              </div>

              <button
                className="rules-close"
                type="button"
                onClick={() =>
                  setShowRules(false)
                }
                aria-label="Close rules"
              >
                ×
              </button>

            </div>


            <div className="rules-content">

              <div className="rules-intro">

                <strong>
                  Rules used for automated screening
                </strong>

                <p>
                  The system maps extracted package
                  declarations to relevant provisions
                  of the Legal Metrology (Packaged
                  Commodities) Rules, 2011.
                </p>

              </div>


              {RULE_REFERENCES.map(
                (item) => (

                  <div
                    className="rule-reference-item"
                    key={item.rule}
                  >

                    <div className="rule-reference-number">
                      {item.rule}
                    </div>

                    <div>

                      <h3>
                        {item.title}
                      </h3>

                      <p>
                        {item.text}
                      </p>

                    </div>

                  </div>

                )
              )}


              <div className="rules-disclaimer">

                <strong>
                  Screening reference only
                </strong>

                <p>
                  A declaration not detected by
                  OCR does not by itself establish
                  physical absence or legal
                  non-compliance. Package
                  verification and final legal
                  determination remain with the
                  competent authority.
                </p>

              </div>

            </div>


            <div className="rules-footer">

              <div>

                <span>
                  OFFICIAL SOURCE
                </span>

                <p>
                  Verify the complete rules and
                  amendments directly through
                  India Code.
                </p>

              </div>

              <a
                href={LEGAL_METROLOGY_RULES_URL}
                target="_blank"
                rel="noopener noreferrer"
              >
                View complete Rules, 2011 ↗
              </a>

            </div>

          </div>

        </div>

      )}


      <main>

        {/* =================================================
            HERO
        ================================================= */}

        <section className="hero">

          <div className="hero-content">

            <div className="hero-label">
              AI-POWERED COMPLIANCE SCREENING
            </div>

            <h2>
              Verify Packaged Commodity
              <span> Compliance</span>
            </h2>

            <p>
              Upload one or more product images
              to automatically extract mandatory
              declarations, check Legal Metrology
              requirements, and identify potential
              compliance issues.
            </p>

            <div className="pipeline">

              <div className="pipeline-item">
                <strong>01</strong>
                <span>Upload</span>
              </div>

              <div className="pipeline-line"></div>

              <div className="pipeline-item">
                <strong>02</strong>
                <span>Preprocess</span>
              </div>

              <div className="pipeline-line"></div>

              <div className="pipeline-item">
                <strong>03</strong>
                <span>Extract</span>
              </div>

              <div className="pipeline-line"></div>

              <div className="pipeline-item">
                <strong>04</strong>
                <span>Verify</span>
              </div>

            </div>

          </div>

        </section>


        {/* =================================================
            UPLOAD
        ================================================= */}

        <section className="upload-section">

          <div className="section-heading">

            <div>

              <span className="section-number">
                01
              </span>

              <h3>
                Upload Product Images
              </h3>

            </div>

            <p>
              Upload one or more clear images
              of different sides or views of
              the same packaged commodity.
            </p>

          </div>


          <div className="upload-card">

            {selectedImages.length === 0 ? (

              <label className="drop-zone">

                <input
                  type="file"
                  accept="image/*"
                  multiple
                  hidden
                  onChange={handleImageChange}
                />

                <div className="upload-icon">
                  ↑
                </div>

                <h4>
                  Upload Product Images
                </h4>

                <p>
                  Select one or multiple images
                </p>

                <span>
                  JPG, JPEG or PNG • Up to 6 images
                </span>

              </label>

            ) : (

              <div className="multi-image-preview">

                <div className="preview-header">

                  <div>

                    <span className="file-label">
                      SELECTED IMAGES
                    </span>

                    <h4>
                      {selectedImages.length}{" "}
                      {selectedImages.length === 1
                        ? "image"
                        : "images"}{" "}
                      selected
                    </h4>

                  </div>

                  <span className="image-count">
                    {selectedImages.length}/
                    {MAX_IMAGES}
                  </span>

                </div>


                <div className="image-grid">

                  {previewUrls.map(
                    (url, index) => (

                      <div
                        className="multi-image-item"
                        key={`${url}-${index}`}
                      >

                        <div className="multi-image-number">
                          {String(
                            index + 1
                          ).padStart(
                            2,
                            "0"
                          )}
                        </div>

                        <img
                          src={url}
                          alt={`Product view ${
                            index + 1
                          }`}
                        />

                        <button
                          className="remove-image-button"
                          type="button"
                          onClick={() =>
                            handleRemoveImage(
                              index
                            )
                          }
                        >
                          ×
                        </button>

                        <div className="image-view-label">
                          IMAGE {index + 1}
                        </div>

                      </div>

                    )
                  )}


                  {selectedImages.length <
                    MAX_IMAGES && (

                    <label className="add-image-card">

                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        hidden
                        onChange={
                          handleImageChange
                        }
                      />

                      <div className="add-image-icon">
                        +
                      </div>

                      <strong>
                        Add More Images
                      </strong>

                      <span>
                        {MAX_IMAGES -
                          selectedImages.length}{" "}
                        remaining
                      </span>

                    </label>

                  )}

                </div>


                <div className="upload-actions">

                  <button
                    className="change-button"
                    type="button"
                    onClick={handleReset}
                  >
                    Clear All Images
                  </button>

                </div>

              </div>

            )}

          </div>


          {errorMessage && (

            <div className="error-message">

              <strong>
                Analysis failed:
              </strong>{" "}

              {errorMessage}

            </div>

          )}


          <div className="analyze-container">

            <button
              className="analyze-button"
              type="button"
              onClick={handleAnalyze}
              disabled={
                selectedImages.length === 0 ||
                analyzing
              }
            >

              {analyzing ? (

                <>
                  <span className="spinner"></span>

                  ANALYZING{" "}
                  {selectedImages.length}{" "}
                  {selectedImages.length === 1
                    ? "IMAGE"
                    : "IMAGES"}...
                </>

              ) : (

                <>
                  ANALYZE PRODUCT
                  <span>→</span>
                </>

              )}

            </button>

          </div>


          {analyzing && (

            <div className="processing-card">

              <div className="processing-header">

                <span className="processing-dot"></span>

                AI ANALYSIS IN PROGRESS

              </div>

              <div className="processing-steps">

                <div className="processing-step active">
                  <span>✓</span>
                  Image preprocessing
                </div>

                <div className="processing-step active">
                  <span>✓</span>
                  Text extraction
                </div>

                <div className="processing-step active">
                  <span>✓</span>
                  Field extraction
                </div>

                <div className="processing-step active">
                  <span>✓</span>
                  Rule verification
                </div>

              </div>

            </div>

          )}

        </section>


        {/* =================================================
            RESULTS
        ================================================= */}

        {showResults && analysisResult && (

          <section className="results-section">

            <div className="result-heading">

              <div>

                <span className="section-number">
                  02
                </span>

                <h3>
                  Compliance Screening Report
                </h3>

              </div>

              <div className="result-status">
                <span></span>
                SCREENING COMPLETED
              </div>

            </div>


            {/* =====================================================
                FORMAL SCREENING ASSESSMENT
                ===================================================== */}

            <div className="formal-assessment-card">

              <div className="formal-assessment-header">

                <div>

                  <span className="formal-kicker">
                    AUTOMATED COMPLIANCE SCREENING
                  </span>

                  <h2>
                    Screening Assessment
                  </h2>

                  <p>
                    Preliminary assessment based on the
                    declarations detected from the submitted
                    product images.
                  </p>

                </div>

                <div
                  className={`formal-status ${getOverallClass()}`}
                >

                  <span className="formal-status-icon">
                    {assessment.status ===
                    "SCREENING_PASS"
                      ? "✓"
                      : "!"}
                  </span>

                  <div>

                    <span>
                      ASSESSMENT STATUS
                    </span>

                    <strong>
                      {getOverallText()}
                    </strong>

                  </div>

                </div>

              </div>


              <div className="formal-assessment-body">

                <div className="assessment-statement">

                  <span className="statement-label">
                    SCREENING CONCLUSION
                  </span>

                  <p>
                    {assessment.reason ||
                      "The submitted package images were screened against the configured Legal Metrology declaration requirements."}
                  </p>

                </div>


                <div className="assessment-facts">

                  <div className="assessment-fact">

                    <span>
                      PRODUCT IMAGES
                    </span>

                    <strong>
                      {typeof ocr.successful_images === "number"
                        ? ocr.successful_images
                        : Array.isArray(ocr.successful_images)
                          ? ocr.successful_images.length
                          : 0}
                    </strong>

                  </div>


                  <div className="assessment-fact">

                    <span>
                      DECLARATIONS CHECKED
                    </span>

                    <strong>
                      {summary.total_checks ??
                        declarations.length}
                    </strong>

                  </div>


                  <div className="assessment-fact">

                    <span>
                      DETECTED
                    </span>

                    <strong>
                      {summary.detected ?? 0}
                    </strong>

                  </div>


                  <div className="assessment-fact">

                    <span>
                      REQUIRES ATTENTION
                    </span>

                    <strong>
                      {(summary.not_detected ?? 0) +
                        (summary.review_required ?? 0)}
                    </strong>

                  </div>

                </div>

              </div>

            </div>


            {/* =====================================================
                SECTION 01 — DECLARATION VERIFICATION
                ===================================================== */}

            <div className="declarations-card">

              <div className="compliance-section-heading">

                <div>

                  <span>
                    01
                  </span>

                  <div>

                    <div className="card-label">
                      COMPLIANCE
                    </div>

                    <h3>
                      Declaration Verification
                    </h3>

                  </div>

                </div>

                <p>
                  Declarations detected from the submitted
                  package images and mapped to the configured
                  Legal Metrology provisions.
                </p>

              </div>


              <div className="declaration-table-wrap">

                <table className="declaration-table">

                  <thead>

                    <tr>

                      <th>
                        Declaration
                      </th>

                      <th>
                        Status
                      </th>

                      <th>
                        Detected Value
                      </th>

                      <th>
                        Applicable Rule
                      </th>

                    </tr>

                  </thead>

                  <tbody>

                    {declarations.map(
                      (item, index) => (

                        <tr
                          key={`${item.field || item.declaration}-${index}`}
                        >

                          <td>
                            <strong>
                              {item.declaration}
                            </strong>
                          </td>

                          <td>

                            <span
                              className={`status-pill ${getStatusClass(
                                item.status
                              )}`}
                            >

                              <span>
                                {getStatusIcon(
                                  item.status
                                )}
                              </span>

                              {getStatusLabel(
                                item.status
                              )}

                            </span>

                          </td>

                          <td>

                            {item.value !== null &&
                            item.value !== undefined &&
                            String(
                              item.value
                            ).trim() !== ""
                              ? item.value
                              : "Not detected"}

                          </td>

                          <td>
                            {item.rule || "—"}
                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>


              <div className="table-note">

                <strong>
                  Interpretation:
                </strong>

                <span>
                  “Not detected” means the declaration was
                  not confidently recovered from the submitted
                  images. It does not by itself establish that
                  the declaration is physically absent.
                </span>

              </div>

            </div>


            {/* =====================================================
                SECTION 02 — ISSUES REQUIRING ATTENTION
                ===================================================== */}

            <div className="attention-card">

              <div className="compliance-section-heading">

                <div>

                  <span>
                    02
                  </span>

                  <div>

                    <div className="card-label">
                      COMPLIANCE
                    </div>

                    <h3>
                      Issues Requiring Attention
                    </h3>

                  </div>

                </div>

                <p>
                  Missing declarations and visual checks
                  requiring verification.
                </p>

              </div>


              {notDetected.length === 0 &&
              reviewItems.length === 0 ? (

                <div className="attention-empty">

                  <span>
                    ✓
                  </span>

                  <div>

                    <strong>
                      No attention items identified
                    </strong>

                    <p>
                      No missing or review-required items
                      were identified by the configured
                      screening checks.
                    </p>

                  </div>

                </div>

              ) : (

                <div className="attention-list">

                  {[...notDetected, ...reviewItems].map(
                    (item, index) => (

                      <div
                        className={`attention-item ${
                          item.status === "REVIEW"
                            ? "review"
                            : "warning"
                        }`}
                        key={`attention-${index}`}
                      >

                        <div className="attention-icon">
                          {item.status === "REVIEW"
                            ? "!"
                            : "✗"}
                        </div>

                        <div className="attention-content">

                          <div className="attention-title">

                            <strong>
                              {item.declaration}
                            </strong>

                            <span
                              className={`status-pill ${getStatusClass(
                                item.status
                              )}`}
                            >
                              {getStatusLabel(
                                item.status
                              )}
                            </span>

                          </div>


                          <div className="attention-meta">

                            <div>

                              <span>
                                APPLICABLE RULE
                              </span>

                              <strong>
                                {item.rule ||
                                  "Applicable provision"}
                              </strong>

                            </div>


                            <div>

                              <span>
                                SCREENING FINDING
                              </span>

                              <p>
                                {item.reason ||
                                  "Manual verification required."}
                              </p>

                            </div>

                          </div>

                        </div>

                      </div>

                    )
                  )}

                </div>

              )}


              <div className="attention-global-note">

                <strong>
                  Officer verification required
                </strong>

                <p>
                  A declaration may be present on another
                  package panel, may be obscured or may not
                  have been correctly recognized by OCR.
                  Final legal determination should be made
                  through physical/package verification by
                  the competent authority.
                </p>

              </div>

            </div>


            {/* =====================================================
                VISUAL EVIDENCE
                ===================================================== */}

            <div className="evidence-card">

              <div className="card-label">
                VISUAL EVIDENCE
              </div>

              <div className="evidence-content">

                <div className="evidence-images">

                  {previewUrls.map(
                    (url, index) => (

                      <div
                        className="evidence-image"
                        key={`evidence-${url}-${index}`}
                      >

                        <img
                          src={url}
                          alt={`Compliance evidence ${
                            index + 1
                          }`}
                        />

                      </div>

                    )
                  )}

                </div>


                <div className="evidence-info">

                  <div className="evidence-status">

                    <span>
                      ✓
                    </span>

                    IMAGE EVIDENCE AVAILABLE

                  </div>

                  <h4>
                    Submitted package images
                  </h4>

                  <p>
                    These images form the visual evidence
                    used during OCR extraction and automated
                    screening. Legibility, prominence,
                    placement and other visual requirements
                    may require manual inspection.
                  </p>

                </div>

              </div>

            </div>


            {/* =====================================================
                AUTOMATED SCREENING NOTE
                ===================================================== */}

            <div className="explanation-card">

              <div className="explanation-icon">
                i
              </div>

              <div>

                <strong>
                  Automated Screening Note
                </strong>

                <p>
                  This system provides a preliminary
                  technology-assisted screening of package
                  declarations. It does not replace physical
                  inspection or the legal determination of
                  an authorized officer.
                </p>

                <ul>

                  <li>
                    OCR accuracy can be affected by blur,
                    glare, orientation, image quality and
                    packaging design.
                  </li>

                  <li>
                    Declarations may exist on package panels
                    that were not submitted for analysis.
                  </li>

                  <li>
                    Visual requirements such as legibility,
                    prominence and placement require
                    image-level or manual verification.
                  </li>

                </ul>

              </div>

            </div>


            {/* =====================================================
                SINGLE REPORT ACTION
                ===================================================== */}

            <div className="result-actions">

              <button
                className="primary-button"
                type="button"
                onClick={handlePrint}
              >
                PRINT / SAVE REPORT
                <span>
                  →
                </span>
              </button>

            </div>

          </section>

        )}

      </main>


      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer className="footer">

        <div>

          <strong>
            AI-Powered Packaged Commodity
            Compliance Verification
          </strong>

          <p>
            Prototype for automated Legal Metrology
            screening.
          </p>

        </div>

        <div className="footer-tech">
          OpenCV • PaddleOCR • NLP • Rule Engine
        </div>

      </footer>

    </div>
  );
}

export default App;
