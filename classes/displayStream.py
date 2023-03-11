import subprocess
import cv2
import numpy as np
import threading
import time
import sys

class camera:
    process=None
    host="stereocam"
    def __init__(self,name,port,width,height,stereo=False):
        self.name=name
        self.port=port
        self.width=width
        self.height=height
        self.stereo=stereo
        if stereo:
            self.width*=2
    def running(self):
        if not self.process.poll() is None:
            return False
        else:
            return True
    def start(self):
        command = ['ffmpeg.exe',
            '-hide_banner',
            '-probesize','32',
            '-analyzeduration','0',
            '-flags', 'low_delay',
            '-strict','experimental',
            '-hwaccel','auto',
            '-i', f'tcp://{self.host}:{self.port}',
            '-vf',f"scale={self.width}:{self.height}",
            '-fflags', "nobuffer",
            '-f', 'rawvideo',      # Get rawvideo output format.
            '-pix_fmt', 'bgr24',   # Set BGR pixel format
            'pipe:']
        try:
            self.process.kill()
        except:
            pass
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    def read(self):
        raw_frame = self.process.stdout.read(self.width*self.height*3)
        return np.frombuffer(raw_frame, np.uint8).reshape((self.height, self.width, 3))
    def display(self):
        cv2.imshow(self.name, self.read())
    def stop(self):
        self.process.stdout.close()  # Closing stdout terminates FFmpeg sub-process.
        self.process.wait()  # Wait for FFmpeg sub-process to finish

cameras=[
    camera("Stereo",8081,1296,972,stereo=True),
    camera("USB",8082,640,480)
    ]

camthreads=[]

def runcamera(cam):
    cam.start()
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if not cam.running():
            cam.start()
        try:
            cam.display()
        except:
            pass
    cam.stop()


for cam in cameras:
    camthreads.append(threading.Thread(target=runcamera,args=(cam,),daemon=True))

for thread in camthreads:
    thread.start()

def stop():
    cv2.destroyAllWindows()
    sys.exit()

while True:
    try:
        running=0
        for thread in camthreads:
            if thread.is_alive():
                running+=1
        if running==0:
            stop()
        time.sleep(.3)
    except KeyboardInterrupt:
        stop()