# Import libraries
import cv2
import pygame
import numpy as np

class FeedManager():
	"""
	Class for managing incoming all incoming images from the rover
	"""
	def __init__(self, mc, names:"list[str]", img_queues:dict):
		"""
		Parameters
		----------
		mc : MissionControl
			The MissionControl object that handles the pygame window
		names : list[str]
			List of camera names
		img_queues : dict
			Dictionary of with keys as camera names and values as queues
		"""
		self.mc = mc
		self.names = names
		self.queues = img_queues

		self.view = 0 # Viewing mode
		self.enlarged = 0 # In view 1, which camera is enlarged

	def get_images(self):
		"""Retrieves images from the queue"""
		for name, queue in self.queues.items():
			if queue.full():
				self.update_image(name, queue.get())

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

	def display_frame(self, frame:np.ndarray, name:str, coords:"tuple[int]", dim:"tuple[int]"):
		"""Display an individual frame on the screen"""
		# Define font
		font = pygame.font.SysFont("monospace", 16)

		# Draw border rectangle
		border_rect = pygame.Rect(
			coords[0],
			coords[1],
			dim[0],
			dim[1]
		)
		pygame.draw.rect(self.mc.screen, (255, 255, 255), border_rect, 2)

		# Get desired frame dimensions (used for centering things)
		frame_rect = pygame.Rect(
			coords[0] + 8,
			coords[1] + 8,
			dim[0] - 16,
			dim[1] - 38
		)

		# If frame is available, display it 
		if type(frame) == np.ndarray:
			prepared_frame = self.prepare_frame(frame, dim)
			surf = pygame.surfarray.make_surface(prepared_frame)
			surf_rect = surf.get_rect()
			surf_rect.center = frame_rect.center
			self.mc.screen.blit(surf, surf_rect)
			
		else:
			# Otherwise, say that is isn't
			text = font.render("[Feed unavailable]", True, (255, 255, 255))
			text_rect = text.get_rect()
			text_rect.center = frame_rect.center
			self.mc.screen.blit(text, text_rect)

		# Show feed name below image, making sure it is centred
		text = font.render(name, True, (255, 255, 255))
		text_rect = text.get_rect(
			center=(
				coords[0] + dim[0] / 2,
				coords[1] + dim[1] - 15
			)
		)
		self.mc.screen.blit(text, text_rect)

	def update_image(self, name:str, image:np.ndarray):
		"""Updates image in pygame window"""
		if self.view == 0:
			# Grid of videos
			coords = [(20, 20), (530, 20), (20, 370), (530, 370)]
			size = (500, 340)
			for i, x in enumerate(self.names):
				if name == x:
					self.display_frame(image, x, coords[i], size)

		elif self.view == 1:
			# Enlarged view
			coords_big = (20, 20)
			size_big = (750, 520)
			coords_sml = [(780, 20), (780, 230)]
			size_sml = (260, 200)
			for i, x in enumerate(self.names):
				if name == x:
					if i == self.enlarged:
						self.display_frame(image, x, coords_big, size_big)
					elif i > self.enlarged:
						self.display_frame(image, x, coords_sml[i-1], size_sml)
					else:
						self.display_frame(image, x, coords_sml[i], size_sml)

