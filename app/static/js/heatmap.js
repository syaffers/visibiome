var width = 500,
height = 50;

var threshold = d3.scale.threshold()
.domain([0, .1, .2, .3, .4, .5, .6])
.range(["#ffffff", "#dde9f3", "#bbd3e7", "#99bddb", "#77a6cf", "#5590c3", "#337ab7"]);

var x_scale = d3.scale.linear()
.domain([0, 1])
.range([0, 240]);

var xAxis_g = d3.svg.axis()
.scale(x_scale)
.orient("top")
.tickSize(0)
.tickValues([0, .6])
.tickFormat(function(d) {
  if (d == 0.6) return 1;
  else return 0;
});


var svgleg = d3.select("#legend").append("svg")
.attr("width", width)
.attr("height", height);

var gleg = svgleg.append("g")
.attr("class", "key")
.attr("transform", "translate(" + (width - 240) / 2 + "," + (height + 10) / 2 + ")");

gleg.selectAll("rect")
.data(threshold.range().map(function(color) {
  var d = threshold.invertExtent(color);
  if (d[0] == null) d[0] = x_scale.domain()[0];
  if (d[1] == null) d[1] = x_scale.domain()[1];
  return d;
}))
.enter().append("rect")
.attr("height", 18)
.attr("x", function(d) {
  return x_scale(d[0]);
})
.attr("width", function(d) {
  return 25;
})
.style("fill", function(d) {
  return threshold(d[0]);
});


gleg.call(xAxis_g).append("text")
.attr("class", "caption")
.attr("x", 10).attr("y", -10).attr("font-size", "10px")
.text("Beta Diversity (Bray Curtis)");

function adjacency(dataPath) {
  queue()
  .defer(d3.csv, dataPath + "All_heatmap_nodelist.csv")
  .defer(d3.csv, dataPath + "All_heatmap_edgelist.csv")
  .await(function(error, nodeList, edgeList) {
    createAdjacencyMatrix(nodeList, edgeList);
  });


  var div = d3.select("#tooltip").append("div")
  .attr("class", "tooltip")
  .style("opacity", 1e-6)
  .style("font", 12)
  .style("background", "#FFFF66")
  .style("border", 0)
  .style("left", 0);

  function createAdjacencyMatrix(nodes, edges) {
    var svgSize = $.unique(nodes).length * 9;
    var edgeHash = {};
    edges.forEach(function(x) {
      var id = x.source + "-" + x.target;
      var id1 = x.target + "-" + x.source;
      edgeHash[id] = x;
      edgeHash[id1] = x;
    });
    
    var matrix = [];
    //create all possible edges
    nodes.forEach(function(a, i) {
      nodes.forEach(function(b, j) {
        var grid = {
          id: a.id + "-" + b.id,
          x: i,
          y: j,
          weight: 0
        };
        if (edgeHash[grid.id]) {
          grid.weight = edgeHash[grid.id].weight;
        }
        matrix.push(grid);
      });
    });

    var svg = d3.select("#plot").append("svg")
    .attr("width", svgSize)
    .attr("height", svgSize);

    var g = svg.append("g")
    .attr("transform", "translate(185,175)")
    .attr("id", "adjacencyG")
    .selectAll("rect")
    .data(matrix)
    .enter()
    .append("rect")
    .attr("width", 8)
    .attr("height", 8)
    .attr("x", function(d) {
      return d.x * 8
    })
    .attr("y", function(d) {
      return d.y * 8
    })
    .style("stroke", "black")
    .style("stroke-width", "1px")
    .style("fill", "#337AB7")
    .style("fill-opacity", function(d) {
      return d.weight
    })
    .on("mouseover", mouseover)
    .on("mousemove", gridOver)
    .on("mouseout", mouseout);

    var scaleSize = nodes.length * 8;
    var nameScale = d3.scale.ordinal().domain(nodes.map(function(el) {
      return el.id
    })).rangePoints([0, scaleSize], 1);

    xAxis = d3.svg.axis().scale(nameScale).orient("top").tickSize(2);
    yAxis = d3.svg.axis().scale(nameScale).orient("left").tickSize(2);

    d3.select("#adjacencyG")
    .append("g")
    .call(xAxis)
    .selectAll("text")
    .style("text-anchor", "end")
    .attr("transform", "translate(-10,-3) rotate(90)")
    .attr("font-size", "9px");

    d3.select("#adjacencyG")
    .append("g")
    .call(yAxis)
    .attr("font-size", "10px");

    function gridOver(d, i) {
      /* really slow code: WARNING! */
      // d3.selectAll("rect").style("stroke-width", function(p) {
      //     return p.x == d.x || p.y == d.y ? "2px" : "1px"
      // })
      var plotScrollLeft = $("#plot").scrollLeft();
      var details = "Sample ID: " + d.id.replace("-", "\nSample ID: ") +
        "\nDistance:  " + d.weight;
      div
      .text(details)
      .style("left", Number(d.x) * 8 + 190 - plotScrollLeft + "px")
      .style("top", Number(d.y) * 8 + 180 + "px");
    }

    function mouseover() {
      div.transition()
      .duration(1)
      .style("opacity", 1);
    }

    function mouseout() {
      div.transition()
      .duration(1)
      .style("opacity", 1e-6);
    }

  }

}
