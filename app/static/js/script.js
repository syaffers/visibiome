"use strict";

var biomSearchFormId = "#biom-search-form",
  removeJobButtons = ".btn-job-remove",
  rerunJobButtons = ".btn-job-rerun",
  allEcoCheckbox = "#id_criteria_0",
  allEcoValue = "1",
  otuTextarea = "#id_otu_text",
  otuTextareaPlaceholder = "Paste OTU table here",
  jobDashboardRow = ".job-row",
  jobStatusTd = "td.job-status",
  jobStatusTdSpan = "td.job-status span",
  jobErrorTd = "td.job-error",
  jobUpdatedAtTd = "td.job-updated-at",
  jobLastRunAtTd = "td.job-last-run-at";

function handleBiomCheckbox() {
  var checkedBoxes = $(biomSearchFormId)
    .find(".checkbox-criteria input[type=checkbox]")
    .map(isChecked).toArray();

  if (allEcoValue == $(this).val()) {
    $(biomSearchFormId)
      .find(".checkbox-criteria input[type=checkbox]")
      .each(uncheck);
  }
  else {
    $(allEcoCheckbox).prop("checked", false);
  }

  if (checkedBoxes.reduce(add, 0) >= 3) {
    $(biomSearchFormId)
      .find(".checkbox-criteria input[type=checkbox]:not(:checked)")
      .prop('disabled', true);
  }
  else {
    $(biomSearchFormId)
      .find(".checkbox-criteria input[type=checkbox]:not(:checked)")
      .prop('disabled', false);
  }
}

function handleClearTextfield() {
  if ($(this).val() == "Paste OTU table here")
    $(this).val("");
}

function handleFillTextfield() {
  if ($(this).val() == "")
    $(this).val("Paste OTU table here");
}

function handleUpdateJobDetails() {
  $(jobDashboardRow).each(function (index, row) {
    var jobId = $(this).attr("id");
    var detailsUrl = "/job/" + jobId + "/details.json";
    var jobStatusCode = $(this).find(jobStatusTd)[0].dataset.statusCode;

    if (jobStatusCode >= 0 && jobStatusCode < 10) {
      $.ajax({"url": detailsUrl}).done(updateJobDetailsText);
    }
  });
}

function updateJobDetailsText(data) {
  if (data.status == 200) {
    var job = data.data;
    var updatedDateString = fecha.format(new Date(job.updatedAt), "MMM. D, YYYY, h:mm A");
    var lastRunDateString = fecha.format(new Date(job.lastRunAt), "MMM. D, YYYY, h:mm A");

    var statusTextSelector = "#" + job.id.toString() + jobDashboardRow + " " + jobStatusTdSpan;
    var rerunButtonSelector = "#" + job.id.toString() + jobDashboardRow + " " + rerunJobButtons;
    var statusTdSelector = "#" + job.id.toString() + jobDashboardRow + " " + jobStatusTd;
    var loaderSelector = "#" + job.id.toString() + jobDashboardRow + " " + jobStatusTd + " .loader";
    var errorTdSelector = "#" + job.id.toString() + jobDashboardRow + " " + jobErrorTd;
    var updatedAtTdSelector = "#" + job.id.toString() + jobDashboardRow + " " + jobUpdatedAtTd;
    var lastRunAtTdSelector = "#" + job.id.toString() + jobDashboardRow + " " + jobLastRunAtTd;

    $(statusTextSelector).text(job.status);
    $(statusTdSelector).attr("data-status-code", job.statusCode);
    $(errorTdSelector).text(job.error);
    $(errorTdSelector).attr("data-status-code", job.errorCode);
    $(lastRunAtTdSelector).text(lastRunDateString);
    if (Number(job.statusCode) >= 10 || Number(job.statusCode) < 0) {
      $(loaderSelector).remove();
      $(updatedAtTdSelector).text(updatedDateString);
      $(rerunButtonSelector).removeClass("disabled");
    }
  }
}

function handleRemoveJob(e) {
  e.preventDefault();
  var removeUrl = $(this).data("remove-url");
  var remove = confirm("This action cannot be undone. Are you sure you want to delete this job?");
  remove ? location.href = removeUrl : false
}

function handleRerunJob(e) {
  e.preventDefault();
  if ($(this).hasClass("disabled")) {
    return false;
  } else {
    var rerunUrl = $(this).data("rerun-url");
    var rerun = confirm("This action cannot be undone. Are you sure you want to rerun this job?");
    rerun ? location.href = rerunUrl : false
  }
}

function uncheck(index, elem) {
  if ($(elem).val() != allEcoValue)
    $(elem).prop("checked", false);
}

function isChecked() {
  return $(this).prop("checked") ? 1 : 0;
}

function add(a, b) {
  return a + b;
}

$(document).ready(function() {
  $(biomSearchFormId)
    .find(".checkbox-criteria input[type=checkbox]")
    .click(handleBiomCheckbox);
  $(otuTextarea).val(otuTextareaPlaceholder);
  $(otuTextarea).click(handleClearTextfield);
  $(otuTextarea).blur(handleFillTextfield);
  $(removeJobButtons).click(handleRemoveJob);
  $(rerunJobButtons).click(handleRerunJob);
  $("#table-dashboard").tablesorter();
  setInterval(handleUpdateJobDetails, 10000);
});
