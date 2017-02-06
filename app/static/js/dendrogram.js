function drawDendrogram(dataPath, jsonFile, sampleId) {
  var width = 200;
  var height = 200;
  var radius = Math.min(width, height) / 2;

  var legendRectSize = 10;
  var legendSpacing = 5;

  var colr = d3.scale.ordinal()
  .range(['blue', 'Darkgreen', 'Gold', 'DarkViolet', 'SaddleBrown', 'Cyan',
    'DarkOrange', 'SlateGray', 'black'])
  .domain(['Freshwater', 'Plant', 'Soil', 'Animal/Human', 'Geothermal',
    'Marine', 'Anthropogenic', 'Biofilm', 'Unknown/User']);

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

  /**
   * drawing the actual dendrogram
   * is there a way to dynamically set the height?
   */
  width = 960;
  height = 5000;

  var cluster = d3.layout.cluster()
  .size([height - 200, width - 550]);

  svg = d3.select("#dendrogram").append("svg")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    // offset the graph by this amount
    .attr("transform", "translate(90,50)");

  // Add tooltip div
  var div = d3.select("#dendrogram-tooltip").append("div")
    .attr("class", "tooltip")
    .style("opacity", 1e-6)
    .style("font", 12)
    .style("background", "#FFFF66")
    .style("border", 0)
    .style("min-width", "150px");

  var div2 = d3.select("#dendrogram-tooltip").append("div")
    .attr("class", "tooltip")
    .style("opacity", 1e-6)
    .style("font", 12)
    .style("background", "#CCFF66")
    .style("border", 0);


  /********************************* DRAWING *********************************/

  d3.json(dataPath + jsonFile, function(json) {
    var nodes = cluster.nodes(json);
    var yscale = scaleBranchLengths(nodes, width - 550);

    // preparing branches
    var link = svg.selectAll("path.link")
      .data(cluster.links(nodes))
      .enter().append("path")
      .attr("class", "link")
      .attr("d", elbow)
      .attr("fill", "none")
      .attr("stroke", "#333333")
      .attr("stroke-width", "1.5px");

    // preparing nodes
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
      });


    // drawing root node
    svg.selectAll('g.root.node')
      .append('svg:circle')
      .attr("r", .5)
      .attr('fill', 'steelblue')
      .attr('stroke', '#369')
      .attr('stroke-width', '2px');

    // drawing inner nodes
    svg.selectAll('g.inner.node')
      .append('circle')
      .on("mouseover", mouseoverNonLeafNode)
      .on("mousemove", function(d) {
        mousemoveNonLeafNode(d);
      })
      .on("mouseout", mouseoutNonLeafNode)
      .attr("r", 2.5)
      .attr('fill', 'black')
      .attr('stroke', 'black')
      .attr('stroke-width', '1px');

    // colored leaf node first eco rect
    svg.selectAll('g.leaf.node')
      .append("rect")
      .on("mouseover", mouseoverLeafNode)
      .on("mousemove", function(d) {
        mousemoveLeafNode(d);
      })
      .on("mouseout", mouseoutLeafNode)
      .attr("x", 5)
      .attr("y", -5)
      .attr("width", 30)
      .attr("height", 10)
      .attr('fill', function(d) {
        if (d.name == sampleId) return "black";
        else return d.ecocolor[0];
      });

    // colored leaf node second eco rect
    svg.selectAll('g.leaf.node')
      .append("rect")
      .on("mouseover", mouseoverLeafNode)
      .on("mousemove", function(d) {
        mousemoveLeafNode(d);
      })
      .on("mouseout", mouseoutLeafNode)
      .attr("x", 35)
      .attr("y", -5)
      .attr("width", 30)
      .attr("height", 10)
      .attr('fill', function(d) {
        if (d.name == sampleId) return "black";
        else return d.ecocolor[1];
      });

    // colored leaf node third eco rect
    svg.selectAll('g.leaf.node')
      .append("rect")
      .on("mouseover", mouseoverLeafNode)
      .on("mousemove", function(d) {
        mousemoveLeafNode(d);
      })
      .on("mouseout", mouseoutLeafNode)
      .attr("x", 65)
      .attr("y", -5)
      .attr("width", 30)
      .attr("height", 10)
      .attr('fill', function(d) {
        if (d.name == sampleId) return "black";
        else return d.ecocolor[2];
      });

    // colored leaf node text
    svg.selectAll('g.leaf.node').append("text")
      .attr("dx", 100)
      .attr("dy", 0)
      .attr("text-anchor", "start")
      .attr("font-weight", "bold")
      .attr('font-size', function(d) {
        if (d.name == sampleId) return "14px";
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


  /******************************** FUNCTIONS ********************************/

  function scaleBranchLengths(nodes, w) {
    // Visit all nodes and adjust y pos width distance metric
    var visitPreOrder = function(root, callback) {
      callback(root);
      if (root.children) {
        for (var i = root.children.length - 1; i >= 0; i--) {
          visitPreOrder(root.children[i], callback)
        }
      }
    };
    visitPreOrder(nodes[0], function(node) {
      node.rootDist = (node.parent ? node.parent.rootDist : 0) +
                      (node.length || 0);
    });
    var rootDists = nodes.map(function(n) {
      return n.rootDist;
    });
    var yscale = d3.scale.linear()
    .domain([0, d3.max(rootDists)])
    .range([0, w]);
    visitPreOrder(nodes[0], function(node) {
      node.y = yscale(node.rootDist)
    });
    return yscale;
  }

  function elbow(d, i) {
    return "M" + d.source.y + "," + d.source.x +
    "V" + d.target.x + "H" + d.target.y;
  }

  function mouseoverLeafNode() {
    div.transition()
    .duration(1)
    .style("opacity", 1);
  }

  function mouseoutLeafNode() {
    div.transition()
    .duration(1)
    .style("opacity", 1e-6);
  }

  function mousemoveLeafNode(d) {
    var ontologyTermClean = d.OntologyTerm.map(cleanOntologyTerm);
    var nodeText = "Sample ID: " + d.name +
      "\n\nEnvironment Ontology:\n" + ontologyTermClean.join("\n") +
      "\n\nEcosystem: " + d.ecosystem.join("\n") +
      "\n\nStudy: " + d.title +
      "\n\nStudy Source: " + d.study_source;

    div
      .text(nodeText)
      .style("left", (d.y + 230) + "px")
      .style("top", (d.x + 50) + "px");
  }

  function mouseoverNonLeafNode() {
    div.transition()
    .duration(300)
    .style("opacity", 1);
  }

  function mouseoutNonLeafNode() {
    div.transition()
    .duration(300)
    .style("opacity", 1e-6);
  }

  function mousemoveNonLeafNode(d) {
    var ontologyTermClean = d.OntologyTerm.map(cleanOntologyTerm);
    var nodeText = "Environment Ontology:\n" + ontologyTermClean.join("\n") +
      "\n\nEcosystem: " + d.ecosystem.join("\n");

    div
    .text(nodeText)
    .style("left", (d3.event.pageX - 40) + "px")
    .style("top", (d3.event.pageY) + "px");
  }

  // replace comma with comma space for cleaner viewing and add index number
  function cleanOntologyTerm(term, index) {
    var t = term.replace(",", ", ");
    t = ++index + ". " + t;
    return t;
  }

}
