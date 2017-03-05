/**
 * Creating the ranking cards
 */
function displayRankings(jobSamplesRankingFile, sampleIds, barchartFiles) {
  $(".tab-pane").first().addClass("active");
  $("li[role=presentation]").first().addClass("active");

  $.ajax(jobSamplesRankingFile).done(function(data, status) {
    sampleIds.forEach(function(sampleId, index) {
      createRankingCards(data[sampleId], index + 1, barchartFiles);
    });
  });

}

/**
 * Cards template for each sample
 */
function createRankingCards(data, index, barchartFiles) {
  data.forEach(function(content) {
    var html = ''+
    '<div class="card">' +
      '<h4>#' +
        content['Ranking'] + ': ' + content['Name'] +
        '<br>'+
        '<small>' +
          '<strong>' +
            '(Distance: ' + content['Total_Distance'] + ', P-value: ' + content['pvalue'] +
            ', Sample size: ' + content['Total_Sample_Size'] + ')' +
          '</strong>' +
        '</small>' +
      '</h4>' +
      '<p>' +
        '<strong>' + content['Study'] + '</strong> ' +
        '<em>' + content['Study_Source'] + '</em>' +
        '<div class="row">' +
          '<div class="col-xs-4">' +
            '<p><strong>EnvO 1</strong> ' +
              (content['S_EnvO_1'] == " " ? "-" : content['S_EnvO_1']) +
            '</p>' +
          '</div>' +
          '<div class="col-xs-4">' +
            '<p><strong>EnvO 2</strong> ' +
              (content['S_EnvO_2'] == " " ? "-" : content['S_EnvO_2']) +
            '</p>' +
          '</div>' +
          '<div class="col-xs-4">' +
            '<p><strong>EnvO 3</strong> ' +
              (content['S_EnvO_3'] == " " ? "-" : content['S_EnvO_3']) +
            '</p>' +
          '</div>' +
        '</div>' +
      '</p>' +
    '</div>';

    $("#sample-" + index + "-card-container").append(html);
  });
}
