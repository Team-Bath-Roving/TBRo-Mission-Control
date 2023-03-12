import subprocess
import cv2
import numpy as np
import threading
import time
import sys

class camera:
    process=None
    host="stereocam"
    frame=None
    def __init__(self,name,host,type,port,width,height,stereo=False):
        self.name=name
        self.host=host
        self.port=port
        self.type=type
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
        options=""
        if self.type=="udp":
            options="?buffer_size=10000"
        else:
            options="?tcp_nodelay=1"
        command = ['ffmpeg.exe',
            '-hide_banner',
            '-probesize','500000',
            '-analyzeduration','0',
            '-flags', 'low_delay',
            '-strict','experimental',
            '-hwaccel','auto',
            '-i', f'{self.type}://{self.host}:{self.port}{options}',
            '-vf',f"scale={self.width}:{self.height}",
            '-fflags', "nobuffer",
            '-f', 'rawvideo',      # Get rawvideo output format.
            '-pix_fmt', 'bgr24',   # Set BGR pixel format
            'pipe:']
        try:
            self.process.kill()
        except:
            pass
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    def read(self):
        raw_frame = self.process.stdout.read(self.width*self.height*3)
        self.frame= np.frombuffer(raw_frame, np.uint8).reshape((self.height, self.width, 3))
        return self.frame
    def display(self):
        cv2.imshow(self.name, self.read())
    def stop(self):
        self.process.stdout.close()  # Closing stdout terminates FFmpeg sub-process.
        self.process.wait()  # Wait for FFmpeg sub-process to finish



def stop():
    cv2.destroyAllWindows()
    sys.exit()

def runcamera(cam):
    cam.start()
    while True:
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
        if not cam.running():
            cam.stop()
            cam.start()
        try:
            cam.read()
            # cam.display()
        except:
            pass
    cam.stop()


cameras=[
        camera("Stereo","stereocam","tcp",8081,640,480,stereo=True),
        # camera("Stereo","127.0.0.1","udp",8081,640,480,stereo=True),
        # camera("USB","stereocam","tcp",8082,640,480),
        camera("USB","127.0.0.1","udp",8082,640,480)
        ]

camthreads=[]

def runCams():
    while True:
        try:
            running=0
            for thread in camthreads:
                if thread.is_alive():
                    running+=1
            if running<2:
                stop()
            time.sleep(.3)
        except KeyboardInterrupt:
            stop()
            break

daemon_thread=None

def startCams():
    for cam in cameras:
        camthreads.append(threading.Thread(target=runcamera,args=(cam,),daemon=True))

    for thread in camthreads:
        thread.start()

    daemon_thread=threading.Thread(target=runCams,daemon=True)

