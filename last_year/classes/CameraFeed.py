import pygame
import cv2
import numpy as np

class CameraFeed:
	'''
	Class controlling a camera feed
	'''
	def __init__(self, name, url, coords, dim=None):
		self.name = name
		self.url = url
		self.coords = coords
		self.dim = dim # Desired dimensions

		self.ready = self.set_up_feed()
		self.on = True

	def set_up_feed(self):
		'''Set up the cv2 capture object'''
		if self.url == None: return False

		self.capture = cv2.VideoCapture(self.url)
		self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 0)
		return not self.capture is None and self.capture.isOpened()  # Return False is the feed isn't present

	def prepare_frame(self):
		'''Transform and scale the frame to the desired size'''
		# Get camera frame
		ret, frame = self.capture.read()

		if ret and self.on:
			# Invert, rotate and correctly colour
			frame = cv2.cvtColor(np.rot90(np.fliplr(frame)), cv2.COLOR_BGR2RGB)

			# Calculate required scale factor
			dim = frame.shape
			sf = min([
				(self.dim[0] - 16) / dim[0],
				(self.dim[1] - 38) / dim[1]
			])

			# Scale frame
			frame = cv2.resize(frame, (
				int(frame.shape[1] * sf), 
				int(frame.shape[0] * sf)
			))

			# Return the prepared frame
			return True, frame

		else:
			# If is unavailable or turned off, do not try to send a frame
			return False, False

	def display_feed(self, screen):
		'''Display the camera image in the screen'''
		# Define font
		font = pygame.font.SysFont("monospace", 16)

		# Check feed is ready and get frame
		if self.ready:
			ret, frame = self.prepare_frame()
		else:
			ret = False

		# Draw border rectangle
		border_rect = pygame.Rect(
			self.coords[0],
			self.coords[1],
			self.dim[0],
			self.dim[1]
		)
		pygame.draw.rect(screen, (255, 255, 255), border_rect, 2)

		# Get desired frame dimensions (used for centering things)
		frame_rect = pygame.Rect(
			self.coords[0] + 8,
			self.coords[1] + 8,
			self.dim[0] - 16,
			self.dim[1] - 38
		)

		# If frame is available, display it 
		if ret:
			surf = pygame.surfarray.make_surface(frame)
			surf_rect = surf.get_rect()
			surf_rect.center = frame_rect.center
			screen.blit(surf, surf_rect)
			
		else:
			# Otherwise, show reason it isn't
			if self.on:
				text = font.render("[Feed unavailable]", True, (255, 255, 255))
			else:
				text = font.render("[Feed disabled]", True, (255, 255, 255))
			
			text_rect = text.get_rect()
			text_rect.center = frame_rect.center
			screen.blit(text, text_rect)

		# Show feed name below image, making sure it is centred
		text = font.render(f"{self.name}", True, (255, 255, 255))
		text_rect = text.get_rect(
			center=(
				self.coords[0] + self.dim[0] / 2,
				self.coords[1] + self.dim[1] - 15
			)
		)
		screen.blit(text, text_rect)
	
	def toggle_feed(self):
		'''Toggle the camera image on/ off'''
		self.on = not self.on
		return self.on

	def release(self):
		'''Quits the capture when app is closed'''
		return self.url is None or self.capture.release() # If url is None, don't need to release