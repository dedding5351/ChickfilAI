from socketIO_client import SocketIO, LoggingNamespace
import sys


if __name__ == '__main__':
    name = sys.argv[1]

    with SocketIO('54.161.203.83', 80, LoggingNamespace) as socketIO:
        socketIO.emit('user_detection', {'name': name}, path='/relay')
