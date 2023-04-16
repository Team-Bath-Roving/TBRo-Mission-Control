# Network information
LAPTOP_IP = "localhost"

# ========================================================

# Import modules
import cv2
import numpy as np
import socket
import time
import struct
from random import randint
import threading
import queue
import json
from RoverSockets import SendSocket, ReceiveSocket

def listen_function(control_queue):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as recvsock:

		s = ReceiveSocket(recvsock, 5001)

		while True:
			control_data = s.recv_data()
			control_queue.put(control_data)

def main_function(control_queue):

	try:

		# Set up cameras (at the moment code only works with exactly 2, this will be changed)
		captures = [cv2.VideoCapture(0), cv2.VideoCapture(0)]
		PAYLOAD_STRING = "<HII"

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sendsock:

			# Connect to laptop
			s = SendSocket(sendsock, LAPTOP_IP, 5002, PAYLOAD_STRING)
			s.connect()

			# Send confirmation message
			msg = {"Connected": True}
			s.send(msg, [np.array([])] * 2)

			# ======

			prev_time = time.perf_counter()
			freq = 1/20

			control_list = []

			# Main rover loop
			while True:

				# Unload control instructions
				while not control_queue.empty():
					instruction = control_queue.get()
					if instruction == "QUIT_ROVER":
						print("Exiting")
						for cap in captures: cap.release()
						raise SystemExit
					else:
						control_list.append(instruction)

				# [Temp] Showing control instructions
				if control_list:
					print(control_list)
					control_list = []

				# Send feedback and images
				if time.perf_counter() - prev_time > freq:
					
					# [Temp] Feedback
					i = randint(0, 1000)
					if i < 100:
						fb = {"Test feedback": f"{i}"}
					else:
						fb = {}

					# Camera
					frames = []
					for i, cap in enumerate(captures):
						ret, frame = cap.read()

						if not ret:
							print(f"Skipped frame {i}")
							frame = np.array([])
						else:
							frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
							sf = 0.4 # Scale factor
							frame = cv2.resize(frame, (0, 0), fx=sf, fy=sf)

						frames.append(frame)

					s.send(fb, frames)
					prev_time = time.perf_counter()

	except KeyboardInterrupt:
		print(" KeyboardInterrupt caught")
		for cap in captures: cap.release()
		raise SystemExit

if __name__ == "__main__":
	control_queue = queue.Queue(0)

	thread = threading.Thread(target=listen_function, daemon=True, args=(control_queue,))
	thread.start()

	main_function(control_queue)