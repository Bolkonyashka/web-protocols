import datetime
import socket
import struct
import sys
import time


try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except Exception as e:
    print(e)
    sys.exit()

try:
    sock.bind(('', 123))
except Exception as e:
    print(e)
    sys.exit()

SYST_T = datetime.date(*time.gmtime(0)[0:3])
NTP_T = datetime.date(1900, 1, 1)
NTP_DELTA = (SYST_T - NTP_T).days * 24 * 3600

file = open('conf.txt')
c = file.readline()
CONF = int(c)


while True:
    d = sock.recvfrom(1024)

    data = d[0]
    addr = d[1]

    if not data:
        break

    if data[0] & 7 == 3:
        print("NTP IS COMMING!")
        cur_time = time.time()
        cur_time += NTP_DELTA
        cur_time = str(cur_time)
        cur_time = cur_time.split('.')
        print(cur_time)
        cur_time = struct.pack('!1I', int(cur_time[0]) + CONF) + struct.pack('!1I', int(cur_time[1]))
        answer = bytearray([int("00100100", 2), 2, 0, 6] + 12 * [0]) + cur_time * 4
        sock.sendto(answer, addr)


sock.close()
