'''List players on a bf4 server

Usage: get_players.py <ip_address> [server_admin_port (default 47200)]
'''
import socket
import sys
from collections import namedtuple

from frostbite_wire.packet import Packet


def recv(sock):
    # Pull enough to get the int headers and instantiate a Packet
    out = sock.recv(12)
    p = Packet.from_buffer(out)
    packet_size = len(p)
    # Pull one character at a time until we've recv'd
    # up to the reported size
    while len(out) < packet_size:
        out += sock.recv(1)
    return out

try:
    address = sys.argv[1]
except:
    print __doc__
    sys.exit(1)

try:
    port = int(sys.argv[2])
except IndexError:
    port = 47200

server = address, port

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server)

serverinfo = Packet(1, False, True, 'serverinfo')
sock.sendall(serverinfo.to_buffer())

response = Packet.from_buffer(recv(sock))
serverinfo = response.words

listplayers = Packet(2, False, True, 'listPlayers all')
sock.sendall(listplayers.to_buffer())
response = Packet.from_buffer(recv(sock))
listplayers = response.words

sock.close()

# Need both of these to go on
assert serverinfo[0] == 'OK'
assert listplayers[0] == 'OK'

# Print out pretty server name/players
curated_serverinfo = (serverinfo[1], serverinfo[2], serverinfo[3])
print '%s (%s/%s)' % curated_serverinfo

# Chomp on the listplayers output and loop out some namedtuples
num_fields, the_rest = int(listplayers[1]), listplayers[2:]
fields, num_players, players = (
    the_rest[:num_fields],
    the_rest[num_fields],
    the_rest[num_fields + 1:]
)

Player = namedtuple('Player', fields)

player_list = list()
while players:
    player_list.append(Player(*players[:num_fields]))
    players = players[num_fields:]

team_1 = filter(lambda player: player.teamId == '1', player_list)
team_2 = filter(lambda player: player.teamId == '2', player_list)

print 'Team 1:'
print '======='
for player in sorted(team_1, key=lambda player: int(player.score), reverse=True):
    print player

print 'Team 2:'
print '======='
for player in sorted(team_2, key=lambda player: int(player.score), reverse=True):
    print player

