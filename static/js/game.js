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

function clear_game_board() {
    $('.column').each( function() {
        $(this).html('');
    });
}

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
            $('#endModal-body-id').html(gameover);
            $('#endModal-footer-id').html('<button type="button" class="btn btn-default" name="playagain" id="playAgain">Play Again?</button>' +
                '<button type="button" class="btn btn-default" name="endgame" id="endGame">Done?</button>');
            $('#endModal').modal('show');
            socket.emit('get reports', {'two_players' : two_players});

            $('#playAgain').click( function(e) {
                console.log("clicked play again");
                my_move = true;
                game_id = 0;
                move_letter = "X";
                clear_game_board();
                $('#endModal').modal('hide');
            });

            $('#endGame').click( function(e) {
                $('#endModal').modal('hide');
            });
    });

    socket.on('display results', function(message) {
        console.log("Display results is", message);
        $('#endGame').click( function(e) {
            $('#resultModal').css('width', '750px');
            $('#resultModal').css('height', '500px');
            $('#resultModal').modal('show');
            $('#resultModal-body-id').html(chart_results(message));
        });
        
    });

    socket.on('dashlog', function(message) {
        $('#dashmessage').html(message);
    });

}

function chart_results(message) {

var ctx = document.getElementById("chart-area").getContext("2d");

  var data = [
    {
        value: message['Computer'],
        color:"#F7464A",
        highlight: "#FF5A5E",
        label: "Red"
    },
    {
        value: message['Draw'],
        color: "#46BFBD",
        highlight: "#5AD3D1",
        label: "Green"
    },
    {
        value: message['jyothi'],
        color: "#FDB45C",
        highlight: "#FFC870",
        label: "Yellow"
    }
  ];

new Chart(ctx).PolarArea(data, {responsive : true});

}





// TODO:
// disable the clicking of the gameboard after game over
