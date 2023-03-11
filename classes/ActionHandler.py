from telnetlib import XASCII
import pygame
import json
from datetime import datetime
from time import sleep
from .CameraFeed import CameraFeed
from tbroLib.Comms import Comms

# zero buffers
zero_buffer = [True] * 6

# Button and axis mapping

from enum import IntEnum

# class Axes(IntEnum):
# 	L_TRIG=4
# 	R_TRIG=5
# 	L_X=0
# 	L_Y=1
# 	R_X=2
# 	R_Y=3

class Axes(IntEnum):
	L_TRIG=pygame.CONTROLLER_AXIS_TRIGGERLEFT
	R_TRIG=pygame.CONTROLLER_AXIS_TRIGGERRIGHT
	L_X=pygame.CONTROLLER_AXIS_LEFTX
	L_Y=pygame.CONTROLLER_AXIS_LEFTY
	R_X=pygame.CONTROLLER_AXIS_RIGHTX
	R_Y=pygame.CONTROLLER_AXIS_RIGHTY

class Dpad(IntEnum):
	LEFT=pygame.CONTROLLER_BUTTON_DPAD_LEFT
	RIGHT=pygame.CONTROLLER_BUTTON_DPAD_RIGHT
	DOWN=pygame.CONTROLLER_BUTTON_DPAD_DOWN
	UP=pygame.CONTROLLER_BUTTON_DPAD_UP

class Buttons(IntEnum):
	A=pygame.CONTROLLER_BUTTON_A
	B=pygame.CONTROLLER_BUTTON_B
	X=pygame.CONTROLLER_BUTTON_X
	Y=pygame.CONTROLLER_BUTTON_Y
	LB=pygame.CONTROLLER_BUTTON_LEFTSTICK
	RB=pygame.CONTROLLER_BUTTON_RIGHTSTICK
	LS=pygame.CONTROLLER_BUTTON_LEFTSHOULDER
	RS=pygame.CONTROLLER_BUTTON_RIGHTSHOULDER
	Back=pygame.CONTROLLER_BUTTON_BACK
	Guide=pygame.CONTROLLER_BUTTON_GUIDE
	Start=pygame.CONTROLLER_BUTTON_START

# Camera Keybinds
SWAP_FEEDS = [pygame.K_o, Buttons.X]
CYCLE_CAM_MODE = [pygame.K_p, Buttons.Y]
RESET_FEEDS = [pygame.K_i]

# Pan Tilt Keybinds
BUTTON_PAN_L         = [pygame.K_j]
BUTTON_PAN_R         = [pygame.K_l]
BUTTON_TILT_UP       = [pygame.K_i]
BUTTON_TILT_DOWN     = [pygame.K_k]
BUTTON_CENTRE_CAMERA = [pygame.K_u,Buttons.RB]

BUTTON_N = [pygame.K_n, Buttons.A] # Can rename these
BUTTON_M = [pygame.K_m, Buttons.B]
BUTTON_T = [pygame.K_t]

# Movement keybinds
BUTTON_FORWARD  = [pygame.K_w]
BUTTON_BACKWARD = [pygame.K_s]
BUTTON_ROLL_L   = [pygame.K_a]
BUTTON_ROLL_R   = [pygame.K_d]
BUTTON_TURN_L   = [pygame.K_q]
BUTTON_TURN_R   = [pygame.K_e]
BUTTON_TURN_MODE = [pygame.K_r,Buttons.LS]


# R_X = pygame.CONTROLLER_AXIS_RIGHTX

class axisCommand:
	previous=None
	controller=None

	def __init__(self,axis,deadzone=0.2,multiplier=1,invertButton=-1):
		self.axis=axis
		self.deadzone=deadzone
		self.multiplier=multiplier
		self.invertButton=invertButton
	def setController(self,controller):
		self.controller=controller
	def transform(self):
		# set value based on joystick axis
		value=self.controller.axes[self.axis]
		if self.controller.buttons[self.invertButton]: # invert axis if button pressed
			if self.invertButton:
				value=-value
		if abs(value)>self.deadzone:
			value=((value-self.deadzone)*self.multiplier)
		else:
			value=0
		return value
	
