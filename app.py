from flask import Flask
from views import views
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
app.register_blueprint(views, url_prefix='/')

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)