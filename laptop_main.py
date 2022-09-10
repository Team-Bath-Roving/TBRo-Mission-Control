'''Config'''
# URLs of video feeds 
URLS = [
	["Webcam", 0],
	["Phone (via IP)", None] # "http://192.168.77.163:4747/video"
]

# Directory of image files
IMG_DIR = "TBRo-Mission-Control/img/"

# Network information
ROVER_IP = "192.168.0.25"
SEND_PORT = 5000
RECEIVE_PORT = 5001
SIZE = 1024

# ========================================================

# Import modules
import pygame
import datetime
import marstime
import json
from socket import socket, AF_INET, SOCK_DGRAM
from multiprocessing import Queue, Process

from classes.FeedManager import FeedManager
from classes.CameraFeed import CameraFeed
from classes.Controller import Controller
from classes.ActionHandler import ActionHandler

# Listening for rover signals
def listen_function(q):

	# Set up socket for receiving
	receive_socket = socket(AF_INET, SOCK_DGRAM)
	receive_socket.bind(("", RECEIVE_PORT))
	
	while True:
		data, _ = receive_socket.recvfrom(1024)
		data = data.decode()

		print(f"{data}")
		q.put(data)

# Pygame function
def pygame_function(q):

	# Set up socket for sending
	send_socket = socket(AF_INET, SOCK_DGRAM)
	send_socket.connect((ROVER_IP, SEND_PORT))

	# List of commands received from rover
	received_commands = []
	
	# Initialise pygame
	pygame.init()

	# Create screen, set dimensions, set caption
	WIDTH, HEIGHT = 1200, 785
	screen = pygame.display.set_mode((WIDTH, HEIGHT + 15), pygame.RESIZABLE)
	pygame.display.set_caption("TBRo Mission Control")

	# Define colour white (commonly used)
	WHITE = (255, 255, 255)

	# Loop until user end the program
	done = False

	# Clock controls how often the screen updates
	clock = pygame.time.Clock()

	# Create instance of FeedManager and set up CameraFeeds 
	fm = FeedManager()

	fm.add_feed(CameraFeed(*URLS[0], (80, 90), (550, 400)))
	fm.add_feed(CameraFeed(*URLS[1], (628, 90), (550, 400)))

	# List of connected controllers
	controllers = []
	cont_index = 0

	# Setting up images
	spacesoc_img = pygame.transform.smoothscale(pygame.image.load(IMG_DIR + "spacesoc.png"), (64, 64))
	olympus_img = pygame.transform.smoothscale(pygame.image.load(IMG_DIR + "olympus.png"), (57, 64))

	# Create ActionHandler object
	ah = ActionHandler(send_socket, fm)

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
				send_socket.sendall("QUIT_ROVER".encode())

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
		pygame.draw.line(screen, WHITE, (60, 70), (60, 660))
		pygame.draw.line(screen, WHITE, (10, 660), (WIDTH - 10, 660))
		pygame.draw.line(screen, WHITE, (530, 660), (530, HEIGHT - 10))

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

		# Displaying camera feeds
		fm.display_feeds(screen)

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

		# Displaying rover feedback
		while not q.empty():
			received_commands.append(q.get())
			if len(received_commands) > 7:
				received_commands.pop(0)

		for i, cmd in enumerate(received_commands[::-1]):
			text = pygame.font.SysFont("monospace", 16).render(cmd, True, WHITE)
			screen.blit(text, (550, 670 + i * 18))

		# Update the screen
		pygame.display.flip()

		# Limit to 60 frames per second
		clock.tick(30)

	fm.release_feeds()
	pygame.quit()
	raise SystemExit


# Running the program
if __name__ == "__main__":
	q = Queue()

	proc = Process(target=listen_function, daemon=True, args=(q,))
	proc.start()

	pygame_function(q)