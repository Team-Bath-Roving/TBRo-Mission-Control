class FeedManager:
	'''
	Manages all the camera feeds (refreshing, positioning, etc)
	'''
	def __init__(self):
		self.feeds = []
		self.mode = 0

	def add_feed(self, feed):
		'''Adds a CameraFeed object to the list of feeds'''
		# Raise exception if there are already two feeds
		if len(self.feeds) >= 2:
			raise Exception("Tried to add more than two camera feeds - only two currently supported")
		
		self.feeds.append(feed)

	def removed_feed(self, index):
		'''Remove CameraFeed ojbect from list'''
		self.feeds.pop(index)

	def display_feeds(self, screen):
		'''Display all the camera feeds on the screen'''
		for cam in self.feeds:
			cam.display_feed(screen)

	def release_feeds(self):
		'''Release (shut down) all the camera feeds'''
		for cam in self.feeds:
			cam.release()

	def swap_feeds(self):
		'''Swaps the positions and dimensions of the two CameraFeeds'''
		self.feeds[0].coords, self.feeds[1].coords = self.feeds[1].coords, self.feeds[0].coords # Swap coords (position)
		self.feeds[0].dim, self.feeds[1].dim = self.feeds[1].dim, self.feeds[0].dim # Swap dimensions
		self.feeds = self.feeds[::-1] # Reverse list order
	
	def cycle_mode(self):
		# Iterate mode number
		self.mode += 1

		# Loop back over if required
		if self.mode > 1: self.mode = 0

		if self.mode == 0:
			# Side-by-side
			self.feeds[0].coords, self.feeds[0].dim = (80, 90), (550, 400)
			self.feeds[1].coords, self.feeds[1].dim = (628, 90), (550, 400)
		elif self.mode == 1:
			# Enlarged
			self.feeds[0].coords, self.feeds[0].dim = (80, 90), (850, 550)
			self.feeds[1].coords, self.feeds[1].dim = (928, 90), (250, 200)