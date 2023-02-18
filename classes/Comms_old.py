from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
import json
import errno
from classes.Output import Output

SIZE = 1024
# TCP communications module
class Comms:
	msg_in=[] # store json messages received
	connected=False
	sock:socket=None
	def __init__(self,host_IP:str,host_port:int,output:Output):
		self.output=output
		self.host_IP=host_IP
		self.host_port=host_port
		self.sock=socket(AF_INET,SOCK_STREAM)
		self.sock.setblocking(False)
	def receive(self):
		try:
			rawdata = self.sock.recv(SIZE)
			self.msg_in.insert(0,rawdata)
			print(rawdata.decode())
		except OSError as e:
			err = e.args[0]
			if not (err == errno.EAGAIN or err == errno.EWOULDBLOCK):
				raise e

	def available(self):
		return len(self.msg_in)
	def read(self):
		if self.available():
			return self.msg_in.pop()
		else:
			# print("Nothing to read in TCP buffer!")
			return {}
	def read_string(self):
		return self.read().decode()
	def read_json(self):
		return json.loads(self.read_string())
	def send(self,msg):
		if self.connected:
			try:
				self.sock.sendall(msg)
				return True
			except Exception as e:
				print(e)
				self.connected=False
				self.output.write(Output.ERROR, "TCP write fail")
		else:
			self.output.write(Output.ERROR, "TCP write fail: Socket closed")
	def send_string(self,msg):
		return self.send(msg.encode())
	def send_json(self,msg):
		return self.send_string(json.dumps(msg))
	def close(self):
		if self.connected:
			print("INFO: Closing TCP socket")
			try:
				self.sock.close()
				self.connected=False
			except:
				print("ERROR: Failed to close TCP sockets")

class CommsServer(Comms):
	def connect(self):
		self.close()
		self.output.write(Output.INFO,"TCP server awaiting connections")
		try:
			self.sock=socket(AF_INET,SOCK_STREAM)
			self.sock.bind(("", self.host_port))
			self.sock.setblocking(True)
			self.sock.listen()
			self.sock.accept()
			self.sock.setblocking(False)
			self.connected=True
			self.output.write(Output.INFO,"TCP client connected")
		except Exception as e:
			print(f"EXCEPT: {e}")
			self.connected=False
			self.output.write(Output.INFO,"No TCP client connected")
		return self.connected
	
class CommsClient(Comms):
	def connect(self):
		self.close()
		self.output.write(Output.INFO,"Connecting to TCP server")
		try:
			self.sock=socket(AF_INET,SOCK_STREAM)
			self.sock.setblocking(True)
			self.sock.connect((self.host_IP, self.host_port))
			self.connected=True
			self.sock.setblocking(False)
			self.output.write(Output.INFO,"TCP connected")
		except Exception as e:
			print(e)
			self.output.write(Output.INFO,"TCP connection failed")
			self.connected=False
		return self.connected
	