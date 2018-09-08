fr_ids = re.search('\"response\":\[(.*)\]', res).group(1)
sp = fr_ids.split(',')
k = len(sp)
data = b''
req = 'GET https://api.vk.com/method/users.get?user_ids={} HTTP/1.1\r\n'.format(gr)
req += 'Host: api.vk.com\r\n\r\n'
wrappedSocket.send(req.encode('utf-8'))

while res:
    try:
        # print('1')
        res = wrappedSocket.recv(4096)
        data += res
    except Exception:
        break
