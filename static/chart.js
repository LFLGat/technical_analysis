document.addEventListener('DOMContentLoaded', function () {
    var graphJSON = document.getElementById('graphJSON').value;
    if (graphJSON) {
        var graph = JSON.parse(graphJSON);
        Plotly.newPlot('chart', graph.data, graph.layout);
    }
});
