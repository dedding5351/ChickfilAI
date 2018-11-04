import socketio
try:
    import eventlet
    import eventlet.wsgi
except ImportError:
    eventlet = None

from flask import Flask, render_template

import socketio
from flask import Flask

from user_data import customerArray

sio = socketio.Server()
app = Flask(__name__, static_url_path = '', static_folder = 'frontEnd', template_folder = 'frontEnd')


@app.route('/')
def index():
    """Serve the client-side application."""
    with open('frontEnd/welcome.html') as f:
        return f.read()

@app.route('/landing')
def populateLandingPage():
    with open('frontEnd/index.html') as f:
        return f.read()

@app.route('/confirmation')
def populateConfirmationPage():
    with open('frontEnd/confirmation.html') as f:
        return f.read()

@sio.on('connect', namespace='/relay')
def connect(sid, environ):
    print('Client {} connected'.format(sid))


@sio.on('user_detection', namespace='/relay')
def message_func(sid, data):

    # data['name'] == whoever's name

    user = None
    for i_user in customerArray:
        if i_user.first_name == data['name']:
            user = i_user
            break

    if user:
        data['last_order'] = user.last_order
        data['order_price'] = user.order_price
        data['description'] = user.description
        data['url'] = user.url

    print("Relaying from {}: user_detection -> {}".format(sid, str(data)[:100]))
    sio.emit('user_detection', data, skip_sid=sid)


@sio.on('disconnect', namespace='/relay')
def disconnect(sid):
    print('Client {} disconnected'.format(sid))


if __name__ == '__main__':
    if eventlet:
        # wrap Flask application with engineio's middleware
        app = socketio.Middleware(sio, app)

        # deploy as an eventlet WSGI server
        eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 80)), app)
    else:
        app.run(debug=True)