class buttonCommand:
	state=0
	def __init__(self,pos=[],neg=[],multiplier=255):
		self.pos=pos
		self.neg=neg
		self.multiplier=multiplier
	def press(self,b):
		oldState=self.state
		if b in self.pos:
			# print("pos")
			self.state=self.multiplier
			# print(self.state!=oldState )
		elif b in self.neg:
			# print("neg")
			self.state=-self.multiplier
			# print(self.state!=oldState )
		return self.state!=oldState # only true if button state has changed!
	def release(self,b):
		oldState=self.state
		if b in self.pos or b in self.neg:
			self.state=0
			# print("release")
			# print(self.state!=oldState )
		return self.state!=oldState # only true if button state has changed! 

# ActionHandler class
class ActionHandler:
	'''
	Handles all actions performed after button presses, etc
	'''

	msg={}

	def __init__(self, comms, fm, cont=None):
		self.comms = comms
		self.FeedManager = fm
		self.Controller = cont

		self.pow_mult = 1

		# self.URLS = URLS

		# dict to store axis based commands
		self.axisAction = {
			"CAM_PAN" :axisCommand(axis=Axes.R_X   ,multiplier=-1  ),
			"CAM_TILT":axisCommand(axis=Axes.R_Y   ,multiplier=-1  ),
			"DRIVE"   :axisCommand(axis=Axes.L_Y   ,multiplier= 255),
			"TURN"    :axisCommand(axis=Axes.L_X   ,multiplier= 255),
			"ROLL_L"  :axisCommand(axis=Axes.L_TRIG,multiplier= 255),
			"ROLL_R"  :axisCommand(axis=Axes.R_TRIG,multiplier= 255)
		}
		# dict to store button based commands
		self.buttonAction = {
			"CAM_PAN"  :buttonCommand(pos=BUTTON_PAN_L  ,neg=BUTTON_PAN_R,    multiplier=-1),
			"CAM_TILT" :buttonCommand(pos=BUTTON_TILT_UP,neg=BUTTON_TILT_DOWN,multiplier=-1),
			"CAM_CENTRE" :buttonCommand(pos=BUTTON_CENTRE_CAMERA,multiplier=1),
			"DRIVE"    :buttonCommand(pos=BUTTON_FORWARD,neg=BUTTON_BACKWARD, multiplier=100),
			"TURN"     :buttonCommand(pos=BUTTON_TURN_L ,neg=BUTTON_TURN_R,   multiplier=100),
			"ROLL_L"   :buttonCommand(pos=BUTTON_ROLL_L ,                       multiplier=100),
			"ROLL_R"   :buttonCommand(pos=BUTTON_ROLL_R ,                       multiplier=100),
			"TURN_MODE":buttonCommand(pos=BUTTON_TURN_MODE, multiplier=1)
		}


	def set_controller(self, new_cont):
		'''Changes the currently stored input controller'''
		self.Controller = new_cont
		for param in self.axisAction.values():
			param.setController(self.Controller)


	def axis_update(self):
		for (command_name,params) in self.axisAction.items():
			roundedVal=float('%.3f'%(params.transform()))
			if roundedVal != params.previous:
				params.previous=roundedVal
				self.msg[command_name]=roundedVal
				# self.send_commands()


	def send_commands(self):
		'''Send commands to rover if the controller is being acted on'''
		# Only send if commands were added
		# print(len(self.msg))
		# if len(self.msg)>:
		# set timestamp
		# self.msg["timestamp"]=datetime.now().strftime("%H:%M:%S.%f")[:-3]
		# print complete msg to console
		# print(self.msg)
		# send message as JSON
		self.comms.send(self.msg)
		# reset to blank message
		self.msg={
			# "timestamp":0
		}
	
			
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
		else:
			# Send commands based on button presses
			for (command_name,params) in self.buttonAction.items():
				if params.press(b):
					self.msg[command_name]=params.state
					# self.send_commands()
					# print(self.msg)

	def button_release(self,b):
		# Send commands based on button releases
		for (command_name,params) in self.buttonAction.items():
			if params.release(b):
				self.msg[command_name]=params.state
				# self.send_commands()
				# print(self.msg)


	def swap_feeds(self):
		'''Swaps camera feeds'''
		self.FeedManager.swap_feeds()

	def cycle_cam_mode(self):
		'''Cycles between ways organising camera feeds'''
		self.FeedManager.cycle_mode()
	
	# def reset_feeds(self):
	# 	self.FeedManager.release_feeds()
	# 	self.FeedManager.feeds = [
	# 		CameraFeed(*self.URLS[0], (80, 90), (550, 400)),
	# 		CameraFeed(*self.URLS[1], (628, 90), (550, 400))
	# 	]

	def button_function(self, button):
		'''[Template] A function triggered by a controller button'''
		pass
		
	def adjust_power(self, x):
		self.pow_mult += x