import datetime
import struct
from socket import *
import time

SYST_T = datetime.date(*time.gmtime(0)[0:3])
NTP_T = datetime.date(1900, 1, 1)
NTP_DELTA = (SYST_T - NTP_T).days * 24 * 3600


sock = socket(AF_INET, SOCK_DGRAM)
# sock.connect(('localhost', 123))
# data = '\x1b' + 47 * '\0'
data = bytearray([int("00100011", 2)] + 47 * [0])
sock.sendto(data, ('10.155.61.104', 123))
ans = sock.recvfrom(1024)
int = ans[0][40:44]
sh = ans[0][44:48]
print(struct.unpack('!1I', int)[0], '.', struct.unpack('!1I', sh)[0])
print(time.time() + NTP_DELTA)
#sock.sendto(''.encode(), ('10.155.61.104', 123))

sock.close()
