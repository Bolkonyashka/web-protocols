import socket


host = "smtp.gmail.com"
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, 587))
while True:
    inp = input("Вводи: \n")
    sock.sendall(bytes(inp, encoding="UTF-8") + b'\r\n')
    data = sock.recv(512)
    print(data.decode())



