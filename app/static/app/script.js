"use strict";

var biom_search_form_id = "#biom-search-form",
    remove_job_button = ".btn-job-remove",
    all_eco_checkbox = "#id_criteria_0",
    all_eco_value = "1",
    otu_textarea = "#id_otu_text",
    otu_textarea_placeholder = "Paste OTU table here";

function handleBiomCheckbox() {
  var checkedBoxes = $(biom_search_form_id).find("input[type=checkbox]").map(isChecked).toArray();

  if (all_eco_value == $(this).val()) {
    $(biom_search_form_id).find("input[type=checkbox]").each(uncheck);
  }
  else {
    $(all_eco_checkbox).prop("checked", false);
  }

  if (checkedBoxes.reduce(add, 0) >= 3) {
    $(biom_search_form_id).find("input[type=checkbox]:not(:checked)").prop('disabled', true);
  }
  else {
    $(biom_search_form_id).find("input[type=checkbox]:not(:checked)").prop('disabled', false);
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

function handleRemoveJob() {
  var removeUrl = $(this).data("remove-url");
  var remove = confirm("Are you sure you want to delete this job?");
  remove ? location.href = removeUrl : false
}

function uncheck(index, elem) {
  if ($(elem).val() != all_eco_value)
    $(elem).prop("checked", false);
}

function isChecked() {
  return $(this).prop("checked") ? 1 : 0;
}

function add(a, b) {
  return a + b;
}

$(document).ready(function() {
  $(biom_search_form_id).find("input[type=checkbox]").click(handleBiomCheckbox);
  $(otu_textarea).val(otu_textarea_placeholder);
  $(otu_textarea).click(handleClearTextfield);
  $(otu_textarea).blur(handleFillTextfield);
  $(remove_job_button).click(handleRemoveJob)
});