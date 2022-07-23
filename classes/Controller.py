import pygame
import numpy as np

'''
Button order: A, B, X, Y, LB, RB, LS, RS, Back, Guide, Start
D-Pad order: L, R, D, U
Axes order: L-Vert, L-Hor, R-Vert, R-Hor, LT, RT
'''

class Controller:
	'''
	Controller class dealing with inputs, displaying current state and sending data to rover
	'''
	def __init__(self, cont_index):
		self.index = cont_index
		self.joystick = pygame.joystick.Joystick(self.index)
		self.joystick.init()
		self.name = self.joystick.get_name()

		self.buttons = [False] * 11
		self.dpad = [False] * 4
		self.axes = [0.0, 0.0, 0.0, 0.0, -1.0, -1.0]

	def dpad_val_to_list(self, hat):
		'''Converts a dpad value (tuple of two ints) to list of bools'''
		dpad_state = [False] * 4
		if hat[0]:  # Left-Right
			if hat[0] == -1:
				dpad_state = [True, False] + dpad_state[2:]
			else:
				dpad_state = [False, True] + dpad_state[2:]
		else:
			dpad_state = [False, False] + dpad_state[2:]

		if hat[1]:  # Up-Down
			if hat[1] == -1:
				dpad_state = dpad_state[:2] + [True, False]
			else:
				dpad_state = dpad_state[:2] + [False, True]
		else:
			dpad_state = dpad_state[:2] + [False, False]

		return dpad_state

	def get_state(self):
		'''Get the current state of the controller inputs and store in the object'''
		# Buttons
		self.buttons = [bool(self.joystick.get_button(i)) for i in range(11)]
	
		# D-pad
		hat = self.joystick.get_hat(0)
		self.dpad = self.dpad_val_to_list(hat)
	
		# Axes
		for obj_index, joystick_index in enumerate([0, 1, 3, 4, 2, 5]):
			if joystick_index in [1, 4]:  # Invert vertical axes
				self.axes[obj_index] = (-self.joystick.get_axis(joystick_index) + 1) / 2
			else:
				self.axes[obj_index] = (self.joystick.get_axis(joystick_index) + 1) / 2
	
	def draw_bar(self, axis, screen, coord, dim=(30, 80)):
		'''Draw a bar for a specific axis'''
		# Border
		pygame.draw.rect(screen, (255, 255, 255), coord + dim, 1)

		# Bar
		bar_height = 1 + (dim[1] - 3) * self.axes[axis]
		pygame.draw.rect(screen, (255, 255, 255),
			(
				coord[0] + 2,
				coord[1] + dim[1] - bar_height,
				dim[0] - 4,
				(dim[1] - 3) * self.axes[axis]
			)
		)

	def draw_bars_list(self, axes, screen, start_coord, dim=(30, 80)):
		'''Draw a set of bars for a list of axes'''
		# Loop through each axis in the input list
		for i, axis in enumerate(axes):
			x = start_coord[0] + (dim[0] + 5) * i
			self.draw_bar(axis, screen, (x, start_coord[1]), dim)

	def draw_joystick(self, joy, screen, coord, radius=80):
		'''Draw a circle for a specified joystick (0 = Left Joy, 1 = Right Joy)'''
		# Border circle
		pygame.draw.circle(
			screen,
			(255, 255, 255),
			(coord[0] + radius, coord[1] + radius),
			radius,
			1
		)

		# Inner circle
		joy_pos = (
			radius * (self.axes[2 * joy] * 1.8 - 0.9),
			radius * -(self.axes[2 * joy + 1] * 1.8 - 0.9)
		)
		pygame.draw.circle(
			screen,
			(255, 255, 255),
			(coord[0] + radius + joy_pos[0], coord[1] + radius + joy_pos[1]),
			radius // 3
		)

	def draw_button_circle(self, button, screen, coord, radius=10):
		'''Draw a circle for a specific button'''
		# Border
		pygame.draw.circle(screen, (255, 255, 255),	coord, radius, 1)

		# Fill
		if self.buttons[button]:
			pygame.draw.circle(screen, (255, 255, 255), coord, radius - 2)

	def draw_dpad(self, screen, coord, size=80):
		'''Draw the current dpad state'''
		# Coordinates for the dpad-shape
		DPAD_SHAPE = [
			np.array([[0.0, 0.0], [-0.25, 0.25], [-1.0, 0.25], [-1.0, -0.25], [-0.25, -0.25]]),
			np.array([[0, 0], [0.25, -0.25], [1, -0.25], [1, 0.25], [0.25, 0.25]]),
			np.array([[0, 0], [0.25, 0.25], [0.25, 1], [-0.25, 1], [-0.25, 0.25]]),
			np.array([[0.0, 0.0], [-0.25, -0.25], [-0.25, -1.0], [0.25, -1.0], [0.25, -0.25]])
		] # LEFT, RIGHT, BOTTOM, TOP (same order as self.dpad)

		# Transform the lists of points then draw polygons
		c = np.array([coord])
		s = size / 2

		for i in range(4):
			points = (s * DPAD_SHAPE[i] + c).tolist()

			# If dpad button being pressed, fill polygon
			if self.dpad[i]:
				pygame.draw.polygon(screen, (255, 255, 255), points)
			else:
				pygame.draw.polygon(screen, (255, 255, 255), points, 1)

	def draw_state(self, screen, max_height):
		'''Draw the full current state of the controller'''
		self.draw_dpad(screen, (70, max_height - 55))
		self.draw_joystick(0, screen, (120, max_height - 95), 40)
		self.draw_joystick(1, screen, (210, max_height - 95), 40)
		self.draw_bars_list([4, 5], screen, (300, max_height - 95), (30, 80))
		for i in range(11):
			self.draw_button_circle(i, screen, (
				385 + 25 * (i % 4), 
				max_height - 80 + 25 * (i // 4)
			))