import io
import time
import fcntl
import socket
import struct
from picamera2 import Picamera2,Preview
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from picamera2.encoders import Quality
from threading import Condition
import threading
from Led import *
from Servo import *
from Thread import *
from Buzzer import *
from Control import *
from ADC import *
from Ultrasonic import *
from Command import COMMAND as cmd
import yaml
import logging
logging.basicConfig(level = logging.INFO)

VIDEO_CONFIG_PATH = "./config/video.yml"
ROBOT_CONFIG_PATH = "./config/robot.yml"
HOST_IP = "0.0.0.0" # Any interface
IMAGE_QUALITY = 90
ENCODING='utf-8'

class StreamingOutput(io.BufferedIOBase):

    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class Server:

    def __init__(self):
        self.tcp_flag=False
        self.led=Led()
        self.adc=ADC()
        self.servo=Servo()
        self.buzzer=Buzzer()
        self.control=Control()
        self.sonic=Ultrasonic()
        self.control.Thread_conditiona.start()
        self.start()

    def start(self):
        self.server_socket = socket.socket()
        self._set_socket(self.server_socket, VIDEO_CONFIG_PATH)
        self.server_socket1 = socket.socket()
        self._set_socket(self.server_socket1, ROBOT_CONFIG_PATH)
        self.tcp_flag=True
        self._start_video_thread()
        self._start_instruction_thread()
        logging.info('Server listening... ')
        
    def _set_socket(self,socket_to_assign, config_path: str):
        socket_to_assign.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
        self._set_port(socket_to_assign, config_path, HOST_IP)

    def _set_port(self, socket_to_assign, config_path: str, ip: str):
        with open(config_path, 'r') as stream:
            data_loaded = yaml.safe_load(stream)
            socket_to_assign.bind((ip, data_loaded['port']))
            socket_to_assign.listen(1)
            
    def _start_video_thread(self):
        self.video_thread = threading.Thread(target=self._transmission_video)
        self.video_thread.start()
        
    def _start_instruction_thread(self):
        self.instruction_thread = threading.Thread(target=self._receive_instruction)
        self.instruction_thread.start()
    
    def _reset_server(self):
        self.stop()
        self.start()
        self._start_video_thread()
        self._start_instruction_thread()

    def send_data(self,connect,data: str):
        try:
            connect.send(data.encode(ENCODING))
        except Exception as e:
            print(e)

    def _transmission_video(self):
        try:
            self.connection, _ = self.server_socket.accept()
            self.connection=self.connection.makefile('wb')
        except:
            pass
        self.server_socket.close()
        logging.info("socket video connected... ")
        camera = self._get_camera_config(VIDEO_CONFIG_PATH)
        output = StreamingOutput()
        encoder = JpegEncoder(q=IMAGE_QUALITY)
        camera.start_recording(encoder, FileOutput(output),quality=Quality.VERY_HIGH)
        self._stream_video(output,camera)
        
    def _stream_video(self,output: StreamingOutput,camera: Picamera2):
        while True:
            with output.condition:
                output.condition.wait()
                frame = output.frame
            try:                
                lenFrame = len(output.frame) 
                lengthBin = struct.pack('<I', lenFrame)
                self.connection.write(lengthBin)
                self.connection.write(frame)
            except Exception as e:
                logging.error(e)
                camera.stop_recording()
                camera.close()
                logging.info("End transmit ... " )
                break

    def _get_camera_config(self, config_path: str) -> Picamera2:
        camera = Picamera2()
        with open(config_path, 'r') as stream:
            data_loaded = yaml.safe_load(stream)
            camera.framerate = data_loaded['framerate']
            camera.resolution = (data_loaded['height'], data_loaded['width'])
            camera.image_effect = data_loaded['effect']
        return camera

    def _receive_instruction(self):
        try:
            self.connection1, _ = self.server_socket1.accept()
            print ("Client connection successful !")
        except:
            print ("Client connect failed")
            self.server_socket1.close()
        
        while True:
            try:
                allData=self.connection1.recv(1024).decode(ENCODING)
            except:
                if self.tcp_flag:
                    self._reset_server()
                    break
                else:
                    break
            if allData=="" and self.tcp_flag:
                self._reset_server()
                break
            else:
                cmdArray=allData.split('\n')
                print(cmdArray)
                if cmdArray[-1] !="":
                    cmdArray==cmdArray[:-1]
            for oneCmd in cmdArray:
                data=oneCmd.split("#")
                if data==None or data[0]=='':
                    continue
                elif cmd.CMD_BUZZER in data:
                    self.buzzer.run(data[1])
                elif cmd.CMD_POWER in data:
                    try:
                        batteryVoltage=self.adc.batteryPower()
                        command=cmd.CMD_POWER+"#"+str(batteryVoltage[0])+"#"+str(batteryVoltage[1])+"\n"
                        self.send_data(self.connection1,command)
                        if batteryVoltage[0] < 5.5 or batteryVoltage[1]<6:
                         for i in range(3):
                            self.buzzer.run("1")
                            time.sleep(0.15)
                            self.buzzer.run("0")
                            time.sleep(0.1)
                    except:
                        pass
                elif cmd.CMD_LED in data:
                    try:
                        stop_thread(thread_led)
                    except:
                        pass
                    thread_led=threading.Thread(target=self.led.light,args=(data,))
                    thread_led.start()   
                elif cmd.CMD_LED_MOD in data:
                    try:
                        stop_thread(thread_led)
                    except:
                        pass
                    thread_led=threading.Thread(target=self.led.light,args=(data,))
                    thread_led.start()
                elif cmd.CMD_SONIC in data:
                    command=cmd.CMD_SONIC+"#"+str(self.sonic.getDistance())+"\n"
                    self.send_data(self.connection1,command)
                elif cmd.CMD_HEAD in data:
                    if len(data)==3:
                        self.servo.setServoAngle(int(data[1]),int(data[2]))
                elif cmd.CMD_CAMERA in data:
                    if len(data)==3:
                        x=self.control.restriction(int(data[1]),50,180)
                        y=self.control.restriction(int(data[2]),0,180)
                        self.servo.setServoAngle(0,x)
                        self.servo.setServoAngle(1,y)
                elif cmd.CMD_RELAX in data:
                    if self.control.relax_flag==False:
                        self.control.relax(True)
                        self.control.relax_flag=True
                    else:
                        self.control.relax(False)
                        self.control.relax_flag=False
                elif cmd.CMD_SERVOPOWER in data:
                    if data[1]=="0":
                        GPIO.output(self.control.GPIO_4,True)
                    else:
                        GPIO.output(self.control.GPIO_4,False)
                else:
                    self.control.order=data
                    self.control.timeout=time.time()
        try:
            stop_thread(thread_led)
        except:
            pass
        try:
            stop_thread(thread_sonic)
        except:
            pass
        logging.info("close_recv")

    def stop(self):
        self.tcp_flag=False
        try:
            stop_thread(self.video_thread)
            stop_thread(self.instruction_thread)
            self.connection.close()
            self.connection1.close()
        except :
            logging.warning("No client connection")