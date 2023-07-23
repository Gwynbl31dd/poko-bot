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

    def turn_on_server(self):
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
        self._set_port(self.server_socket, VIDEO_CONFIG_PATH, HOST_IP)
        self.server_socket1 = socket.socket()
        self.server_socket1.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
        self._set_port(self.server_socket1, ROBOT_CONFIG_PATH, HOST_IP)
        logging.info('Server address: '+HOST_IP)

    def _set_port(self, socket_to_assign, config_path: str, ip: str):
        with open(config_path, 'r') as stream:
            data_loaded = yaml.safe_load(stream)
            socket_to_assign.bind((ip, data_loaded['port']))
            socket_to_assign.listen(1)
    
    def _reset_server(self):
        self.turn_off_server()
        self.turn_on_server()
        self.video=threading.Thread(target=self._transmission_video)
        self.instruction=threading.Thread(target=self.receive_instruction)
        self.video.start()
        self.instruction.start()

    def send_data(self,connect,data):
        try:
            connect.send(data.encode('utf-8'))
        except Exception as e:
            print(e)

    def _transmission_video(self):
        try:
            self.connection, _ = self.server_socket.accept()
            self.connection=self.connection.makefile('wb')
        except:
            pass
        self.server_socket.close()
        logging.info("socket video connected ... ")
        camera = self._get_camera_config(VIDEO_CONFIG_PATH)
        output = StreamingOutput()
        encoder = JpegEncoder(q=90)
        camera.start_recording(encoder, FileOutput(output),quality=Quality.VERY_HIGH)
        self._send_video(output,camera)
        

    def _send_video(self,output,camera: Picamera2):
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

    def receive_instruction(self):
        try:
            self.connection1, _ = self.server_socket1.accept()
            print ("Client connection successful !")
        except:
            print ("Client connect failed")
        self.server_socket1.close()
        
        while True:
            try:
                allData=self.connection1.recv(1024).decode('utf-8')
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

    def turn_off_server(self):
        try:
            self.connection.close()
            self.connection1.close()
        except :
            logging.warning('\n'+"No client connection")
