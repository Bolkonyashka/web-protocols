import re
import socket
import ssl

import sys

HOST = 'api.vk.com'
PORT = 443

us_id = input()

req = 'GET https://api.vk.com/method/users.get?user_ids={}&v=5.64 HTTP/1.1\r\n'.format(us_id)
req += 'Host: api.vk.com\r\n\r\n'
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)
wrappedSocket = ssl.wrap_socket(sock)
wrappedSocket.connect((HOST, PORT))
wrappedSocket.send(req.encode('utf-8'))
res = wrappedSocket.recv(4096).decode()
try:
    e = re.search('\"error\":(.*?)', res).group(1)
    print('Ошибка: неправильный id или просто звезды не сошлись')
    sys.exit(1)
except Exception:
    pass
first_name = re.search('\"first_name\":\"(.*?)\"', res).group(1)
last_name = re.search('\"last_name\":\"(.*?)\"', res).group(1)
uid = re.search('\"id\":(.*?),', res).group(1)
print('Пользователь: ' + first_name + " " + last_name + " " + uid)
deleted = False
try:
    d = re.search('\"deactivated\":\"(.*?)\"', res).group(1)
    if d == "deleted" or d == "banned":
        deleted = True
        print('Пользователь удалил аккаунт или был заблокирован  :(')
except Exception:
    pass
if not deleted:
    req = 'GET https://api.vk.com/method/friends.get?user_id={}&fields=first_name,last_name&v=5.64 HTTP/1.1\n'.format(uid)
    req += 'Host: api.vk.com\n\n'
    wrappedSocket.send(req.encode('utf-8'))
    data = b''
    while res:
        try:
            res = wrappedSocket.recv(4096)
            data += res
        except Exception:
            break
    count = 1
    data = data.decode()
    data = re.search('\"items\":\[(.*)\]', data).group(1)
    print('Друзья:')
    while True:
            try:
                index = 0
                first_name = re.search('\"first_name\":\"(.*?)\"', data).group(1)
                index1 = data.index(first_name) + len(first_name)
                last_name = re.search('\"last_name\":\"(.*?)\"', data).group(1)
                uid = re.search('\"id\":(.*?),', data).group(1)
                # if data.index(last_name) + len(last_name) > index:
                index = data.index(last_name) + len(last_name)
                if index1 == index:
                    data = data[index1:]
                    index = data.index(last_name) + len(last_name)
                data = data[index:]
                print(str(count) + ': ' + last_name + ' ' + first_name + ' ' + uid)
                count += 1
            except Exception:
                break
    wrappedSocket.close()
