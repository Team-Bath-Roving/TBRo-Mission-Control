'''Config'''
# Directory of image files
IMG_DIR = "img/"

# Network information
ROVER_IP = "localhost"

# Camera information
CAM_NAMES = ["Cam 1", "Cam 2"]
# CAM_RES = [(1080, 1920, 3), (1080, 1920, 3)]

# ========================================================

# Import modules
from base64 import encode
import pygame
import datetime
import marstime
import struct
import socket
import json
import threading
import queue

from classes.FeedManager import FeedManager
# from classes.CameraFeed import CameraFeed
from classes.Controller import Controller
from classes.ActionHandler import ActionHandler
from classes.Sockets import SocketTimeout, SendSocket, ReceiveSocket

# Listening for rover signals
def listen_function(fb_queue, img_queue):
	PAYLOAD_STRING = "<H" + "I" * len(CAM_NAMES)
	PAYLOAD_SIZE = struct.calcsize(PAYLOAD_STRING)

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as recvsock:

		s = ReceiveSocket(recvsock, 5002)
		overflow = b""

		while True:
			try:
				# Unpack the size of the encoded feedback and images
				encoded_sizes, overflow = s.recv_data(PAYLOAD_SIZE, overflow)
				sizes = struct.unpack(PAYLOAD_STRING, encoded_sizes)

				# Receive and decode feedback, then queue if not empty
				encoded_feedback, overflow = s.recv_data(sizes[0], overflow)
				fb = json.loads(encoded_feedback.decode())
				if fb: fb_queue.put(fb)

				# Receive encoded image frames
				for size in sizes[1:]:
					encoded_img, overflow = s.recv_data(size, overflow)
					img_queue.put(encoded_img)

			except SocketTimeout:
				print("Socket timed out, reconnecting...")
				s.accept()

