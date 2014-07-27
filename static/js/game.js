var move_letter = "X";  //first move is X
var my_move = true;

$(document).ready(function() {
    $(".column").click( function() {
        if(!my_move) return
        var x = parseInt($( this ).attr("data-value"));
        console.log("User position is...", x);
        console.log("Move letter is....", move_letter);
        $( this ).html(move_letter);
        // $( this ).gameboard.disabled = true;
        socket.emit('game move', {'position' : x, 'position_value' : move_letter});
        my_move = false;
    });

    $("#socketButton").click(function(clickEvt) {
        
        socket.on('move made', function(message) {
            $("[data-value=" + message['move'] + "]").html(message['move_value']);
            move_letter = (message['move_value'] == "X" ? "O" : "X");
            my_move = true;
            console.log("Move made by", message['session_name']);
        });

        socket.on('game over', function(message) {
            alert(message['result']);
        });
    });

});