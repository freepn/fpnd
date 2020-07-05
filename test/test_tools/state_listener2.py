import signal

from time import sleep
from multiprocessing import Process
from nanoservice import Subscriber


def log(message):
    print('Subscriber got new message: {}'.format(message))


def start_listener(addr):
    """ Start a subscriber service with options """

    s = Subscriber(addr, bind=True)
    s.subscribe('diff', log)
    s.start()


# socket_addr = 'ipc:///tmp/fpnd.sock'
socket_addr = 'ipc:///run/fpnd/fpnd.sock'


def listen_main():
    print('Listening on socket {}'.format(socket_addr))

    proc = Process(target=start_listener, args=(socket_addr,))
    proc.start()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    listen_main()

    while True:
        print('doing something...')
        sleep(5)
        print('doing something else...')
        sleep(5)
