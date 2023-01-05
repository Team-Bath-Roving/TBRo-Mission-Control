import socket
import json
import struct
import numpy as np

# class SocketTimeout(Exception):
# 	'''
# 	Custom Exception to catch when a socket is disconnected
# 	'''
# 	def __init__(self, message=""):
# 		self.message = message

class SendSocket:
	'''
	Handles sending of information over socket
	'''
	def __init__(self, sock, target, port, payload_string):
		self.socket = sock
		self.target = target
		self.port = port
		self.payload_string = payload_string

	def connect(self):
		'''Connects/ reconnects socket to target'''
		self.socket.connect((self.target, self.port))
		print(f"Send socket connected to port {self.port}")

	def send(self, fb, imgs):
		'''Decode, calculate sizes and send feedback + camera frames'''
		encoded_fb = json.dumps(fb).encode()
		fb_size = len(encoded_fb)

		encoded_imgs = [img.tobytes() for img in imgs]
		img_sizes = [len(img) for img in encoded_imgs]

		sizes = struct.pack(self.payload_string, fb_size, *img_sizes)

		self.socket.sendall(sizes + encoded_fb + b"".join(encoded_imgs))

class ReceiveSocket:
	'''
	Handles receiving information over socket
	'''
	def __init__(self, sock, port):
		self.socket = sock
		self.port = port
		self.conn = None

		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(("", self.port))
		self.socket.listen(1)

		self.accept()

	def accept(self):
		'''Connects/ reconnects to incoming traffic'''
		self.conn, _ = self.socket.accept()
		print(f"Receive socket connected to port {self.port}")

	def recv_data(self):
		'''Receive and decode control instructions'''
		encoded_control = self.conn.recv(1024)
		return json.loads(encoded_control.decode())