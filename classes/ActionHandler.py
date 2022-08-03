import pygame
import json
from datetime import datetime

# Keybinds
SWAP_FEEDS = [pygame.K_o, pygame.CONTROLLER_BUTTON_A]
CYCLE_CAM_MODE = [pygame.K_p, pygame.CONTROLLER_BUTTON_B]

# ActionHandler class
class ActionHandler:
	'''
	Handles all actions performed after button presses, etc
	'''
	def __init__(self, sendSocket, fm, cont=None):
		self.soc = sendSocket
		self.FeedManager = fm
		self.Controller = cont

	def set_controller(self, new_cont):
		'''Changes the currently stored input controller'''
		self.Controller = new_cont

	def send_commands(self):
		'''Send commands to rover if the controller is being acted on'''
		# Set up msg with current time
		msg = [
			datetime.now().strftime("%H:%M:%S.%f")[:-3]
		]

		# LJOY (VERTICAL) - MOVE FORWARD/ BACKWARDS
		if abs(self.Controller.axes[1]) > 0.01:
			msg.append({"FORWARD": self.Controller.axes[1]})

		# RJOY (HORIZONTAL) - MOVE LEFT/ RIGHT
		if abs(self.Controller.axes[3]) > 0.01:
			msg.append({"TURN": self.Controller.axes[3]})

		# DPAD (LEFT/ RIGHT) - PAN CAMERA
		if self.Controller.dpad[0]:
			msg.append({"CAM_PAN": -1})
		elif self.Controller.dpad[1]:
			msg.append({"CAM_PAN": 1})

		# DPAD (DOWN/ UP) - TILT CAMERA
		if self.Controller.dpad[2]:
			msg.append({"CAM_TILT": -1})
		elif self.Controller.dpad[3]:
			msg.append({"CAM_TILT": 1})

		# LEFT/ RIGHT BUMPER - TRIGGER DIRECTION
		trigger_dir = -int(self.Controller.buttons[4]) + int(self.Controller.buttons[5]) 

		# LEFT TRIGGER - SCOOP
		if trigger_dir and self.Controller.axes[2] > 0.05:
			msg.append({"SCOOP": trigger_dir * self.Controller.axes[2]})

		# RIGHT TRIGGER - BRUSH
		if trigger_dir and self.Controller.axes[5] > 0.05:
			msg.append({"BRUSH": trigger_dir * self.Controller.axes[5]})

		# Only send if commands were added
		if len(msg) > 1:
			# Catch exception if msg cannot be sent
			try:
				# Convert list to JSON string then encode to bytes and send
				self.soc.sendall(json.dumps(msg).encode())
			except:
				# TODO: Log this somehow
				return

	def button_press(self, b):
		'''Calls a function after button on keyboard or controller is pressed'''
		if b in SWAP_FEEDS:
			self.swap_feeds()
		elif b in CYCLE_CAM_MODE:
			self.cycle_cam_mode()

	def swap_feeds(self):
		'''Swaps camera feeds'''
		self.FeedManager.swap_feeds()

	def cycle_cam_mode(self):
		'''Cycles between ways organising camera feeds'''
		self.FeedManager.cycle_mode()