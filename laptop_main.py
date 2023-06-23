# CONFIG
# Network information
# ROVER_IP = "rover.local"
ROVER_IP = "localhost"

# Camera information
CAM_NAMES = ["Cam 1"] # , "Cam 2", "Cam 3"]

# Window size
WIDTH, HEIGHT = 1200, 765

# ===================================

# Import libraries
import queue
import pygame
import numpy as np

# Import classes
from classes.FeedManager import FeedManager
from classes.ActionHandler import ActionHandler
from classes.MissionControl import MissionControl
from classes.Gamepad import GamepadManager, Gamepad
from classes.Sockets import SocketTimeout, ControlSend, FeedbackReceive, CameraReceive


def main_function(fb_queue, img_queues):
	sock = ControlSend(ROVER_IP, 5001)
	mc = MissionControl(WIDTH, HEIGHT)
	fm = FeedManager(mc, CAM_NAMES, img_queues)
	gm = GamepadManager()
	ah = ActionHandler(sock, mc, fm, gm)

	# Main loop
	done = False
	while not done:
		# Check connection
		conn = sock.check_connection()

		# Handle pygame events (eg button presses, quitting)
		done = ah.handle_events(pygame.event.get(), conn)

		# Attempt to fetch images from video streams
		fm.get_images()

		# *** Draw things on the pygame screen here
		# ***

		# Write if connection lost [Temp]
		mc.write_status(conn)
		
		mc.update_display()

		# Handle any feedback
		while not fb_queue.empty():
			# [Temp] For now just print to console
			print(fb_queue.get())

	# Quitting
	pygame.quit()
	raise SystemExit

if __name__ == "__main__":
	feedback_queue = queue.Queue(0)
	fb = FeedbackReceive(feedback_queue, 5002)
	fb.start()

	# Create dict with cam names as keys and length 1 queues as values
	img_queues = dict(zip(CAM_NAMES, [queue.Queue(1) for _ in CAM_NAMES]))
	cr = CameraReceive(img_queues)

	main_function(feedback_queue, img_queues)