from flask import Flask, request, session, render_template, g, redirect, url_for, flash
import jinja2
from flask.ext.socketio import SocketIO, emit, join_room, leave_room
from game_model import Game, Move, User, dbsession, createBoard, updateGameBoard, isWinner, isFull, compMove, create_results_dict, getWinningloc


app = Flask(__name__)
app.secret_key = 'secret key'
socketio = SocketIO(app)

global play

@app.route("/")
def index():
	return render_template("index.html")

@socketio.on('connect', namespace='/test')
def test_connect():
	emit('log', {'data': 'Connected', 'count': 0})
	emit('my response')

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
	print 'Client disconnected:' + session['user']

# todo comment this fn
@socketio.on('get media', namespace='/test')
def get_media_from_all_clients():
	clients = get_clients_in_room()
	for socket in clients:
		if socket != request.namespace:
			print("Sending get media to other clients")
			socket.emit('get media')
			emit('dashlog', 'Accessing media from other player')

# todo comment this
@socketio.on('message', namespace='/test')
def handle_message(message):
	print('Message received on server:', message)
	emit('message', message, broadcast=True)

# todo comment this
# todo try to simplify this by splitting this into smaller functions
@socketio.on('game move', namespace='/test')
def move_made(message):
	global play

	print('Move info received on the server')
	clients = get_clients_in_room()

	#check if a new game has started
	#create an empty gameboard
	#set winning location to an empty list
	if message['game_id'] == 0:
		createBoard()
		play = False
		emit('dashlog', 'Game started', broadcast=True)
		winloc = []

	#assign game id at the start of the game, to the database
	if not play:
		game = Game()
		dbsession.add(game)
		dbsession.commit()
		game_id = game.id
		play = True
	else:
		game_id = message['game_id']
	print "Game id is", game_id

	#store the move info into the database
	move = Move(gameid=game_id, board_loc=message['position'], user=session['user'])
 	dbsession.add(move)
 	dbsession.commit()
  	print('Successfully added new game move to database!')

  	#send the move info to other clients before making a decision on winner
  	if message['two_players'] == True:
		for socket in clients:
			if socket != request.namespace:
				socket.emit('log', 'Incoming move')
				socket.emit('move made', { 'session_name' : session['user'], 'move' : message['position'], 
											'move_value' : message['position_value'], 'game_id' : game_id })
 	
 	#Update the board with the input move
 	newboard = updateGameBoard(message['position_value'], message['position'])
 	
 	#check if the incoming move is a last move ==> game board full
 	if isFull(newboard):
 		emit('game over', {'result' : 'Game is a draw', 'winloc' : [0,0,0]}, broadcast=True)
		dbuser1 = dbuser1_get_first_socket()
		if message['two_players'] == False:
			db_game_update(game_id, dbuser1.username, 'Computer', 'Draw')
		else:
			dbuser2 = dbuser2_get_second_socket()
			db_game_update(game_id, dbuser1.username, dbuser2.username, 'Draw')

	#check if incoming move is a winning move. Incoming socket wins and second socket loses the game
	elif isWinner(newboard, message['position_value']):
		winloc = getWinningloc(newboard, message['position_value'])
	 	dbuser1 = dbuser1_get_first_socket()
	 	emit('game over', {'result' : 'You win the game', 'winloc' : winloc})
	 	if message['two_players'] == False:
			db_game_update(game_id, dbuser1.username, 'Computer', dbuser1.username)
		else:
			dbuser2 = dbuser2_get_second_socket()
			db_game_update(game_id, dbuser1.username, dbuser2.username, dbuser1.username)
			for socket in clients:
				if socket != request.namespace:
					socket.emit('game over', {'result' : 'You lose the game', 'winloc' : winloc})
	#single player game with computer
	else: 	
		if message['two_players'] == False:
			comploc = compMove(newboard)
 			print "Computer picked location: ", comploc
 			comp_newboard = updateGameBoard("O", comploc)

 			# update game board with the computer picked location
 			move = Move(gameid=game_id, board_loc=comploc, user="Computer")
 			dbsession.add(move)	
 			dbsession.commit()
 			emit('move made', {'session_name' : "computer", 'move' : comploc, 'move_value' : "O", 'game_id' : game_id})

 			# check if computer makes a move that makes the board full ==> draw condition
 			if isFull(comp_newboard):
 				emit('game over', {'result' : 'Game is a draw', 'winloc' : [0,0,0]}, broadcast=True)
 				dbuser1 = dbuser1_get_first_socket()
 				db_game_update(game_id, dbuser1.username, 'Computer', 'Draw')

 			# check if computer makes a winning move
 			elif isWinner(comp_newboard, "O"):
 				winloc = getWinningloc(newboard, "O")
 				emit('game over', {'result' : 'Computer wins the game', 'winloc' : winloc})
 				dbuser1 = dbuser1_get_first_socket()
 				db_game_update(game_id, dbuser1.username, 'Computer', 'Computer')
 				
 	print "new board is %r", newboard

