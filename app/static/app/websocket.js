$(document).ready(function() {
  var ws = new WebSocket("ws://echo.websocket.org");

  ws.onopen = function (event) {
    console.log("Opened.")
  };

  ws.onmessage = function(event) {
    console.log(event.data);
    console.log(event.currentTarget.URL);
    window.alert(event.data);
  };

  ws.onclose = function(event) {
    console.log("Closed.")
  };

});
