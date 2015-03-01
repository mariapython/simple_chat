"""Decentralized chat example"""

import argparse
import os
import json
from threading import Thread

from netifaces import interfaces, ifaddresses, AF_INET

import zmq


def listen(masked):
    """listen for messages

    masked is the first three parts of an IP address:

        192.168.1

    The socket will connect to all of X.Y.Z.{1-254}.
    """
    ctx = zmq.Context.instance()
    listener = ctx.socket(zmq.SUB)
    for last in range(1, 255):
        listener.connect("tcp://{0}.{1}:9000".format(masked, last))

    listener.setsockopt(zmq.SUBSCRIBE, b'')
    while True:
        try:
            print(listener.recv_json())
        except (KeyboardInterrupt, zmq.ContextTerminated):
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface", type=str, help="the network interface",
                        choices=interfaces(),)
    parser.add_argument("user", type=str, default=os.environ['USER'],
                        nargs='?',
                        help="Your username",)
    args = parser.parse_args()
    inet = ifaddresses(args.interface)[AF_INET]
    addr = inet[0]['addr']
    masked = addr.rsplit('.', 1)[0]
    print masked

    ctx = zmq.Context.instance()

    listen_thread = Thread(target=listen, args=(masked,))
    listen_thread.start()

    bcast = ctx.socket(zmq.PUB)
    bcast.bind("tcp://%s:9000" % args.interface)
    print("starting chat on %s:9000 (%s.*)" % (args.interface, masked))
    while True:
        try:
            raw_input('>')
            bcast.send_json(json.dumps({1: 1}))
        except KeyboardInterrupt:
            break
    bcast.close(linger=0)
    ctx.term()

if __name__ == '__main__':
    main()
