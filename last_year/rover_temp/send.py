from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime
import json

# Network information
LAPTOP_IP = "192.168.0.50"
SEND_PORT = 5001

# Set up socket connection to rover
send_socket = socket(AF_INET, SOCK_DGRAM)
send_socket.connect((LAPTOP_IP, SEND_PORT))

print("Rover code for sending commands to mission control\n")

command = input("Type string to send to mission control: ")
msg = [
	datetime.now().strftime("%H:%M:%S.%f")[:-3],
	{"ROVER_FEEDBACK": command}
]

try:
	# Convert the msg into a json string, then encode it into bytes, 
	# then send it through send_socket to mission control
	send_socket.sendall(json.dumps(msg).encode())
except:
	# Catch any errors from not being able to send
	print("Couldn't send command, check LAPTOP_IP is correct")