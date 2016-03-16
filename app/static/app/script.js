"use strict";

var biom_search_form_id = "#biom-search-form";

$(document).ready(function() {
  $(biom_search_form_id).find("input[type=checkbox]").click(handleBiomCheckbox);
});

function handleBiomCheckbox() {
  var checkedBoxes = $(biom_search_form_id).find("input[type=checkbox]").map(isChecked).toArray();

  if(checkedBoxes.reduce(add, 0) >= 3) {
    $(biom_search_form_id).find("input[type=checkbox]:not(:checked)").prop('disabled', true);
  }
  else {
    $(biom_search_form_id).find("input[type=checkbox]:not(:checked)").prop('disabled', false);
  }
  if ("all" == $(this).val()) {
    $(biom_search_form_id).find("input[type=checkbox]").each(uncheck);
  }
else {
    $(biom_search_form_id).find("input[type=checkbox]").each(uncheckAllEco)
  }
}

function uncheck(index, elem) {
  if($(elem).val() != "all") {
    $(elem).prop('checked', false);
  }
}

function uncheckAllEco(index, elem) {
  $("#id_selection_criteria_0").prop('checked', false);
}

function isChecked() {
  return $(this).prop('checked') ? 1 : 0;
}

function add(a, b) {
  return a + b;
}
