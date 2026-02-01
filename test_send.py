import socket
import keep_pb2  # <-- the generated file

p = keep_pb2.Packet()
p.typ = 0  # ask
p.id = "test-123"
p.src = "human:tester"
p.dst = "server"
p.body = "make tea please"

data = p.SerializeToString()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect(('localhost', 9009))
s.sendall(data)

try:
    response = s.recv(4096)
    print("FAIL — got reply (unsigned should be dropped):", response)
except socket.timeout:
    print("PASS — unsigned packet dropped (no reply, as expected)")

s.close()
