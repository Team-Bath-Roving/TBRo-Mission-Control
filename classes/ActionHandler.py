# Import libraries
import json
import pygame
import datetime
from enum import IntEnum

# Import classes
from .FeedManager import FeedManager
from .ActionHandler import ActionHandler
from .MissionControl import MissionControl
from .Gamepad import GamepadManager, Gamepad
from .Sockets import SocketTimeout, ControlSend, FeedbackReceive, CameraReceive

# Button and axis indicies
class Axes(IntEnum):
	L_HOR=0
	L_VER=1
	L_TRIG=2
	R_HOR=3
	R_VER=4
	R_TRIG=5

class Dpad(IntEnum):
	LEFT=0
	RIGHT=1
	DOWN=2
	UP=3

class Buttons(IntEnum):
	A=0
	B=1
	X=2
	Y=3
	LB=4
	RB=5
	LS=6
	RS=7
	BACK=8
	GUIDE=9
	START=10

# Deadzone for axis motion
DEADZONE = 0.1

# Keybinds
TEST_KEYBIND_1 = [pygame.K_f, Buttons.A]
TEST_KEYBIND_2 = [pygame.K_g, Buttons.B]
TEST_KEYBIND_3 = [pygame.K_h, Buttons.X]

# ActionHandler Class
class ActionHandler:
	"""
	Handles button presses, axis movements, etc and sends information to rover
	"""
	def __init__(self, send_socket:ControlSend, mc:MissionControl, fm:FeedManager, gm:GamepadManager):
		"""
		Parameters
		----------
		send_socket : ControlSend
			Socket for sending control messages to rover
		mc : MissionControl
			The MissionControl object that handles the pygame window
		fm : FeedManager
			The FeedManager object that handles displaying video streams
		gm : GamepadManager
			The GamepadManager object that handles all connected gamepads
		"""
		self.sock = send_socket
		self.MissionControl = mc
		self.FeedManager = fm
		self.GamepadManager = gm

	def send_msg(self, msg:dict):
		"""
		Send message (with control instructions) to rover
		
		Parameters
		----------
		msg : dict
			List of commands to be sent to rover
		"""
		# Add current time to dict
		msg["TIME"] = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

		# Run socket method which converts to JSON and sends
		self.sock.send(msg)

	def button_press(self, button, down=True):
		"""All the actions to be carried out after a button is pressed"""
		if button in TEST_KEYBIND_1: # Do something purely client side (i.e. don't send to rover) 
			print(f"Test 1 {'down' if down else 'up'}")
			
		elif button in TEST_KEYBIND_2: # Send to rover, but only when button goes down
			if down: 
				print("Test 2 down")
				return ["TEST BUTTON 2", True]

		elif button in TEST_KEYBIND_3: # Send button up and down to rover
			print(f"Test 3 {'down' if down else 'up'}")
			return ["TEST BUTTON 3", down]

	def axis_motion(self, id:int, axis:int, value:float):
		"""
		Commands to send to rover when an axis is moved
		
		Parameters
		----------
		id : int
			The ID of the controller the motion is from
		axis : int
			The index for the axis which was moved
		value : float
			Value of the axis in its current position
		"""
		# Joystick
		if axis in [Axes.L_HOR, Axes.L_VER, Axes.R_HOR, Axes.R_VER]:
			# Check movement is further than the deadzone
			if abs(value) <= DEADZONE:
				return None
			
			# Measure movement past the deadzone (need to account for positive and negative value)
			value = min([value - DEADZONE, value + DEADZONE], key=abs) / (1 - DEADZONE)
			
			# Forwards/ backwards
			if axis == Axes.L_VER:
				return ["FORWARD", -value] # Note: up on joystick is negative so we invert this
			
			# Turning
			elif axis == Axes.R_HOR:
				return ["TURN", value]

		# Trigger
		elif axis in [Axes.L_TRIG, Axes.R_TRIG]:
			# Convert range from (-1, 1) to (0, 1)
			value = (value + 1) / 2

			# Check movement is further than the deadzone
			if value <= DEADZONE:
				return None
			
			# Measure movement past the deadzone 
			value = (value - DEADZONE) / (1 - DEADZONE)

			# [Test] Left Trigger 
			if axis == Axes.L_TRIG:
				# Invert if left bumper is held
				if self.GamepadManager.get_button_state(id, Buttons.LB):
					value *= -1

				return ["L_TRIG", value]

	def handle_events(self, events, conn=True) -> bool:
		"""
		Handles any pygame event (eg button presses, quitting) and returns whether to quit or not

		Parameters
		----------
		events : list[Event]
			Instance of the list `pygame.event.get()`
		conn : bool
			Whether the send socket is connected or not 
		"""
		done = False
		msg = {}

		for event in events:
			command = None

			# Quitting
			if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
				command = ["QUIT_ROVER", True]
				done = True

			# Keyboard activity
			elif event.type in [pygame.KEYDOWN, pygame.KEYUP]:
				command = self.button_press(event.key, event.type == pygame.KEYDOWN)

			# Controller button activity
			elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP]:
				command = self.button_press(event.button, event.type == pygame.JOYBUTTONDOWN)
			
			# Controller axis movement
			elif event.type == pygame.JOYAXISMOTION:
				command = self.axis_motion(event.joy, event.axis, event.value)

			# Controller connected
			elif event.type == pygame.JOYDEVICEADDED:
				self.GamepadManager.add_gamepad(event.device_index)
				print("Gamepad connected")

			# Controller disconnected
			elif event.type == pygame.JOYDEVICEREMOVED:
				self.GamepadManager.remove_gamepad(event.instance_id)
				print("Gamepad disconnected")


			# If there was a command, append it to msg
			if command: msg[command[0]] = command[1]

		# If connected and msg list isn't empty, send commands
		if conn and msg: self.send_msg(msg)
		return done