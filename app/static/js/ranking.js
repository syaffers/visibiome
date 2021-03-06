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
      var noBarchartHtml = '<hr>' +
        '<p>No barcharts available for this sample. ' +
          '<a href="/help#ranking">Help</a>' +
        '</p>' +
      '<hr>';

      if (data[sampleId]["barcharts"] === null) {
        $(sampleBarchartsContainer + " .barchart-container").remove()
        $(sampleBarchartsContainer).html(noBarchartHtml);

      } else {
        if (Object.keys(data[sampleId]["barcharts"]).length === 0) {
          $(sampleBarchartsContainer + " .barchart-container").remove()
          $(sampleBarchartsContainer).html(noBarchartHtml);

        } else {
          var loaderHtml = '<span>Loading...<span>';
          $(sampleBarchartsContainer + " .barchart-container").children().remove();
          $(sampleBarchartsContainer + " .barchart-container").html(loaderHtml);
          $.ajax(jobSamplesRankingFile).done(function(data, status) {
            var selectedTaxons = taxonomySort(Object.keys(data[sampleId]["barcharts"]));
            mpld3.draw_figure("barchart-left-" + (index+1), data[sampleId]["barcharts"][selectedTaxons[0]]);
            mpld3.draw_figure("barchart-middle-" + (index+1), data[sampleId]["barcharts"][selectedTaxons[1]]);
            mpld3.draw_figure("barchart-right-" + (index+1), data[sampleId]["barcharts"][selectedTaxons[2]]);

            $(sampleBarchartsContainer + " .barchart-container > span").remove();
          });

        }
      }

      $(".card-placeholder").remove();
    });

  });

  $($(".sample-tab")[0]).click();

}

function taxonomySort(userTaxonList) {
  var orderedTaxons = ["kingdom", "phylum", "class", "order", "family", "genus"];
  var orderedSubTaxons = [];

  orderedTaxons.forEach(function(taxon) {
    if (userTaxonList.indexOf(taxon) >= 0) {
      orderedSubTaxons.push(taxon);
    }
  });

  return orderedSubTaxons;
}

function showBarchartsContainer(containerIndex) {
  $(".ranking-barcharts-section").addClass("hidden");
  $("#ranking-barcharts-" + containerIndex).removeClass("hidden");
}

/**
 * Cards template for each sample
 */
function createRankingCards(data, index, barchartFiles) {
  data.forEach(function(sample) {
    if (sample !== null) {
      var formatPvalue = ""
      if (Number(sample["pvalue"]) < 0.000001) {
        formatPvalue = "< 0.000001"
      } else {
        if (Number(sample["pvalue"]) == 1) {
          formatPvalue = "1"
        } else {
            formatPvalue = String(Math.round(sample["pvalue"] * 1000000) / 1000000);
        }
      }

      var studyLink = sample["Link"];
      var sampleHeader = '<span title="' + sample['Name'] + '">#'
        + sample['Ranking'] + ': ' + sample['Name'] + '</span>';

      if (studyLink !== null && studyLink !== undefined) {
        var loginNotice = "";
        if (studyLink.indexOf("qiita") >= 0) {
          loginNotice = '<span class="small">(login required)</span>'
        }
        sampleHeader = '<a href="' + studyLink + '" target="_blank">' +
          sampleHeader +
          ' <span class="glyphicon glyphicon-new-window glyphicon-sm"></span></a> ' +
          loginNotice;
      }

      studyTitleTruncated = (sample['Study'].length > 50)
        ? sample['Study'].slice(0, 50) + "..."
        : sample['Study'];

      var html = ''+
      '<div class="card">' +
        '<h4>' +
          sampleHeader +
          '<br>'+
          '<small>' +
            '<strong>' +
              '(Distance: ' + sample['Total_Distance'] + ', ' +
                '<abbr title="' + sample["pvalue"] + '">P-value: ' + formatPvalue + '</abbr>' +
              ', Sample size: ' + sample['Total_Sample_Size'] + ')' +
            '</strong>' +
          '</small>' +
        '</h4>' +
        '<p>' +
          '<strong title="' + sample["Study"] + '">' + studyTitleTruncated + '</strong> ' +
          '<em>(Source: ' + sample['Study_Source'] + ')</em>' +
          '<div class="row">' +
            '<div class="col-xs-4">' +
              '<p><strong>EnvO 1</strong> ' +
                (sample['S_EnvO_1'] == " " ? "-" : sample['S_EnvO_1']) +
              '</p>' +
            '</div>' +
            '<div class="col-xs-4">' +
              '<p><strong>EnvO 2</strong> ' +
                (sample['S_EnvO_2'] == " " ? "-" : sample['S_EnvO_2']) +
              '</p>' +
            '</div>' +
            '<div class="col-xs-4">' +
              '<p><strong>EnvO 3</strong> ' +
                (sample['S_EnvO_3'] == " " ? "-" : sample['S_EnvO_3']) +
              '</p>' +
            '</div>' +
          '</div>' +
        '</p>' +
      '</div>';
    } else {
      html = '<div class="card"><p>No matches found for this sample.</p></div>'
    }

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
