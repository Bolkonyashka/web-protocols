import socket
import ssl
import re
import base64
import sys
import os.path
import quopri


def auth(sock, user, password):
    cmd = b'USER ' + user.encode('windows-1251') + b'\r\n'
    sock.send(cmd)
    data = sock.recv(4096)
    sock.send(b'PASS ' + password.encode('windows-1251') + b'\r\n')
    data = sock.recv(4096)
    match = re.search(b'\+OK', data)
    if not match:
        print('ERROR')
        raise ConnectionResetError
    print('OK')


def connect(mailbox):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    sock = ssl.wrap_socket(sock)
    sock.settimeout(2)
    try:
        sock.connect((mailbox, 995))
        sock.recv(4096)
    except Exception as e:
        print('Ошибка соединения c сервером')
        print(e)
        sock.close()
        raise ConnectionResetError
    print('ОК')
    sock.settimeout(None)
    return sock


def quit(sock):
    sock.send(b'QUIT\r\n')
    sock.recv(4096)
    sock.close()
    print('OK')
    raise ConnectionResetError


def importer(sock, num_msg):
    cmd = b'RETR ' + num_msg.encode('windows-1251') + b' \r\n'
    sock.send(cmd)
    data = b''
    sock.settimeout(2)
    while True:
        try:
            data += sock.recv(4096)
            match = re.search(b'-ERR', data)
            if match:
                print('Письма не существует или звезды не сошлись.')
                return
        except socket.timeout:
            break
    sock.settimeout(None)
    name = 1
    while os.path.exists('emails/mail' + str(name)):
        name += 1
    name = 'mail' + str(name)
    try:
        os.mkdir('emails/' + name)
        os.mkdir('emails/' + name + '/Content')
    except FileExistsError:
        pass

    headers = headers_finder(data)
    with open('emails/' + name + '/headers.txt', 'w') as f:
        f.write(headers)

    match = re.findall(b'boundary="(.*)"', data)
    if len(match) != 0:
        gen_boundary = match[0]
    if len(match) > 1:
        i = 1
        while i < len(match):
            data = data.replace(match[i], gen_boundary)
            i += 1
    c = data.index(b'\r\n\r\n')
    if len(match) != 0:
        datas = data[c:].split(gen_boundary)
    else:
        c = data.index(b'Content-Transfer-Encoding:')
        data = data[c:]
        datas = []
        datas.append(data)
    for record in datas:
        match = re.search(b'Content-Type: (.*)', record)
        if match and (re.search(b'text/plain', record[match.start(1): match.end(1)])
                      or re.search(b'text/html', record[match.start(1): match.end(1)])):
            parse_text(record, 1, name)
            break
        # elif match and re.search(b'text/html', record[match.start(1): match.end(1)]):
            # parse_text(record, 1, name)
            # break
    for record in datas:
        match = re.search(b'Content-Type: (.*)', record)
        if match and (re.search(b'image', record[match.start(1): match.end(1)].split(b'/')[0])
                      or re.search(b'application', record[match.start(1): match.end(1)].split(b'/')[0])
                      or re.search(b'text/html', record[match.start(1): match.end(1)])):
            parse_image(record, name)
        # elif match and re.search(b'application', record[match.start(1): match.end(1)].split(b'/')[0]):
            # parse_image(record, name)
        # elif match and re.search(b'text/html', record[match.start(1): match.end(1)]):
            # parse_image(record, name)
    print('OK')


def parse_text(string, type, name):
    match = re.search(b'Content-Transfer-Encoding: (.*)', string)
    coding = string[match.start(1): match.end(1)]
    code_str = string.split(b'Content-Transfer-Encoding: ' + coding)[1]
    if not re.search(b'quoted-printable', string):
        if not re.search(b'8bit', coding):
            code_str = code_str.replace(b'\r\n', b'')
    else:
        try:
            code_str = code_str.split(b'format="flowed"\r\n\r\n')[1]
            code_str = code_str.replace(b'\r\n\r\n--_', b'')
            code_str = code_str.replace(b'\r\n\r\n', b'\n')
            code_str = code_str.replace(b'=\r\n', b'')
            code_str = code_str.replace(b'\n', b'\r\n\r\n')
        except IndexError:
            c = code_str.index(b'<div>')
            datas = code_str[c:]
            datas = datas.replace(b'=\r\n', b'')
            arr = re.findall(b'<div>(.*?)</div>', datas)
            str_8bit = b''
            for el in arr:
                str_8bit += el + b'\r\n'
            code_str = str_8bit
    code_str = code_str.replace(b'\.', b'')
    if re.search(b'base64', coding):
        str_base64 = base64.b64decode(code_str)
        if type:
            with open('emails/' + name + '/msg_text.txt', 'w') as f:
                f.write(str_base64.decode('utf-8'))
            return
        else:
            return str_base64.decode('utf-8')
    elif re.search(b'8bit', coding):
        if not re.search(b'<div>', code_str):
            if type:
                with open('emails/' + name + '/msg_text.txt', 'w') as f:
                    f.write(code_str.decode('utf-8'))
                return
            else:
                return code_str.decode('utf-8')[1:]
        c = code_str.index(b'<div>')
        datas = code_str[c:]
        arr = re.findall(b'<div>(.*?)</div>', datas)
        str_8bit = ''
        for el in arr:
            str_8bit += el.decode('utf-8') + '\r\n'
        if type:
            with open('emails/' + name + '/msg_text.txt', 'w') as f:
                f.write(str_8bit)
            return
        else:
            return str_8bit
    elif re.search(b'quoted-printable', coding):
        str_quopri = quopri.decodestring(code_str)
        if type:
            with open('emails/' + name + '/msg_text.txt', 'w') as f:
                f.write(str_quopri.decode('utf-8'))
            return
        else:
            return str_quopri.decode('utf-8')


