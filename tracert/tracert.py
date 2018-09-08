from select import select
from socket import *
import re
import sys
from struct import pack


def get_info(ip, whois, pattern):
    sock = socket(AF_INET, SOCK_STREAM)
    try:
        sock.settimeout(2)
        sock.connect((whois, 43))
        sock.setblocking(0)
        sock.sendall((ip + "\r\n").encode())
        data = b''
        while select([sock], [], [], 0.25)[0]:
            who_data = sock.recv(4096)
            if len(who_data) == 0:
                break
            data += who_data
    except:
        data = ''
    result = []
    if data:
        for pat in pattern:
            d = re.search(pat+b':(.*)', data.upper())
            if d:
                result.append(d.group(1).decode().lstrip())
            else:
                result.append('*')
    else:
        for pat in pattern:
            result.append('*')
    return result


def tracert(host):
    host = gethostbyname(host)
    hope = 30
    port = 33434
    ttl = 1
    while True:
        tracer = socket(AF_INET, SOCK_RAW, getprotobyname('icmp'))
        tracer.setsockopt(SOL_IP, IP_TTL, ttl)
        data = bytearray([8, 0, 247, 248, 0, 1, 0, 6] + 64 * [0])
        tracer.sendto(data, (host, port))
        tracer.settimeout(2)
        try:
            data = tracer.recvfrom(1024)
            ip = data[1][0]
            addr = ip
            whois = get_info(ip, "whois.iana.org", [b'REFER'])[0]
            info = get_info(ip, whois, [b'COUNTRY', b'ORIGIN', b'NETNAME'])
            if info[2]:
                addr = addr + "\n\t\t\t\t" + info[2]
            print('{}\t{}\t{}\t{}'.format(str(ttl).rjust(3), info[0], info[1], addr))
            if ip == host:
                break
        except timeout:
            print('{}     *\t*\t*\t{}'.format(str(ttl).rjust(3), 'Превышен timeout'))
        except Exception as e:
            print(e)
        finally:
            tracer.close()
        if ttl >= hope:
            sys.exit("Превышен лимит TTL")
        ttl += 1


if __name__ == '__main__':
    try:
        tracert(sys.argv[1])
    except Exception as e:
        sys.exit(e)
