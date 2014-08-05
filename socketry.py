from flask import Flask, request, session, render_template, g, redirect, url_for, flash
import jinja2
from flask.ext.socketio import SocketIO, emit, join_room, leave_room
from game_model import Game, Move, User, dbsession, createBoard, updateGameBoard, isWinner, isFull, compMove, create_results_dict, getWinningloc


app = Flask(__name__)
app.secret_key = 'secret key'
socketio = SocketIO(app)

global play
global client_count

@app.route("/")
def index():
	return render_template("index.html")

@socketio.on('connect', namespace='/test')
def test_connect():
	print("*************************************")
	emit('log', {'data': 'Connected', 'count': 0})
	emit('my response')


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

@socketio.on('get media', namespace='/test')
def get_media_from_all_clients():
	clients = socketio.rooms.get('/test', {}).get('game', set())
	for socket in clients:
		if socket != request.namespace:
			print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
			print("Sending get media to other clients")
			socket.emit('get media')
			emit('dashlog', 'Accessing media from other player')

@socketio.on('message', namespace='/test')
def handle_message(message):
	print('Message received on server:', message)
	emit('message', message, broadcast=True)

@socketio.on('game move', namespace='/test')
def move_made(message):
	global play
	global client_count

	print('Move info received on the server')
	clients = socketio.rooms.get('/test', {}).get('game', set())

	#check if a new game has started
	if message['game_id'] == 0:
		createBoard()
		play = False
		emit('dashlog', 'Game started', broadcast=True)
		winloc = []
		client_count = 0

	#assign game id to the database
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
 	
 	#check if the incoming move is a winning move (or) last move ==> game board full
 	if isFull(newboard):
 		emit('game over', {'result' : 'Game is a draw', 'winloc' : [0,0,0]}, broadcast=True)
		dbuser1 = dbsession.query(User).filter_by(socketid=request.namespace.socket.sessid).first()
		if message['two_players'] == False:
			usr2 = 'Computer'
			game = dbsession.query(Game).filter_by(id=game_id)
			game.update({"usr1" : dbuser1.username, "usr2" : usr2, "winner" : 'Draw'}) 
		else:
			for socket in clients:
				if socket != request.namespace:
					dbuser2 = dbsession.query(User).filter_by(socketid=socket.socket.sessid).first()
					game = dbsession.query(Game).filter_by(id=game_id)
					game.update({"usr1" : dbuser1.username, "usr2" : dbuser2.username, "winner" : 'Draw' }) 
		dbsession.commit()

	elif isWinner(newboard, message['position_value']):
		winloc = getWinningloc(newboard, message['position_value'])
	 	dbuser1 = dbsession.query(User).filter_by(socketid=request.namespace.socket.sessid).first()
	 	winner = dbuser1.username
	 	emit('game over', {'result' : 'you win the game', 'winloc' : winloc})
	 	if message['two_players'] == False:
			usr2 = 'Computer'
			game = dbsession.query(Game).filter_by(id=game_id)
			game.update({"usr1" : dbuser1.username, "usr2" : usr2, "winner" : winner})
		else:
			for socket in clients:
				if socket != request.namespace:
					dbuser2 = dbsession.query(User).filter_by(socketid=socket.socket.sessid).first()
					game = dbsession.query(Game).filter_by(id=game_id)
					game.update({"usr1" : dbuser1.username, "usr2" : dbuser2.username, "winner" : winner})
					socket.emit('game over', {'result' : 'you lose the game', 'winloc' : winloc})
		dbsession.commit()

	else: 	#single player game with comp
		if message['two_players'] == False:
			comploc = compMove(newboard)
 			print "Computer picked location: ", comploc
 			comp_newboard = updateGameBoard("O", comploc)

 			move = Move(gameid=game_id, board_loc=comploc, user="Computer")
 			dbsession.add(move)	
 			dbsession.commit()
 			emit('move made', {'session_name' : "computer", 'move' : comploc, 'move_value' : "O", 'game_id' : game_id})

 			if isFull(comp_newboard):
 				emit('game over', {'result' : 'Game is a draw', 'winloc' : [0,0,0]}, broadcast=True)
 				winner = 'Draw'
 				dbuser1 = dbsession.query(User).filter_by(socketid=request.namespace.socket.sessid).first()
 				game = dbsession.query(Game).filter_by(id=game_id)
 				game.update({ "usr1" : dbuser1.username, "usr2" : 'Computer', "winner" : 'Draw' }) 

 			elif isWinner(comp_newboard, "O"):
 				winloc = getWinningloc(newboard, "O")
 				emit('game over', {'result' : 'Computer wins the game', 'winloc' : winloc})
 				dbuser1 = dbsession.query(User).filter_by(socketid=request.namespace.socket.sessid).first()
 				game = dbsession.query(Game).filter_by(id=game_id)
 				game.update({ "usr1" : dbuser1.username, "usr2" : 'Computer', "winner" : 'Computer' }) 		

 	print "new board is %r", newboard

