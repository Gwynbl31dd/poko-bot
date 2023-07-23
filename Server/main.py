#!/usr/bin/env python3

import os
import sys,getopt
from Server import *
from Control import *
import logging

class App():

    def __init__(self):
        self.server=Server()
        self.start_server()

    def start_server(self):
        self.server.turn_on_server()
        self.server.tcp_flag=True
        self.video=threading.Thread(target=self.server._transmission_video)
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
            logging.warning(e)
        
if __name__ == '__main__':
    try:
        app = App()
        app.start_server()
        while True:
            pass
    except KeyboardInterrupt:
        app.stop_server()
        os._exit(0)
