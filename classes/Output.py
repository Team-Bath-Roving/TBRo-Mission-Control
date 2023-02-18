# from classes.Comms import Comms
import colorama
from colorama import Fore

PREFIX={
	"INFO"   :(Fore.GREEN,Fore.WHITE),
	"WARN"   :(Fore.YELLOW,Fore.WHITE),
	"ERROR"  :(Fore.RED,Fore.WHITE),
	"EXCEPT" :(Fore.MAGENTA,Fore.WHITE),
	"TCP"    :(Fore.CYAN,Fore.WHITE),
	"SERIAL" :(Fore.BLUE,Fore.WHITE),
	"PING"	 :(Fore.LIGHTBLACK_EX,Fore.WHITE),
}

def colorise(msg:str):
	for prefix,colour in PREFIX.items():
		msg=msg.replace(prefix,colour[0]+prefix+colour[1])
	return msg
# output class for printing to terminal and over TCP
class Output:
	# Output prefixes
	comms=None
	def assignTCP(self,comms):
		self.comms=comms
	def write(self,prefix:str,msg:str,tcp=False):
		# print(msg)
		print(colorise(f"{prefix.ljust(6)}: {msg}"))
		if tcp:
			try:
				self.comms.send({prefix:msg}) # formatted as a JSON key:val pair
			except:
				pass