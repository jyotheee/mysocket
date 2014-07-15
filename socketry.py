from flask import Flask, request, session, render_template, g, redirect, url_for, flash
import jinja2
from flask.ext.socketio import SocketIO, emit, join_room, leave_room


app = Flask(__name__)
app.secret_key = 'secret key'
socketio = SocketIO(app)


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
	clients = socketio.rooms.get('/test', {}).get('foo', set())
	for socket in clients:
		if socket != request.namespace:
			print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
			print("Sending get media to other clients")
			socket.emit('get media')

@socketio.on('message', namespace='/test')
def handle_message(message):
	print('Message received on server:', message)
	emit('message', message, broadcast=True)

@socketio.on('create or join room', namespace='/test')
def create_join_room(message):
	
	print ("create join room route in the server")
	print('socketio is:'), socketio.rooms.get('/test', {}).get('foo', set())
	

	# namespaces = socketio.rooms
	# namespace = namespaces.get('/test', {})
	# room = namespace.get('foo', set())
	clients = socketio.rooms.get('/test', {}).get('foo', set())
	numClients = len(clients);
	print("number of clients in the room", numClients)


	print message

 	emit('log', {'Request to create or join room' : message['room']})
 	emit('log', {'numClients before adding:' : numClients})

 	if(numClients == 0):
 		join_room(message['room']) 		
 		emit('created',
         	{'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          		'count': numClients+1})
 	elif (numClients == 1):
 		for client in clients:
 			client.emit('join', message)
		join_room(message['room'])
		emit('joined',
         	{'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          		'count': numClients+1})
	else:
		emit('full', message, broadcast=True)
    
	clients = socketio.rooms.get('/test', {}).get('foo', set())
	numClients = len(clients)
	emit('log', {'numClients after adding:' : numClients}) 			

	# if numClients == 0:
	# 	socketio.join(room)
	# 	socketio.emit('created', room)
	# elif numClients == 1:
	# 	socketsio.io.i  (room).emit('join', room)
	# 	socketio.join(room);
	# 	socketio.emit('joined', room);
	# else:
	# 	socketio.emit('full', room);

	# socketio.emit('emit(): client ' + socketio.id + ' joined room ' + room);
	# socketio.broadcast.emit('broadcast(): client ' + socketio.id + ' joined room ' + room);

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0')