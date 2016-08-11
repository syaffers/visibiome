var width = 900,
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
    .text("Beta Diveristy (Bray Curtis)");


function adjacency(dataPath) {

    queue()
        .defer(d3.csv, dataPath + "All_heatmap_nodelist.csv")
        .defer(d3.csv, dataPath + "All_heatmap_edgelist.csv")
        .await(function(error, nodeList, edgeList) {
            createAdjacencyMatrix(nodeList, edgeList);
        });

    dendrogram(dataPath);

    var usersamplejson = dataPath + "2558_4508977_3.json"

    $.ajax(usersamplejson).done(function(data, status) {
        createRankingTable(data.sample);
    });

    /* function to draw adjacency matrix on the ranking page */
    function createAdjacencyMatrix(nodes, edges) {
        var div = d3.select("#tooltip-heatmap").append("div")
          .attr("class", "tooltip")
          .style("opacity", 1e-6)
          .style("font", 12)
          .style("background", "#BDC3C7")
          .style("border", 0);

        var edgeHash = {};
        for (x in edges) {
            var id = edges[x].source + "-" + edges[x].target;
            var id1 = edges[x].target + "-" + edges[x].source;
            edgeHash[id] = edges[x];
            edgeHash[id1] = edges[x];

        }
        matrix = [];
        //create all possible edges
        for (a in nodes) {
            for (b in nodes) {
                var grid = {
                    id: nodes[a].id + "-" + nodes[b].id,
                    x: b,
                    y: a,
                    weight: 0
                };
                if (edgeHash[grid.id]) {
                    grid.weight = edgeHash[grid.id].weight;
                }
                matrix.push(grid);
            }
        }

        var svg = d3.select("#heatmap").append("svg")
            .attr("width", 570)
            .attr("height", 570);


        var g = svg.append("g")
            .attr("transform", "translate(175,175)")
            .attr("id", "adjacencyG")
            .selectAll("rect")
            .data(matrix)
            .enter()
            .append("rect")
            .attr("width", 18)
            .attr("height", 18)
            .attr("x", function(d) {
                return d.x * 18
            })
            .attr("y", function(d) {
                return d.y * 18
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

        var scaleSize = nodes.length * 18;
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
            d3.selectAll("rect").style("stroke-width", function(p) {
                return p.x == d.x || p.y == d.y ? "3x" : "1px"
            })
            div
                .text("Sample ID:  " + d.id.replace("-", "\nSample ID:  ") + "\nDistance:  " + d.weight)
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY) + "px");

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

    }

    /* funciton to create the ranking table in the raking page */
    function createRankingTable(data) {
        var headers = [
            "Name",
            "Similarity Ranking",
            "EnvO 1",
            "EnvO 2",
            "EnvO 3",
            "Study",
            "Study Source",
            "Distance",
            "Sample Size"
        ];
        var rankingTable = document.createElement("table");

        // bordered table, optional
        $(rankingTable).addClass("table table-bordered table-striped");
        // thead necessary for bootstrap styling
        $(rankingTable).append("<thead><tr></tr></thead>");

        // make the table headers first
        headers.forEach(function(header) {
            $(rankingTable).find("thead > tr").append("<th>" + header + "</th>");
        });

        // fill the tbody
        $(rankingTable).append("<tbody></tbody>");
        data.forEach(function(content, index) {
            $(rankingTable)
                .find("tbody")
                .append('<tr id="ranking-' + index + '"></tr>');
            Object.keys(content).forEach(function(key) {
                $(rankingTable)
                    .find("tr#ranking-" + index)
                    .append("<td>" + content[key] + "</td>");
            });
        });

        // put everything together onto the page
        $("#ranking-table").append(rankingTable);

    }

    /* function to create the dendrogram on the ranking page */
    function dendrogram(dataPath) {
        var width = 600,
            height = 570;

        var div1 = d3.select("#tooltip-dendrogram").append("div")
            .attr("class", "tooltip")
            .style("opacity", 1e-6)
            .style("font", 12)
            .style("background", "#FFFF66")
            .style("border", 0);

        var cluster = d3.layout.cluster()
            .size([height - 50, width - 350]);

        var svgh = d3.select("#dendrogram").append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(50,50)");
        d3.json(dataPath + "d3dendrogram_sub_sub.json", function(json) {
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
                })



            svgh.selectAll('g.root.node')
                .append('svg:circle')
                .attr("r", .5)
                .attr('fill', 'steelblue')
                .attr('stroke', '#369')
                .attr('stroke-width', '2px');

            svgh.selectAll('g.inner.node')
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

            svgh.selectAll('g.leaf.node')
                .append("circle")
                .on("mouseover", mouseover_lf)
                .on("mousemove", function(d) {
                    mousemove_lf(d);
                })
                .on("mouseout", mouseout_lf)
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
                    if (d.name == '2558_4508977_3') return "15px";
                    else return "9px";
                })
                .attr('fill', function(d) {
                    if (d.name == '2558_4508977_3') return "red";
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

        function mouseover_notlf() {
            div1.transition()
                .duration(300)
                .style("opacity", 1);
        }

        function mouseout_notlf() {
            div1.transition()
                .duration(300)
                .style("opacity", 1e-6);
        }

        function mousemove_notlf(d) {
            div1
                .text("Environment Ontology:\n" + d.OntologyTerm.join("\n") + "\n\nEcosystem: " + d.ecosystem.join("\n"))
                .style("left", (d3.event.pageX - 40) + "px")
                .style("top", (d3.event.pageY) + "px");
        }

        function mouseover_lf() {
            div1.transition()
                .duration(300)
                .style("opacity", 1);
        }

        function mouseout_lf() {
            div1.transition()
                .duration(300)
                .style("opacity", 1e-6);
        }

        function mousemove_lf(d) {
            div1
                .text("Sample ID:  " + d.name + "\n\nEnvironment Ontology:\n" + d.OntologyTerm.join("\n") + "\n\nEcosystem: " + d.ecosystem.join("\n") + "\n\nStudy: " + d.title + "\n\nStudy Source: " + d.study_source)
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

}
