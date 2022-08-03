from socket import socket, AF_INET, SOCK_DGRAM
import json

PORT_NUMBER = 5000
SIZE = 1024

mySocket = socket(AF_INET, SOCK_DGRAM)
mySocket.bind(("", PORT_NUMBER))

print("Receiving commands from mission control")
print(f"Listening on port {PORT_NUMBER}\n")

while True:
	data, addr = mySocket.recvfrom(SIZE)
	data = data.decode()

	if "QUIT_ROVER" in str(data):
		raise SystemExit
	else:
		data = json.loads(data)
		print(f"{data}")