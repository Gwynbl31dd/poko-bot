# -*- coding: utf-8 -*-
import os
import sys,getopt
from Server import *
from Control import *

class Robot():

    def __init__(self):
        self.server=Server()
        self.server.turn_on_server()
        self.server.tcp_flag=True
        self.video=threading.Thread(target=self.server.transmission_video)
        self.video.start()
        self.instruction=threading.Thread(target=self.server.receive_instruction)
        self.instruction.start()

    def start_server(self):
        self.server.turn_on_server()
        self.server.tcp_flag=True
        self.video=threading.Thread(target=self.server.transmission_video)
        self.video.start()
        self.instruction=threading.Thread(target=self.server.receive_instruction)
        self.instruction.start()

    def stop_server(self):
        self.server.tcp_flag=False
        try:
            stop_thread(self.video)
            stop_thread(self.instruction)
            self.server.server_socket.shutdown(2)
            self.server.server_socket1.shutdown(2)
        except Exception as e:
            print(e)
        
if __name__ == '__main__':
    try:
        robot = Robot()
        robot.start_server()
        while True:
            pass
    except KeyboardInterrupt:
        robot.stop_server()
        os._exit(0)
