from telnetlib import XASCII
import pygame
import json
from datetime import datetime
from time import sleep

# zero buffers
zero_buffer = [True] * 6

# Keybinds
SWAP_FEEDS = [pygame.K_o, pygame.CONTROLLER_BUTTON_X]
CYCLE_CAM_MODE = [pygame.K_p, pygame.CONTROLLER_BUTTON_Y]
RESET_FEEDS = [pygame.K_i]
BUTTON_N = [pygame.K_n, pygame.CONTROLLER_BUTTON_A] # Can rename these
BUTTON_M = [pygame.K_m, pygame.CONTROLLER_BUTTON_B]
BUTTON_T = [pygame.K_t]

# ActionHandler class
class ActionHandler:
	'''
	Handles all actions performed after button presses, etc
	'''
	def __init__(self, sendSocket, fm, cont=None):
		self.soc = sendSocket
		self.FeedManager = fm
		self.Controller = cont

		self.pow_mult = 1

		# self.URLS = URLS

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
			# Log this somehow
			print("Could not send data")
			return

	def send_commands(self):
		'''Send commands to rover if the controller is being acted on'''
		msg = []

		# LJOY (VERTICAL) - MOVE FORWARD/ BACKWARDS
		if abs(self.Controller.axes[1]) > 0.01:
			msg.append({"FORWARD": self.pow_mult * self.Controller.axes[1]})
			zero_buffer[0] = False
		elif not zero_buffer[0]:
			msg.append({"FORWARD": 0})
			zero_buffer[0] = True

		# RJOY (HORIZONTAL) - MOVE LEFT/ RIGHT
		if abs(self.Controller.axes[2]) > 0.01:
			msg.append({"TURN": self.Controller.axes[2]})
			zero_buffer[1] = False
		elif not zero_buffer[1]:
			msg.append({"TURN": 0})
			zero_buffer[1] = True

		# # DPAD (LEFT/ RIGHT) - PAN CAMERA
		# if self.Controller.dpad[0]:
		# 	msg.append({"CAM_PAN": -1})
		# 	zero_buffer[2] = False
		# elif self.Controller.dpad[1]:
		# 	msg.append({"CAM_PAN": 1})
		# 	zero_buffer[2] = False
		# elif not zero_buffer[2]:
		# 	msg.append({"CAM_PAN": 0})
		# 	zero_buffer[2] = True

		# # DPAD (DOWN/ UP) - TILT CAMERA
		# if self.Controller.dpad[2]:
		# 	msg.append({"CAM_TILT": -1})
		# 	zero_buffer[3] = False
		# elif self.Controller.dpad[3]:
		# 	msg.append({"CAM_TILT": 1})
		# 	zero_buffer[3] = False
		# elif not zero_buffer[3]:
		# 	msg.append({"CAM_TILT": 0})
		# 	zero_buffer[3] = True

		# LEFT TRIGGER - SCOOP
		if self.Controller.axes[4] > 0.05:
			v = 2 * int(self.Controller.buttons[4]) - 1
			msg.append({"SCOOP": v * self.Controller.axes[4]})
			zero_buffer[4] = False
		elif not zero_buffer[4]:
			msg.append({"SCOOP": 0})
			zero_buffer[4] = True

		# RIGHT TRIGGER - BRUSH
		if self.Controller.axes[5] > 0.05:
			v = -2 * int(self.Controller.buttons[5]) + 1
			msg.append({"BRUSH": v * self.Controller.axes[5]})
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
		# elif b in RESET_FEEDS:
		# 	self.reset_feeds()
		elif b in BUTTON_N:
			if self.pow_mult > 0:
				self.adjust_power(-0.05)
		elif b in BUTTON_M:
			if self.pow_mult < 1:
				self.adjust_power(0.05)
		elif b in BUTTON_T:
			self.button_function("T")

	def swap_feeds(self):
		'''Swaps camera feeds'''
		self.FeedManager.swap_feeds()

	def cycle_cam_mode(self):
		'''Cycles between ways organising camera feeds'''
		self.FeedManager.cycle_mode()

	def button_function(self, button):
		'''[Template] A function triggered by a controller button'''
		pass
		
	def adjust_power(self, x):
		self.pow_mult += x