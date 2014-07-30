var move_letter = "X";  //first move is X
var my_move = true;
var game_id = 0; //first game id is 0 and the server assigns a new game id

$(document).ready(function() {
    $(".column").click( function() {
        if(!my_move) return
        var x = parseInt($( this ).attr("data-value"));
        console.log("User position is...", x);
        console.log("Move letter is....", move_letter);
        $( this ).html(move_letter);
        socket.emit('game move', {'position' : x, 'position_value' : move_letter, 'two_players' : two_players, 'game_id' : game_id});
        my_move = false;
    });
});

function game_socket_events() {

    socket.on('move made', function(message) {
            $("[data-value=" + message['move'] + "]").html(message['move_value']);
            move_letter = (message['move_value'] == "X" ? "O" : "X");
            my_move = true;
            game_id = message['game_id'];
            console.log("Move made by", message['session_name']);
            console.log("Game ID is", message['game_id']);
    });

    socket.on('game over', function(message) {
            var gameover = message['result'];
            $('#endModal').modal('show');
            $('#endModal').on('show.bs.modal', function(e) {
                $('#endModal-body-id').html('something');
            });
    });
}

// TODO:
// disable the clicking of the gameboard after game over
