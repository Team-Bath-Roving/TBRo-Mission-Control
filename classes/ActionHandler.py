import pygame

# Keybinds
SWAP_FEEDS = [pygame.K_o, pygame.CONTROLLER_BUTTON_A]
CYCLE_CAM_MODE = [pygame.K_p, pygame.CONTROLLER_BUTTON_B]

# ActionHandler class
class ActionHandler:
	'''
	Handles all actions performed after button presses, etc
	'''
	def __init__(self, fm, cont=None):
		self.FeedManager = fm
		self.Controller = cont

	def set_controller(self, new_cont):
		'''Changes the currently stored input controller'''
		self.Controller = new_cont

	def send_controller_state(self):
		'''Send the current state of the controller to the rover'''
		if (not self.Controller is None):
			pass

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