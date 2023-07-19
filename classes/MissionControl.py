# Import libraries
import numpy as np
import pygame
import time
import cv2

WHITE = (255, 255, 255) # We use white a lot so we define it seperately

class MissionControl():
	'''Class for managing the pygame window'''
	
	def __init__(self, WIDTH, HEIGHT, CAM_NAMES):
		pygame.init()

		self.WIDTH = WIDTH
		self.HEIGHT = HEIGHT
		self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
		pygame.display.set_caption("TBRo Mission Control")
		self.clock = pygame.time.Clock()
		self.CAMS = dict([(name, i) for i, name in enumerate(CAM_NAMES)])

		self.map_info = {
			"current": np.array([0, 0]),
			"heading": 0,
			"trail": [np.array([0, 0])],
			"shift": np.array([0, 0]),
			"zoom": 1
		}
		self.scoop_info = {} # format?
		self.telemetry_info = {
			"speed": 0,
			"elevation": 0,
			"pitch": 0, # All in radians
			"roll": 0,
			"heading": 0
		}
		self.system_info = {
			"timeractive": False,
			"timerend": 0,
			"battery": 100,
			"voltage": 10,
			"current": 10,
			"conn": False
		}
		self.actions_info = {
			"state": [0] * 16,
			"labels": [""] * 16,
			"bboxes": [[0,0,0,0]] * 16
		}

	def get_width_vu(self):
		"""Useful function for getting these values. Called in `handle_feedback` in ActionHandler"""
		return self.WIDTH, self.vu

	def update_display(self):
		"""Runs the `pygame.display.flip()` function to show the update to the pygame window"""
		pygame.display.flip()
		self.clock.tick(30)

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

	def draw_line(self, start, end, colour=WHITE):
		"""Draws line between two coordinates"""
		pygame.draw.line(self.screen, colour, start, end)

	def draw_borders(self):
		self.vu = self.HEIGHT // 6 # Vertical unit (building block for organising the screen)
		self.div = self.WIDTH - 4 * self.vu # Vertical self.dividing line (value is used a lot)

		self.draw_line((self.div, 10), (self.div, self.HEIGHT - 10))
		self.draw_line((10, self.HEIGHT // 2), (self.div, self.HEIGHT // 2))

		self.draw_line((self.div, 2 * self.vu), (self.WIDTH - 10, 2 * self.vu))
		self.draw_line((self.div, 4 * self.vu), (self.div + 2 * self.vu, 4 * self.vu))
		self.draw_line((self.div + 2 * self.vu, 10), (self.div + 2 * self.vu, self.HEIGHT - 10))


		# [Temp]
		self.overhead_map(np.array([self.WIDTH - 2 * self.vu, 2 * self.vu]))
		self.scoop_status(np.array([self.WIDTH - 4 * self.vu, 4 * self.vu]))
		self.telemetry(np.array([self.WIDTH - 4 * self.vu, 2 * self.vu]))
		self.system(np.array([self.WIDTH - 4 * self.vu, 0]))
		self.actions(np.array([self.WIDTH - 2 * self.vu, 0]))


	def overhead_map(self, pos):
		sf = 2 * self.vu # Scale factor
		centre = np.array([sf // 2, sf]) # Relative centre

		# Fill background
		pygame.draw.rect(self.screen, (0, 0, 0), [pos[0]+1, pos[1]+1, sf-2, 2 * sf-2])

		# Draw trail
		for i in range(len(self.map_info["trail"]) - 1):
			current = self.map_info["trail"][::-1][i]
			next = self.map_info["trail"][::-1][i+1]

			# Opacity
			# if i < 10:
			# 	colour = (255, 0, 0, 1 - 0.7 * i/9)
			# else:
			# 	colour = (255, 0, 0, 0.3)

			self.draw_line(
				pos + centre + current * sf / 100 * self.map_info["zoom"],
				pos + centre + next * sf / 100 * self.map_info["zoom"],
				(255, 0, 0)
			)

		# Current position
		pygame.draw.circle(
			self.screen, (255, 0, 0), 
			pos + centre + self.map_info["current"] * sf / 100 * self.map_info["zoom"], 
			2 * sf / 100
		)

		# Centre cross
		self.draw_line(pos + centre + np.array([-5, -5]), pos + centre + np.array([5, 5]))
		self.draw_line(pos + centre + np.array([-5, 5]), pos + centre + np.array([5, -5]))

	def scoop_status(self, pos):
		sf = 2 * self.vu # Scale factor
		origin = pos + np.array([10, 50]) * sf / 100

		top_points = origin + np.array([
			[0, -20], [50, -20], [60, 25] # [temp values]
		]) * sf / 100
		bottom_points = origin + np.array([
			[0, 0], [20, 30], [50, 30]
		]) * sf / 100

		# Fill background
		pygame.draw.rect(self.screen, (0, 0, 0), [pos[0]+1, pos[1]+1, sf-2, sf-2])

		for i in range(2):
			self.draw_line(top_points[i,], top_points[i+1,])
			self.draw_line(bottom_points[i,], bottom_points[i+1,])

	def telemetry(self, pos):
		sf = 2 * self.vu

		# Fill background
		pygame.draw.rect(self.screen, (0, 0, 0), [pos[0]+1, pos[1]+1, sf-2, sf-2])
	
		# Speed and elevation
		self.write_text(f"Speed: {self.telemetry_info['speed']:3} | Elev: {self.telemetry_info['elevation']:2}", pos + np.array([4, 4]) * sf / 100, int(7 * sf / 100))

		# Orientation
		radius = 25 * sf / 100

		# - Green circle and outline
		pygame.draw.circle(self.screen, (20, 190, 20), pos + np.array([50, 55]) * sf / 100, radius)
		pygame.draw.circle(self.screen, WHITE, pos + np.array([50, 55]) * sf / 100, radius, 1)

		# - Heading (left/ right)
		pygame.draw.circle(self.screen, WHITE, pos + np.array([50 + 25 * np.sin(self.telemetry_info["heading"]), 55]) * sf / 100, radius // 6)

		# - Pitch (up/ down)
		pygame.draw.circle(self.screen, WHITE, pos + np.array([50, 55 + 25 * np.sin(self.telemetry_info["pitch"])]) * sf / 100, radius // 5, 2)

		# - Roll (outer circle)
		pygame.draw.circle(self.screen, WHITE, pos + np.array([50, 55]) * sf / 100, 35 * sf / 100, 1)
		pygame.draw.circle(self.screen, WHITE, pos + np.array(
			[50 + 35 * np.sin(self.telemetry_info["roll"]), 55 + 35 * np.cos(self.telemetry_info["roll"])]
		) * sf / 100, radius // 6)

	def system(self, pos):
		sf = 2 * self.vu

		# Fill background
		pygame.draw.rect(self.screen, (0, 0, 0), [pos[0]+1, pos[1]+1, sf-2, sf-2])

		# Clock
		if self.system_info["timeractive"]:
			m, s = divmod(self.system_info["timerend"] - time.time(), 60)
			m, s = int(m), int(s)
			if m < 0: 
				self.system_info["timeractive"] = False
				m, s = 0, 0
		else:
			m, s = 0, 0
		self.write_text(f"{m:0>{2}}:{s:0>{2}}", pos + np.array([8, 4]) * sf / 100, int(26 * sf / 100))

		# Battery
		self.write_text(f"  Speed: {self.system_info['battery']:3}%", pos + np.array([6, 22 + 8]) * sf / 100, int(7 * sf / 100))
		self.write_text(f"Voltage: {self.system_info['voltage']:3}V", pos + np.array([6, 22 + 2 * 8]) * sf / 100, int(7 * sf / 100))
		self.write_text(f"Current: {self.system_info['current']:3}A", pos + np.array([6, 22 + 3 * 8]) * sf / 100, int(7 * sf / 100))
		self.write_text(f"Connected: {self.system_info['conn']}", pos + np.array([6, 22 + 5 * 8]) * sf / 100, int(7 * sf / 100))

	def actions(self, pos):
		sf = 2 * self.vu

		# Fill background
		pygame.draw.rect(self.screen, (0, 0, 0), [pos[0]+1, pos[1]+1, sf-2, sf-2])

		# Button size
		size = 20 * sf / 100

		# Draw buttons with labels
		for i in range(4):
			for j in range(4):
				index = 4 * j + i

				border = pygame.Rect(
					pos[0] + 15 + (size + 5) * i, 
					pos[1] + 10 + (size + 5) * j, 
					size, size
				)
				pygame.draw.rect(self.screen, WHITE, border, 1)

				font = pygame.font.SysFont("monospace", 16)
				text = font.render(self.actions_info["labels"][index], True, (255, 255, 255))
				text_rect = text.get_rect()
				text_rect.center = border.center
				self.screen.blit(text, text_rect)

				self.actions_info["bboxes"][index] = [pos[0] + 15 + (size + 5) * i, pos[1] + 10 + (size + 5) * j] * 2
				self.actions_info["bboxes"][index][2] += size
				self.actions_info["bboxes"][index][3] += size

	def prepare_frame(self, frame:np.ndarray, des_dim:"tuple[int]"):
		"""Transform and scale the frame to the desired dimensions"""
		# Invert, rotate and correctly colour (by checking if frame has 2 dimensions)
		if frame.ndim == 2:
			frame = cv2.cvtColor(np.rot90(np.fliplr(frame)), cv2.COLOR_GRAY2RGB) # GRAYSCALE
		else:
			frame = cv2.cvtColor(np.rot90(np.fliplr(frame)), cv2.COLOR_BGR2RGB) # RGB

		# Calculate the required scale factor
		cur_dim = frame.shape
		sf = min([
			(des_dim[0] - 16) / cur_dim[0],
			(des_dim[1] - 38) / cur_dim[1]
		])

		# Scale frame
		frame = cv2.resize(frame, (
			int(frame.shape[1] * sf), 
			int(frame.shape[0] * sf)
		))

		# Return the prepared frame
		return frame

	def draw_images(self, name, img):
		i = self.CAMS[name]
		
		bounding_box = pygame.Rect(
				0, i * self.HEIGHT // 2, 
				self.WIDTH - 4 * self.vu, 
				self.HEIGHT // 2
		)

		# If frame is available, display it
		if type(img) == np.ndarray:
			dim = (self.WIDTH - 2 * self.vu, self.HEIGHT // 2)
			prepared_frame = self.prepare_frame(img, dim)
			surf = pygame.surfarray.make_surface(prepared_frame)
			surf_rect = surf.get_rect()
			surf_rect.center = bounding_box.center
			self.screen.blit(surf, surf_rect)
			
		else:
			# Otherwise, say that is isn't
			font = pygame.font.SysFont("monospace", 16)
			text = font.render("[Feed unavailable]", True, (255, 255, 255))
			text_rect = text.get_rect()
			text_rect.center = bounding_box.center
			self.screen.blit(text, text_rect)

	def write_coords(self):
		"""[Temp] Writes current coords of mouse to screen"""
		self.screen.fill((0, 0, 0), (0, 0, 150, 20))
		self.write_text(pygame.mouse.get_pos(), (0, 0))
