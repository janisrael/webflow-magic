// document.getElementById("convert-form").addEventListener("submit", async function (event) {
//   event.preventDefault();

//   const formData = new FormData();
//   const webflowFolderInput = document.getElementById("webflow-folder");
//   const themeFolderInput = document.getElementById("theme-folder");

//   // Add files to FormData
//   for (let i = 0; i < webflowFolderInput.files.length; i++) {
//     formData.append("webflow_folder", webflowFolderInput.files[i]);
//   }
//   formData.append("theme_folder", themeFolderInput.value);

//   try {
//     const response = await fetch("/convert", {
//       method: "POST",
//       body: formData,
//     });

//     if (!response.ok) {
//       throw new Error("Conversion failed");
//     }

//     const blob = await response.blob();

//     // Extract filename
//     let filename = "converted-theme.zip";
//     const disposition = response.headers.get("Content-Disposition");
//     if (disposition) {
//       const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
//       if (match && match[1]) {
//         filename = match[1].replace(/['"]/g, "").trim();
//       }
//     }

//     // Ensure file picker is supported
//     if (!window.showSaveFilePicker) {
//       throw new Error("Your browser doesn't support file saving. Try Chrome or Edge.");
//     }

//     // Save prompt
//     const handle = await window.showSaveFilePicker({
//       suggestedName: filename,
//       types: [
//         {
//           description: "ZIP Files",
//           accept: { "application/zip": [".zip"] },
//         },
//       ],
//     });

//     const writable = await handle.createWritable();
//     await writable.write(blob);
//     await writable.close();

//     document.getElementById("status-output").textContent = "Saved successfully!";

//     // ✅ Notify backend to delete temp file
//     const tempFilePath = response.headers.get("X-Temp-Zip-Path");
//     if (tempFilePath) {
//       await fetch("/delete_temp_zip", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ zip_path: tempFilePath }),
//       });
//     }
//   } catch (error) {
//     document.getElementById("status-output").textContent = `Error: ${error.message}`;
//   }
// });

document.getElementById("convert-form").addEventListener("submit", async function (event) {
  event.preventDefault();

  const formData = new FormData(this); // Use the form directly instead of creating new FormData
  const statusOutput = document.getElementById("status-output");
  const convertButton = this.querySelector('button[type="submit"]');

  // Clear previous status
  statusOutput.textContent = "Starting conversion...";
  statusOutput.classList.remove("text-danger");
  convertButton.disabled = true;

  try {
    // Check if CMS is enabled and validate fields
    const enableCMS = document.getElementById("enable-cms").checked;
    if (enableCMS) {
      const apiToken = document.getElementById("api-token").value;
      const siteId = document.getElementById("site-id").value;

      if (!apiToken || !siteId) {
        throw new Error("Please provide both API Token and Site ID for CMS import");
      }

      // These will automatically be included in formData since they're part of the form
    }

    const response = await fetch("/convert", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Conversion failed");
    }

    const blob = await response.blob();

    // Extract filename
    let filename = "converted-theme.zip";
    const disposition = response.headers.get("Content-Disposition");
    if (disposition) {
      const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, "").trim();
      }
    }

    // Modern browser file saving
    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [
            {
              description: "ZIP Files",
              accept: { "application/zip": [".zip"] },
            },
          ],
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        statusOutput.textContent = "Saved successfully!";
      } catch (error) {
        if (error.name !== "AbortError") {
          throw error;
        }
        return; // User canceled the save
      }
    }
    // Legacy browser fallback
    else {
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
      }, 100);
      statusOutput.textContent = "Download started!";
    }

    // Clean up temp file
    const tempFilePath = response.headers.get("X-Temp-Zip-Path");
    if (tempFilePath) {
      await fetch("/delete_temp_zip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ zip_path: tempFilePath }),
      });
    }
  } catch (error) {
    console.error("Conversion error:", error);
    statusOutput.textContent = `Error: ${error.message}`;
    statusOutput.classList.add("text-danger");
  } finally {
    convertButton.disabled = false;
  }
});
