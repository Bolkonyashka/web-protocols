import socket
import re
import threading
import ssl

BAD_SITES = ['reklama.ngs.ru', 'www.googleadservices.com', 'reklama2.ngs.ru', 'reklama3.ngs.ru', 'reklama4.ngs.ru',
             'reklama5.ngs.ru', 'reklama6.ngs.ru', 'adclick.g.doubleclick.net', 'tpc.googlesyndication.com',
             'securepubads.g.doubleclick.net', 'reklama0.ngs.ru', 'www.googletagservices.com', 'an.yandex.ru',
             'googleads.g.doubleclick.net', 'cas.criteo.com']


def get_recv(conn):
    recv = b''
    conn.settimeout(0.5)
    while True:
        try:
            data = conn.recv(2048)
        except:
            return recv
        recv += data
        if not data:
            break
    return recv


def filter(host, recv, conn):
    for site in BAD_SITES:
        if host in site:
            conn.send(b'HTTP/1.1 400 Bad Request\r\n\r\n')
            raise socket.timeout
    return host, recv


def ssl_handler(conn, recv):
    try:
        host = re.search(r'Host:\s*([a-z.1-9-]*)', recv.decode()).group(1)
        host, recv = filter(host, recv, conn)
        ssl_sock = ssl.create_connection((host, 443))
        sock = ssl_sock
        conn.send('HTTP/1.1 200 OK\r\n\r\n'.encode())
        recv = get_recv(conn)
        sock.send(recv)
    except:
        conn.close()
        return
    while True:
        try:
            recv_host = get_recv(sock)
            if not recv_host:
                break
            conn.send(recv_host)
            recv_client = get_recv(conn)
            if not recv_client:
                break
            sock.send(recv_client)
        except Exception as e:
            print(e)
            break
    sock.close()
    conn.close()


def handler(conn, recv):
    try:
        host = re.search(r'Host:\s*([a-z.1-9-]*)', recv.decode()).group(1)
        host, recv = filter(host, recv, conn)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, 80))
        sock.send(recv)
        recv_host = get_recv(sock)
        conn.send(recv_host)
        while True:
            try:
                recv_client = get_recv(conn)
                if not recv_client:
                    break
                sock.send(recv_client)
                recv_host = get_recv(sock)
                if not recv_host:
                    break
                conn.send(recv_host)
            except Exception as e:
                print(e)
                break
    except:
        pass
    try:
        sock.close()
    except:
        pass
    conn.close()


def connect(conn):
    try:
        recv = get_recv(conn)
        is_ssl = recv.lower().startswith(b'connect')
        if is_ssl:
            ssl_handler(conn, recv)
        else:
            handler(conn, recv)
    except Exception as e:
        print(e)


def start():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 8080))
    sock.listen(1000)
    while True:
        conn, addr = sock.accept()
        thread = threading.Thread(target=connect, args=(conn,))
        thread.setDaemon(True)
        thread.start()


if __name__ == '__main__':
    start()
