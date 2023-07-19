# CONFIG
# Network information
# ROVER_IP = "rover.local"
ROVER_IP = "localhost"

# Camera information
CAM_NAMES = ["Pi Cam"]

# Window size
WIDTH, HEIGHT = 1200, 780

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
	mc = MissionControl(WIDTH, HEIGHT, CAM_NAMES)
	fm = FeedManager(mc, CAM_NAMES, img_queues)
	gm = GamepadManager()
	ah = ActionHandler(sock, mc, fm, gm)

	# Main loop
	done = False
	while not done:
		# Check connection
		conn = sock.check_connection()
		mc.system_info["connected"] = conn

		# Handle any feedback
		fb = []
		while not fb_queue.empty():
			ah.handle_feedback(fb_queue.get()) # <-- THIS FUNCTION NEEDS TO BE WRITTEN

		# Handle pygame events (eg button presses, quitting) and send axis movements
		done = ah.handle_events(pygame.event.get(), conn)
		ah.send_axes(conn)

		# Attempt to fetch images from video streams
		fm.get_images()

		# Draw things on the pygame screen here
		mc.draw_borders()

		# mc.write_coords() # [Temp]
		mc.update_display()

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