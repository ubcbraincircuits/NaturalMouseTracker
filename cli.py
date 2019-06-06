import socket

HOST = '206.87.104.209'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST,PORT))
    s.sendall(b'Hey boys')
    data = s.recv(1024)

print('Received', repr(data))                    
