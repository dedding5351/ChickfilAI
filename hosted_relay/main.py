import socketio
import eventlet
import eventlet.wsgi
from flask import Flask, render_template

sio = socketio.Server()
app = Flask(__name__)

relayed_messages = ['user_detection']

@app.route('/')
def index():
    """Serve the client-side application."""
    return 'Ok'

@sio.on('connect', namespace='/relay')
def connect(sid, environ):
    print('Client {} connected'.format(sid))

for message in relayed_messages:
    @sio.on(message, namespace='/relay')
    def message_func(sid, data):
        print("Relaying from {}: {} -> {}".format(sid, message, str(data)[:100]))
        sio.emit(message, data, skip_sid=sid)

@sio.on('disconnect', namespace='/relay')
def disconnect(sid):
    print('Client {} disconnected'.format(sid))

if __name__ == '__main__':
    # wrap Flask application with engineio's middleware
    app = socketio.Middleware(sio, app)

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 80)), app)

