"""Decentralized chat example"""

import argparse
import os
import msg_pb2
from threading import Thread
import time
from datetime import datetime
import redis

from netifaces import interfaces, ifaddresses, AF_INET

import zmq

rds = redis.StrictRedis(host='localhost', port=6379, db=0)


def send_pb(socket, sender, msg, flags=0, protocol=-1):
    pbmsg = msg_pb2.Msg()
    pbmsg.content = msg
    pbmsg.sender = sender
    ts = time.time()
    timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    pbmsg.timestamp = timestamp
    rds.rpush('chat_logs',
              '[%s] %s: %s' % (pbmsg.timestamp, pbmsg.sender, pbmsg.content))
    return socket.send(pbmsg.SerializeToString(), flags=flags)


def recv_pb(socket, flags=0, protocol=-1):
    pbmsg = msg_pb2.Msg()
    pbmsg.ParseFromString(socket.recv(flags))
    return '[%s] %s: %s' % (pbmsg.timestamp, pbmsg.sender, pbmsg.content)


def listen(ip, port_st, port_nd):
    """listen for messages

    masked is the first three parts of an IP address:

        192.168.1

    The socket will connect to all of X.Y.Z.{1-254}.
    """
    ctx = zmq.Context.instance()
    listener = ctx.socket(zmq.SUB)
    for port in range(int(port_st), int(port_nd)+1):
        listener.connect("tcp://{0}:{1}".format(ip, port))

    listener.setsockopt(zmq.SUBSCRIBE, b'')
    while True:
        try:
            print(recv_pb(listener))
        except (KeyboardInterrupt, zmq.ContextTerminated):
            break


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument("interface", type=str, help="the network interface",
    #                     choices=interfaces(),)
    parser.add_argument("sip", type=str, help="the ip of the self",)
    parser.add_argument("sport", type=str, help="the port of the self",)
    parser.add_argument("dip", type=str, help="the ip of the peer",)
    parser.add_argument("dport_st", type=str,
                        help="the start port of the peers",)
    parser.add_argument("dport_nd", type=str,
                        help="the end port of the peers",)
    parser.add_argument("user", type=str, default=os.environ['USER'],
                        nargs='?',
                        help="Your username",)
    args = parser.parse_args()

    ctx = zmq.Context.instance()

    listen_thread = Thread(target=listen,
                           args=(args.dip, args.dport_st, args.dport_nd))
    listen_thread.start()

    bcast = ctx.socket(zmq.PUB)
    bcast.bind("tcp://%s:%s" % (args.sip, args.sport))
    # print("starting chat on %s:9000" % (args.interface))
    while True:
        try:
            msg = raw_input('>')
            send_pb(bcast, args.user, msg)
        except KeyboardInterrupt:
            break
    bcast.close(linger=0)
    ctx.term()

if __name__ == '__main__':
    main()
