from socket import socket, AF_INET, SOCK_DGRAM
import json

# Network information
RECEIVE_PORT = 5000
SIZE = 1024

# Set up socket for listening
receive_socket = socket(AF_INET, SOCK_DGRAM)
receive_socket.bind(("", RECEIVE_PORT))

print("Receiving commands from mission control")
print(f"Listening on port {RECEIVE_PORT}\n")

while True:
	data, addr = receive_socket.recvfrom(SIZE)
	data = data.decode()

	# Press Q in mission control to kill this program
	if "QUIT_ROVER" in str(data):
		print("\nQUITTING")
		break
	else:
		data = json.loads(data)
		print(f"{data}")

receive_socket.close()
raise SystemExit