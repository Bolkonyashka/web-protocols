from socket import *
import sys


def tcp_scanner(host, p_min, p_max):
    res = []
    for i in range(int(p_min), int(p_max) + 1):
        sock = socket(AF_INET, SOCK_STREAM, getprotobyname('tcp'))
        sock.settimeout(1)
        try:
            sock.connect((host, i))
            res.append(i)
            print("Port was found: ", i)
        except:
            print("---")
            pass
        finally:
            sock.close()
    if len(res) > 0:
        print("RESULT: the following TCP ports open in the range {} - {}:".format(p_min, p_max))
        for j in res:
            print(j)
    else:
        print("RESULT: open tcp ports is not found in range {} - {}".format(p_min, p_max))

if __name__ == "__main__":
    tcp_scanner(sys.argv[1], sys.argv[2], sys.argv[3])
