import socket
import json
import time

class SocketTimeout(Exception):
	'''
	Custom Exception to catch when a socket is disconnected
	'''
	def __init__(self, message=""):
		self.message = message

class SendSocket:
	'''
	Handles sending of information over socket
	'''
	def __init__(self, sock, target, port):
		self.socket = sock
		self.target = target
		self.port = port

	def connect(self):
		'''Connects/ reconnects socket to target'''
		self.socket.connect((self.target, self.port))
		print(f"Send socket connected to port {self.port}")

	def send_msg(self, msg):
		'''Encode and send dict/ list over socket'''
		self.socket.sendall(json.dumps(msg).encode())

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

	def recv_data(self, size, overflow=b""):
		'''Receive encoded data of specified size over socket'''
		data = overflow
		start_time = time.perf_counter()

		while len(data) < size:
			data += self.conn.recv(4096)
			if time.perf_counter() - start_time > 0.5:
				raise SocketTimeout

		return data[:size], data[size:]