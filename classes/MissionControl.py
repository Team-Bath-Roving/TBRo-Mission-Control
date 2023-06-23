# Import libraries
import pygame

# Import classes
from .FeedManager import FeedManager
from .ActionHandler import ActionHandler
from .MissionControl import MissionControl
from .Gamepad import GamepadManager, Gamepad
from .Sockets import SocketTimeout, ControlSend, FeedbackReceive, CameraReceive

WHITE = (255, 255, 255) # We use white a lot so we define it seperately

class MissionControl():
	'''Class for managing the pygame window'''
	
	def __init__(self, WIDTH, HEIGHT):
		pygame.init()

		self.WIDTH = WIDTH
		self.HEIGHT = HEIGHT
		self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT + 15))
		pygame.display.set_caption("TBRo Mission Control")
		self.clock = pygame.time.Clock()

		self.conn_status = False # Whether ControlSend socket is connected

	def write_text(self, s, coords, size=16, col=(255, 255, 255)):
		"""
		Function for writing text directly onto the pygame screen

		Parameters
		----------
		s : str
			Text to write
		coords : list[int]
			x, y coordinates for where to write text
		size : int
			Font size
		col : list[int]
			Font colour
		"""
		text = pygame.font.SysFont("monospace", size).render(f"{s}", True, col)
		self.screen.blit(text, coords)

	def set_up_window(self):
		"""Draw the initial features of the pygame screen (eg borders)"""
		# pygame.draw.line(self.screen, WHITE, (150, 10), (150, self.HEIGHT - 125))
		# pygame.draw.line(self.screen, WHITE, (10, self.HEIGHT - 125), (self.WIDTH - 10, self.HEIGHT - 125))
		# pygame.draw.line(self.screen, WHITE, (530, self.HEIGHT - 125), (530, self.HEIGHT + 5))
		# pygame.draw.line(self.screen, WHITE, (self.WIDTH - 60, self.HEIGHT - 125), (self.WIDTH - 60, self.HEIGHT + 5))

	def write_status(self, conn):
		"""If the connection status has changed, updates text in corner of window to reflect that"""
		if conn != self.conn_status:
			if conn:
				self.write_text("Connection lost", (self.WIDTH - 200, self.HEIGHT - 20))
			else:
				self.screen.fill((0, 0, 0), (self.WIDTH - 200, self.HEIGHT - 20, self.WIDTH, self.HEIGHT))

			self.conn_status = conn

	def update_display(self):
		pygame.display.flip()
		self.clock.tick(30)