# Pygame function
def pygame_function(fb_queue, img_queue):

	# Set up send socket
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sendsock:

		s = SendSocket(sendsock, ROVER_IP, 5001)
		
		# Wait until rover is connected
		while True:
			if not fb_queue.empty():
				fb = fb_queue.get()
				if fb["Connected"]:
					break
		
		s.connect()

		# ======
		
		# Initialise pygame
		pygame.init()

		# Create screen, set dimensions, set caption
		WIDTH, HEIGHT = 1200, 785
		# WIDTH, HEIGHT = 1440, 845
		screen = pygame.display.set_mode((WIDTH, HEIGHT + 15), pygame.RESIZABLE)
		pygame.display.set_caption("TBRo Mission Control")

		# Define colour white (commonly used)
		WHITE = (255, 255, 255)

		# Loop until user end the program
		done = False

		# Clock controls how often the screen updates
		clock = pygame.time.Clock()

		# Create instance of FeedManager and set up CameraFeeds 
		fm = FeedManager(screen, ["External Webcam", "Built-in Webcam"])

		# List of feedback received from rover
		fb_list = []

		# Encoded frames received from rover
		encoded_frames = [False, False]

		# List of connected controllers
		controllers = []
		cont_index = 0

		# Setting up images
		spacesoc_img = pygame.transform.smoothscale(pygame.image.load(IMG_DIR + "spacesoc.png"), (64, 64))
		olympus_img = pygame.transform.smoothscale(pygame.image.load(IMG_DIR + "olympus.png"), (57, 64))

		# Create ActionHandler object
		ah = ActionHandler(s, fm)

		while not done:
			# Handling events
			for event in pygame.event.get():
				# Resizing window
				if event.type == pygame.VIDEORESIZE:
					screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
					WIDTH, HEIGHT = event.w, event.h

				# Exiting with Escape
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
					done = True

				# Reset controllers
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
					controllers = []
					
				# Closing window
				elif event.type == pygame.QUIT:
					done = True

				# [Temp] sStop "rover" python script
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
					s.send_msg("QUIT_ROVER")

				# Handling keyboard/ controller button presses
				else:
					# Keyboard
					if event.type == pygame.KEYDOWN:
						ah.button_press(event.key)

					# Controller (button)
					elif event.type == pygame.JOYBUTTONDOWN and event.joy == cont_index:
						ah.button_press(event.button)

					# # Controller (dpad) --- DPAD buttons will be held down to pan/ tilt camera
					# elif event.type == pygame.JOYHATMOTION and event.joy == cont_index:
					# 	dirs = ["L", "R", "D", "U"]
					# 	for i, x in enumerate(controllers[cont_index].dpad_val_to_list(event.value)):
					# 		if x: ah.button_press(f"DPAD_{dirs[i]}")

			# Clear screen to black
			screen.fill((0, 0, 0))

			# Border lines
			pygame.draw.line(screen, WHITE, (10, 70), (WIDTH - 10, 70))
			pygame.draw.line(screen, WHITE, (60, 70), (60, HEIGHT - 125))
			pygame.draw.line(screen, WHITE, (10, HEIGHT - 125), (WIDTH - 10, HEIGHT - 125))
			pygame.draw.line(screen, WHITE, (530, HEIGHT - 125), (530, HEIGHT - 10))

			# Corner images
			screen.blit(spacesoc_img, (10, 3))
			screen.blit(olympus_img, (WIDTH - 67, 3))

			# Set up for date & mars date/ time in header
			d = datetime.datetime

			mtc = marstime.Coordinated_Mars_Time() # Coordinated Mars Time
			mars_h = mtc
			mars_m = (mtc * 60) % 60
			if mars_m >= 59.5: mars_m = 0
			mars_s = (mtc * 3600) % 60
			if mars_s >= 59.5: mars_s = 0
			mtc_f = f"{mars_h:02.0f}:{mars_m:02.0f}:{mars_s:02.0f}" # MTC Formatted

			# Set up for header text positioning
			m_w = (WIDTH - 180) * 13 / 102 # module width
			if m_w < 130: m_w = 130
			g_w = m_w * 24 / 65 # gap width
			
			div1 = 90 + 3 * m_w + 2.5 * g_w
			div2 = div1 + 2 * (m_w + g_w)
			pygame.draw.line(screen, WHITE, (div1, 10), (div1, 70))
			pygame.draw.line(screen, WHITE, (div2, 10), (div2, 70))

			# Write header text
			for i, (top, bottom) in enumerate([
				["Earth Date", f"{d.now().strftime('%Y-%m-%d')}"],
				["Local (BST)", f"{d.now().strftime('%H:%M:%S')}"],
				["UTC", f"{d.utcnow().strftime('%H:%M:%S')}"],
				["Mars Sol Date", f"{marstime.Mars_Solar_Date():.2f}"],
				["Mars Time", f"{mtc_f}"],
				["Mission Timer", f"00:00"]
			]):
				x = 90 + i * (m_w + g_w)
				top_rect = pygame.Rect(x, 18, m_w, 16)
				top_text = pygame.font.SysFont("monospace", 16).render(top, True, WHITE)
				ttr = top_text.get_rect()
				ttr.center = top_rect.center
				screen.blit(top_text, ttr)

				bottom_rect = pygame.Rect(x, 34, m_w, 22)
				bottom_text = pygame.font.SysFont("monospace", 22).render(bottom, True, WHITE)
				btr = bottom_text.get_rect()
				btr.center = bottom_rect.center
				screen.blit(bottom_text, btr)

			# Set up controllers
			num_conts = pygame.joystick.get_count()
			if num_conts != len(controllers):
				controllers = [Controller(i) for i in range(num_conts)]
				cont_index = 0

			# Display controller state
			if len(controllers) == 0:
				# Handle no controllers connected
				text = pygame.font.SysFont("monospace", 16).render("No controllers connected", True, WHITE)
				screen.blit(text, (20, HEIGHT - 120))
				ah.set_controller(None)

			else:
				# Set controller in ActionHandler object
				ah.set_controller(controllers[cont_index])

				# Display text
				text = pygame.font.SysFont("monospace", 16).render(f"Controller: {cont_index}, {controllers[cont_index].name}", True, WHITE)
				screen.blit(text, (20, HEIGHT - 120))

				# Store current controller state
				controllers[cont_index].get_state()

				# Draw current state on screen
				controllers[cont_index].draw_state(screen, HEIGHT)

				# Send controller state to rover
				ah.send_commands()

				# BUMPERS
				s = ""
				s += "SCOOP UP  " if (controllers[cont_index].buttons[4]) else "SCOOP DOWN"
				s += " | "
				s += "BRUSH OUT" if (controllers[cont_index].buttons[5]) else "BRUSH IN"
				text = pygame.font.SysFont("monospace", 20).render(s, True, WHITE)
				screen.blit(text, (540, HEIGHT - 115))

				# POWER
				s = f"Power Mult: {ah.pow_mult:.2f}"
				text = pygame.font.SysFont("monospace", 20).render(s, True, WHITE)
				screen.blit(text, (540, HEIGHT - 91))

			# Displaying rover feedback 830
			while not fb_queue.empty():
				fb_list.append(fb_queue.get())
			if len(fb_list) > 6:
				fb_list = fb_list[-6:]

			for i, fb in enumerate(fb_list[::-1]):
				text = pygame.font.SysFont("monospace", 16).render(str(fb), True, WHITE)
				screen.blit(text, (830, HEIGHT - 115 + i * 18))

			# Displaying camera feeds
			if img_queue.full():
				encoded_frames = [img_queue.get(), img_queue.get()]	
			
			fm.display_feeds(*encoded_frames)

			# [Temp] Show mouse coords
			s = f"{pygame.mouse.get_pos()}"
			text = pygame.font.SysFont("monospace", 14).render(s, True, (0, 255, 0))
			screen.blit(text, (WIDTH - 170, 5))

			# Update the screen
			pygame.display.flip()

			# Limit to 60 frames per second
			clock.tick(30)

		# fm.release_feeds()
		pygame.quit()
		# raise SystemExit


# Running the program
if __name__ == "__main__":
	fb_queue = queue.Queue(0)
	img_queue = queue.Queue(len(CAM_NAMES))

	thread = threading.Thread(target=listen_function, daemon=True, args=(fb_queue,img_queue,))
	thread.start()

	pygame_function(fb_queue, img_queue)