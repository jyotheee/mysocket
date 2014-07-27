from flask import Flask, request, session, render_template, g, redirect, url_for, flash
import jinja2
from flask.ext.socketio import SocketIO, emit, join_room, leave_room
from game_model import Game, Move, User, dbsession, createBoard, updateGameBoard, isWinner, isFull

app = Flask(__name__)
app.secret_key = 'secret key'
socketio = SocketIO(app)

global play

@app.route("/")
def index():
	return render_template("index.html")

@socketio.on('connect', namespace='/test')
def test_connect():
	print("*************************************")
	createBoard()
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

@socketio.on('message', namespace='/test')
def handle_message(message):
	print('Message received on server:', message)
	emit('message', message, broadcast=True)

@socketio.on('game move', namespace='/test')
def move_made(message):
	global play

	print('Move info received on the server')
	clients = socketio.rooms.get('/test', {}).get('game', set())

	#assign game id to the database
	# if not play:
	# 	game = Game()
	# 	dbsession.add(game)
	# 	dbsession.commit()
	# 	game_id = game.id
	# 	play = True

	# print "Game id is", game_id

	#store the move info into the database
	# move = Move(gameid=game.id, board_loc=message['position'], user=session['user'])
 	# dbsession.add(move)
 	# dbsession.commit()
  # 	print('Successfully added new game move to database!')

  	#send move info to client other than who sent it
	for socket in clients:
		if socket != request.namespace:
			print "Sending move info"
			socket.emit('log', 'Incoming move')
			socket.emit('move made', { 'session_name' : session['user'], 'move' : message['position'], 'move_value' : message['position_value']})
 	
 	#Update the board with the input move
 	newboard = updateGameBoard(message['position_value'], message['position'])
 	
 	#check for winning condition. If gameboard full, it is a draw, else check for win condition
 	if isFull(newboard):
 		emit('game over', {'result' : 'Game is a draw'}, broadcast=True)
 		winner = 'Draw'
 	elif isWinner(newboard, message['position_value']):
 		print 'Winner of the game'
 		emit('game over', {'result' : 'you win the game'})
 		# dbuser1 = dbsession.query(User).filter_by(socketid=request.namespace.socket.sessid).first()
 		winner = dbuser1.username
 		for socket in clients:
 			if socket != request.namespace:
 				socket.emit('game over', {'result' : 'you lose the game'})
 				# dbuser2 = dbsession.query(User).filter_by(socketid=socket.socket.sessid).first()
 		game = Game(usr1=dbuser1.username, usr2=dbuser2.username, winner=winner)


 	print "new board is %r", newboard

@socketio.on('create or join room', namespace='/test')
def create_join_room(message):
	global play
	play = False
	print ("create join room route in the server")
	#print('socketio is:'), socketio.rooms.get('/test', {}).get('game', set())

	# namespaces = socketio.rooms
	# namespace = namespaces.get('/test', {})
	# room = namespace.get('foo', set())
	clients = socketio.rooms.get('/test', {}).get('game', set())

	numClients = len(clients);
	print("number of clients in the room", numClients)


	print message

 	emit('log', {'Request to create or join room' : message['room']})
 	emit('log', {'numClients before adding:' : numClients})

 	if(numClients == 0):
 		join_room(message['room'])
 		session['user'] = "tintin"
 		print "first session user is", session['user']
 		newuser = User(socketid=request.namespace.socket.sessid, username=session['user'])
 		dbsession.add(newuser)
 		dbsession.commit() 		
 		emit('created',
         	{'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          		'count': numClients+1})
 	elif (numClients == 1):
 		for client in clients:
 			client.emit('join', message)
		join_room(message['room'])
		session['user'] = "snowy"
		print "second session user is", session['user']
		newuser = User(socketid=request.namespace.socket.sessid, username=session['user'])
 		dbsession.add(newuser)
 		dbsession.commit() 	
		emit('joined',
         	{'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          		'count': numClients+1})
	else:
		emit('full', message, broadcast=True)
    
	clients = socketio.rooms.get('/test', {}).get('game', set())
	numClients = len(clients)
	
	# client_map = {}
	# for c in clients:
	# 	print "!!!!!!!!!!!!!!!!!!!!!!!"	
	# 	print "name of sessid" , c.socket.sessid
	# 	print dir(c.socket)
	# 	print dir(c)
	# 	client_map[c.socket] = c
	# print client_map
	
	emit('log', {'numClients after adding:' : numClients}) 	


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0')