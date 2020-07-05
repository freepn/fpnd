import signal

from nanoservice import Subscriber


def log(message):
    print('Subscriber got new message: {}'.format(message))


# socket_addr = 'ipc:///tmp/fpnd.sock'
socket_addr = 'ipc:///run/fpnd/fpnd.sock'
s = Subscriber(socket_addr, bind=True)
s.subscribe('diff', log)


def main():
    print('Listening on socket {}'.format(socket_addr))
    s.start()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