@socketio.on('get reports', namespace='/test')
def create_db_reports(message):

	clients = get_clients_in_room()

	#if the user is playing with computer
	if message['two_players'] == False:
		usr1 = session['user']
		usr2 = "Computer"		
		results = dbsession.query(Game).filter_by(usr1=usr1).filter_by(usr2=usr2).all()
		display_results = create_results_dict(results)

		# display_results from the db, report how many times a user has won a game
		# if the user did not win a single game, the result is "0"
		# similarly, for no draw between the two, the result is "0"
		adjust_dbresults(usr1, usr2, display_results)

	#if user is playing with another person
	else: 
		dbuser1 = dbsession.query(User).filter_by(socketid=request.namespace.socket.sessid).first()
		for socket in clients:
			if socket != request.namespace:
				dbuser2 = dbsession.query(User).filter_by(socketid=socket.socket.sessid).first()

		results = dbsession.query(Game).filter(((Game.usr1==dbuser1.username) | (Game.usr1==dbuser2.username)) & ((Game.usr2==dbuser1.username) | (Game.usr2==dbuser2.username))).all()
		display_results = create_results_dict(results)

		# display_results from the db, report how many times a user has won a game
		# if the user did not win a single game, the result is "0"
		# similarly, for no draw between the two, the result is "0"
		adjust_dbresults(dbuser1.username, dbuser2.username, display_results)		
	
	emit('display results', display_results, broadcast=True)

@socketio.on('create or join room', namespace='/test')
def create_join_room(message):
	print ("create join room route in the server")
	emit('log', {'Request to create or join room' : message['room']})

	# number of clients before adding to the room
	clients = get_clients_in_room()
	numClients = len(clients);
	emit('log', {'numClients before adding:' : numClients})

	# If there are no clients in the room, add a client
 	if(numClients == 0):
 		add_client_to_room_and_db(message)	
 		emit('created', {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          		'count': numClients+1, 'room' : message['room']})
 	
 	# If there is one client in the game room and if the game is a twoplayer game, add another client
 	elif (numClients == 1 and message['two_players'] == True):
 		for client in clients:
 			client.emit('join', message)
		add_client_to_room_and_db(message)
		emit('joined', {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          		'count': numClients+1, 'room' : message['room']})
	else:
		emit('full', message, broadcast=True)
    
    # number of clients after adding to the room
	clients = get_clients_in_room()
	numClients = len(clients)
	emit('log', {'numClients after adding:' : numClients}) 
	
	# messages sent to the UI element dashboard
	if message['two_players'] == False:
		emit('dashlog', 'You joined the room. Make your move')
	else:
		if numClients == 1:
			emit('dashlog', 'You joined the game room. Waiting for another player to join')
		else:
			emit('dashlog', 'Two players in the room. Start playing', broadcast=True)

# SOCKET MODEL FUNCTIONS
# add a client to the game room and database
def add_client_to_room_and_db(message):
	join_room(message['room'])
	session['user'] = message['username']
	newuser = User(socketid=request.namespace.socket.sessid, username=session['user'])
 	dbsession.add(newuser)
 	dbsession.commit() 

# get the number of clients connected to the game room
def get_clients_in_room():
	return socketio.rooms.get('/test', {}).get('game', set())

# display_results from the db, report how many times a user has won a game
# if the user did not win a single game, the result is "0"
# similarly, for no draw between the two, the result is "0"
def adjust_dbresults(usr1, usr2, display_results):
	if not usr1 in display_results:
		display_results[usr1] = 0;
	if not usr2 in display_results:
		display_results[usr2] = 0;
	if not 'Draw' in display_results:
		display_results['Draw'] = 0;

# store the result of a game into the database
def db_game_update(gameid, usr1, usr2, result):
 	game = dbsession.query(Game).filter_by(id=gameid)
 	game.update({ "usr1" : usr1, "usr2" : usr2, "winner" : result })
 	dbsession.commit() 

# query the database for the second socket connected to the server, other than incoming socket
def dbuser2_get_second_socket():
	clients = get_clients_in_room()

	for socket in clients:
		if socket != request.namespace:
			return dbsession.query(User).filter_by(socketid=socket.socket.sessid).first()

# query the database for the incoming socket connected to the server
def dbuser1_get_first_socket():
	return dbsession.query(User).filter_by(socketid=request.namespace.socket.sessid).first()


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0')