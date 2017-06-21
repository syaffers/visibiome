"use strict";

var biomSearchFormId = "#biom-search-form",
  removeJobButtons = ".btn-job-remove",
  rerunJobButtons = ".btn-job-rerun",

  allEcoCheckbox = "#id_criteria_0",
  allEcoValue = "1",

  phylumCheckbox = "#id_taxonomy_ranks_0",
  familyCheckbox = "#id_taxonomy_ranks_3",
  genusCheckbox = "#id_taxonomy_ranks_4",

  otuTextarea = "#id_otu_text",
  otuTextareaPlaceholder = "Paste OTU table here",

  jobDashboardRow = ".job-row",
  jobStatusTd = "td.job-status",
  jobStatusTdSpan = "td.job-status span",
  jobErrorTd = "td.job-error",
  jobUpdatedAtTd = "td.job-updated-at",
  jobLastRunAtTd = "td.job-last-run-at";


/**
 * Search page checkbox select handler.
 *
 * This function limits user criteria selection to a maximum of 3 individual
 * ecosystems xor the "All" ecosystem. This is checked every time a user
 * clicks one of the checkboxes.
 */
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

function handleTaxonCheckbox() {
  var checkedBoxes = $(biomSearchFormId)
    .find(".checkbox-taxon input[type=checkbox]")
    .map(isChecked).toArray();

  if (checkedBoxes.reduce(add, 0) >= 3) {
    $(biomSearchFormId)
      .find(".checkbox-taxon input[type=checkbox]:not(:checked)")
      .prop('disabled', true);
  }
  else {
    $(biomSearchFormId)
      .find(".checkbox-taxon input[type=checkbox]:not(:checked)")
      .prop('disabled', false);
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


/**
 * Dashboard AJAX job update handler.
 *
 * This is run every few seconds (see end of file for the actual value of
 * seconds) and is used to automatically update the details of jobs which are
 * currently running. It calls the following function to actually do the text
 * updating etc.
 */
function handleUpdateJobDetails() {
  $(jobDashboardRow).each(function (index, row) {
    var jobId = $(this).attr("id");
    var detailsUrl = "/jobs/" + jobId + "/details.json";
    var jobStatusCode = $(this).find(jobStatusTd)[0].dataset.statusCode;

    if (jobStatusCode >= 0 && jobStatusCode < 10) {
      $.ajax({"url": detailsUrl}).done(updateJobDetailsText);
    }
  });
}


/**
 * Job row details updater.
 *
 * This is called from handleUpdateJobDetails to do text manipulation and
 * actually update the view on the dashboard. The function normalizes strings
 * and checks job statuses to properly set the classes and texts for each
 * running job row.
 */
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


/**
 * Remove job buttons functionality.
 *
 * On clicking, redirect to the remove job URL. The user must be the job's
 * owner for this to be successfully executed.
 */
function handleRemoveJob(e) {
  e.preventDefault();
  var removeUrl = $(this).data("remove-url");
  var remove = confirm("This action cannot be undone. Are you sure you want to delete this job?");
  remove ? location.href = removeUrl : false
}


/**
 * Rerun job buttons functionality.

 * On clicking, redirect to the rerun job URL. The user must be the job's
 * owner for this to be successfully executed.
 */
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


/**
 * Table sorter options for the dashboard.
 *
 * Columns 6 and 7 are the rerun and delete button columns respectively
 */
var tablesorterOptions = {
  headers: {
    6: {
      sorter: false
    },
    7: {
      sorter: false
    }
  }
}


/**
 * RUN!
 */
$(document).ready(function() {
  $(biomSearchFormId)
    .find(".checkbox-criteria input[type=checkbox]")
    .click(handleBiomCheckbox);
  $(biomSearchFormId)
    .find(".checkbox-taxon input[type=checkbox]")
    .click(handleTaxonCheckbox);
  $(allEcoCheckbox).click();
  $(phylumCheckbox).click();
  $(familyCheckbox).click();
  $(genusCheckbox).click();
  $(removeJobButtons).click(handleRemoveJob);
  $(rerunJobButtons).click(handleRerunJob);
  $("#table-dashboard").tablesorter(tablesorterOptions);
  $("#adaptive-rarefaction-modal").modal({show: false});
  $('[data-toggle="tooltip"]').tooltip();
  setInterval(handleUpdateJobDetails, 10000);
});
