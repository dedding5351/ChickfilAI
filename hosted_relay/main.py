import socketio
import eventlet
import eventlet.wsgi
from flask import Flask, render_template

sio = socketio.Server()
app = Flask(__name__)

@app.route('/')
def index():
    """Serve the client-side application."""
    return 'Ok'

@sio.on('connect', namespace='/relay')
def connect(sid, environ):
    print('Client {} connected'.format(sid))

@sio.on('user_detection', namespace='/relay')
def message_func(sid, data):
    print("Relaying from {}: user_detection -> {}".format(sid, str(data)[:100]))
    sio.emit('user_detection', data, skip_sid=sid)

@sio.on('disconnect', namespace='/relay')
def disconnect(sid):
    print('Client {} disconnected'.format(sid))

if __name__ == '__main__':
    # wrap Flask application with engineio's middleware
    app = socketio.Middleware(sio, app)

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 80)), app)

