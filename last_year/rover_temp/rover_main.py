import cv2
import numpy as np
import socket
import struct
from random import randint
import time

MY_IP = "localhost"
# MY_IP = "192.168.0.25"
# MY_IP = "DESKTOP-DK0M68F.local"


# EXTERNAL WEBCAM #
cap1 = cv2.VideoCapture(0)
# MAC WEBCAM #
cap2 = cv2.VideoCapture(0)

mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
mysocket.connect((MY_IP, 9850))
print("socket connected")

a = time.perf_counter()

freq = 1 / 20 # 20 fps

while True:
	# Only loop once every 0.05 seconds (20 fps) -- *** Make easily customisable
	if time.perf_counter() - a > freq:

		try:
			# CAP 1

			# Get the frame
			ret, frame = cap1.read()

			if ret:

				# Convert to greyscale (1/3 of size)
				# frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

				# Scale down to lower resolution
				sc = 0.3
				res_frame1 = cv2.resize(frame, (0,0), fx=sc, fy=sc)

				# Flip the frame
				# res_frame = cv2.flip(res_frame, 1)
			else:
				print(f"Skipped 1 {randint(100, 999)}")

			# CAP 2

			# Get the frame
			ret, frame = cap2.read()

			if ret:

				# Convert to greyscale (1/3 of size)
				# frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

				# Scale down to lower resolution
				sc = 0.4
				res_frame2 = cv2.resize(frame, (0,0), fx=sc, fy=sc)

				# Flip the frame
				# res_frame = cv2.flip(res_frame, 1)
			else:
				print(f"Skipped 2 {randint(100, 999)}")



			# Convert numpy array to bytes
			encoded_data1 = res_frame1.tobytes()
			encoded_data2 = res_frame2.tobytes()

			# Get length of encoded_data and convert to bytes
				# Explanation: We need to know how many bytes the encoded frame is so that 
				# we know when we've received it all. So we use the "struct" library to 
				# encode that integer length, l, into a fixed number of bytes - which can
				# then be decoded and only data after than considered on the other end 
			l1 = len(encoded_data1)
			l2 = len(encoded_data2)
			msg_sizes = struct.pack("<II", l1, l2)


			# Send to PC
			mysocket.sendall(msg_sizes + encoded_data1 + encoded_data2)

		
		except KeyboardInterrupt as e:
			print(f" -- keyboard interrupt: {e}")
			break
		except socket.error as e:
			print(f"socket error: {e}")
			break
		except cv2.error as e:
			print(f"cv2 error: ret={ret}: {e}")

		# Time after loop
		a = time.perf_counter()

cap1.release()
cap2.release()
# cv2.destroyAllWindows()
raise SystemExit