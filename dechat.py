"""Simple chat using a PUB-SUB pattern."""

import argparse
import os
import msg_pb2
from threading import Thread
import time
from datetime import datetime
import redis
from netifaces import interfaces, ifaddresses, AF_INET
import zmq

try:
    raw_input          # Python 2
except NameError:
    raw_input = input  # Python 3

# redis is used to log the messages exchanged in the chat.
msg_logs = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
# NOTE
# msg_logs = redis.StrictRedis(host='localhost', port=6379, db=0)
# on linux, 'localhost' doesn't write to redis

def send_pb(socket, sender, msg, flags=0, protocol=-1):
    """sends a protocol buffer of the message and logs it.""" 
    # Compose message with sender, content, and timestamp. """
    pb_data = msg_pb2.Msg() 
    pb_data.timestamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    pb_data.sender = sender
    pb_data.content = msg
    # Write information to a log (redis) 
    msg_logs.rpush('chat_logs',
              '[%s] %s: %s' % (pb_data.timestamp, pb_data.sender, pb_data.content))
    # Serialize message
    return socket.send(pb_data.SerializeToString(), flags=flags)


def recv_pb(socket, flags=0, protocol=-1):
    """receives a protocol buffer of the message."""
    # Parse message
    pb_data = msg_pb2.Msg()
    pb_data.ParseFromString(socket.recv(flags))
    return '[%s] %s: %s' % (pb_data.timestamp, pb_data.sender, pb_data.content)


def listen(ip, first_port, last_port):
    """listen for messages from one IP address and a range of ports."""
    ctx = zmq.Context.instance()
    receiver = ctx.socket(zmq.SUB)
    for port in range(first_port, last_port+1):
        receiver.connect("tcp://{0}:{1}".format(ip, port))

    receiver.setsockopt(zmq.SUBSCRIBE, b'')
    while True:
        try:
            print(recv_pb(receiver))
        except (KeyboardInterrupt, zmq.ContextTerminated):
            break

def main():
    ip = '127.0.0.1'	 # hard-coded to ease up testing
    first_port, last_port = 9000, 9100
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int, 
                        help="my port number (from %d to %d)" 
                             % (first_port, last_port),) 
    parser.add_argument("usr", type=str, default=os.environ['USER'],
                        nargs='?',
                        help="my user name",)
    args = parser.parse_args()

    ctx = zmq.Context.instance()

    # Extra thread for listening
    listen_thread = Thread(target=listen,
                           args=(ip, first_port, last_port))
    listen_thread.start()

    # Main thread for broadcasting
    sender = ctx.socket(zmq.PUB)
    sender.bind("tcp://%s:%s" % (ip, args.port))
    while True:
        try:
            msg = raw_input('>')
            send_pb(sender, args.usr, msg)
        except KeyboardInterrupt:
            break
    sender.close(linger=0)
    ctx.term()

if __name__ == '__main__':
    main()