@socketio.on('get reports', namespace='/test')
def create_db_reports(message):
	global client_count

	clients = socketio.rooms.get('/test', {}).get('game', set())

	#check if the user is playing with computer (or) other player
	if message['two_players'] == False:
		usr1 = session['user']
		usr2 = "Computer"		
		results = dbsession.query(Game).filter_by(usr1=usr1).filter_by(usr2=usr2).all()
		display_results = create_results_dict(results)
		print display_results
		#if only one game is played, the results are zero for a draw case and for other user
		if not usr1 in display_results:
			display_results[usr1] = 0;
		if not usr2 in display_results:
			display_results[usr2] = 0;
		if not 'Draw' in display_results:
			display_results['Draw'] = 0;
		emit('display results', display_results)
	else:
		client_count += 1
		if(client_count == 2):
			dbuser1 = dbsession.query(User).filter_by(socketid=request.namespace.socket.sessid).first()
			print "dbuser1:", dbuser1.username
			for socket in clients:
					if socket != request.namespace:
						dbuser2 = dbsession.query(User).filter_by(socketid=socket.socket.sessid).first()
						print "dbuser2:", dbuser2.username
			#results = dbsession.query(Game).filter_by(usr1=dbuser1.username).filter_by(usr2=dbuser2.username).all()
			results = dbsession.query(Game).filter(((Game.usr1==dbuser1.username) | (Game.usr1==dbuser2.username)) & ((Game.usr2==dbuser1.username) | (Game.usr2==dbuser2.username))).all()
			print "results:", results
			display_results = create_results_dict(results)
			print display_results
			#if only one game is played, the results are zero for a draw case and for other user
			if not dbuser1.username in display_results:
				display_results[dbuser1.username] = 0;
			if not dbuser2.username in display_results:
				display_results[dbuser2.username] = 0;
			if not 'Draw' in display_results:
				display_results['Draw'] = 0;
			emit('display results', display_results, broadcast=True)

@socketio.on('create or join room', namespace='/test')
def create_join_room(message):
	print ("create join room route in the server")
	print ("username on the server is" + message['username'])

	clients = socketio.rooms.get('/test', {}).get('game', set())

	numClients = len(clients);
	print("number of clients in the room", numClients)

	print message

 	emit('log', {'Request to create or join room' : message['room']})
 	emit('log', {'numClients before adding:' : numClients})

 	if(numClients == 0):
 		join_room(message['room'])
 		session['user'] = message['username']
 		print "first session user is", session['user']
 		newuser = User(socketid=request.namespace.socket.sessid, username=session['user'])
 		dbsession.add(newuser)
 		dbsession.commit() 		
 		emit('created',
         	{'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          		'count': numClients+1})
 	elif (numClients == 1 and message['two_players'] == True):
 		for client in clients:
 			client.emit('join', message)
		join_room(message['room'])
		session['user'] = message['username']
		print "second session user is", session['user']
		newuser = User(socketid=request.namespace.socket.sessid, username=session['user'])
 		dbsession.add(newuser)
 		dbsession.commit() 	
		emit('joined',
         	{'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          		'count': numClients+1, 'room' : message['room']})
	else:
		emit('full', message, broadcast=True)
    
	clients = socketio.rooms.get('/test', {}).get('game', set())
	numClients = len(clients)
	emit('log', {'numClients after adding:' : numClients}) 
	
	if message['two_players'] == False:
		emit('dashlog', 'You joined the room. Make your move')
	else:
		if numClients == 1:
			emit('dashlog', 'You joined the game room. Waiting for another player to join')
		else:
			emit('dashlog', 'Two players in the room. Start playing', broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0')