import numpy as np
import cv2
import pygame

class FeedManager:
	'''
	Manages all the camera feeds (refreshing, positioning, etc)
	'''
	def __init__(self, screen, names):
		self.mode = 0
		self.order = 0
		self.screen = screen
		self.names = names
		self.frame1 = None
		self.frame2 = None

	def swap_feeds(self):
		'''Swaps the positions and dimensions of the two feeds'''
		# Iterate mode number
		self.order += 1

		# Loop back over if required
		if self.order > 1: self.order = 0

		# Swap names (what about more cameras?)
		self.names = self.names[::-1]
	
	def cycle_mode(self):
		# Iterate mode number
		self.mode += 1

		# Loop back over if required
		if self.mode > 1: self.mode = 0

	def decode_frame(self, encoded_data, ratio=16/9):
		'''Decodes bytes into a numpy array representing a frame'''
		# If there is no data, return False
		if not encoded_data: return False

		flat_frame = np.frombuffer(encoded_data, dtype="uint8")

		BPP = 1 # bytes per pixel (3 for RGB, 1 for greyscale (or other compression))

		j = ratio # 16/9 # known ratio of width/height
		k = flat_frame.shape[0] // BPP

		w = int(np.sqrt(k * j)) # here we do some maths to work out width and height
		h = k // w

		frame = flat_frame.reshape(h, w, BPP)

		return frame

	def prepare_frame(self, frame, des_dim):
		'''Transform and scale the frame to the desired size'''
		# Invert, rotate and correctly colour
		frame = cv2.cvtColor(np.rot90(np.fliplr(frame)), cv2.COLOR_GRAY2RGB)

		# Calculate required scale factor
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

	def display_frame(self, screen, frame, name, coords, dim):
		'''Display an individual frame on the screen'''
		# Define font
		font = pygame.font.SysFont("monospace", 16)

		# Draw border rectangle
		border_rect = pygame.Rect(
			coords[0],
			coords[1],
			dim[0],
			dim[1]
		)
		pygame.draw.rect(screen, (255, 255, 255), border_rect, 2)

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
			screen.blit(surf, surf_rect)
			
		else:
			# Otherwise, say that is isn't
			text = font.render("[Feed unavailable]", True, (255, 255, 255))
			text_rect = text.get_rect()
			text_rect.center = frame_rect.center
			screen.blit(text, text_rect)

		# Show feed name below image, making sure it is centred
		text = font.render(f"{name}", True, (255, 255, 255))
		text_rect = text.get_rect(
			center=(
				coords[0] + dim[0] / 2,
				coords[1] + dim[1] - 15
			)
		)
		screen.blit(text, text_rect)

	def display_feeds(self, data1, data2, decode=True):
		'''Decode, display and format all feeds'''

		if decode:
			# Decode the data into frames and assign depending on order
			if self.order == 0:
				self.frame1 = self.decode_frame(data1)
				self.frame2 = self.decode_frame(data2)
			else:
				self.frame1 = self.decode_frame(data2)
				self.frame2 = self.decode_frame(data1)
			
		# Display each frame depending on the mode
		if self.mode == 0:
			# Side-by-side
			self.display_frame(self.screen, self.frame1, self.names[0], (80, 90), (550, 400))
			self.display_frame(self.screen, self.frame2, self.names[1], (628, 90), (550, 400))

		elif self.mode == 1:
			# Enlarged
			self.display_frame(self.screen, self.frame1, self.names[0], (80, 90), (850, 550))
			self.display_frame(self.screen, self.frame2, self.names[1], (928, 90), (250, 200))