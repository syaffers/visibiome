function drawPcoa(dataPath, csvFile, sampleId) {
  var margin = {
    top: 20,
    right: 20,
    bottom: 30,
    left: 80
  },
    width = 720 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

  // when user clicks the view by ecosystem button
  $("#view-by-eco").click(function (e) {
    // don't scroll back up
    e.preventDefault();
    // auto toggle
    $("#toggle-user-sample").addClass("active");

    $(this).addClass('active');
    $("#view-by-envo").removeClass('active');
    // reset when replotting pcoa
    d3.select("svg")
    .remove();
    d3.select("svg")
    .remove();
    d3.select("svg")
    .remove();

    var colorMap = d3.scale.ordinal()
      .domain(
        [' Freshwater', ' Plant', ' Soil', ' Animal/Human', ' Geothermal',
         ' Marine', ' Anthropogenic', ' Biofilm', ' Unknown/User']
       )
      .range(
        ['blue', 'Darkgreen', 'Gold', 'DarkViolet', 'SaddleBrown', 'Cyan',
         'DarkOrange', 'SlateGray', 'Black']
       );

    drawAllPcoa('Ecosystem1', colorMap, margin, width, height, dataPath,
                csvFile, sampleId, true);
  });

  // when user clicks the view by envo button
  $("#view-by-envo").click(function (e) {
    // don't scroll back up
    e.preventDefault();
    // auto toggle
    $("#toggle-user-sample").addClass("active");

    $(this).addClass('active');
    $("#view-by-eco").removeClass('active');
    // reset when replotting pcoa
    d3.select("svg").remove();
    d3.select("svg").remove();
    d3.select("svg").remove();

    var colorMap = d3.scale.category20();

    drawAllPcoa('OntologyTerm1', colorMap, margin, width, height, dataPath,
                csvFile, sampleId, false);
  });

  // when user clicks toggle query label
  $("#toggle-user-sample").click(function (e) {
     // hide/unhide label
    $(this).toggleClass("active");
    $("svg .query-sample").toggle();
    e.preventDefault();
  });

  // when user clicks any of the download links
  $("#plots .download-link").click(function (e) {
    var plot = $(this).data("plot");
    writeDownloadLink(plot);
    e.preventDefault();
  });

  $(document).ready(function() {
    $("#view-by-eco").click();
  });
}

/**
 * Function that generates an SVG of the provided plot and opens a new window
 * showing the respective plot
 */
function writeDownloadLink(plotId) {
  var html = d3.select("#" + plotId + " svg")
      .attr("title", plotId.toUpperCase().split("-").join(" "))
      .attr("version", 1.1)
      .attr("xmlns", "http://www.w3.org/2000/svg")
      .node().parentNode.innerHTML;

  window.open("data:image/svg+xml;base64,"+ btoa(html), '_blank');
};


/**
* Function to draw all PCoA plots onto the page
*/
function drawAllPcoa(plotType, colorMap, margin, width, height, dataPath,
                     csvFile, sampleId, showLegend) {
  drawPcXVsPcYByType(1, 2, plotType, colorMap, width, height,
                     margin, dataPath, csvFile, sampleId, showLegend);
  drawPcXVsPcYByType(1, 3, plotType, colorMap, width, height,
                     margin, dataPath, csvFile, sampleId, showLegend);
  drawPcXVsPcYByType(2, 3, plotType, colorMap, width, height,
                     margin, dataPath, csvFile, sampleId, showLegend);
}


