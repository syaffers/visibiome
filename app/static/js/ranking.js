/**
 * Creating the ranking cards
 */
function displayRankings(jobSamplesRankingFile, sampleIds, barchartFiles) {
  $(".tab-pane").first().addClass("active");
  $("li[role=presentation]").first().addClass("active");

  $(".sample-tab").click(function() {
    showBarchartsContainer($(this).data("sampleId"));
  });

  $.ajax(jobSamplesRankingFile).done(function(data, status) {
    sampleIds.forEach(function(sampleId, index) {
      createRankingCards(data[sampleId]["ranking"], index + 1, barchartFiles);
      var cssSafeSampleId = sampleId.replace(/[^0-9a-zA-Z]/g, "-");
      var sampleBarchartsContainer = "#ranking-barcharts-" + (index + 1);

      if (data[sampleId]["barcharts"] === null) {
        $(sampleBarchartsContainer + " .barchart-container").remove()
        $(sampleBarchartsContainer).html("<p>No barcharts available for this sample.</p>");

      } else {
        if (Object.keys(data[sampleId]["barcharts"]).length === 0) {
          $(sampleBarchartsContainer + " .barchart-container").remove()
          $(sampleBarchartsContainer).html("<p>No barcharts available for this sample.</p>");

        } else {
          var loaderHtml = '<span>Loading...<span>';
          $(sampleBarchartsContainer + " .barchart-container").children().remove();
          $(sampleBarchartsContainer + " .barchart-container").html(loaderHtml);
          $.ajax(jobSamplesRankingFile).done(function(data, status) {
            mpld3.draw_figure("barchart-family-" + (index+1), data[sampleId]["barcharts"]["family"]);
            mpld3.draw_figure("barchart-genus-" + (index+1), data[sampleId]["barcharts"]["genus"]);
            mpld3.draw_figure("barchart-phylum-" + (index+1), data[sampleId]["barcharts"]["phylum"]);

            $(sampleBarchartsContainer + " .barchart-container > span").remove();
          });

        }
      }

    });

  });

  $($(".sample-tab")[0]).click();

}

function showBarchartsContainer(containerIndex) {
  $(".ranking-barcharts-section").addClass("hidden");
  $("#ranking-barcharts-" + containerIndex).removeClass("hidden");
}

/**
 * Cards template for each sample
 */
function createRankingCards(data, index, barchartFiles) {
  data.forEach(function(content) {
    var formatPvalue = ""
    if (Number(content["pvalue"]) < 0.01) {
      formatPvalue = "< 0.01"
    } else {
      if (Number(content["pvalue"]) == 1) {
        formatPvalue = "N/A"
      } else {
          formatPvalue = String(Math.round(content["pvalue"] * 100) / 100);
      }
    }
    var html = ''+
    '<div class="card">' +
      '<h4>#' +
        content['Ranking'] + ': ' + content['Name'] +
        '<br>'+
        '<small>' +
          '<strong>' +
            '(Distance: ' + content['Total_Distance'] + ', ' +
              '<abbr title="' + content["pvalue"] + '">P-value: ' + formatPvalue + '</abbr>' +
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

/**
* Functions copied from MPLD3 HTML outputs, try not to mess with this
*/
mpld3.register_plugin("htmltooltip", HtmlTooltipPlugin);
HtmlTooltipPlugin.prototype = Object.create(mpld3.Plugin.prototype);
HtmlTooltipPlugin.prototype.constructor = HtmlTooltipPlugin;
HtmlTooltipPlugin.prototype.requiredProps = ["id"];
HtmlTooltipPlugin.prototype.defaultProps = {labels:null, hoffset:0, voffset:10};

function HtmlTooltipPlugin(fig, props){
  mpld3.Plugin.call(this, fig, props);
};

HtmlTooltipPlugin.prototype.draw = function(){
  var obj = mpld3.get_element(this.props.id);
  var labels = this.props.labels;
  var tooltip = d3.select("body").append("div")
  .attr("class", "mpld3-tooltip")
  .style("position", "absolute")
  .style("z-index", "10")
  .style("visibility", "hidden");

  obj.elements()
  .on("mouseover", function(d, i){
    tooltip.html(labels[i])
    .style("visibility", "visible");})
  .on("mousemove", function(d, i){
    tooltip
    .style("top", d3.event.pageY + this.props.voffset + "px")
    .style("left",d3.event.pageX + this.props.hoffset + "px");
  }.bind(this))
  .on("mouseout",  function(d, i){
    tooltip.style("visibility", "hidden");});
  };
