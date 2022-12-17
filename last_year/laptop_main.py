'''Config'''
# Directory of image files
IMG_DIR = "img/"

# Network information
ROVER_IP = "localhost" # "192.168.0.50"
SEND_PORT = 5000
RECEIVE_PORT = 9850
SIZE = 4096 # not used below

# ========================================================

# Import modules
from base64 import encode
import pygame
import datetime
import marstime
import struct
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from multiprocessing import Queue, Process

from classes.FeedManager import FeedManager
# from classes.CameraFeed import CameraFeed
from classes.Controller import Controller
from classes.ActionHandler import ActionHandler

# Listening for rover signals
def listen_function(q):

	# Set up socket for receiving
	receive_socket = socket(AF_INET, SOCK_STREAM)
	receive_socket.bind(("", RECEIVE_PORT))
	receive_socket.listen(10)

	conn, _ = receive_socket.accept()

	data = b"" 
	
	# Set payload size to match client
	payload_size = struct.calcsize("<II")

	while True:
		while len(data) < payload_size:
			data += conn.recv(4096)

		# Get the expected message size from received data
		msg_sizes = struct.unpack("<II", data[:payload_size])
		msg_size1 = msg_sizes[0]
		msg_size2 = msg_sizes[1]

		# Exclude the msg_size from data
		data = data[payload_size:]

		# Retrieve all the data now that we know message size
		while len(data) < msg_size1 + msg_size2:
			data += conn.recv(4096)

		# Exclude any additional bytes at the end of the binary string
		encoded_data1 = data[:msg_size1]
		encoded_data2 = data[msg_size1:msg_size1 + msg_size2]

		q.put(encoded_data1)
		q.put(encoded_data2)

		# Exclude the encoded data, taking anything extra forward to the next iteration
		data = data[msg_size1 + msg_size2:]

# Pygame function
def pygame_function(q):

	# Set up socket for sending
	send_socket = socket(AF_INET, SOCK_DGRAM)
	send_socket.connect((ROVER_IP, SEND_PORT))
	
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

	# Encoded frames received from rover
	encoded_frames = [False, False]

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
			text = pygame.font.SysFont("monospace", 24).render(s, True, WHITE)
			screen.blit(text, (560, HEIGHT - 85))

			# POWER
			s = f"Power Mult: {ah.pow_mult:.2f}"
			text = pygame.font.SysFont("monospace", 24).render(s, True, WHITE)
			screen.blit(text, (560, HEIGHT - 57))

		# Displaying rover feedback
		if q.full():
			encoded_frames = [q.get(), q.get()]
			
		# Displaying camera feeds
		fm.display_feeds(*encoded_frames)

		# Update the screen
		pygame.display.flip()

		# Limit to 60 frames per second
		clock.tick(30)

	# fm.release_feeds()
	pygame.quit()
	raise SystemExit


# Running the program
if __name__ == "__main__":
	q = Queue(2)

	proc = Process(target=listen_function, daemon=True, args=(q,))
	proc.start()

	pygame_function(q)