def parse_image(string, name):
    match = re.search(b'name="(.*?)"', string)
    if match is None:
        return
    arr = re.findall('=\?(.*)?\?.?\?(.*?)\?=', string[match.start():match.end()].decode('utf-8'))
    if len(arr) == 0:
        exchange = string[match.start(1):match.end(1)].decode('utf-8')
    else:
        exchange = base64.b64decode(arr[0][1])
        exchange = exchange.decode('utf-8')
    parts = string.split(b'\r\n\r\n')
    if len(parts) < 3 or parts[2] == b'--_----------':
        code_str = string.split(b'\r\n\r\n')[1]
    else:
        code_str = string.split(b'\r\n\r\n')[2]
        if code_str == b'':
            code_str = string.split(b'\r\n\r\n')[1]
    code_str = code_str.replace(b'\r\n', b'')
    code_str = code_str.replace(b'\.', b'')
    str_base64 = base64.b64decode(code_str)
    f = open('emails/' + name + '/Content/' + exchange, 'wb')
    f.write(str_base64)
    f.close()


def headers_finder(data):
    # print(data)
    data_head = data.split(b'\r\n\r\n')[0]
    strings = data_head.split(b'\r\n')
    headers = ''
    for string in strings:
        boundary_match = re.findall(b'boundary="(.*)"', string)
        if boundary_match:
            boundary = boundary_match[0].decode()
            headers += ' boundary="' + boundary + '"'
            continue
        match_gen = re.findall(b'(.*): (.*)', string)
        if match_gen:
            headers += '\r\n'
            headers += match_gen[0][0].decode() + ': '
        match = re.findall(b'=\?(.*)?\?(.?)\?(.*?)\?=', string)
        if match:
            pass
            # if match[0][1] == b'B':
                # headers += base64.b64decode(match[0][2]).decode(match[0][0].decode())
                # s = match[0][2] + b'?='
                # headers += string.split(s)[1].decode()
        else:
            if match_gen:
                headers += match_gen[0][1].decode()
            else:
                headers += string.decode()
    return headers

def data_finder(data):
    match = re.findall(b'boundary="(.*)"', data)
    if len(match) != 0:
        gen_boundary = match[0]
    if len(match) > 1:
        i = 1
        while i < len(match):
            data = data.replace(match[i], gen_boundary)
            i += 1
    c = data.index(b'\r\n\r\n')
    if len(match) != 0:
        data1 = data[c:].split(gen_boundary)
    else:
        c = data.index(b'Content-Transfer-Encoding:')
        data = data[c:]
        data1 = []
        data1.append(data)
    for record in data1:
        match = re.search(b'Content-Type: (.*)', record)
        if match and (re.search(b'text/plain', record[match.start(1): match.end(1)])
                      or re.search(b'text/html', record[match.start(1): match.end(1)])):
            data = parse_text(record, 0, None).split('\n')
            break
        # elif match and re.search(b'text/html', record[match.start(1): match.end(1)]):
            # data = parse_text(record, 0, None).split('\n')
            # break
    return data

def top(sock, num_msg, count, type):
    try:
        s = int(count)
    except:
        print('Число строк введено неправильно :с')
        return
    max = str(sys.maxsize - 1)
    cmd = b'TOP ' + num_msg.encode('windows-1251') + b' ' + max.encode('windows-1251') + b' \r\n'
    sock.send(cmd)
    data = b''
    sock.settimeout(2)
    while True:
        try:
            data += sock.recv(4096)
            match = re.search(b'-ERR', data)
            if match:
                print('Письма не существует или звезды не сошлись.')
                return
        except socket.timeout:
            break
    sock.settimeout(None)
    if type:
        print('Top письма')
        print("***********************************************************")
        data = data_finder(data)
        for i in range(int(count)):
            if i >= len(data):
                break
            print(data[i])
        print("***********************************************************")
    else:
        print('Заголовки')
        print("***********************************************************")
        print(headers_finder(data))
        print("***********************************************************")


def start(mail, user, password):
    try:
        print('Соединение...')
        sock = connect(mail)
        sock.setblocking(True)
        print('Аутентификация...')
        auth(sock, user, password)
    except ConnectionResetError:
        return
    # thr_noop = threading.Thread(target=update, args=(sock,))
    # thr_noop.setDaemon(True)
    # thr_noop.start()
    while True:
        try:
            com = input('Введите команду: ')
            c_data = com.split(' ')
            cmd = c_data[0]
            if cmd == 'quit':
                print('Отключение от сервера...')
                quit(sock)
            if cmd == 'head':
                if len(c_data) < 2:
                    print('Неверная команда')
                    continue
                else:
                    arg = c_data[1]
                top(sock, arg, 0, 0)
            elif cmd == 'top':
                if len(c_data) < 3:
                    print('Неверная команда')
                    continue
                else:
                    arg1 = c_data[1]
                    arg2 = c_data[2]
                top(sock, arg1, arg2, 1)
            elif cmd == 'import':
                if len(c_data) < 2:
                    print('Неверная команда')
                    continue
                arg = c_data[1]
                print('Скачивание...')
                importer(sock, arg)
            # command_NOOP(sock)
        except ConnectionResetError:
            break
        except Exception as e:
            print(e)
            print('Звезды не сошлись. Давай еще разочек.')

if __name__ == '__main__':
    while True:
        mail = input('pop mail server: ')
        user = input('user: ')
        password = input('password: ')
        start(mail, user, password)
