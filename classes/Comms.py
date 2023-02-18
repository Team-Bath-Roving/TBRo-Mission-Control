from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
import jsock
import json
import errno
from classes.Output import Output
import os 
import sys
import select

SIZE = 1024
# TCP json communications module
class Comms:
	msg_in=[] # store json messages received
	connected=False
	client_sock=None
	host_port=None
	def __init__(self,host_IP:str,host_ports:int,output:Output,key):
		self.output=output
		self.host_IP=host_IP
		self.host_ports=host_ports
		self.key=key
		# self.create_socket()
	def receive(self):
		if self.connected:
			# socket_list=[sys.stdin,self.client_sock._socket]
			# read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
			# for sock in read_sockets:
			# 	if sock==self.client_sock._socket:
			try:
				data=self.client_sock.receive()
				if not data is None:
					self.msg_in.insert(0,data)
			except:
				pass
	def available(self):
		return len(self.msg_in)
	def read(self):
		if self.available():
			return self.msg_in.pop()
		else:
			raise Exception("Nothing to read")
	def send(self,msg,retry=True):
		if self.connected:
			try:
				self.client_sock.send(msg)
			except:
				if retry:
					self.send(msg,False)
				else:
					self.connected=False

class CommsServer(Comms):
	server_sock=None
	def create_socket(self):
		self.server_sock=jsock.ServerSocket(self.key)
		self.client_sock=self.server_sock.accept()
	def bind(self,port):
		self.output.write("INFO",f"TCP server awaiting connections at {self.host_IP}:{port}",False)
		try:
			self.server_sock.bind(self.host_IP,port)
			return True
		except Exception as e:
			self.output.write("EXCEPT",e)
			return False
	def connect(self):
		try:
			self.create_socket()
			# self.server_sock._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
			for port in self.host_ports:
				if self.bind(port):
					self.host_port=port
					break
			while not self.connected:
				self.client_sock=self.server_sock.accept()
				self.connected=(not self.client_sock is None) and self.client_sock.poll()
				if self.connected:
					self.output.write("INFO",f"TCP client connected from {self.client_sock.remote_address} via port {self.host_port}",False)
			# print(self.client_sock.poll())
		except Exception as e:
			self.output.write("EXCEPT",e,False)
			self.connected=False
			self.output.write("ERROR","No TCP client connected",False)
		
	def close(self):
		self.output.write("INFO","Closing sockets",False)
		try:
			if not self.server_sock is None:
				self.server_sock._socket.shutdown(SHUT_RDWR)
				self.server_sock.close()
			if not self.client_sock is None:
				self.client_sock._socket.shutdown(SHUT_RDWR)
				self.client_sock.close()
			self.client_sock=None
			self.server_sock=None
			self.connected=False
			self.output.write("INFO","Sockets Closed",False)
		except Exception as e:
			self.output.write("ERROR","Failed to close sockets",False)
			self.output.write("EXCEPT",e,False)

class CommsClient(Comms):
	def create_socket(self):
		self.client_sock=jsock.ClientSocket(self.key)
	def conn(self,port):
		self.client_sock._socket.settimeout(1)
		self.output.write("INFO",f"Connecting to TCP server at {self.host_IP}:{port}",False)
		try:
			self.client_sock.connect(self.host_IP,port)
			return True
		except Exception as e:
			self.output.write("EXCEPT",e)
			return False
	def connect(self):
		while not self.connected:
			# print("create sock")
			for port in self.host_ports:
				self.create_socket()
				if self.conn(port):
					self.host_port=port
					self.connected=self.client_sock.poll()
					break
		self.output.write("INFO",f"Connected to TCP server at {self.host_IP}:{self.host_port} from {self.client_sock.local_address}",False)
	def close(self):
		self.output.write("INFO","Closing sockets",False)
		try:
			if not self.client_sock is None:
				self.client_sock._socket.shutdown(SHUT_RDWR)
				self.client_sock.close()
			self.client_sock=None
			self.connected=False
			self.output.write("INFO","Sockets Closed",False)
		except Exception as e:
			self.output.write("ERROR","Failed to close sockets",False)
			self.output.write("EXCEPT",e,False)
	