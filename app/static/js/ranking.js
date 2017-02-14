var width = 720,
height = 50,
blockSize = 16;

/**
 * Drawing the heatmap legend
 */
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
.attr("height", blockSize)
.attr("x", function(d) {
  return x_scale(d[0]);
})
.attr("width", function(d) {
  return 24;
})
.style("fill", function(d) {
  return threshold(d[0]);
});


gleg.call(xAxis_g).append("text")
.attr("class", "caption")
.attr("x", 8).attr("y", -14).attr("font-size", "11px")
.text("β-Diversity (Bray Curtis)");


/**
 * Drawing the actual heatmap
 */
function adjacency(dataPath, sampleIds, jobSamplesSummaryFile) {

  queue()
  .defer(d3.csv, dataPath + "/top_nodelist.csv")
  .defer(d3.csv, dataPath + "/top_edgelist.csv")
  .await(function(error, nodeList, edgeList) {
    createAdjacencyMatrix(nodeList, edgeList);
  });

  dendrogram(dataPath);

  $.ajax(jobSamplesSummaryFile).done(function(data, status) {
    createRankingCards(data.sample);
  });

  /* function to draw adjacency matrix on the ranking page */
  function createAdjacencyMatrix(nodes, edges) {
    var offset = 220;
    var div = d3.select("#tooltip-heatmap").append("div")
    .attr("class", "tooltip")
    .style("opacity", 1e-6)
    .style("font", 12)
    .style("background", "#FFFF66")
    .style("border", 0);

    var edgeHash = {};
    edges.forEach(function(x) {
      var id = x.source + "-" + x.target;
      var id1 = x.target + "-" + x.source;
      edgeHash[id] = x;
      edgeHash[id1] = x;
    });

    //create all possible edges
    var matrix = [];
    nodes.forEach(function(a, i) {
      nodes.forEach(function (b, j) {
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

    var svg = d3.select("#heatmap").append("svg")
    .attr("width", width)
    .attr("height", width);


    var g = svg.append("g")
    .attr("transform", "translate(" + offset + "," + offset + ")")
    .attr("id", "adjacencyG")
    .selectAll("rect")
    .data(matrix)
    .enter()
    .append("rect")
    .attr("width", blockSize)
    .attr("height", blockSize)
    .attr("x", function(d) {
      return d.x * blockSize
    })
    .attr("y", function(d) {
      return d.y * blockSize
    })
    .style("stroke", "black")
    .style("stroke-width", "1px")
    .style("fill", "#337ab7")
    .style("fill-opacity", function(d) {
      return d.weight
    })
    .on("mouseover", mouseover)
    .on("mousemove", gridOver)
    .on("mouseout", mouseout);

    var scaleSize = nodes.length * blockSize;
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
    .attr("transform", "translate(-10,-10) rotate(90)")
    .attr("font-size", "10px");

    d3.select("#adjacencyG")
    .append("g")
    .call(yAxis)
    .attr("font-size", "10px");

    function gridOver(d, i) {
      /* really slow code: WARNING */
      // d3.selectAll("rect").style("stroke-width", function(p) {
      //   return p.x == d.x || p.y == d.y ? "3x" : "1px"
      // })
      div
      .text("Sample ID:  " + d.id.replace("-", "\nSample ID:  ") + "\nDistance:  " + d.weight)
      .style("left", Number(d.x) * blockSize + offset + (blockSize / 1.5) + "px")
      .style("top", Number(d.y) * blockSize + offset + (blockSize / 1.5) + "px");
    }

    function mouseover() {
      div.transition()
      .duration(10)
      .style("opacity", 1);
    }

    function mouseout() {
      div.transition()
      .duration(10)
      .style("opacity", 1e-6);
    }

  }

  /* funciton to create the ranking cards page */
  function createRankingCards(data) {
    data.forEach(function(content) {
      var html = ''+
      '<div class="card">' +
        '<h4>#' +
          content['Ranking'] + ': ' + content['Name'] +
          '<br>'+
          '<small>' +
            '<strong>' +
              '(Distance: ' + content['Total_Distance'] +
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

      $("#card-container").append(html);
    });
  }

  /* function to create the dendrogram on the ranking page */
  function dendrogram(dataPath) {
    var width = 630,
    height = 630;

    var div1 = d3.select("#tooltip-dendrogram").append("div")
    .attr("class", "tooltip")
    .style("opacity", 1e-6)
    .style("font", 12)
    .style("background", "#FFFF66")
    .style("max-width", "240px")
    .style("border", 0);

    var cluster = d3.layout.cluster()
    .size([height - 50, width - 350]);

    var svgh = d3.select("#dendrogram").append("svg")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", "translate(50,50)");

    d3.json(dataPath + "/d3dendrogram_sub_sub.json", function(json) {
      var nodes = cluster.nodes(json);

      var yscale = scaleBranchLengths(nodes, width - 350);

      var link = svgh.selectAll("path.link")
      .data(cluster.links(nodes))
      .enter().append("path")
      .attr("class", "link")
      .attr("d", elbow)
      .attr("fill", "none")
      .attr("stroke", "#260000")
      .attr("stroke-width", "1.5px");

      var node = svgh.selectAll("g.node")
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

      svgh.selectAll('g.root.node')
      .append('svg:circle')
      .attr("r", .5)
      .attr('fill', 'steelblue')
      .attr('stroke', '#369')
      .attr('stroke-width', '2px');

      svgh.selectAll('g.inner.node')
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

      svgh.selectAll('g.leaf.node')
      .append("circle")
      .on("mouseover", mouseoverLeafNode)
      .on("mousemove", function(d) {
        mousemoveLeafNode(d);
      })
      .on("mouseout", mouseoutLeafNode)
      .attr("r", 4.5)
      .attr('fill', 'black')
      .attr('stroke', 'black')
      .attr('stroke-width', '1px');

      // bolden the submitted sample
      svgh.selectAll('g.leaf.node').append("text")
      .attr("dx", 10)
      .attr("dy", 0)
      .attr("text-anchor", "start")
      .attr("font-weight", "bold")
      .attr('font-size', function(d) {
        if (sampleIds.indexOf(d.name) >= 0) return "15px";
        else return "9px";
      })
      .attr('fill', function(d) {
        if (sampleIds.indexOf(d.name) >= 0) return "red";
        else return "black";
      })
      .text(function(d) {
        return d.name;
      });
    });

    /*********************** DENDROGRAM FUNCTIONS ***********************/

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
        node.rootDist = (node.parent ? node.parent.rootDist : 0) + (node.length || 0)
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
      return yscale
    }

    function elbow(d, i) {
      return "M" + d.source.y + "," + d.source.x +
      "V" + d.target.x + "H" + d.target.y;
    }

    function mouseoverNonLeafNode() {
      div1.transition()
      .duration(10)
      .style("opacity", 1);
    }

    function mouseoutNonLeafNode() {
      div1.transition()
      .duration(10)
      .style("opacity", 1e-6);
    }

    function mousemoveNonLeafNode(d) {
      // replace comma with comma space for cleaner viewing and add index
      // number
      var ontologyTermClean = d.OntologyTerm.map(cleanOntologyTerm);
      var nodeText = "Environment Ontology:\n" +
      ontologyTermClean.join("\n") +
      "\n\nEcosystem: " + d.ecosystem.join("\n");

      div1
      .text(nodeText)
      .style("left", (d.y) + "px")
      .style("top", (d.x) + "px");
    }

    function mouseoverLeafNode() {
      div1.transition()
      .duration(10)
      .style("opacity", 1);
    }

    function mouseoutLeafNode() {
      div1.transition()
      .duration(10)
      .style("opacity", 1e-6);
    }

    function mousemoveLeafNode(d) {
      var ontologyTermClean = d.OntologyTerm.map(cleanOntologyTerm);
      var nodeText = "Sample ID:  " + d.name +
      "\n\nEnvironment Ontology:\n" + ontologyTermClean.join("\n") +
      "\n\nEcosystem: " + d.ecosystem.join("\n") +
      "\n\nStudy: " + d.title +
      "\n\nStudy Source: " + d.study_source;
      div1
      .text(nodeText)
      .style("left", 450 + "px")
      .style("top", d.x + 50 + "px");
    }

    // replace comma with comma space for cleaner viewing and add index
    // number
    function cleanOntologyTerm(term, index) {
      var t = term.replace(",", ", ");
      t = ++index + ". " + t;
      return t;
    }
  }

}
