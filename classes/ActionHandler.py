import pygame
import json
from datetime import datetime

from .CameraFeed import CameraFeed

# zero buffers
zero_buffer = [True] * 6

# Keybinds
SWAP_FEEDS = [pygame.K_o]
CYCLE_CAM_MODE = [pygame.K_p]
RESET_FEEDS = [pygame.K_i]
BUTTON_A = [pygame.K_a, pygame.CONTROLLER_BUTTON_A] # Can rename these
BUTTON_B = [pygame.K_b, pygame.CONTROLLER_BUTTON_B]
BUTTON_X = [pygame.CONTROLLER_BUTTON_X]
BUTTON_Y = [pygame.CONTROLLER_BUTTON_Y]

# ActionHandler class
class ActionHandler:
	'''
	Handles all actions performed after button presses, etc
	'''
	def __init__(self, sendSocket, fm, URLS, cont=None):
		self.soc = sendSocket
		self.FeedManager = fm
		self.Controller = cont

		self.URLS = URLS

	def set_controller(self, new_cont):
		'''Changes the currently stored input controller'''
		self.Controller = new_cont

	def send_msg(self, msg):
		'''Convert a message into json string and try to send it to the rover'''
		# Prepend current time
		msg.insert(0, datetime.now().strftime("%H:%M:%S.%f")[:-3])

		# Catch exception if msg cannot be sent
		try:
			# Convert list to JSON string then encode to bytes and send
			self.soc.sendall(json.dumps(msg).encode())
		except:
			# TODO: Log this somehow
			return

	def send_commands(self):
		'''Send commands to rover if the controller is being acted on'''
		msg = []

		# LJOY (VERTICAL) - MOVE FORWARD/ BACKWARDS
		if abs(self.Controller.axes[1]) > 0.01:
			msg.append({"FORWARD": self.Controller.axes[1]})
			zero_buffer[0] = False
		elif not zero_buffer[0]:
			msg.append({"FORWARD": 0})
			zero_buffer[0] = True

		# RJOY (HORIZONTAL) - MOVE LEFT/ RIGHT
		if abs(self.Controller.axes[3]) > 0.01:
			msg.append({"TURN": self.Controller.axes[3]})
			zero_buffer[1] = False
		elif not zero_buffer[1]:
			msg.append({"TURN": 0})
			zero_buffer[1] = True

		# DPAD (LEFT/ RIGHT) - PAN CAMERA
		if self.Controller.dpad[0]:
			msg.append({"CAM_PAN": -1})
			zero_buffer[2] = False
		elif self.Controller.dpad[1]:
			msg.append({"CAM_PAN": 1})
			zero_buffer[2] = False
		elif not zero_buffer[2]:
			msg.append({"CAM_PAN": 0})
			zero_buffer[2] = True

		# DPAD (DOWN/ UP) - TILT CAMERA
		if self.Controller.dpad[2]:
			msg.append({"CAM_TILT": -1})
			zero_buffer[3] = False
		elif self.Controller.dpad[3]:
			msg.append({"CAM_TILT": 1})
			zero_buffer[3] = False
		elif not zero_buffer[3]:
			msg.append({"CAM_TILT": 0})
			zero_buffer[3] = True

		# LEFT/ RIGHT BUMPER - TRIGGER DIRECTION
		trigger_dir = -int(self.Controller.buttons[4]) + int(self.Controller.buttons[5]) 

		# LEFT TRIGGER - SCOOP
		if trigger_dir and self.Controller.axes[2] > 0.05:
			msg.append({"SCOOP": trigger_dir * self.Controller.axes[2]})
			zero_buffer[4] = False
		elif not zero_buffer[4]:
			msg.append({"SCOOP": 0})
			zero_buffer[4] = True

		# RIGHT TRIGGER - BRUSH
		if trigger_dir and self.Controller.axes[5] > 0.05:
			msg.append({"BRUSH": trigger_dir * self.Controller.axes[5]})
			zero_buffer[5] = False
		elif not zero_buffer[5]:
			msg.append({"BRUSH": 0})
			zero_buffer[5] = True

		# Only send if commands were added
		if len(msg) > 0:
			self.send_msg(msg)

	def button_press(self, b):
		'''Calls a function after button on keyboard or controller is pressed'''
		if b in SWAP_FEEDS:
			self.swap_feeds()
		elif b in CYCLE_CAM_MODE:
			self.cycle_cam_mode()
		elif b in RESET_FEEDS:
			self.reset_feeds()
		elif b in BUTTON_A:
			self.button_function("A")
		elif b in BUTTON_B:
			self.button_function("B")
		elif b in BUTTON_X:
			self.button_function("X")
		elif b in BUTTON_Y:
			self.button_function("Y")

	def swap_feeds(self):
		'''Swaps camera feeds'''
		self.FeedManager.swap_feeds()

	def cycle_cam_mode(self):
		'''Cycles between ways organising camera feeds'''
		self.FeedManager.cycle_mode()
	
	def reset_feeds(self):
		self.FeedManager.release_feeds()
		self.FeedManager.feeds = [
			CameraFeed(*self.URLS[0], (80, 90), (550, 400)),
			CameraFeed(*self.URLS[1], (628, 90), (550, 400))
		]

	def button_function(self, button):
		'''[Template] A function triggered by a controller button'''
		command = {"BUTTON_PRESSED": button}
		self.send_msg([command])