import io
import time
import fcntl
import socket
import struct
from picamera2 import Picamera2
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
from Command import COMMAND
import yaml
import logging
import traceback

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
        self.tcp_flag=True
        self.led=Led()
        self.adc=ADC()
        self.servo=Servo()
        self.buzzer=Buzzer()
        self.control=Control()
        self.sonic=Ultrasonic()
        self.control.Thread_conditiona.start()
        self.start()

    def start(self):
        self.video_socket = socket.socket()
        self._set_socket(self.video_socket, VIDEO_CONFIG_PATH)
        self.robot_socket = socket.socket()
        self._set_socket(self.robot_socket, ROBOT_CONFIG_PATH)
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
        logging.info("start instruction thread")
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
            logging.error(e)

    def _transmission_video(self):
        logging.info("Video thread started...")
        try:
            self.video_connection, _ = self.video_socket.accept()
            self.video_connection = self.video_connection.makefile('wb')
            logging.info("socket video connected... ")
        except Exception as e:
            logging.error(e)
        
        self.video_socket.close()
        logging.info("socket video connected... ")
        self.camera = self._get_camera_config(VIDEO_CONFIG_PATH)
        output = StreamingOutput()
        encoder = JpegEncoder(q=IMAGE_QUALITY)
        self.camera.start_recording(encoder, FileOutput(output),quality=Quality.VERY_HIGH)
        self._stream_video(output)
        
    def _stream_video(self,output: StreamingOutput):
        while True:
            with output.condition:
                output.condition.wait()
                frame = output.frame
            try:                
                lenFrame = len(output.frame) 
                lengthBin = struct.pack('<I', lenFrame)
                self.video_connection.write(lengthBin)
                self.video_connection.write(frame)
            except Exception as e:
                logging.error(e)
                self._stop_camera()
                logging.info("End transmit ... " )
                break
            
    def _stop_camera(self):
        self.camera.stop_recording()
        self.camera.close()

    def _get_camera_config(self, config_path: str) -> Picamera2:
        camera = Picamera2()
        with open(config_path, 'r') as stream:
            data_loaded = yaml.safe_load(stream)
            camera.framerate = data_loaded['framerate']
            camera.resolution = (data_loaded['height'], data_loaded['width'])
            camera.image_effect = data_loaded['effect']
        return camera
            
    def _receive_instruction(self):
        logging.info("Instruction thread started...")
        self._accept_instructions()
        try:
            logging.info("process_instruction")
            self._process_instruction()
        except:
            traceback.print_exc()
            if self.tcp_flag:
                self._reset_server()
                
        logging.info("close_recv")
        
    def _accept_instructions(self):
        try:
            self.robot_connection, _ = self.robot_socket.accept()
            logging.info("Client connection successful !")
        except:
            logging.error("Client connect failed")
            self.robot_socket.close()
            
    def _split_instructions(self, instruction_data: str) -> list:
        commands = instruction_data.split('\n')
        logging.info(f"commands {commands}")
        if commands[-1] != "":
            commands = commands[:-1]
        return commands
            
    def _process_instruction(self):
        while True:
            instruction_data=self._read_data()
            commands=self._split_instructions(instruction_data)
            for instruction in commands:
                data=instruction.split("#")
                if data==None or data[0]=='':
                    continue
                instruction_type = data[0]
                if COMMAND.CMD_BUZZER == instruction_type:
                    self.buzzer.run(data[1])
                elif COMMAND.CMD_POWER == instruction_type:
                    try:
                        batteryVoltage=self.adc.batteryPower()
                        command=COMMAND.CMD_POWER+"#"+str(batteryVoltage[0])+"#"+str(batteryVoltage[1])+"\n"
                        self.send_data(self.robot_connection,command)
                        if batteryVoltage[0] < 5.5 or batteryVoltage[1]<6:
                            for i in range(3):
                                self.buzzer.run("1")
                                time.sleep(0.15)
                                self.buzzer.run("0")
                                time.sleep(0.1)
                    except:
                        pass
                elif COMMAND.CMD_LED == instruction_type:
                    try:
                        stop_thread(thread_led)
                    except:
                        pass
                    thread_led=threading.Thread(target=self.led.light,args=(data,))
                    thread_led.start()   
                elif COMMAND.CMD_LED_MOD == instruction_type:
                    try:
                        stop_thread(thread_led)
                    except:
                        pass
                    thread_led=threading.Thread(target=self.led.light,args=(data,))
                    thread_led.start()
                elif COMMAND.CMD_SONIC == instruction_type:
                    command=COMMAND.CMD_SONIC+"#"+str(self.sonic.getDistance())+"\n"
                    self.send_data(self.robot_connection,command)
                elif COMMAND.CMD_HEAD == instruction_type:
                    if len(data)==3:
                        self.servo.setServoAngle(int(data[1]),int(data[2]))
                elif COMMAND.CMD_CAMERA == instruction_type:
                    if len(data)==3:
                        x=self.control.restriction(int(data[1]),50,180)
                        y=self.control.restriction(int(data[2]),0,180)
                        self.servo.setServoAngle(0,x)
                        self.servo.setServoAngle(1,y)
                elif COMMAND.CMD_RELAX == instruction_type:
                    if self.control.relax_flag==False:
                        self.control.relax(True)
                        self.control.relax_flag=True
                    else:
                        self.control.relax(False)
                        self.control.relax_flag=False
                elif COMMAND.CMD_SERVOPOWER == instruction_type:
                    if data[1]=="0":
                        GPIO.output(self.control.GPIO_4,True)
                    else:
                        GPIO.output(self.control.GPIO_4,False)
                else:
                    self.control.order=data
                    self.control.timeout=time.time()
                    
    def _read_data(self) -> str:
        try:
            data=self.robot_connection.recv(1024).decode(ENCODING)
            if data=="":
                raise Exception("Client disconnected")
            return data
        except Exception as e:
            logging.error(e)
            raise e

    def stop(self):
        self.tcp_flag=False
        try:
            stop_thread(self.video_thread)
            self.video_connection.close()
            self._stop_camera()
            stop_thread(self.instruction_thread)
            self.robot_connection.close()
        except :
            logging.warning("No client connection")