/**
* Function to draw PCX agaisnt PCY, you know, to generate the graphs colored
* by ecosystem
*/
function drawPcXVsPcYByType(pcx, pcy, type, colorMap, width, height, margin,
                            dataPath, csvFile, sampleId, showLegend) {
  // setup x axis
  var xValue = function(d) { return d["PC" + pcx]; }, // data -> value
    xScale = d3.scale.linear().range([0, width]), // value -> display
    xMap = function(d) { return xScale(xValue(d)); }, // data -> display
    xAxis = d3.svg.axis().scale(xScale).orient("bottom");

  // setup y axis
  var yValue = function(d) { return d["PC" + pcy]; }, // data -> value
    yScale = d3.scale.linear().range([height, 0]), // value -> display
    yMap = function(d) { return yScale(yValue(d)); }, // data -> display
    yAxis = d3.svg.axis().scale(yScale).orient("left");

  // setup fill color
  var cValue = function(d) {
    return d[type];
  },
  color = colorMap;

  var legendLabelHeight = 20;
  var legendHeight = color.domain().length * legendLabelHeight;

  // add the graph canvas to the body of the webpage
  var svg = d3.select("#pcoa-pc" + pcx + "-pc" + pcy)
  .append("svg")
  .attr("font-family", "Helvetica, Arial, sans-serif")
  .attr("width", width + 100 + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  // Add tooltip div
  var tooltip = d3.select("#pcoa-pc" + pcx + "-pc" + pcy + "-tooltip")
  .append("div")
  .attr("class", "tooltip")
  .style("opacity", 1e-6)
  .style("font", 12)
  .style("background", "#FFFF66")
  .style("border", 0);

  d3.csv(dataPath + csvFile, function(error, data) {

    // change string (from CSV) into number format
    data.forEach(function(d) {
      d["PC" + pcx] = Number(d["PC" + pcx]);
      d["PC" + pcy] = Number(d["PC" + pcy]);
    });

    // don't want dots overlapping axis, so add in buffer to data domain
    xScale.domain([d3.min(data, xValue) - 0.1, d3.max(data, xValue) + 0.1]);
    yScale.domain([d3.min(data, yValue) - 0.1, d3.max(data, yValue) + 0.1]);

    // draw x-axis
    svg.append("g")
    .attr("class", "x axis")
    .attr("transform", "translate(0," + height + ")")
    .call(xAxis)
    .append("text")
    .attr("class", "label")
    .attr("x", width)
    .attr("y", -6)
    .style("text-anchor", "end")
    .text("PC" + pcx);

    // draw y-axis
    svg.append("g")
    .attr("class", "y axis")
    .call(yAxis)
    .append("text")
    .attr("class", "label")
    .attr("transform", "rotate(-90)")
    .attr("y", 6)
    .attr("dy", ".71em")
    .style("text-anchor", "end")
    .text("PC" + pcy);

    // draw dotted line at x = 0
    svg.append("line")
    .attr("class", "x line")
    .attr("x1", xScale(0))
    .attr("y1", 0)
    .attr("x2", xScale(0))
    .attr("y2", height)
    .style('stroke', 'black')
    .style('stroke-width', 1)
    .style('stroke-dasharray', "5, 5");

    // draw dotted line at y = 0
    svg.append("line")
    .attr("class", "y line")
    .attr("x1", 0)
    .attr("y1", yScale(0))
    .attr("x2", width)
    .attr("y2", yScale(0))
    .style('stroke', 'black')
    .style('stroke-width', 1)
    .style('stroke-dasharray', "5, 5");

    // draw all points from data
    svg.selectAll(".dot")
    .data(data)
    .enter().append("circle")
    .attr("class", "dot")
    .attr("r", 2.75)
    .attr("cx", xMap)
    .attr("cy", yMap)
    .style("fill", function(d) {
      // set user queried point to black
      if (d["Sample Name"] == sampleId)
        return 'black';
      return color(cValue(d));
    })
    .on("mouseover", function(d) {
      tooltip.transition()
      .duration(10)
      .style("opacity", .9);

      tooltip.html(
        "Sample: " + d["Sample Name"] +
        "<br>Ecosystem: " + d.Ecosystem1 + " " +
        d.Ecosystem2.replace(' Unknown', '') + " " +
        d.Ecosystem3.replace(' Unknown', '') +
        "<br>Envo ID : " + d.OntologyID1 + ", " +
        d.OntologyID2.replace(' Unknown', '') + " " +
        d.OntologyID3.replace(' Unknown', '') +
        "<br>Envo term: " + d.OntologyTerm1 + ", " +
        d.OntologyTerm2.replace(' Unknown', '') + " " +
        d.OntologyTerm3.replace(' Unknown', '') +
        "<br>Study: " + d.Title + "<br>Study Source " + d["Study Source"]
      )
      .style("left", margin.left + xScale(d["PC" + pcx]) + "px")
      .style("top", margin.top + yScale(d["PC" + pcy]) + "px");
    })
    .on("mouseout", function(d) {
      tooltip.transition()
      .duration(10)
      .style("opacity", 0);
    });

    // draw text label for the user queried sample point
    svg.selectAll("text")
    .data(data).enter()
    .append("text")
    .attr("class", "query-sample")
    .attr("dx", xMap)
    .attr("dy", yMap)
    .attr("text-anchor", "start")
    .attr("font-weight", "bold")
    .attr('font-size', "10px")
    .attr('fill', "red")
    .text(function(d) {
      if (d["Sample Name"] == sampleId)
        return "..................." + d["Sample Name"];
      return "";
    });

  });

  // draw legend
  if (showLegend) {
    var legend = svg.selectAll(".legend")
    .data(color.domain())
    .enter().append("g")
    .attr("class", "legend")
    .attr("transform", function(d, i) {
      var yCenter = ((height + margin.top) / 2.) - (legendHeight / 2.);
      return "translate(10," + (yCenter + i * legendLabelHeight) + ")";
    });

    // draw legend colored rectangles
    legend.append("rect")
    .attr("x", width - 0)
    .attr("width", legendLabelHeight / 2.)
    .attr("height", legendLabelHeight / 2.)
    .style("fill", color);

    // draw legend text
    legend.append("text")
    .attr("x", width +14)
    .attr("y", 6)
    .attr("dy", ".35em")
    .style("text-anchor", "start")
    .text(function(d) { return d;});
  }

}
