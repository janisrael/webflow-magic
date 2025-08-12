jQuery(document).ready(function ($) {
  $("#start-import").on("click", function (e) {
    e.preventDefault();
    var $btn = $(this);

    $btn.prop("disabled", true).text("Importing...");

    $.ajax({
      url: webflowImporter.ajax_url,
      type: "POST",
      data: {
        action: "webflow_start_import",
        nonce: webflowImporter.nonce,
      },
      success: function () {
        checkImportProgress();
      },
      error: function () {
        alert("Error starting import");
        $btn.prop("disabled", false).text("Start Import");
      },
    });
  });

  function checkImportProgress() {
    $.ajax({
      url: webflowImporter.ajax_url,
      data: {
        action: "webflow_check_progress",
        nonce: webflowImporter.nonce,
      },
      success: function (response) {
        if (response.data.complete) {
          // Import complete
          $(".progress-bar").css("width", "100%");
          $(".percentage").text("100%");
          $(".current-action").text("Import complete!");
          $("#start-import").remove();
          location.reload();
        } else {
          // Update progress
          var progress = response.data.progress;
          $(".progress-bar").css("width", progress.percent + "%");
          $(".percentage").text(progress.percent + "%");
          $(".current-action").text(progress.message);

          // Check again in 1 second
          setTimeout(checkImportProgress, 1000);
        }
      },
      error: function () {
        $(".current-action").text("Error checking progress");
        $("#start-import").prop("disabled", false).text("Retry Import");
      },
    });
  }
});
