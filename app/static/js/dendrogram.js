function drawDendrogram(dataPath, jsonFile, sampleId="2558_4508977_3.json") {
  var width = 200;
  var height = 200;
  var radius = Math.min(width, height) / 2;

  var legendRectSize = 10;
  var legendSpacing = 5;

  var colr = d3.scale.ordinal()
  .range(['blue', 'Darkgreen', 'Gold', 'DarkViolet', 'SaddleBrown', 'Cyan', 'DarkOrange', 'SlateGray'])
  .domain(['Freshwater', 'Plant', 'Soil', 'Animal_Human', 'Geothermal', 'Marine', 'Anthropogenic', 'Biofilm']);

  var svg = d3.select('#legend')
  .append('svg')
  .attr('width', width)
  .attr('height', height)
  .append('g')
  .attr('transform', 'translate(' + (width / 2) + ',' + (height / 2) + ')');

  var legend = svg.selectAll('.legend-point')
  .data(colr.domain())
  .enter()
  .append('g')
  .attr('class', 'legend')
  .attr('transform', function(d, i) {
    var height = legendRectSize + legendSpacing;
    var offset = height * 2;
    var horz = -2 * legendRectSize;
    var vert = i * height - offset;
    return 'translate(' + horz + ',' + vert + ')';
  });

  legend.append('rect')
  .attr('width', legendRectSize)
  .attr('height', legendRectSize)
  .style('fill', colr)
  .style('stroke', colr)
  .style('stroke-width', 2);

  legend.append('text')
  .attr('x', legendRectSize + (legendSpacing))
  .attr('y', legendRectSize)
  .text(function(d) {
    return d;
  });

  /* probably drawing some other thing */
  var width = 1210,
  height = 2500;

  var cluster = d3.layout.cluster()
  .size([height - 200, width - 550]);

  var svg = d3.select("#dendrogram").append("svg")
  .attr("width", width)
  .attr("height", height)
  .append("g")
  .attr("transform", "translate(200,50)");

  // Add tooltip div
  var div = d3.select("#dendrogram-tooltip").append("div")
  .attr("class", "tooltip")
  .style("opacity", 1e-6)
  .style("font", 12)
  .style("background", "#FFFF66")
  .style("border", 0);

  var div2 = d3.select("#dendrogram-tooltip").append("div")
  .attr("class", "tooltip")
  .style("opacity", 1e-6)
  .style("font", 12)
  .style("background", "#CCFF66")
  .style("border", 0);


  d3.json(dataPath + jsonFile, function(json) {
    var nodes = cluster.nodes(json);

    var yscale = scaleBranchLengths(nodes, width - 550);

    var link = svg.selectAll("path.link")
    .data(cluster.links(nodes))
    .enter().append("path")
    .attr("class", "link")
    .attr("d", elbow)
    .attr("fill", "none")
    .attr("stroke", "#260000")
    .attr("stroke-width", "1.5px");

    var node = svg.selectAll("g.node")
    .data(nodes)
    .enter().append("g")
    .attr("class", function(n) {
      if (n.children) {
        if (n.depth == 0) {
          return "root node"
        } else {
          return "inner node"
        }
      } else {
        return "leaf node"
      }
    })
    .attr("transform", function(d) {
      return "translate(" + d.y + "," + d.x + ")";
    })



    svg.selectAll('g.root.node')
    .append('svg:circle')
    .attr("r", .5)
    .attr('fill', 'steelblue')
    .attr('stroke', '#369')
    .attr('stroke-width', '2px');

    svg.selectAll('g.inner.node')
    .append('circle')
    .on("mouseover", mouseover_notlf)
    .on("mousemove", function(d) {
      mousemove_notlf(d);
    })
    .on("mouseout", mouseout_notlf)
    .attr("r", 2.5)
    .attr('fill', 'black')
    .attr('stroke', 'black')
    .attr('stroke-width', '1px');

    svg.selectAll('g.leaf.node')
    .append("rect")
    .on("mouseover", mouseover)
    .on("mousemove", function(d) {
      mousemove(d);
    })
    .on("mouseout", mouseout)
    .attr("x", 5)
    .attr("y", -5)
    .attr("width", 30)
    .attr("height", 10)
    .attr('fill', function(d) {
      return d.ecocolor[0];
    });

    svg.selectAll('g.leaf.node')
    .append("rect")
    .on("mouseover", mouseover)
    .on("mousemove", function(d) {
      mousemove(d);
    })
    .on("mouseout", mouseout)

    .attr("x", 35)
    .attr("y", -5)
    .attr("width", 30)
    .attr("height", 10)
    .attr('fill', function(d) {
      return d.ecocolor[1];
    });

    svg.selectAll('g.leaf.node')
    .append("rect")
    .on("mouseover", mouseover)
    .on("mousemove", function(d) {
      mousemove(d);
    })
    .on("mouseout", mouseout)

    .attr("x", 65)
    .attr("y", -5)
    .attr("width", 30)
    .attr("height", 10)
    .attr('fill', function(d) {
      return d.ecocolor[2];
    });


    svg.selectAll('g.leaf.node').append("text")
    .attr("dx", 100)
    .attr("dy", 0)
    .attr("text-anchor", "start")
    .attr("font-weight", "bold")

    .attr('font-size', function(d) {
      if (d.name == sampleId) return "20px";
      else return "7px";
    })
    .attr('fill', function(d) {
      if (d.name == sampleId) return "red";
      else return "black";
    })
    .text(function(d) {
      return d.name;
    });
  });

  function elbow(d, i) {
    return "M" + d.source.y + "," + d.source.x +
    "V" + d.target.x + "H" + d.target.y;
  }

  function mouseover() {
    div.transition()
    .duration(300)
    .style("opacity", 1);
  }

  function mouseout() {
    div.transition()
    .duration(300)
    .style("opacity", 1e-6);
  }

  function mousemove(d) {
    div
    .text("Sample ID:  " + d.name + "\n\nEnvironment Ontology:\n" + d.OntologyTerm.join("\n") + "\n\nEcosystem: " + d.ecosystem.join("\n") + "\n\nStudy: " + d.title + "\n\nStudy Source: " + d.study_source)
    .style("left", (d3.event.pageX - 40) + "px")
    .style("top", (d3.event.pageY) + "px");
  }

  function mouseover_notlf() {
    div.transition()
    .duration(300)
    .style("opacity", 1);
  }

  function mouseout_notlf() {
    div.transition()
    .duration(300)
    .style("opacity", 1e-6);
  }

  function mousemove_notlf(d) {
    div
    .text("Environment Ontology:\n" + d.OntologyTerm.join("\n") + "\n\nEcosystem: " + d.ecosystem.join("\n"))
    .style("left", (d3.event.pageX - 40) + "px")
    .style("top", (d3.event.pageY) + "px");
  }


  function scaleBranchLengths(nodes, w) {
    // Visit all nodes and adjust y pos width distance metric
    var visitPreOrder = function(root, callback) {
      callback(root)
      if (root.children) {
        for (var i = root.children.length - 1; i >= 0; i--) {
          visitPreOrder(root.children[i], callback)
        };
      }
    }
    visitPreOrder(nodes[0], function(node) {
      node.rootDist = (node.parent ? node.parent.rootDist : 0) + (node.length || 0)
    })
    var rootDists = nodes.map(function(n) {
      return n.rootDist;
    });
    var yscale = d3.scale.linear()
    .domain([0, d3.max(rootDists)])
    .range([0, w]);
    visitPreOrder(nodes[0], function(node) {
      node.y = yscale(node.rootDist)
    })
    return yscale
  }

}
