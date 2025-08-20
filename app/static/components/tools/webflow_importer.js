class WebflowImporter {
  constructor() {
    this.isProcessing = false;
    this.submitHandler = (e) => this.handleSubmit(e);
    this.initialize();
  }

  initialize() {
    const form = document.getElementById("webflow-importer-form");
    if (form) {
      // Remove any existing listener to prevent duplicates
      form.removeEventListener("submit", this.submitHandler);
      // Add the properly bound handler
      form.addEventListener("submit", this.submitHandler);
    }

    // File name display handlers
    document.getElementById("webflow-zip")?.addEventListener("change", function () {
      const zipFileNameEl = document.getElementById("zip-file-name");

      if (this.files.length > 0) {
        zipFileNameEl.textContent = this.files[0].name;
        zipFileNameEl.style.color = "#79ffdb"; // Change text color
      } else {
        zipFileNameEl.textContent = "No file selected";
        zipFileNameEl.style.color = ""; // Reset to default
      }
    });

    document.getElementById("screenshot")?.addEventListener("change", function () {
      const screenshotFileNameEl = document.getElementById("screenshot-file-name");

      if (this.files.length > 0) {
        screenshotFileNameEl.textContent = this.files[0].name;
        screenshotFileNameEl.style.color = "#79ffdb"; // Change text color
      } else {
        screenshotFileNameEl.textContent = "No file selected";
        screenshotFileNameEl.style.color = ""; // Reset to default
      }
    });

    // CMS toggle handler
    document.getElementById("enable-cms")?.addEventListener("change", function () {
      document.getElementById("cms-fields").style.display = this.checked ? "block" : "none";
    });
  }

  handleSubmit(e) {
    e.preventDefault();
    e.stopImmediatePropagation(); // Crucial to prevent duplicate submissions

    if (this.isProcessing) {
      console.log("Conversion already in progress - ignoring duplicate request");
      return;
    }

    this.startImport();
  }

  updateProgress(percent, message) {
    const progressBar = document.getElementById("import-progress-bar");
    const percentageText = document.querySelector(".percentage");
    const currentAction = document.querySelector(".current-action");
    const statusOutput = document.getElementById("status-output");

    if (progressBar) progressBar.style.width = `${percent}%`;
    if (percentageText) percentageText.textContent = `${percent}%`;
    if (currentAction) currentAction.textContent = message;

    if (statusOutput) {
      const timestamp = new Date().toLocaleTimeString();
      statusOutput.innerHTML += `<div>[${timestamp}] ${message}</div>`;
      statusOutput.scrollTop = statusOutput.scrollHeight;
    }
  }

  updateStatus(message, isError = false) {
    const statusOutput = document.getElementById("status-output");
    if (statusOutput) {
      const timestamp = new Date().toLocaleTimeString();
      const messageClass = isError ? "error-message" : "status-message";
      statusOutput.innerHTML += `<div>[${timestamp}] <span class="${messageClass}">${message}</span></div>`;
      statusOutput.scrollTop = statusOutput.scrollHeight;
    }
  }

  async startImport() {
    this.isProcessing = true;
    const button = document.getElementById("start-import");
    const originalContent = button.innerHTML;

    try {
      // Validate required fields
      const themeName = document.getElementById("theme-name").value.trim();
      const webflowZip = document.getElementById("webflow-zip").files[0];

      if (!themeName) {
        this.updateStatus("Error: Template name is required", true);
        return;
      }

      if (!webflowZip) {
        this.updateStatus("Error: Webflow ZIP file is required", true);
        return;
      }

      // Prepare form data
      const formData = new FormData(document.getElementById("webflow-importer-form"));

      // Update UI
      button.disabled = true;
      button.innerHTML =
        '<span class="button-icon">...</span><span class="button-text">Processing...</span>';
      this.updateProgress(0, "Preparing files");
      this.updateStatus("Starting conversion process...");

      // Single API call
      await this.sendConversionRequest(formData);
    } catch (error) {
      console.error("Conversion error:", error);
      this.updateStatus(`Error: ${error.message}`, true);
      this.updateProgress(0, "Conversion failed");
    } finally {
      button.disabled = false;
      button.innerHTML = originalContent;
      this.isProcessing = false;
    }
  }

  async sendConversionRequest(formData) {
    try {
      const response = await fetch("/convert", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Server error: ${response.status}`);
      }

      // Check for SEO report URL in headers
      const seoReportUrl = response.headers.get("X-SEO-Report-URL");
      if (seoReportUrl) {
        const seoReportsDiv = document.getElementById("seo-reports-url");
        if (seoReportsDiv) {
          seoReportsDiv.innerHTML = `
          <a href="${seoReportUrl}" 
             id="seoReportBtn" 
             class="btn btn-success" 
             target="_blank"
             style="display: inline-block; margin-top: 10px;">
             View SEO Report
          </a>
        `;
        }
      }

      // Get the filename from Content-Disposition header
      const contentDisposition = response.headers.get("content-disposition");
      let filename = "converted-theme.zip"; // Default fallback

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+?)"?(;|$)/i);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      // Handle ZIP response
      const contentType = response.headers.get("content-type");
      if (contentType?.includes("application/zip")) {
        const blob = await response.blob();
        this.downloadFile(blob, filename); // Use the extracted filename
        this.updateProgress(100, "Conversion complete!");
        this.updateStatus(`Downloading ${filename}`);
        return;
      }

      // Handle JSON response
      const result = await response.json();
      if (result.success) {
        this.updateProgress(100, "Conversion complete!");
        this.updateStatus("Conversion completed successfully!");
      } else {
        throw new Error(result.message || "Conversion failed");
      }
    } catch (error) {
      console.error("Request failed:", error);
      throw error;
    }
  }

  downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename; // Use the dynamic filename
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  }
}

// Initialize only once when DOM is loaded
if (!window.webflowImporterInitialized) {
  document.addEventListener("DOMContentLoaded", () => {
    new WebflowImporter();
  });
  window.webflowImporterInitialized = true;
}
