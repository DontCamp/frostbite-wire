import hashlib
import os
from collections import defaultdict
from itertools import chain

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

from frostbite_wire.packet import Packet


class ProtocolPlugin(object):
    def __init__(self, protocol):
        self.protocol = protocol
        for command in self.subscribe_commands:
            protocol.subscribe(self, command)
        self.onConnect()

    def __call__(self, command, seq_num, sent, received):
        # Check OK, handle errors here?
        self.handlePacket(command, seq_num, sent, received)

    def onConnect(self):
        # override this!
        pass


# TODO Logging in is a special case, and should be configured from
# BF4Protocol on down
class LoginPlugin(ProtocolPlugin):
    subscribe_commands = [
        'login.hashed',
        'version',
        'admin.EventsEnabled',
        'serverinfo'
    ]
    logged_in = False

    def onConnect(self):
        self.protocol.sendMessage('version')
        self.protocol.sendMessage('serverinfo')

    def handlePacket(self, command, seq_num, sent, received):
        if command == 'version':
            print 'Version is %s' % received[1]
            if received[1] == 'BF4':
                self.protocol.sendMessage('login.hashed')
            # else: splode if not BF4?
        elif command == 'serverinfo':
            print '%s' % received[1]
            print '%s/%s Players' % (received[2], received[3])
        elif command == 'login.hashed':
            if len(sent) == 1 and not self.logged_in:
                # Login packet to get salt; log in
                try:
                    salt = received[1].decode("hex")
                    pwhash = hashlib.md5(salt + os.environ['BF4_RCON_PASS'])
                    pwhash_hexupper = pwhash.hexdigest().upper().strip()
                    self.protocol.sendMessage(['login.hashed', pwhash_hexupper])
                except:
                    pass
            elif len(sent) == 2 and received[0] == 'OK':
                print 'Logged in'
                self.logged_in = True
                self.protocol.sendMessage('admin.EventsEnabled true')
            else:
                pass
        elif command == 'admin.EventsEnabled' and received[0] == 'OK':
            print 'Receiving events'


class EventPlugin(ProtocolPlugin):
    subscribe_commands = [
        'ALL'
    ]

    def handlePacket(self, command, seq_num, sent, received):
        print '%s: %s' % (command, ' '.join(received[1:]))


class BF4Protocol(Protocol):
    _to_process = None
    _sent = dict()
    _plugins = defaultdict(set)

    def connectionMade(self):
        self._to_process = bytearray('')
        for plugin in self.factory.plugins:
            plugin(self)

    def sendMessage(self, msg):
        p = Packet(self.factory.sequence_number, words=msg)
        self.factory.packets[p.sequence_number] = [p.words, None]
        # Increment the seq_num on the class for future instances
        self.factory.sequence_number += 1
        self.transport.write(str(p.to_buffer()))

    def dataReceived(self, data):
        self._to_process += bytearray(data)
        while self._to_process:
            bytes_to_process = len(self._to_process)
            if bytes_to_process < 12:
                break

            # Enough bytes received to construct a Packet and get
            # the size of the incoming data
            p = Packet.from_buffer(self._to_process[:12])
            if bytes_to_process < p.size:
                break

            # Have enough bytes to process a complete packet
            p = Packet.from_buffer(self._to_process[:p.size])
            self._to_process = self._to_process[p.size:]

            if p.is_response:
                self.factory.packets[p.sequence_number][1] = p.words
                self.notifySubscribers(p.sequence_number,
                    *self.factory.packets.pop(p.sequence_number))
            else:
                # ACK packet. For now, everything is OK!
                ack = Packet(p.sequence_number, is_response=True, is_client=True,
                    words='OK')
                self.transport.write(str(ack.to_buffer()))
                self.notifySubscribers(p.sequence_number, [p.words[0]], p.words)

    def subscribe(self, plugin, command):
        self._plugins[command].add(plugin)

    def notifySubscribers(self, seq_num, sent, received):
        command = sent[0]
        # TODO document 'ALL' magic
        plugins = chain(self._plugins[command], self._plugins['ALL'])
        for plugin in plugins:
            plugin(command, seq_num, sent, received)


class BF4ClientFactory(ReconnectingClientFactory):
    protocol = BF4Protocol
    sequence_number = 0
    packets = dict()
    plugins = set()

    def clientConnectionFailed(self, connector, reason):
        print 'Connection Failed:', reason
        reactor.stop()

    @classmethod
    def subscribe(cls, plugin):
        cls.plugins.add(plugin)


def react(host, port):
    #63.251.20.89:25200
    BF4ClientFactory.subscribe(LoginPlugin)
    reactor.connectTCP(host, port, BF4ClientFactory())
    reactor.run()
