import subprocess
import cv2
import numpy as np
import threading
import time
import sys
import tbroLib.Output

class stream:
    process=None
    frame=None
    host=None
    num_frames=0
    connected=False
    def __init__(self,host,name,port,out,width,height,stereo=False):
        self.out=out
        self.host=host
        self.name=name
        self.port=port
        self.width=width
        self.height=height
        self.stereo=stereo
        if stereo:
            self.width*=2
        out.write("STREAM",f"INFO  : Added {self.width}x{self.height} camera stream \"{self.name}\" from {host}:{port}")
        self.start()
        self.watchdog_thread=threading.Thread(target=self.daemon,daemon=True)
        self.watchdog_thread.start()
        self.daemon_thread=threading.Thread(target=self.watchdog,daemon=True)
        self.daemon_thread.start()
    def running(self):
        if self.process.poll() is None:
            return True
        else:
            return False
    def watchdog(self):
        while True:
            # time.sleep(5)
            for line in self.process.stderr.readlines():
                # self.out.write("STATUS",f"INFO  : {line.decode().strip()}")
                if f"{self.host}:{self.port} failed" in line.decode().lower():
                    self.connected=False
                    self.stop()
                    self.out.write("STREAM",f"ERROR : {line.decode().strip()}")
                if "Successfully connected" in line.decode():
                    self.connected=True
                    self.out.write("STREAM",f"INFO  : Connected {self.name} at {self.host}:{self.port}")
            if not self.running():
                print(f"{self.name} Stopped")
                self.start()
            else:
                time.sleep(5)
                if self.connected:
                    self.out.write("STREAM",f"STATUS: {self.name} {self.num_frames/5}fps")
                    self.num_frames=0
                else:
                    self.stop()
    def daemon(self):
        while True:
            if self.connected:
                cv2.waitKey(1)
                try:
                    self.read()
                    self.display()
                    self.num_frames+=1
                except Exception as e:
                    self.out.write("EXCEPT",e)
    def start(self):
        command = ['ffmpeg.exe',
            '-hide_banner',
            '-loglevel','debug',
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
            self.stop()
        except:
            pass
        self.out.write("STREAM",f"INFO: Starting {self.name}")
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def read(self):
        if self.process.stdout.readable():
            raw_frame = self.process.stdout.read(self.width*self.height*3)
            if len(raw_frame)>0:
                self.frame=np.frombuffer(raw_frame, np.uint8).reshape((self.height, self.width, 3))
        return self.frame
    def display(self):
        if (not self.frame is None):
            cv2.imshow(self.name, self.frame)
    def stop(self):
        self.process.stdout.close()  # Closing stdout terminates FFmpeg sub-process.
        self.process.kill()
        # self.process.wait()  # Wait for FFmpeg sub-process to finish

# cameras=[
#     camera("Stereo",8081,1296,972,stereo=True),
#     camera("USB",8082,640,480)
#     ]

# camthreads=[]



# for cam in cameras:
#     camthreads.append(threading.Thread(target=runcamera,args=(cam,),daemon=True))

# for thread in camthreads:
#     thread.start()

# def stop():
#     cv2.destroyAllWindows()
#     sys.exit()

# while True:
#     try:
#         running=0
#         for thread in camthreads:
#             if thread.is_alive():
#                 running+=1
#         if running==0:
#             stop()
#         time.sleep(.3)
#     except KeyboardInterrupt:
#         stop()